import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import migrate_config as mc  # noqa: E402


def keys(report, level=None):
    return {k for lv, k, _ in report if level is None or lv == level}


def test_parse_segments_keeps_multiline_values_and_comments():
    text = ("# head\n"
            "A = 1\n"
            "B = {\n"
            "    'x': 1,\n"
            "}\n"
            "\n"
            "from x import y\n"
            "C = {{ environ('C') }}\n")
    segs = mc.parse_segments(text)
    assert ''.join(s.text for s in segs) == text
    by_key = mc.last_by_key(segs)
    assert by_key['B'].text == "B = {\n    'x': 1,\n}\n"
    assert by_key['C'].text == "C = {{ environ('C') }}\n"
    assert [s.key for s in segs if s.key] == ['A', 'B', 'C']


def test_site_value_is_carried_over_and_untouched_keys_take_target():
    base = "A = 1\nB = 2\n"
    site = "A = 10\nB = 2\n"
    target = "A = 1\nB = 3\nN = 4\n"
    merged, report = mc.merge_instance_cfg(base, site, target)
    assert merged == "A = 10\nB = 3\nN = 4\n"
    assert ('INFO', 'A', 'carried over the site value') in report


def test_both_changed_is_reported_for_review():
    merged, report = mc.merge_instance_cfg("A = 1\n", "A = 2\n", "A = 3\n")
    assert merged == "A = 2\n"
    assert 'A' in keys(report, 'WARN')


def test_site_only_key_is_appended():
    merged, _ = mc.merge_instance_cfg("A = 1\n", "A = 1\nX = 'site'\n", "A = 1\n")
    assert merged.startswith("A = 1\n")
    assert merged.endswith("X = 'site'\n")
    assert mc.CARRY_OVER_HEADER in merged


def test_key_removed_upstream_and_not_customised_is_dropped():
    merged, report = mc.merge_instance_cfg("A = 1\nOLD = 1\n", "A = 1\nOLD = 1\n",
                                           "A = 1\n")
    assert 'OLD' not in merged
    assert 'OLD' in keys(report, 'INFO')


def test_removed_key_is_dropped_even_if_customised():
    key = 'WEKO_WORKFLOW_APPROVE_DONE'
    merged, report = mc.merge_instance_cfg(key + " = 'a'\n", key + " = 'b'\n", "")
    assert key not in merged
    assert key in keys(report, 'WARN')


def test_shibboleth_login_keeps_old_default():
    key = 'WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED'
    merged, report = mc.merge_instance_cfg(key + " = True\n", key + " = True\n",
                                           key + " = False\n")
    assert merged == key + " = True\n"
    assert key in keys(report, 'WARN')


def test_shibboleth_login_set_by_site_is_kept():
    key = 'WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED'
    merged, _ = mc.merge_instance_cfg(key + " = True\n", key + " = False\n",
                                      key + " = False\n")
    assert merged == key + " = False\n"


def test_incompatible_site_value_is_not_carried_over():
    key = 'WEKO_WORKFLOW_ACCESS_ACTIVITY_URL'
    merged, report = mc.merge_instance_cfg(key + ' = "a.tpl"\n', key + ' = "b.tpl"\n',
                                           key + ' = "1"\n')
    assert merged == key + ' = "1"\n'
    assert key in keys(report, 'ACTION')


def test_misspelled_s3_keys_are_renamed():
    base = "S3_SECRECT_ACCESS_KEY = None\n"
    site = "S3_SECRECT_ACCESS_KEY = 'secret'\n"
    target = "S3_ACCCESS_KEY_ID = None\nS3_SECRET_ACCESS_KEY = None\n"
    merged, _ = mc.merge_instance_cfg(base, site, target)
    assert 'S3_ACCCESS_KEY_ID' not in merged
    assert 'S3_SECRECT_ACCESS_KEY' not in merged
    assert "S3_ACCESS_KEY_ID = None\n" in merged
    assert "S3_SECRET_ACCESS_KEY = 'secret'\n" in merged
    assert merged.count('S3_SECRET_ACCESS_KEY') == 1


def test_module_default_change_is_warned_when_not_set():
    _, report = mc.merge_instance_cfg("", "", "")
    assert 'SECURITY_RECOVERABLE' in keys(report, 'WARN')
    _, report = mc.merge_instance_cfg("", "SECURITY_RECOVERABLE = True\n", "")
    assert 'SECURITY_RECOVERABLE' not in keys(report, 'WARN')


def test_review_target_default():
    key = 'WEKO_ACCOUNTS_WAYF_URL'
    _, report = mc.merge_instance_cfg("", "", key + " = 'https://test'\n")
    assert key in keys(report, 'ACTION')
    _, report = mc.merge_instance_cfg("", key + " = 'https://prod'\n",
                                      key + " = 'https://test'\n")
    assert key not in keys(report, 'ACTION')


def test_merge_file_reports_conflicts():
    merged, conflicts = mc.merge_file("a\nb\nc\n", "a\nB\nc\n", "a\nb\nc\nd\n")
    assert conflicts == 0
    assert merged == "a\nB\nc\nd\n"
    merged, conflicts = mc.merge_file("a\nb\nc\n", "a\nX\nc\n", "a\nY\nc\n")
    assert conflicts == 1
    assert '<<<<<<< site' in merged and '>>>>>>> v2.0.5' in merged


def test_read_env_file_dotenv_and_configmap(tmp_path):
    dotenv = tmp_path / 'env'
    dotenv.write_text("# c\nexport A=1\nB='two'\n")
    assert mc.read_env_file(str(dotenv)) == {'A': '1', 'B': 'two'}
    cm = tmp_path / 'cm.yaml'
    cm.write_text("kind: ConfigMap\ndata:\n  A: \"1\"\n  B: two\nmetadata:\n  name: x\n")
    assert mc.read_env_file(str(cm)) == {'A': '1', 'B': 'two'}


def test_check_env():
    cfg = ("SECRET_KEY = '{{ environ('SECRET_KEY') }}'\n"
           "FLAG = {{ environ(\"FLAG\") }}\n")
    report = mc.check_env(cfg, {'SECRET_KEY': 'abc', 'FLAG': 'True'})
    assert report == []
    report = mc.check_env(cfg, {'SECRET_KEY': "a'b"})
    assert {'FLAG', 'SECRET_KEY', 'invenio.cfg'} <= keys(report, 'ACTION')


def test_render_or_default():
    cfg = "P = '{{ environ('POOL') or 'QueuePool'}}'\n"
    assert mc.render_instance_cfg(cfg, {}) == ("P = 'QueuePool'\n", [])
    assert mc.render_instance_cfg(cfg, {'POOL': 'NullPool'}) == ("P = 'NullPool'\n", [])
