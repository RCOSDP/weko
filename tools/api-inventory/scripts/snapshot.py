# -*- coding: utf-8 -*-
"""API スナップショット生成 — 経路の正は実機 url_map、属性は AST で付与する。

    python3 snapshot.py --out api_snapshot.json

なぜ実機 url_map が正か:
  AST で `@bp.route` / `add_url_rule` を拾っても 357件。実機は 903ルート。static 配信ルートも収録する(is_static で識別)。
  差は Flask-Admin の自動生成 / `@expose` / config駆動 REST /
  modules配下に無い pip パッケージ / route が式の add_url_rule / framework 由来。

  ただし **実機 url_map はこの環境で登録された経路しか映さない**。config で無効・
  プラグイン未導入・設定値が真のときだけ登録される経路は、API として存在するのに
  ここには出ない。その穴は `detect_routes.py`(ソースだけから 6系統で検知)が埋める。
  台帳の網羅性は「実機(reconcile.py) + 静的(detect_routes.py)」の二段で担保する。

出力構造:
  meta       … 生成条件(リビジョン・プロファイル・件数)
  endpoints  … 経路ごとの属性 + auth_hash/body_hash
  modelviews … ModelView の権限属性(can_delete/can_export 等。url_map には出ない)
  config     … 認可を左右する config キーのウォッチリスト

`endpoints` に載っていて AST と結合できなかったものは `attrs: "unknown"` として
明示的に残す(黙って落とさない)。差分レビューで人が見に行く導線になる。
"""
import argparse
import ast
import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings

warnings.filterwarnings('ignore', category=SyntaxWarning)

# --- audit_decorators.py と同一の認証デコレータ辞書 -------------------------
AUTH_NAMES = {
    'login_required', 'login_required_customize', 'roles_required',
    'require_api_auth', 'require_oauth_scopes', 'need_record_permission',
    'need_permissions', 'check_authority', 'stats_api_access_required',
    'check_index_access_permissions', 'check_on_behalf_of', 'require_oauth',
    'pass_record',
}

# --- 認可を左右する config キー(値が危険側に倒れたら FAIL) -----------------
CONFIG_WATCH = [
    (r'.*_PERMISSION_FACTORY(_IMP)?$', '*_PERMISSION_FACTORY'),
    (r'^[A-Z_]*REST_ENDPOINTS$',       'REST endpoint 定義'),
    (r'^WTF_CSRF_ENABLED$',            'CSRF保護'),
    (r'^CSRF_ENABLED$',                'CSRF保護'),
    (r'^LOGIN_DISABLED$',              '認証の全無効化'),
    (r'^WEKO_ITEMS_UI_SHARED_USER_ROLE_ID_LIST$', '共有ユーザ候補範囲'),
    (r'^WEKO_PERMISSION_.*',           'ロール定義'),
    (r'^WEKO_ADMIN_ACCESS_TABLE$',     'Flask-Admin ロール制御表'),
    (r'^ACCOUNTS_.*ENABLED$',          'アカウント機能の有効/無効'),
]

SKIP_DIRS = ('/tests', '/examples', '/.tox', '/node_modules', '/cookiecutter', '/docs/', '/build/')

# --- コンテナ内で実行するダンプスクリプト ----------------------------------
DUMP_PY = r'''
import json
from flask import current_app as a

def rules(app, tag, out):
    for r in app.url_map.iter_rules():
        vf = app.view_functions.get(r.endpoint)
        out.append({
            "app": tag,
            "endpoint": r.endpoint,
            "methods": sorted(m for m in r.methods if m not in ("HEAD", "OPTIONS")),
            "rule": str(r),
            "module": getattr(vf, "__module__", "") or "",
            "func": getattr(vf, "__name__", "") or "",
        })

out = []
rules(a, "ui", out)
mounts = getattr(a.wsgi_app, "mounts", {}) or {}
for prefix, sub in mounts.items():
    app2 = getattr(sub, "__self__", None) or sub
    if hasattr(app2, "url_map"):
        rules(app2, prefix.strip("/") or "sub", out)

def safe(obj, name):
    """can_* は権限を実行時評価する property のことがあるので必ず握る。"""
    try:
        return getattr(obj, name, None)
    except Exception as exc:
        return "<dynamic:%s>" % type(exc).__name__

mv = []
admin_exts = a.extensions.get("admin") or []
for adm in admin_exts:
    for v in getattr(adm, "_views", []):
        model = safe(v, "model")
        if model is None or isinstance(model, str):
            continue
        mv.append({
            "endpoint": safe(v, "endpoint"),
            "cls": type(v).__name__,
            "model": getattr(model, "__name__", None),
            "table": getattr(model, "__tablename__", None),
            "can_create": safe(v, "can_create"),
            "can_edit": safe(v, "can_edit"),
            "can_delete": safe(v, "can_delete"),
            "can_export": safe(v, "can_export"),
            "can_view_details": safe(v, "can_view_details"),
            "column_export_list": [str(x) for x in (safe(v, "column_export_list") or [])],
        })

# 外部ライブラリが登録した経路を、どの配布物の何版が持ち込んだかに帰着させる。
# 依存の更新で経路が増減したときに原因を特定できる。
pkgs = {}
modmap = {}
try:
    import pkg_resources
    for dist in pkg_resources.working_set:
        pkgs[dist.project_name] = dist.version
        try:
            tops = dist.get_metadata("top_level.txt").split()
        except Exception:
            tops = [dist.project_name.replace("-", "_")]
        for t in tops:
            modmap.setdefault(t, dist.project_name)
except Exception as exc:
    pkgs = {"__error__": str(exc)}

json.dump({"rules": out, "modelviews": mv, "packages": pkgs, "module_to_package": modmap},
          open("/tmp/_snapshot_dump.json", "w"), ensure_ascii=False, indent=1)
print("rules=%d modelviews=%d packages=%d" % (len(out), len(mv), len(pkgs)))
'''


def default_weko_root():
    """解析対象リポジトリのルートを決める。

    1. 環境変数 WEKO_ROOT
    2. このスクリプトを含む git リポジトリのトップ(`modules/` があれば採用)
       → WEKO3 リポジトリ内(例: tools/api-inventory/scripts/)に配置した場合に効く
    3. 従来の既定(weko-document から wekov2 を解析する場合)
    """
    env = os.environ.get('WEKO_ROOT')
    if env:
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        top = subprocess.run(['git', '-C', here, 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True).stdout.strip()
    except Exception:
        top = ''
    if top and os.path.isdir(os.path.join(top, 'modules')):
        return top
    return '/home/mhaya/wekov2'


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                          text=True, **kw)


def list_web_containers():
    """compose の service=web ラベルを持つ起動中コンテナ名。"""
    r = sh(['docker', 'ps', '--filter', 'label=com.docker.compose.service=web',
            '--format', '{{.Names}}'])
    return [x for x in r.stdout.split('\n') if x.strip()]


def resolve_container(name):
    """web コンテナを解決する。省略時は compose ラベルから自動検出する。

    `docker compose -f X.yml ps -q web` は X.yml のプロジェクト名でしか探さないため、
    別ファイル/別プロジェクト名で起動したスタックでは空になる
    (例: install.sh は docker-compose2.yml=project wekov2、
     手動起動は docker-compose.yml -p weko)。ここは compose ラベルで直接探す。
    """
    if name:
        r = sh(['docker', 'inspect', '-f', '{{.State.Running}}', name])
        if r.stdout.strip() == 'true':
            return name
        cands = list_web_containers()
        sys.exit(f"コンテナ '{name}' が見つからないか停止しています。\n"
                 f"  起動中の web コンテナ: {', '.join(cands) if cands else '(なし)'}")

    cands = list_web_containers()
    if len(cands) == 1:
        print(f'  コンテナを自動検出: {cands[0]}')
        return cands[0]
    if not cands:
        sys.exit('web コンテナが見つかりません。スタックを起動してください。\n'
                 '  例: ./install.sh   /   docker compose -p weko up -d web\n'
                 '  起動済みなら --container <名前> を明示してください。')
    sys.exit('web コンテナが複数あります。--container か $WEKO_WEB_CONTAINER で'
             '指定してください:\n  ' + '\n  '.join(cands)
             + '\n  (compose の service=web ラベルは WEKO3 以外のスタックも持ちうる)')


def live_dump(container, workdir):
    """実機 url_map と ModelView 属性をコンテナから取得する。"""
    container = resolve_container(container)
    local = os.path.join(workdir, '_dump.py')
    with open(local, 'w', encoding='utf-8') as f:
        f.write(DUMP_PY)
    r = sh(['docker', 'cp', local, f'{container}:/tmp/_dump.py'])
    if r.returncode:
        sys.exit(f'docker cp 失敗: {r.stderr.strip()}')
    r = sh([
        'docker', 'exec', container, 'bash', '-lc',
        'source ~/.virtualenvs/invenio/bin/activate; cd /code; '
        'invenio shell -c "exec(open(\'/tmp/_dump.py\').read())"',
    ])
    if 'rules=' not in r.stdout:
        sys.exit(f'url_map ダンプ失敗:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}')
    print('  ' + [l for l in r.stdout.splitlines() if l.startswith('rules=')][-1])
    out = os.path.join(workdir, '_snapshot_dump.json')
    r = sh(['docker', 'cp', f'{container}:/tmp/_snapshot_dump.json', out])
    if r.returncode:
        sys.exit(f'docker cp 取得失敗: {r.stderr.strip()}')
    with open(out, encoding='utf-8') as f:
        return json.load(f)


# --- AST 側 -----------------------------------------------------------------
def dec_name(d):
    c = d.func if isinstance(d, ast.Call) else d
    parts = []
    while isinstance(c, ast.Attribute):
        parts.append(c.attr)
        c = c.value
    if isinstance(c, ast.Name):
        parts.append(c.id)
    return '.'.join(reversed(parts))


def dec_repr(d):
    name = dec_name(d)
    if not isinstance(d, ast.Call):
        return name
    args = []
    for a in d.args:
        try:
            args.append(repr(ast.literal_eval(a)))
        except Exception:
            args.append(ast.unparse(a))
    for k in d.keywords:
        try:
            args.append(f'{k.arg}={ast.literal_eval(k.value)!r}')
        except Exception:
            args.append(f'{k.arg}={ast.unparse(k.value)}')
    return f"{name}({', '.join(args)})"


def is_auth_dec(name):
    last = name.split('.')[-1]
    return (last in AUTH_NAMES
            or name.endswith('permission.require')
            or 'require' in last)


def is_route_dec(name):
    last = name.split('.')[-1]
    return last in ('route', 'expose', 'add_url_rule')


def dotted(rel_path):
    """modules/weko-admin/weko_admin/views.py -> weko_admin.views"""
    p = rel_path[:-3] if rel_path.endswith('.py') else rel_path
    parts = p.split('/')
    if parts[:1] == ['modules']:
        parts = parts[2:]          # modules/<dist>/ を落とす
    if parts and parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)


def scan_ast(root):
    """(module, funcname) -> 属性 の索引を作る。route デコレータの有無は問わない。

    `@expose` や as_view 経由でも実装本体は掴めるようにするため、全 def を拾う。
    """
    index = {}
    commented = collections.defaultdict(list)
    for dirpath, _dirnames, filenames in os.walk(os.path.join(root, 'modules')):
        if any(s in dirpath + '/' for s in SKIP_DIRS):
            continue
        for fn in sorted(filenames):
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root)
            try:
                text = open(fp, encoding='utf-8', errors='replace').read()
                tree = ast.parse(text)
            except Exception:
                continue
            lines = text.splitlines()
            mod = dotted(rel)

            # コメントアウトされた認証/認可デコレータ(no.34 の IIIF がこれ)
            for i, line in enumerate(lines, 1):
                s = line.strip()
                if s.startswith('#') and '@' in s:
                    body = s.lstrip('#').strip()
                    if body.startswith('@'):
                        nm = body[1:].split('(')[0]
                        if is_auth_dec(nm) or 'permission' in nm:
                            commented[mod].append({'line': i, 'text': body[:120]})

            def record(node, cls=None):
                decs = [dec_repr(d) for d in node.decorator_list]
                auth = sorted({d for d in decs
                               if is_auth_dec(dec_name_of(d)) and not is_route_dec(dec_name_of(d))})
                start = min([node.lineno] + [d.lineno for d in node.decorator_list])
                end = getattr(node, 'end_lineno', node.lineno)
                body = '\n'.join(l.rstrip() for l in lines[start - 1:end])
                info = {
                    'impl': f'{rel}:{node.lineno}',
                    'decorators': decs,
                    'auth_decorators': auth,
                    'auth_hash': sha1('\n'.join(auth)),
                    'body_hash': sha1(body),
                    'lines': [start, end],
                }
                index.setdefault((mod, node.name), info)
                if cls:
                    index[(mod, f'{cls}.{node.name}')] = info

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for b in node.body:
                        if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            record(b, cls=node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    record(node)
    return index, commented


def dec_name_of(repr_str):
    return repr_str.split('(')[0]


def sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:12]


def scan_config(root):
    """認可を左右する config キーを収集する(config 経由の認可無効化の検知用)。"""
    out = {}
    pats = [(re.compile(p), label) for p, label in CONFIG_WATCH]
    for dirpath, _dn, filenames in os.walk(os.path.join(root, 'modules')):
        if any(s in dirpath + '/' for s in SKIP_DIRS):
            continue
        if 'config.py' not in filenames:
            continue
        fp = os.path.join(dirpath, 'config.py')
        rel = os.path.relpath(fp, root)
        try:
            tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
        except Exception:
            continue
        for node in tree.body:
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)):
                continue
            key = node.targets[0].id
            label = next((lb for rx, lb in pats if rx.match(key)), None)
            if not label:
                continue
            try:
                val = repr(ast.literal_eval(node.value))
            except Exception:
                val = ast.unparse(node.value)
            out[f'{rel}::{key}'] = {
                'label': label, 'line': node.lineno,
                'value': val if len(val) <= 300 else val[:300] + '...',
                'value_hash': sha1(val),
            }
    return out


def build(args):
    root = os.path.abspath(args.weko_root)
    # 中間ファイル(_dump.py / _snapshot_dump.json)は既定で一時ディレクトリに置く。
    # 出力先ディレクトリに書くとリポジトリを汚す。
    tmp = None
    if args.workdir:
        work = args.workdir
        os.makedirs(work, exist_ok=True)
    else:
        tmp = tempfile.mkdtemp(prefix='api-snapshot-')
        work = tmp

    print('[1/4] 実機 url_map / ModelView をダンプ')
    if args.dump:
        with open(args.dump, encoding='utf-8') as f:
            dump = json.load(f)
    else:
        dump = live_dump(args.container, work)

    print('[2/4] AST で実装属性を索引化')
    index, commented = scan_ast(root)
    print(f'  索引: {len(index)} 関数 / コメントアウト認証: '
          f'{sum(len(v) for v in commented.values())} 箇所')

    print('[3/4] config ウォッチリストを収集')
    conf = scan_config(root)
    print(f'  監視対象キー: {len(conf)}')

    print('[4/4] 結合')
    pkgs = dump.get('packages', {})
    modmap = dump.get('module_to_package', {})
    mod_root = os.path.join(root, 'modules')
    local_dists = set()
    if os.path.isdir(mod_root):
        for name in os.listdir(mod_root):
            local_dists.add(name)
            local_dists.add(name.replace('_', '-'))

    # 1エンドポイントに複数ルールが付くことがある:
    #   ・末尾スラッシュ違い / 省略可能パラメータ
    #   ・同じ view_func を add_url_rule で複数回登録(endpoint 名が同一になる)
    # 後者はルールごとにメソッドが異なるため、メソッドを endpoint 単位で union しては
    # ならない(例: weko_index_tree_rest.ima は create=POST / update=PUT / delete=DELETE を
    # それぞれ別ルールで持つ)。ルール単位で保持する。
    # static 配信ルート(`*.static` / send_static_file)も**台帳の対象に含める**。
    # 以前は除外していたが、外部調査との突合で「経路として存在するのに台帳に無い」
    # 状態になり比較のたびに説明が要ったため、is_static を立てて収録する方針に変えた。
    grouped = {}
    for r in dump['rules']:
        g = grouped.setdefault(f"{r['app']}:{r['endpoint']}", dict(r, routes={}))
        g['routes'].setdefault(r['rule'], set()).update(r['methods'])
        if r['func'] == 'send_static_file' or r['endpoint'].endswith('.static'):
            g['is_static'] = True

    endpoints = {}
    unknown = 0
    for key, r in grouped.items():
        routes = [{'rule': rule, 'methods': sorted(ms)}
                  for rule, ms in sorted(r['routes'].items())]
        e = {
            'app': r['app'],
            'endpoint': r['endpoint'],
            'routes': routes,                                   # ルール単位(正)
            'rules': [x['rule'] for x in routes],               # 概観用
            'methods': sorted({m for x in routes for m in x['methods']}),   # 概観用
            'view': f"{r['module']}.{r['func']}" if r['module'] else r['func'],
        }
        if r.get('is_static'):
            e['is_static'] = True
        top = (r['module'] or '').split('.')[0]
        dist = modmap.get(top)
        if dist and dist not in local_dists:
            # modules/ に無い = 外部ライブラリが登録した経路。
            # ソース走査では原理的に見えないので、実機ダンプでしか捕捉できない。
            e['provider'] = f'{dist}=={pkgs.get(dist, "?")}'
        hit = index.get((r['module'], r['func']))
        if hit is None and '.' in r['func']:
            hit = index.get((r['module'], r['func'].split('.')[-1]))
        if hit:
            e.update({
                'attrs': 'ast',
                'impl': hit['impl'],
                'decorators': hit['decorators'],
                'auth_decorators': hit['auth_decorators'],
                'auth_hash': hit['auth_hash'],
                'body_hash': hit['body_hash'],
            })
            near = [c for c in commented.get(r['module'], [])
                    if hit['lines'][0] - 6 <= c['line'] <= hit['lines'][1]]
            if near:
                e['commented_auth'] = near
        else:
            # ④ 経路はあるが静的解析で属性が取れないもの。黙って落とさない。
            e['attrs'] = 'unknown'
            e['reason'] = classify_unknown(r)
            unknown += 1
        endpoints[key] = e

    mvs = {m['endpoint']: m for m in dump.get('modelviews', []) if m.get('endpoint')}

    rev = sh(['git', '-C', root, 'rev-parse', '--short', 'HEAD']).stdout.strip()
    tag = sh(['git', '-C', root, 'describe', '--tags']).stdout.strip()

    snap = {
        'meta': {
            'weko_root': root,
            'revision': rev,
            'tag': tag,
            'profile': args.profile,
            'counts': {
                'endpoints': len(endpoints),
                'attrs_ast': len(endpoints) - unknown,
                'attrs_unknown': unknown,
                'modelviews': len(mvs),
                'config_keys': len(conf),
                'external_endpoints': sum(1 for e in endpoints.values() if e.get('provider')),
                'packages': len(pkgs),
                'commented_auth': sum(len(v) for v in commented.values()),
            },
        },
        # 依存の版。経路の増減を依存更新に帰着させるために保持する。
        'packages': dict(sorted(pkgs.items())),
        'endpoints': dict(sorted(endpoints.items())),
        'modelviews': dict(sorted(mvs.items())),
        'config': dict(sorted(conf.items())),
        # エンドポイントに紐付かないコメントアウト認証も残す。
        # no.34 の IIIF `protect_api` はビュー関数ではなくハンドラフックなので、
        # エンドポイント単位の検査だけでは捕まらない。
        'commented_auth': {
            mod: sorted(items, key=lambda x: x['line'])
            for mod, items in sorted(commented.items())
        },
    }
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(snap, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write('\n')
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    c = snap['meta']['counts']
    print(f"\n{args.out}: endpoints={c['endpoints']} "
          f"(AST結合={c['attrs_ast']} / 属性不明={c['attrs_unknown']}) "
          f"modelviews={c['modelviews']} config={c['config_keys']}  rev={rev} {tag}")
    return snap


def classify_unknown(r):
    """属性が取れなかった理由を推定する(差分レビューの手がかり)。"""
    mod = r['module']
    if mod.startswith('flask_admin'):
        return 'Flask-Admin ModelView 自動生成'
    if mod.startswith('flask_security') or mod.startswith('flask_login'):
        return 'flask-security/login 由来'
    if mod.startswith('flask'):
        return 'framework 由来'
    if '_rest' in mod or mod.endswith('.views') and r['func'].islower() is False:
        return 'config駆動 REST の可能性'
    if not mod.startswith(('weko_', 'invenio_')):
        return 'modules 配下に無いパッケージ'
    return 'AST未結合(as_view / 動的登録 / pip側パッケージ)'


def main():
    p = argparse.ArgumentParser(description='API スナップショットを生成する')
    p.add_argument('--out', default='api_snapshot.json')
    p.add_argument('--weko-root', default=default_weko_root())
    p.add_argument('--container', default=os.environ.get('WEKO_WEB_CONTAINER', ''),
                   help='実機ダンプ元のコンテナ名。既定は $WEKO_WEB_CONTAINER、'
                        'それも無ければ compose ラベルから自動検出')
    p.add_argument('--dump', help='ダンプ済み JSON を使う(コンテナ起動不要)')
    p.add_argument('--profile', default='default', help='設定プロファイル名(条件付き登録の差を区別する)')
    p.add_argument('--workdir', help='中間ファイル置き場')
    build(p.parse_args())


if __name__ == '__main__':
    main()
