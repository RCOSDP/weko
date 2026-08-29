# -*- coding: utf-8 -*-
"""WEKO3 全ルート構造抽出 (AST)."""
import ast, os, json, sys, re

import os as _os
ROOT = _os.environ.get('WEKO_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
SKIP = ('/tests', '/examples', '/.tox', '/node_modules', '/docs/', '/build/', '/cookiecutter')

def iter_py():
    for dp, dn, fn in os.walk(os.path.join(ROOT, 'modules')):
        if any(s in dp + '/' for s in SKIP):
            continue
        for f in sorted(fn):
            if f.endswith('.py'):
                yield os.path.join(dp, f)

def lit(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None

def src_of(node):
    return getattr(node, 'lineno', None), getattr(node, 'end_lineno', None)

def dec_name(d):
    c = d.func if isinstance(d, ast.Call) else d
    parts = []
    while isinstance(c, ast.Attribute):
        parts.append(c.attr); c = c.value
    if isinstance(c, ast.Name):
        parts.append(c.id)
    return '.'.join(reversed(parts))

def dec_repr(d):
    name = dec_name(d)
    if isinstance(d, ast.Call):
        args = []
        for a in d.args:
            v = lit(a)
            args.append(repr(v) if v is not None else ast.unparse(a))
        for k in d.keywords:
            v = lit(k.value)
            args.append(f"{k.arg}={v!r}" if v is not None else f"{k.arg}={ast.unparse(k.value)}")
        return f"{name}({', '.join(args)})"
    return name

def body_facts(node, src_lines):
    """関数本体からの機械的事実."""
    raises, excepts, calls = set(), set(), set()
    aborts = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Raise) and n.exc is not None:
            e = n.exc.func if isinstance(n.exc, ast.Call) else n.exc
            nm = dec_name(e) if not isinstance(e, ast.Name) else e.id
            if nm: raises.add(nm)
        if isinstance(n, ast.ExceptHandler) and n.type is not None:
            t = n.type
            if isinstance(t, ast.Tuple):
                for x in t.elts:
                    excepts.add(dec_name(x) or getattr(x, 'id', ''))
            else:
                excepts.add(dec_name(t) or getattr(t, 'id', ''))
        if isinstance(n, ast.Call):
            nm = dec_name(n.func)
            if nm: calls.add(nm)
            if nm == 'abort':
                v = lit(n.args[0]) if n.args else None
                if v is not None: aborts.add(str(v))
    return {
        'raises': sorted(x for x in raises if x),
        'excepts': sorted(x for x in excepts if x),
        'aborts': sorted(aborts),
        'calls': sorted(calls),
    }

DB_PAT = re.compile(r'db\.session\.(add|commit|delete|merge|bulk)|\.query\.|session\.execute')
ES_PAT = re.compile(r'RecordsSearch|search_index|\bes\.|indexer|Elasticsearch|_search|percolat')
REDIS_PAT = re.compile(r'RedisConnection|current_cache|redis')
MAIL_PAT = re.compile(r'send_mail|send_email|MailSettingView|flask_mail|send_request_mail')
TASK_PAT = re.compile(r'\.delay\(|\.apply_async\(|celery')
FILE_PAT = re.compile(r'ObjectVersion|FileInstance|Bucket|tempfile|open\(|send_file|Location')
EXT_PAT = re.compile(r'requests\.(get|post|put|delete)|urlopen|HandleClient|http[s]?://')

def store_hints(seg):
    h = []
    if DB_PAT.search(seg): h.append('DB')
    if ES_PAT.search(seg): h.append('ES')
    if REDIS_PAT.search(seg): h.append('Redis')
    if FILE_PAT.search(seg): h.append('File')
    if MAIL_PAT.search(seg): h.append('Mail')
    if TASK_PAT.search(seg): h.append('Celery')
    if EXT_PAT.search(seg): h.append('External')
    return h

REQ_PAT = re.compile(r"request\.(?:args|form|values|json|get_json|headers|files|data|cookies)(?:\.get\(\s*['\"]([^'\"]+)['\"])?")

def request_fields(seg):
    out = set()
    for m in re.finditer(r"request\.(args|form|values|json|headers|files|cookies)(?:\.get\(\s*['\"]([^'\"]+)['\"]|\[\s*['\"]([^'\"]+)['\"]\s*\])?", seg):
        kind = m.group(1); key = m.group(2) or m.group(3)
        out.add(f"{kind}:{key}" if key else f"{kind}:*")
    if 'get_json' in seg or 'request.json' in seg or 'request.data' in seg:
        out.add('body:json')
    return sorted(out)

results = []
blueprints = []

for fp in iter_py():
    rel = os.path.relpath(fp, ROOT)
    try:
        text = open(fp, encoding='utf-8', errors='replace').read()
        tree = ast.parse(text)
    except Exception as e:
        continue
    lines = text.splitlines()

    # Blueprint definitions
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            fn = dec_name(n.value.func)
            if fn.endswith('Blueprint'):
                var = ast.unparse(n.targets[0]) if n.targets else '?'
                bpname = lit(n.value.args[0]) if n.value.args else None
                kw = {k.arg: lit(k.value) for k in n.value.keywords}
                blueprints.append({'file': rel, 'line': n.lineno, 'var': var,
                                   'name': bpname, 'url_prefix': kw.get('url_prefix'),
                                   'static_folder': kw.get('static_folder')})

    # route decorators
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in n.decorator_list:
                c = d.func if isinstance(d, ast.Call) else d
                if isinstance(c, ast.Attribute) and c.attr == 'route':
                    bpvar = ast.unparse(c.value)
                    route = lit(d.args[0]) if d.args else None
                    methods = None
                    for k in d.keywords:
                        if k.arg == 'methods': methods = lit(k.value)
                        if k.arg == 'endpoint': pass
                    s, e = src_of(n)
                    seg = '\n'.join(lines[s-1:e]) if s and e else ''
                    results.append({
                        'kind': 'route',
                        'file': rel, 'line': n.lineno, 'end_line': e,
                        'bp_var': bpvar, 'route': route,
                        'methods': methods or ['GET'],
                        'func': n.name,
                        'decorators': [dec_repr(x) for x in n.decorator_list],
                        'doc': (ast.get_docstring(n) or '').strip().splitlines()[:3],
                        'facts': body_facts(n, lines),
                        'stores': store_hints(seg),
                        'req': request_fields(seg),
                    })

    # add_url_rule calls
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'add_url_rule':
            bpvar = ast.unparse(n.func.value)
            route = lit(n.args[0]) if n.args else None
            route_expr = ast.unparse(n.args[0]) if n.args else None
            kw = {}
            for k in n.keywords:
                kw[k.arg] = ast.unparse(k.value)
                if k.arg == 'rule': route_expr = ast.unparse(k.value); route = lit(k.value)
                if k.arg == 'methods':
                    kw['methods'] = lit(k.value)
            results.append({
                'kind': 'add_url_rule',
                'file': rel, 'line': n.lineno,
                'bp_var': bpvar, 'route': route, 'route_expr': route_expr,
                'view_func': kw.get('view_func'), 'methods': kw.get('methods'),
                'endpoint': kw.get('endpoint'),
            })

out = {'routes': results, 'blueprints': blueprints}
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('routes:', len(results), 'blueprints:', len(blueprints))
