# -*- coding: utf-8 -*-
"""ソースだけから「あるべき経路」を検知し、台帳と突き合わせる。

    python3 detect_routes.py                      # 検知結果のサマリ
    python3 detect_routes.py --json out.json      # 明細を出す
    python3 detect_routes.py --cross-check        # 台帳と突き合わせる
    python3 detect_routes.py --cross-check --gate # 未収載があれば exit 1
    python3 detect_routes.py --cross-check --summary-only   # 件数のみ(public CI 用)

## なぜ実機スナップショットだけでは足りないか

`reconcile.py` は **実機 url_map** を正として突き合わせる。これは「今このコンテナで
登録されている経路」しか見ない。したがって次を構造的に取りこぼす:

  - プラグイン未導入・config で無効になっている経路(`/plugins`, `/api/admin/indexjournal`)
  - `suggesters` のように **設定値が真のときだけ**登録される経路(`/api/records/_suggest`)
  - 起動後に動的登録される経路(`WidgetDesignPage.url`)
  - 別サイト・別設定では有効になる経路

これらは「この環境に無い」だけで、**API としては存在する**。台帳から漏れれば
そのまま監査の穴になる。本スクリプトは実機を一切使わず、ソースと設定だけから
経路を検知して台帳と突き合わせる。実機検知(`reconcile.py`)との二段構えにより、
どちらか一方でしか見えない経路も拾える。

## 検知源(すべて AST。実機・Docker 不要)

| source        | 拾うもの |
|---------------|---------|
| `route`       | `@bp.route(...)` / `@app.route(...)` |
| `expose`      | Flask-Admin の `@expose(...)`(BaseView 派生。url_map には出るが AST 抽出では従来落ちていた) |
| `add_url_rule`| `bp.add_url_rule(...)`。rule が式(config 由来)の場合も view_func で追う |
| `rest_config` | `config.py` の `*ENDPOINTS` 辞書にある `*route` 値(config 駆動 REST) |
| `modelview`   | `class X(ModelView)` と `invenio_admin.views` entry point の登録先 URL |
| `entry_point` | `setup.py` の `invenio_base.{apps,blueprints,api_blueprints}` |

## 突き合わせの規則

検知 1件につき、台帳に対応行があるかを次の順で見る。

  1. 実装一致 … (impl_file, 関数名) または (impl_file, `Class.method`)
  2. URI 一致 … 正規化 URI。先頭 `/api` の有無は吸収する
  3. 登録名一致 … blueprint / endpoint 名(entry_point・modelview 用)

どれにも当たらなければ「台帳未収載の疑い」。正当な理由があるものは
`$WEKO_API_INVENTORY_DIR/detect_allow.json` に**理由を書いて**登録する
(`reconcile_allow.json` と同じ思想。黙って消さない)。

出力は `--summary-only` を付けると件数だけになる。public リポジトリの CI ログ・
artifact・PR コメントは誰でも読めるため、経路名を出したくない場面で使う。
"""
import argparse
import ast
import collections
import json
import os
import re
import sys
import warnings

warnings.filterwarnings('ignore', category=SyntaxWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
from snapshot import default_weko_root  # noqa: E402

SKIP_DIRS = ('/tests', '/examples', '/.tox', '/node_modules', '/cookiecutter',
             '/docs/', '/build/', '/.git/')

# route を持つ辞書キー。invenio 系は route / item_route / list_route / *_route。
ROUTE_KEY = re.compile(r'(^|_)route$')

# 台帳の impl_file が実ファイルを指さない行の総称表記。
# これらは AST では裏取りできない(pip パッケージ・framework 自動生成)。
NON_SOURCE_IMPL = re.compile(r'^\((provider|site-packages|framework)|^Flask-Admin ModelView')

SOURCES = ('route', 'expose', 'add_url_rule', 'rest_config', 'modelview', 'entry_point')


# --------------------------------------------------------------------------
# 収集
# --------------------------------------------------------------------------

def iter_py(root, sub='modules'):
    base = os.path.join(root, sub)
    for dp, dn, fn in os.walk(base):
        if any(s in dp.replace(os.sep, '/') + '/' for s in SKIP_DIRS):
            dn[:] = []
            continue
        for f in sorted(fn):
            if f.endswith('.py'):
                yield os.path.join(dp, f)


def lit(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def dotted(node):
    """Attribute/Name を 'a.b.c' に戻す。"""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return '.'.join(reversed(parts))


def as_view_class(node):
    """`X.as_view(...)` から X(クラス名)を取り出す。それ以外は None。"""
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute) and node.attr == 'as_view':
        return dotted(node.value).rsplit('.', 1)[-1] or None
    return None


def dec_call_name(d):
    c = d.func if isinstance(d, ast.Call) else d
    if isinstance(c, ast.Attribute):
        return c.attr
    return getattr(c, 'id', '')


def methods_of(call):
    if not isinstance(call, ast.Call):
        return ['GET']
    for k in call.keywords:
        if k.arg == 'methods':
            v = lit(k.value)
            if v:
                return sorted({str(m).upper() for m in v})
    return ['GET']


def _parse(path):
    try:
        return ast.parse(open(path, encoding='utf-8', errors='replace').read())
    except Exception:
        return None


def collect_module(root, path):
    """1ファイルから route / expose / add_url_rule / modelview を拾う。"""
    tree = _parse(path)
    if tree is None:
        return []
    rel = os.path.relpath(path, root)
    out = []

    # クラス配下の関数 -> 所属クラス名
    owner = {}
    bases_of = {}
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        bases_of[cls.name] = [dotted(b).rsplit('.', 1)[-1] for b in cls.bases]
        for m in cls.body:
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                owner[id(m)] = cls.name

    # `view_func = SomeResource.as_view(...)` の束縛を追う。
    # config 駆動の create_blueprint() は例外なくこの形で、view_func だけを見ると
    # 変数名 'view_func' しか取れず、どのクラスの経路かが分からなくなる。
    asview = collections.defaultdict(list)   # 変数名 -> [(lineno, クラス名)]
    for n in ast.walk(tree):
        if not isinstance(n, ast.Assign):
            continue
        cls_name = as_view_class(n.value)
        if not cls_name:
            continue
        for t in n.targets:
            if isinstance(t, ast.Name):
                asview[t.id].append((n.lineno, cls_name))

    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cls = owner.get(id(n))
            for d in n.decorator_list:
                name = dec_call_name(d)
                if name not in ('route', 'expose'):
                    continue
                rule = lit(d.args[0]) if isinstance(d, ast.Call) and d.args else None
                out.append({
                    'source': 'route' if name == 'route' else 'expose',
                    'file': rel, 'line': n.lineno,
                    'cls': cls, 'func': n.name,
                    'qual': f'{cls}.{n.name}' if cls else n.name,
                    'rule': rule,
                    'rule_expr': (ast.unparse(d.args[0])
                                  if isinstance(d, ast.Call) and d.args and rule is None
                                  else None),
                    'methods': methods_of(d),
                    'holder': (dotted(d.func.value)
                               if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                               else None),
                })

        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == 'add_url_rule':
            kw = {k.arg: k.value for k in n.keywords}
            rnode = n.args[0] if n.args else kw.get('rule')
            vf = kw.get('view_func')
            if vf is None and len(n.args) > 2:
                vf = n.args[2]
            vname = dotted(vf).rsplit('.', 1)[-1] if vf is not None else None
            vcls = as_view_class(vf) if vf is not None else None
            if not vcls and vname:
                # 直前に束縛された `X.as_view(...)` に遡る
                cands = [(ln, c) for ln, c in asview.get(vname, []) if ln <= n.lineno]
                if cands:
                    vcls = max(cands)[1]
            ep = lit(kw['endpoint']) if 'endpoint' in kw else (
                lit(n.args[1]) if len(n.args) > 1 else None)
            # `add_url_rule(**rule)` のような一括登録は、rule も view_func も
            # 静的には取り出せない。個々の経路は config 側(rest_config)で検知するので、
            # ここでは「config 駆動の一括登録がある」事実だけを記録して門番からは外す。
            dispatch = (rnode is None and vf is None)
            out.append({
                'source': 'add_url_rule',
                'file': rel, 'line': n.lineno,
                'cls': vcls,
                'func': vname,
                'qual': vcls or vname or (ep if isinstance(ep, str) else None),
                'endpoint': ep if isinstance(ep, str) else None,
                'rule': lit(rnode) if rnode is not None else None,
                'rule_expr': (ast.unparse(rnode)
                              if rnode is not None and lit(rnode) is None else None),
                'methods': methods_of(n),
                'holder': dotted(n.func.value),
                'dispatch': dispatch,
            })

    # ModelView 派生クラス(/admin/<url>/ が自動生成される)
    for cls_name, bases in bases_of.items():
        if any(b.endswith('ModelView') for b in bases):
            out.append({'source': 'modelview', 'file': rel, 'line': 0,
                        'cls': cls_name, 'func': None, 'qual': cls_name,
                        'rule': None, 'rule_expr': None, 'methods': ['GET'],
                        'holder': None})
    return out


def collect_rest_config(root, path):
    """config.py の `*ENDPOINTS` 辞書から route 値を拾う。"""
    tree = _parse(path)
    if tree is None:
        return []
    rel = os.path.relpath(path, root)
    out = []
    for n in tree.body:
        if not isinstance(n, ast.Assign) or not isinstance(n.targets[0], ast.Name):
            continue
        var = n.targets[0].id
        if 'ENDPOINTS' not in var:
            continue
        for sub in ast.walk(n.value):
            if not isinstance(sub, ast.Dict):
                continue
            for k, v in zip(sub.keys, sub.values):
                if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                    continue
                if not ROUTE_KEY.search(k.value):
                    continue
                val = lit(v)
                if not isinstance(val, str) or not val.startswith('/'):
                    continue
                out.append({'source': 'rest_config', 'file': rel,
                            'line': getattr(v, 'lineno', n.lineno),
                            'cls': None, 'func': None,
                            'qual': f'{var}:{k.value}',
                            'rule': val, 'rule_expr': None,
                            'methods': ['GET'], 'holder': var})
    return out


# 経路を生む登録だけを見る。`invenio_base.apps` / `api_apps` は拡張(Flask extension)の
# 登録で、それ自体は経路を作らない。混ぜると常時 13件の偽陽性になり、ゲートが形骸化する。
EP_GROUPS = ('invenio_base.blueprints', 'invenio_base.api_blueprints',
             'invenio_admin.views')


def collect_adminview_dicts(root, path):
    """`xxx_adminview = {'view_class': FooView, ...}` を集める。

    `invenio_admin.views` entry point は `module:xxx_adminview` を指すだけなので、
    その辞書が指すクラス名まで辿らないと Flask-Admin の登録名が分からない
    (`session_adminview` -> `SessionActivityView` -> 登録名 `sessionactivity`)。
    """
    tree = _parse(path)
    if tree is None:
        return {}
    rel = os.path.relpath(path, root)
    mod = rel[:-3].replace('/', '.').replace(os.sep, '.')
    mod = mod.split('.', 2)[-1] if mod.startswith('modules.') else mod
    out = {}
    for n in tree.body:
        if not isinstance(n, ast.Assign) or not isinstance(n.targets[0], ast.Name):
            continue
        var = n.targets[0].id
        if 'adminview' not in var and not var.endswith('_view'):
            continue
        names = [x.id for x in ast.walk(n.value) if isinstance(x, ast.Name)]
        if names:
            out[f'{mod}:{var}'] = names
    return out


def collect_entry_points(root, path):
    """setup.py の entry_points から blueprint / admin view の登録を拾う。"""
    tree = _parse(path)
    if tree is None:
        return []
    rel = os.path.relpath(path, root)
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Dict):
            continue
        for k, v in zip(n.keys, n.values):
            if not (isinstance(k, ast.Constant) and k.value in EP_GROUPS):
                continue
            for item in (lit(v) or []):
                if not isinstance(item, str) or '=' not in item:
                    continue
                name, target = (x.strip() for x in item.split('=', 1))
                out.append({'source': 'entry_point', 'file': rel,
                            'line': getattr(v, 'lineno', n.lineno),
                            'cls': None, 'func': target.rsplit(':', 1)[-1],
                            'qual': name, 'target': target,
                            'rule': None, 'rule_expr': None,
                            'methods': ['GET'], 'holder': k.value})
    return out


def detect(root):
    """全検知源を回して検知一覧を返す。"""
    found = []
    adminviews = {}
    for p in iter_py(root):
        found += collect_module(root, p)
        if os.path.basename(p) == 'config.py':
            found += collect_rest_config(root, p)
        if os.path.basename(p) in ('admin.py', 'views.py'):
            adminviews.update(collect_adminview_dicts(root, p))
    for dp, dn, fn in os.walk(os.path.join(root, 'modules')):
        if any(s in dp.replace(os.sep, '/') + '/' for s in SKIP_DIRS):
            dn[:] = []
            continue
        if 'setup.py' in fn:
            found += collect_entry_points(root, os.path.join(dp, 'setup.py'))
    # entry point が指す `*_adminview` を、その辞書が参照するクラス名まで解決する
    for d in found:
        if d['source'] == 'entry_point' and d.get('target') in adminviews:
            d['via'] = adminviews[d['target']]
    return found


# --------------------------------------------------------------------------
# 台帳との突き合わせ
# --------------------------------------------------------------------------

def norm_uri(u):
    u = u.strip()
    if len(u) > 1 and u.endswith('/'):
        u = u[:-1]
    return u


def uri_variants(u):
    """先頭 `/api` の有無を吸収した比較キー。"""
    u = norm_uri(u)
    out = {u}
    if u.startswith('/api'):
        out.add(norm_uri(u[4:]) or '/')
    else:
        out.add(norm_uri('/api' + u))
    return {x for x in out if x}


def load_ledger(path):
    rows = [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8') if l.strip()]
    hdr = rows[0]
    H = {n: i for i, n in enumerate(hdr)}
    data = rows[1:]

    by_impl = collections.defaultdict(list)
    by_uri = collections.defaultdict(list)
    by_name = collections.defaultdict(list)
    by_ep_prefix = collections.defaultdict(list)
    for r in data:
        no = r[H['no']]
        f = r[H['impl_file']]
        fn = r[H['impl_func']]
        # impl_func は `A→B`(委譲) / `A/B`(別名) / `f(...)`(内訳) の表記を取りうる
        for part in re.split(r'[/→]', fn.split('(')[0]):
            part = part.strip()
            if not part:
                continue
            by_impl[(f, part)].append(no)
            by_impl[(f, part.rsplit('.', 1)[-1])].append(no)
            if '.' in part:
                # `Class.method` はクラス名だけでも引けるようにする。
                # add_url_rule は `Class.as_view(...)` を渡すので、台帳側の
                # メソッド名までは分からない。
                by_impl[(f, part.split('.', 1)[0])].append(no)
        for u in r[H['uri']].split(';'):
            for v in uri_variants(u):
                by_uri[v].append(no)
        for col in ('blueprint', 'endpoint'):
            v = r[H[col]].strip()
            if v and v not in ('-', 'TODO'):
                by_name[v].append(no)
                by_name[v.rsplit('.', 1)[-1]].append(no)
                # Flask-Admin は `role.index_view` のように「登録名.ビュー名」になる。
                # ModelView クラスや *_adminview からはビュー名まで分からないので、
                # 登録名だけでも引けるようにする。
                if '.' in v:
                    by_ep_prefix[v.split('.', 1)[0]].append(no)
    return {'hdr': hdr, 'H': H, 'rows': data, 'by_impl': by_impl,
            'by_uri': by_uri, 'by_name': by_name, 'by_ep_prefix': by_ep_prefix}


ADMIN_SUFFIX = re.compile(r'(ModelView|AdminView|View|_adminview|_view)$')


def admin_prefixes(d):
    """ModelView クラス名 / `*_adminview` から Flask-Admin の登録名候補を作る。

    `RoleView` -> `role`、`SessionActivityView` -> `sessionactivity`、
    `user_adminview` -> `user`。登録名は台帳の endpoint 列の `.` の手前に出る。
    """
    if d['source'] not in ('modelview', 'entry_point'):
        return []
    out = []
    for raw in [d.get('cls'), d.get('func'), d.get('qual')] + list(d.get('via') or []):
        if not raw:
            continue
        base = ADMIN_SUFFIX.sub('', raw)
        if base:
            out.append(base.lower())
    return out


def match(d, L):
    """検知1件を台帳に当てる。当たれば (規則, [no]) を返す。"""
    f, q, fn = d['file'], d.get('qual'), d.get('func')
    for key in (q, fn):
        if key and (f, key) in L['by_impl']:
            return 'impl', L['by_impl'][(f, key)]
    if d.get('rule'):
        for v in uri_variants(d['rule']):
            if v in L['by_uri']:
                return 'uri', L['by_uri'][v]
    for key in (d.get('qual'), d.get('func'), d.get('cls'), d.get('endpoint')):
        if key and key in L['by_name']:
            return 'name', L['by_name'][key]
    for key in admin_prefixes(d):
        if key in L['by_ep_prefix']:
            return 'admin', L['by_ep_prefix'][key]
    # entry_point / modelview は「登録名」でしか追えないことがある。
    # 同じファイルの行が台帳にあれば、その登録は台帳に届いているとみなす。
    if d['source'] in ('entry_point', 'modelview'):
        mod = d['file'].split('/')[1] if '/' in d['file'] else ''
        for (ff, _), nos in L['by_impl'].items():
            if mod and ff.startswith(f'modules/{mod}/'):
                return 'module', nos
    return None, []


def load_allow():
    p = data_path('detect_allow.json', required=False)
    if not p or not os.path.isfile(p):
        return {}
    try:
        a = json.load(open(p, encoding='utf-8'))
    except Exception:
        return {}
    return {k: v for k, v in a.items() if not k.startswith('_')}


def allow_key(d):
    """許可リストのキー。ファイル+識別子で、行番号の移動に影響されない形にする。"""
    return f"{d['file']}::{d.get('qual') or d.get('rule') or '?'}"


# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description='ソースだけから経路を検知し、台帳と突き合わせる')
    p.add_argument('--weko-root', default=None, help='既定: $WEKO_ROOT')
    p.add_argument('--tsv', default=None,
                   help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--json', help='検知明細の書き出し先')
    p.add_argument('--cross-check', action='store_true', help='台帳と突き合わせる')
    p.add_argument('--gate', action='store_true', help='未収載があれば exit 1')
    p.add_argument('--summary-only', action='store_true',
                   help='件数のみ出力する(public な CI ログに経路名を出さない)')
    p.add_argument('--out', help='Markdown 出力先')
    a = p.parse_args()

    root = a.weko_root or default_weko_root()
    found = detect(root)

    by_src = collections.Counter(d['source'] for d in found)
    L = ['# ソース由来の経路検知', '', f'- 解析対象: `{root}`', '']
    L += ['| 検知源 | 件数 |', '|---|---:|']
    for s in SOURCES:
        L.append(f'| `{s}` | {by_src.get(s, 0)} |')
    L += [f'| **計** | **{len(found)}** |', '']

    unexplained = []
    if a.cross_check:
        tsv = a.tsv or data_path('weko3_api_list_full.tsv')
        led = load_ledger(tsv)
        allow = load_allow()
        miss, known, dispatched, hit = [], [], [], collections.Counter()
        matched_nos = set()
        for d in found:
            rule, nos = match(d, led)
            if nos:
                hit[d['source']] += 1
                matched_nos.update(nos)
                continue
            if d.get('dispatch'):
                dispatched.append(d)
                continue
            k = allow_key(d)
            if k in allow:
                d = dict(d, reason=allow[k])
                known.append(d)
            else:
                miss.append(d)
        unexplained = miss

        L += [f"## 判定: {'❌ 台帳未収載の疑いあり' if miss else '✅ 全検知が台帳に対応'}"
              f' ({len(miss)}件)', '']
        L += ['| 検知源 | 検知 | 台帳に対応 | 未収載 | 既知・許容 |', '|---|---:|---:|---:|---:|']
        for s in SOURCES:
            n = by_src.get(s, 0)
            m = sum(1 for x in miss if x['source'] == s)
            kn = sum(1 for x in known if x['source'] == s)
            L.append(f'| `{s}` | {n} | {hit.get(s, 0)} | {m} | {kn} |')
        L.append('')
        if dispatched:
            L += [f'> `add_url_rule(**rule)` 形式の config 駆動一括登録が '
                  f'{len(dispatched)} 箇所。個々の経路は `rest_config` 側で検知する。',
                  '']

        if miss and not a.summary_only:
            L += ['## 台帳未収載の疑い — 行の追加、または理由付きで '
                  '`detect_allow.json` へ登録が必要', '']
            for d in miss:
                where = f"{d['file']}:{d['line']}"
                what = d.get('rule') or d.get('rule_expr') or d.get('qual') or '?'
                L.append(f"- `{d['source']}` `{what}` — {where} "
                         f"({d.get('qual') or ''} {','.join(d['methods'])})")
            L.append('')
        if known and not a.summary_only:
            L += ['## 既知・許容(`detect_allow.json`)', '']
            for d in known:
                L.append(f"- `{d['source']}` `{allow_key(d)}` — {d['reason']}")
            L.append('')

        # 静的に裏取りできなかった台帳行。ModelView・framework・pip 由来は
        # ソースに定義が無いので当然入る。数が急に動いたら台帳側の異常を疑う。
        unbacked = [r for r in led['rows'] if r[led['H']['no']] not in matched_nos]
        real = [r for r in unbacked
                if not NON_SOURCE_IMPL.match(r[led['H']['impl_file']])]
        L += ['## 参考: 静的検知と結びつかなかった台帳行', '',
              f'- 全体: {len(unbacked)} / {len(led["rows"])} 行',
              f'- うち実ファイルを持つ行: {len(real)}'
              '(pip・framework・ModelView 総称表記を除いた数)', '']
        if real and not a.summary_only:
            for r in real[:40]:
                L.append(f"- no={r[led['H']['no']]} `{r[led['H']['uri']][:60]}` "
                         f"— {r[led['H']['impl_file']]}")
            if len(real) > 40:
                L.append(f'- … 他 {len(real) - 40} 行')
            L.append('')

    md = '\n'.join(L)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(md + '\n')
        print(f'{a.out} を書き出しました')
    else:
        print(md)
    if a.json:
        json.dump({'meta': {'weko_root': root, 'counts': dict(by_src)},
                   'detections': found},
                  open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'{a.json} を書き出しました')

    if a.gate and unexplained:
        sys.exit(1)


if __name__ == '__main__':
    main()
