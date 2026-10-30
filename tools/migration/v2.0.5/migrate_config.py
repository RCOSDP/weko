#!/usr/bin/env python3
"""Migrate the configuration of a WEKO site from feature/a11y to v2.0.5.

The site's files are merged with the files of the two code versions:

* base:   the file as shipped with the code the site runs now
          (default: ``git show origin/feature/a11y_pre:PATH``)
* site:   the file the site actually uses
* target: the file as shipped with v2.0.5
          (default: ``git show origin/develop_v2.0.5:PATH``)

Subcommands:

``instance-cfg``
    Merges ``scripts/instance.cfg`` key by key. A key the site changed
    keeps the site's value; every other key takes the v2.0.5 value. Keys
    whose meaning changed in v2.0.5 are handled as listed in this module
    and reported.
``merge``
    Three-way merges any other text file (nginx/weko.conf,
    docker-compose2.yml, ...) with ``git merge-file``. Conflicts are left
    as diff3 markers and reported.
``check-env``
    Renders ``instance.cfg`` the way ``jinja2`` in the entrypoints does,
    with the variables of an env file or a Kubernetes ConfigMap/Secret,
    and checks that every variable is set and that the result is valid
    Python.

Only the standard library is used, so the script runs on the operator's
host with Python 3.6 or later.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

DEFAULT_BASE_REF = 'origin/feature/a11y_pre'
DEFAULT_TARGET_REF = 'origin/develop_v2.0.5'

KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=]*)?=(?!=)')
ENVIRON_RE = re.compile(
    r"""\{\{\s*environ\(\s*(['"])([A-Za-z_][A-Za-z0-9_]*)\1\s*\)"""
    r"""\s*(?:or\s*(['"])(.*?)\3\s*)?\}\}""")

# Keys whose v2.0.5 default would silently change the behaviour of a site
# that never set them: the old default is written out explicitly.
KEEP_OLD_DEFAULT = {
    'WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED':
        'the default changed from True to False; at startup v2.0.5 also '
        'overwrites shib_login_enable in admin_settings with this value',
}

# Keys whose value format changed: a site value written for the old code
# is not carried over.
INCOMPATIBLE_SITE_VALUE = {
    'WEKO_WORKFLOW_ACCESS_ACTIVITY_URL':
        'now the id of a row in mail_templates instead of a .tpl file name; '
        'move the customised text to the mail template in the admin screen',
    'WEKO_WORKFLOW_REQUEST_FOR_REGISTER_USAGE_REPORT':
        'now the id of a row in mail_templates instead of a .tpl file name; '
        'move the customised text to the mail template in the admin screen',
}

# Keys that v2.0.5 no longer reads.
REMOVED_KEYS = {
    'WEKO_WORKFLOW_USAGE_REPORT_ACTIVITY_URL',
    'WEKO_WORKFLOW_APPROVE_DONE',
    'WEKO_WORKFLOW_APPROVE_REJECTED',
    'WEKO_WORKFLOW_REQUEST_APPROVAL',
    'WEKO_DEPOSIT_ES_PARSING_ERROR_KEYWORD',
    'WEKO_DEPOSIT_ES_PARSING_ERROR_PROCESS_ENABLE',
    'WEKO_MAX_FILE_SIZE_FOR_ES',
    'WEKO_ITEMS_UI_EXPORT_FORMAT_JSON',
}

# Misspelled keys. invenio_s3 lets a misspelled key override the correct
# one whenever it is defined, even as None, so the misspelled keys are
# removed and their values moved to the correct names.
TYPO_KEYS = {
    'S3_ACCCESS_KEY_ID': 'S3_ACCESS_KEY_ID',
    'S3_SECRECT_ACCESS_KEY': 'S3_SECRET_ACCESS_KEY',
}

# Defaults in v2.0.5 that point to test services or need a site value.
REVIEW_TARGET_DEFAULT = {
    'WEKO_ACCOUNTS_WAYF_URL': 'points to the GakuNin test discovery service',
    'WEKO_ACCOUNTS_WAYF_ADDITIONAL_IDPS': 'lists the Orthros test IdP',
    'WEKO_ACCOUNTS_GAKUNIN_MAP_BASE_URL': 'points to the GakuNin mAP test server',
    'WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_BASE_URL':
        'points to the researchmap trial API',
    'WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_HOST':
        'points to the researchmap trial API',
    'WEKO_ACCOUNTS_REAL_IP':
        'None trusts X-Real-IP / X-Forwarded-For sent by the client',
    'WEKO_NOTIFICATIONS_INBOX_ADDRESS': 'address of the inbox service',
}

# Module defaults (config.py, not instance.cfg) that changed between the
# versions. A site that does not set the key gets the new behaviour.
MODULE_DEFAULT_CHANGES = {
    'SECURITY_RECOVERABLE': ('True', 'False',
                             'password reset by e-mail is disabled'),
    'SECURITY_REGISTERABLE': ('True', 'False', 'sign-up is disabled'),
    'THEME_LOGO': ("'images/weko-logo.png'", "'images/jairocloud-logo.png'",
                   'the default logo changed'),
    'THEME_LOGO_ADMIN': ("'images/weko-logo.png'",
                         "'images/jairocloud-logo.png'",
                         'the default admin logo changed'),
    'WEKO_SEARCH_UI_BULK_EXPORT_LIMIT': ('1000', '300', ''),
    'WEKO_SEARCH_UI_BULK_EXPORT_EXPIRED_TIME': ('3', '1440', ''),
    'WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF': ('False', 'True', ''),
    'OAUTH2_CACHE_TYPE': ("'redissentinel'", "'redis'", ''),
}

CARRY_OVER_HEADER = (
    '\n# ---------------------------------------------------------------\n'
    '# Settings carried over from the previous instance.cfg that the\n'
    '# v2.0.5 instance.cfg does not define.\n'
    '# ---------------------------------------------------------------\n'
)


class Segment(object):
    """A top-level statement of a config file, with the key it assigns."""

    def __init__(self, key, text):
        self.key = key
        self.text = text

    def normalized(self):
        """Text without trailing spaces and trailing blank lines."""
        lines = [line.rstrip() for line in self.text.splitlines()]
        while lines and not lines[-1]:
            lines.pop()
        return '\n'.join(lines)


def parse_segments(text):
    """Split a Python-like config file into top-level segments.

    A segment starts at a line in column 0 that is not blank, not a comment
    and not a closing bracket, and runs to the next such line. Comments and
    blank lines in column 0 are segments of their own (key None), so the
    layout of the target file is kept. Placeholders like ``{{ environ(..) }}``
    outside strings make the file invalid Python, hence no ``ast``.
    """
    segments = []
    current = None
    for line in text.splitlines(True):
        starts = (line[:1] not in ('', ' ', '\t', '\n', '\r', ')', ']', '}')
                  and not line.startswith('#'))
        if current is not None and current.key is not None and not starts \
                and not line.startswith('#') and line.strip():
            current.text += line
            continue
        if starts:
            match = KEY_RE.match(line)
            current = Segment(match.group(1) if match else None, line)
        else:
            current = Segment(None, line)
        segments.append(current)
    return segments


def last_by_key(segments):
    """Map each key to its last segment (the one Python keeps)."""
    result = {}
    for seg in segments:
        if seg.key:
            result[seg.key] = seg
    return result


def rename_key(seg, new_key):
    return Segment(new_key, re.sub(r'^' + re.escape(seg.key), new_key,
                                   seg.text, count=1))


def ensure_newline(text):
    return text if text.endswith('\n') else text + '\n'


def merge_instance_cfg(base_text, site_text, target_text):
    """Merge instance.cfg key by key.

    Returns (merged_text, report) where report is a list of
    (level, key, message) tuples; level is INFO, WARN or ACTION.
    """
    base = last_by_key(parse_segments(base_text))
    site = last_by_key(parse_segments(site_text))
    target_segments = parse_segments(target_text)
    target = last_by_key(target_segments)
    report = []
    replace = {}
    appended = []

    for key, seg in site.items():
        if key in TYPO_KEYS:
            continue
        in_base, in_target = key in base, key in target
        customised = (not in_base) or seg.normalized() != base[key].normalized()
        if in_target:
            if not customised:
                if key in KEEP_OLD_DEFAULT and \
                        base[key].normalized() != target[key].normalized():
                    replace[key] = seg
                    report.append(('WARN', key, 'kept the previous value: '
                                   + KEEP_OLD_DEFAULT[key]))
                continue
            if seg.normalized() == target[key].normalized():
                continue
            if key in INCOMPATIBLE_SITE_VALUE:
                report.append(('ACTION', key, 'site value NOT carried over: '
                               + INCOMPATIBLE_SITE_VALUE[key]))
                continue
            replace[key] = seg
            if in_base and base[key].normalized() != target[key].normalized():
                report.append(('WARN', key, 'carried over the site value, but '
                               'v2.0.5 also changed this setting; review it'))
            else:
                report.append(('INFO', key, 'carried over the site value'))
        else:
            if key in REMOVED_KEYS:
                if customised:
                    report.append(('WARN', key, 'not used by v2.0.5; the site '
                                   'value is dropped'))
                continue
            if in_base and not customised:
                report.append(('INFO', key, 'removed from the v2.0.5 '
                               'instance.cfg; dropped'))
                continue
            appended.append(seg)
            report.append(('INFO', key, 'not in the v2.0.5 instance.cfg; '
                           'appended at the end'))

    for key in base:
        if key not in site and key in target:
            report.append(('WARN', key, 'the site had removed this setting; '
                           'the v2.0.5 value is used'))

    # Misspelled S3 keys: the site value goes to the correct key.
    typo_values = {}
    for typo, correct in TYPO_KEYS.items():
        seg = site.get(typo)
        customised = seg is not None and (
            typo not in base or seg.normalized() != base[typo].normalized())
        if customised and correct not in site:
            typo_values[correct] = rename_key(seg, correct)
            report.append(('INFO', typo, 'site value moved to ' + correct))

    out = []
    defined = set()
    for seg in target_segments:
        if seg.key in TYPO_KEYS:
            correct = TYPO_KEYS[seg.key]
            if correct not in target and correct not in defined:
                new = typo_values.get(correct) or rename_key(seg, correct)
                out.append(ensure_newline(new.text))
                defined.add(correct)
            report.append(('INFO', seg.key, 'misspelled key removed'))
            continue
        if seg.key and seg.key in typo_values:
            seg = typo_values.pop(seg.key)
        elif seg.key and seg.key in replace and target[seg.key] is seg:
            seg = replace[seg.key]
        if seg.key:
            defined.add(seg.key)
        out.append(ensure_newline(seg.text) if seg.key else seg.text)

    tail = list(typo_values.values()) + appended
    if tail:
        out.append(CARRY_OVER_HEADER)
        for seg in tail:
            out.append(ensure_newline(seg.text))

    merged = ''.join(out)
    merged_keys = last_by_key(parse_segments(merged))
    for key, why in REVIEW_TARGET_DEFAULT.items():
        if key in replace:
            continue
        if key in merged_keys:
            report.append(('ACTION', key, 'check the value: ' + why))
        else:
            report.append(('WARN', key, 'the module default ' + why
                           + '; set it here if the site uses the feature'))
    for key, (old, new, why) in MODULE_DEFAULT_CHANGES.items():
        if key not in merged_keys:
            message = 'module default changed from {} to {}'.format(old, new)
            if why:
                message += ' (' + why + ')'
            message += '; set it here to keep the previous behaviour'
            report.append(('WARN', key, message))
    return merged, report


def git_show(repo, ref, path):
    return subprocess.check_output(
        ['git', '-C', repo, 'show', '{}:{}'.format(ref, path)]
    ).decode('utf-8')


def merge_file(base_text, site_text, target_text):
    """Three-way merge with git merge-file. Returns (text, conflicts)."""
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for name, text in (('site', site_text), ('base', base_text),
                           ('target', target_text)):
            path = os.path.join(tmp, name)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            paths.append(path)
        proc = subprocess.run(
            ['git', 'merge-file', '-p', '--diff3',
             '-L', 'site', '-L', 'base (old code)', '-L', 'v2.0.5'] + paths,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode < 0 or proc.returncode > 127:
            raise RuntimeError(proc.stderr.decode('utf-8'))
        return proc.stdout.decode('utf-8'), proc.returncode


def read_env_file(path):
    """Read KEY=VALUE lines, or the data/stringData of a k8s manifest."""
    env = {}
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    if any(re.match(r'^(data|stringData):\s*$', line) for line in lines):
        in_data = False
        for line in lines:
            if re.match(r'^(data|stringData):\s*$', line):
                in_data = True
                continue
            if in_data and line and not line.startswith((' ', '\t')):
                in_data = False
            match = re.match(r'^\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$', line)
            if in_data and match:
                value = match.group(2).strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                    value = value[1:-1]
                env[match.group(1)] = value
        return env
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[len('export '):]
        key, sep, value = line.partition('=')
        if not sep:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
            value = value[1:-1]
        env[key.strip()] = value
    return env


def render_instance_cfg(text, env):
    """Render like jinja2-cli: environ() is os.environ.get, so a missing
    variable becomes the text None. Returns (rendered, missing names)."""
    missing = []

    def substitute(match):
        name, default = match.group(2), match.group(4)
        if env.get(name):
            return env[name]
        if default is not None:
            return default
        if name in env:
            return ''
        missing.append(name)
        return 'None'

    return ENVIRON_RE.sub(substitute, text), sorted(set(missing))


def check_env(cfg_text, env):
    """Return a report for check-env."""
    report = []
    rendered, missing = render_instance_cfg(cfg_text, env)
    for name in missing:
        report.append(('ACTION', name, 'not set; jinja2 renders it as None'))
    for name in sorted(set(m.group(2) for m in ENVIRON_RE.finditer(cfg_text))):
        value = env.get(name)
        if value is None:
            continue
        if "'" in value or '\\' in value:
            report.append(('ACTION', name, 'the value contains a quote or a '
                           'backslash and breaks the rendered Python'))
        if value.strip() in ('CHANGE ME', 'changeme', '# change me', ''):
            report.append(('ACTION', name, 'still has a placeholder value'))
    try:
        compile(rendered, 'invenio.cfg', 'exec')
    except SyntaxError as err:
        report.append(('ACTION', 'invenio.cfg', 'rendered file is not valid '
                       'Python: line {}: {}'.format(err.lineno, err.msg)))
    return report


def print_report(report, stream):
    order = {'ACTION': 0, 'WARN': 1, 'INFO': 2}
    for level, key, message in sorted(report, key=lambda r: (order[r[0]], r[1])):
        stream.write('{:<6} {}: {}\n'.format(level, key, message))


def load_inputs(args, path):
    def read(p):
        with open(p, encoding='utf-8') as f:
            return f.read()
    base = read(args.base) if args.base else git_show(args.repo, args.base_ref, path)
    target = read(args.target) if args.target else \
        git_show(args.repo, args.target_ref, path)
    return base, read(args.site), target


def write_output(path, text):
    if path == '-':
        sys.stdout.write(text)
        return
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command')

    def add_inputs(p):
        p.add_argument('--site', required=True, help='file the site uses now')
        p.add_argument('--base', help='file of the old code (default: git show)')
        p.add_argument('--target', help='file of v2.0.5 (default: git show)')
        p.add_argument('--repo', default='.', help='WEKO git repository')
        p.add_argument('--base-ref', default=DEFAULT_BASE_REF)
        p.add_argument('--target-ref', default=DEFAULT_TARGET_REF)
        p.add_argument('--out', required=True, help="output file ('-' for stdout)")

    p = sub.add_parser('instance-cfg', help='merge scripts/instance.cfg')
    add_inputs(p)
    p = sub.add_parser('merge', help='three-way merge another file')
    add_inputs(p)
    p.add_argument('--path', required=True,
                   help='path of the file in the repository, e.g. nginx/weko.conf')
    p = sub.add_parser('check-env', help='check the variables of instance.cfg')
    p.add_argument('--cfg', required=True, help='instance.cfg to check')
    p.add_argument('--env', action='append', default=[],
                   help='env file or k8s ConfigMap/Secret YAML (repeatable)')

    args = parser.parse_args(argv)
    if args.command == 'instance-cfg':
        base, site, target = load_inputs(args, 'scripts/instance.cfg')
        merged, report = merge_instance_cfg(base, site, target)
        write_output(args.out, merged)
        print_report(report, sys.stderr)
        return 1 if any(r[0] == 'ACTION' for r in report) else 0
    if args.command == 'merge':
        base, site, target = load_inputs(args, args.path)
        merged, conflicts = merge_file(base, site, target)
        write_output(args.out, merged)
        if conflicts:
            sys.stderr.write('ACTION {}: {} conflict(s); resolve the <<<<<<< '
                             'markers in {}\n'.format(args.path, conflicts,
                                                     args.out))
            return 1
        sys.stderr.write('INFO   {}: merged without conflicts\n'.format(args.path))
        return 0
    if args.command == 'check-env':
        env = {}
        for path in args.env:
            env.update(read_env_file(path))
        with open(args.cfg, encoding='utf-8') as f:
            report = check_env(f.read(), env)
        print_report(report, sys.stderr)
        if not report:
            sys.stderr.write('INFO   all variables are set and the rendered '
                             'file is valid Python\n')
        return 1 if any(r[0] == 'ACTION' for r in report) else 0
    parser.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
