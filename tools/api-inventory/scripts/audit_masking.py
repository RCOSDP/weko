# -*- coding: utf-8 -*-
"""応答本文が WEKO の非公開判定を通っているかを、ソース(AST)だけから見る。

    python3 audit_masking.py                  # 4つの検知のサマリ
    python3 audit_masking.py --serializers    # 応答シリアライザごとのマスク表(明細)
    python3 audit_masking.py --factories      # 認可ファクトリが None に潰された設定(明細)
    python3 audit_masking.py --rows           # 本文を返すのにマスクに届かない台帳の行(明細)
    python3 audit_masking.py --helpers        # マスクヘルパを fan-in 順に並べる
    python3 audit_masking.py --json out.json  # 明細を JSON で
    python3 audit_masking.py --gate           # 検知があれば exit 1
    python3 audit_masking.py --summary-only   # 件数だけ(public CI 用)

## なぜ要るか

`audit_authz.py` は「**誰が**その経路に入れるか」を見る。本スクリプトが見るのは
その先で、「入れた人に **何が返るか**」である。WEKO の「非公開」は1つの旗では
なく、次の6種類が別々の場所で判定される。

| 種類 | 判定 |
|---|---|
| アイテム非公開・公開日 | `check_publish_status`(publish_status と pubdate の未来日) |
| インデックス権限 | `check_index_permissions`(public_state / browsing_role / browsing_group / 公開日) |
| オーナ権限 | `check_created_id` / `hide_meta_data_for_role`(owner・weko_shared_ids) |
| ファイル公開条件 | `hide_by_file`(accessrole=open_no を落とす) / `check_file_download_permission` |
| アイテムタイプの非公開項目 | `hide_by_itemtype`(option.hidden の項目を落とす) |
| メールアドレス | `hide_by_email` |

**入口の認可と応答のマスクは別物で、片方だけ通っている経路がある。** 同じ対象を
返すのに、画面側は一式のマスクを通し、API 側は一部しか通さない、という食い違いが
起きうる。入口で弾けなかった経路がそのまま本文を返せば、隠すはずのものが応答に
載る。**どの経路が該当するかは書かない**(docs/RULE.md §1)。具体例は非公開側の
調査記録にある。

## 精度について

呼び出し名の一致で辿るヒューリスティックで、`audit_authz.py` / `detect_routes.py`
と同じく**偽陽性を許して取りこぼしを減らす**側に振ってある。出力は「指摘」では
なく**確認待ちの行列**であり、確認した結果を台帳の `sec_pattern` / `sec_exposed`
に書くことで消える。デコレータ経由で届くマスクは `条件付き` として区別する。
判定を factory 名で差し込む型のデコレータは、その factory が設定で無効化されて
いれば素通りするので、**呼び出しが在ることは判定が効くことを意味しない**。

索引(`Index`)は `audit_authz.py` と同じ作りだが、あちらは別ブランチで育っている
ため今は持たない。合流したら `from audit_authz import Index` に寄せること。
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
from detect_routes import iter_py, lit  # noqa: E402
from paths import data_path  # noqa: E402
from snapshot import default_weko_root  # noqa: E402


# 6種類の非公開判定と、それを実際に行う関数名。
# **名前で辿るので、判定の本体を別名に切り出したらここを足すこと。**
MASKS = collections.OrderedDict((
    ('publish', ('アイテム非公開・公開日', {'check_publish_status'})),
    ('index', ('インデックス権限', {'check_index_permissions'})),
    ('owner', ('オーナ権限', {'check_created_id', 'check_created_id_by_recid',
                              'hide_meta_data_for_role'})),
    ('file', ('ファイル公開条件', {'hide_by_file', 'check_file_download_permission'})),
    ('itemtype', ('アイテムタイプの非公開項目', {'hide_by_itemtype'})),
    ('email', ('メールアドレス', {'hide_by_email'})),
))

# アイテム本体の非公開を守る4種。ここが全部空の経路が、本文を返してはいけない
# ものを返している疑いのある経路になる。email/itemtype は項目単位の伏字なので、
# 「アイテムごと見せてよいか」の判断には数えない。
ITEM_MASKS = ('publish', 'index', 'owner', 'file')

FUNC_TO_MASK = {fn: key for key, (_ja, fns) in MASKS.items() for fn in fns}

# 入口のデコレータ。ここから辿ったマスクは permission_factory の設定次第で
# 素通りするので、直接呼びと区別する。
GATE_DECORATORS = ('need_record_permission', 'need_permissions',
                   'need_bucket_permission', 'require_api_auth',
                   'login_required', 'require_oauth_scopes')

# 応答シリアライザを宣言している設定のキー。
SERIALIZER_KEYS = ('record_serializers', 'files_serializers',
                   'search_serializers', 'item_serializers')

# アイテム/ファイルの実体が置かれているテーブル。`data_store` がここを指す行だけを
# 見る。コミュニティ設定や画面テンプレートまで広げると行列が読まれなくなるため、
# **6種の非公開判定が守っている対象**に絞る。`--all` で外せる。
ITEM_STORE = re.compile(
    r'records_metadata|record_files|ObjectVersion|files_object|files_bucket'
    r'|FilesInstance|_buckets', re.I)

# 「本文にアイテム/ファイル由来のデータが載る」とみなす応答の書き方。
BODY_DATA = re.compile(
    r'(レコード|メタデータ|アイテム|デポジット|ファイル|インデックス|'
    r'ObjectVersion|record|metadata|item|file|index|Status ?Document)', re.I)

# 本文が無い応答。**主文だけを見る。** 「更新後のレコードJSON。例外時は空ボディ500」の
# ような書き方があり、全文に当てると本文を返す行を取りこぼす。
NO_BODY = re.compile(r'(空ボディ|ボディ ?なし|^なし$|^-$|^\s*$|^204)')


# --------------------------------------------------------------------------
# ソースの索引
# --------------------------------------------------------------------------

def called_names(node):
    """関数の中から呼び出し名(単純名・属性名の末尾)を拾う。

    **自分のデコレータは数えない。** `ast.walk` は decorator_list も歩くため、
    素通りしうる `@need_record_permission(...)` が直接呼びに混ざり、
    「入口で守られている」ように見えてしまう。デコレータは
    `decorator_names()` が別に拾い、`条件付き` として扱う。
    """
    out = []
    skip = {id(d) for d in getattr(node, 'decorator_list', [])}
    for child in ast.iter_child_nodes(node):
        if id(child) in skip:
            continue
        for n in ast.walk(child):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name):
                    out.append(f.id)
                elif isinstance(f, ast.Attribute):
                    out.append(f.attr)
    return out


def decorator_names(node):
    """デコレータ名を拾う。`@a.b(c)` は `b` を返す。"""
    return [n for n, _arg in decorator_gates(node)]


def decorator_gates(node):
    """デコレータを (名前, 最初の文字列引数) で拾う。

    引数を取るのは `@need_record_permission('update_permission_factory')` の
    ように**どの factory を読むか**がそこに書いてあるため。その factory が
    設定で None に潰されていれば、デコレータは在っても何も守らない。
    """
    out = []
    for d in getattr(node, 'decorator_list', []):
        t = d.func if isinstance(d, ast.Call) else d
        name = t.id if isinstance(t, ast.Name) else (
            t.attr if isinstance(t, ast.Attribute) else None)
        if not name:
            continue
        arg = None
        if isinstance(d, ast.Call):
            for a in d.args:
                if isinstance(lit(a), str):
                    arg = lit(a)
                    break
        out.append((name, arg))
    return out


class Index:
    """`modules/` 配下の関数・クラス・モジュール直下の代入を1度だけ読む。"""

    def __init__(self, root):
        self.root = root
        self.funcs = {}                                 # (rel, qual) -> node
        self.by_name = collections.defaultdict(list)    # 単純名 -> [(rel, qual)]
        self.classes = {}                               # (rel, name) -> ClassDef
        self.class_by_name = collections.defaultdict(list)
        self.assigns = collections.defaultdict(list)    # 名前 -> [(rel, Call)]
        self.aliases = collections.defaultdict(list)    # 名前 -> [別名の元]
        for path in iter_py(root):
            rel = os.path.relpath(path, root)
            try:
                tree = ast.parse(open(path, encoding='utf-8', errors='replace').read())
            except Exception:
                continue
            self._collect(rel, tree, prefix='')
            for st in tree.body:
                if not isinstance(st, ast.Assign):
                    continue
                for t in st.targets:
                    if not isinstance(t, ast.Name):
                        continue
                    if isinstance(st.value, ast.Call):
                        self.assigns[t.id].append((rel, st.value))
                    elif isinstance(st.value, ast.Name):
                        self.aliases[t.id].append(st.value.id)

    def _collect(self, rel, node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                self.classes[(rel, child.name)] = child
                self.class_by_name[child.name].append((rel, child.name))
                self._collect(rel, child, prefix + child.name + '.')
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = prefix + child.name
                self.funcs[(rel, qual)] = child
                self.by_name[child.name].append((rel, qual))
                self._collect(rel, child, qual + '.')

    def find(self, rel, name):
        """(ファイル, 関数名) で引く。同名が複数あるときは同一ファイルを優先する。"""
        simple = name.split('.')[-1]
        if (rel, name) in self.funcs:
            return rel, name, self.funcs[(rel, name)]
        for r, qual in self.by_name.get(simple, []):
            if r == rel:
                return r, qual, self.funcs[(r, qual)]
        cands = self.by_name.get(simple, [])
        if len(cands) == 1:
            r, qual = cands[0]
            return r, qual, self.funcs[(r, qual)]
        return None

    def method(self, class_name, meth, seen=None):
        """クラス名からメソッドを引く。無ければ基底クラスを名前で辿る。"""
        seen = seen if seen is not None else set()
        for rel, cname in self.class_by_name.get(class_name, []):
            if (rel, cname) in seen:
                continue
            seen.add((rel, cname))
            node = self.classes[(rel, cname)]
            got = self.find(rel, cname + '.' + meth)
            if got:
                return got
            for base in node.bases:
                bn = base.id if isinstance(base, ast.Name) else (
                    base.attr if isinstance(base, ast.Attribute) else None)
                if bn:
                    got = self.method(bn, meth, seen)
                    if got:
                        return got
        return None

    def reach(self, seeds, depth):
        """種になる関数から `depth` 段だけ呼び出しを辿り、到達した関数を返す。

        1段目のデコレータだけ別扱いで拾う(入口の認可はデコレータに書かれる)。
        """
        out, seen, frontier = [], set(), []
        for s in seeds:
            if s and (s[0], s[1]) not in seen:
                seen.add((s[0], s[1]))
                out.append(s)
                frontier.append(s)
        gated = []
        for r, _q, node in list(frontier):
            for dec in decorator_names(node):
                if dec in GATE_DECORATORS:
                    got = self.find(r, dec)
                    if got:
                        gated.append(got)
        for _ in range(max(0, depth - 1)):
            nxt = []
            for r, _q, node in frontier:
                for callee in called_names(node):
                    got = self.find(r, callee)
                    if got and (got[0], got[1]) not in seen:
                        seen.add((got[0], got[1]))
                        out.append(got)
                        nxt.append(got)
            frontier = nxt
            if not frontier:
                break
        return out, gated

    def gate_factories(self, seeds):
        """種になる関数のデコレータが読む factory 名を返す。"""
        out = set()
        for _r, _q, node in seeds:
            for name, arg in decorator_gates(node):
                if name in GATE_DECORATORS and arg:
                    out.add(arg)
        return sorted(out)

    def masks_from(self, seeds, depth):
        """到達した関数名から、効いているマスクの種類を集める。

        戻り値は (直接届くもの, デコレータ経由で届くもの)。
        """
        direct, cond = set(), set()
        reached, gated = self.reach(seeds, depth)
        for _r, qual, node in reached:
            for name in [qual.split('.')[-1]] + called_names(node):
                if name in FUNC_TO_MASK:
                    direct.add(FUNC_TO_MASK[name])
        if gated:
            g_reached, _ = self.reach(gated, depth)
            for _r, qual, node in g_reached:
                for name in [qual.split('.')[-1]] + called_names(node):
                    if name in FUNC_TO_MASK:
                        cond.add(FUNC_TO_MASK[name])
        return direct, cond - direct


# --------------------------------------------------------------------------
# A. 応答シリアライザごとのマスク表
# --------------------------------------------------------------------------

def collect_serializer_names(root):
    """設定から応答シリアライザの `module:name` を集める。"""
    out = collections.defaultdict(set)      # 'name' -> {設定した場所}
    for path in iter_py(root):
        rel = os.path.relpath(path, root)
        if not rel.endswith('config.py'):
            continue
        try:
            tree = ast.parse(open(path, encoding='utf-8', errors='replace').read())
        except Exception:
            continue
        for n in ast.walk(tree):
            key = None
            if isinstance(n, ast.keyword) and n.arg in SERIALIZER_KEYS:
                key, val = n.arg, n.value
            elif isinstance(n, ast.Assign):
                # `RECORDS_REST_ENDPOINTS['recid']['record_serializers'] = {...}`
                for t in n.targets:
                    if isinstance(t, ast.Subscript) and lit(t.slice) in SERIALIZER_KEYS:
                        key, val = lit(t.slice), n.value
                        break
            elif isinstance(n, ast.Dict):
                for k, v in zip(n.keys, n.values):
                    if lit(k) in SERIALIZER_KEYS:
                        key, val = lit(k), v
                        break
            if not key or not isinstance(val, ast.Dict):
                continue
            for v in val.values:
                s = lit(v)
                if isinstance(s, str) and ':' in s:
                    out[s].add(rel)
    return out


def resolve_serializer(idx, dotted, depth=6):
    """`module:name` を、応答を組み立てる関数まで解く。"""
    name = dotted.split(':')[-1]
    seeds, seen = [], set()

    def walk(n, budget):
        if budget <= 0 or n in seen:
            return
        seen.add(n)
        got = idx.find('', n)
        if got:
            seeds.append(got)
            return
        m = idx.method(n, 'serialize')
        if m:
            seeds.append(m)
            return
        for alias in idx.aliases.get(n, []):
            walk(alias, budget - 1)
        for _rel, call in idx.assigns.get(n, []):
            f = call.func
            fn = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else None)
            if fn:
                walk(fn, budget - 1)
            for a in call.args:
                if isinstance(a, ast.Name):
                    walk(a.id, budget - 1)

    walk(name, depth)
    return seeds


def audit_serializers(idx, root, depth):
    rows = []
    for dotted, where in sorted(collect_serializer_names(root).items()):
        seeds = resolve_serializer(idx, dotted)
        direct, cond = idx.masks_from(seeds, depth) if seeds else (set(), set())
        rows.append({
            'serializer': dotted,
            'configured_in': sorted(where),
            'resolved': bool(seeds),
            'masks': sorted(direct),
            'masks_conditional': sorted(cond),
            'missing_item_masks': [m for m in ITEM_MASKS if m not in direct],
        })
    return rows


# --------------------------------------------------------------------------
# B. 認可ファクトリを None に潰している設定
# --------------------------------------------------------------------------

FACTORY_NAME = re.compile(r'PERMISSION_FACTORY|permission_factory')


def audit_factories(root):
    out = []
    for path in iter_py(root):
        rel = os.path.relpath(path, root)
        if not rel.endswith('config.py'):
            continue
        try:
            tree = ast.parse(open(path, encoding='utf-8', errors='replace').read())
        except Exception:
            continue
        for n in ast.walk(tree):
            targets, val = [], None
            if isinstance(n, ast.Assign):
                targets, val = n.targets, n.value
            elif isinstance(n, ast.keyword) and n.arg:
                targets, val = [ast.Name(id=n.arg)], n.value
            for t in targets:
                name = t.id if isinstance(t, ast.Name) else None
                if name and FACTORY_NAME.search(name) and _is_none(val):
                    out.append({'file': rel, 'line': getattr(n, 'lineno', 0),
                                'setting': name})
    return sorted(out, key=lambda d: (d['file'], d['line']))


def _is_none(node):
    return isinstance(node, ast.Constant) and node.value is None


# --------------------------------------------------------------------------
# C. 本文を返すのにマスクに届かない台帳の行
# --------------------------------------------------------------------------

def load_ledger(path):
    lines = open(path, encoding='utf-8').read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    H = {n: i for i, n in enumerate(hdr)}
    return [dict(zip(hdr, l.split('\t'))) for l in lines[1:]], H


# 実機に経路が立たないと台帳が記録している行。同一ルールの重複登録などで、
# 読んでも確認の手間が増えるだけなので外す。**判断の根拠は台帳側にある。**
UNREACHABLE = '測定対象外'


def returns_item_body(row, all_stores=False):
    """応答にアイテム/ファイル由来のデータが載る行か。"""
    resp = (row.get('response') or '').strip()
    if NO_BODY.search(resp.split('。')[0]):
        return False
    if not BODY_DATA.search(resp):
        return False
    if all_stores:
        return True
    return bool(ITEM_STORE.search(row.get('data_store') or ''))


def disabled_factory_names(factories):
    """B の検出(設定名)を、デコレータが書く factory 名と突き合わせる形にする。"""
    return {f['setting'] for f in factories}


def audit_rows(idx, rows, depth, methods=None, factories=(), all_stores=False):
    """確認待ちの行列を返す。戻り値は (行, 確認済みとして外した件数)。

    `sec_exposed` が埋まっている行は**人が確認して結論を書いた行**なので外す。
    これが無いと、直した/判断した行が毎回出続けて誰も読まなくなり、`--gate` も
    使えない。外した件数は必ず一緒に返す(黙って消さない)。
    """
    disabled = disabled_factory_names(factories)
    out, settled = [], 0
    for row in rows:
        if methods and not (set(row['method'].split(',')) & set(methods)):
            continue
        if UNREACHABLE in (row.get('dynamic_verified') or ''):
            continue
        if not returns_item_body(row, all_stores):
            continue
        if (row.get('sec_exposed') or '-').strip() not in ('', '-'):
            settled += 1
            continue
        rel = (row.get('impl_file') or '').strip()
        fn = (row.get('impl_func') or '').strip().split('/')[0]
        if not rel or not fn or fn == '-':
            continue
        seed = idx.find(rel, fn)
        if not seed:
            continue
        direct, cond = idx.masks_from([seed], depth)
        missing = [m for m in ITEM_MASKS if m not in direct]
        if len(missing) != len(ITEM_MASKS):
            continue
        gates = idx.gate_factories([seed])
        killed = sorted({s for g in gates for s in disabled
                         if s.upper().endswith(g.upper())})
        out.append({
            'no': row['no'], 'method': row['method'], 'uri': row['uri'],
            'impl': f"{rel}:{fn}", 'masks': sorted(direct),
            'masks_conditional': sorted(cond),
            'missing_item_masks': missing,
            'gate_factories': gates,
            'disabled_by_config': killed,
            'sec_pattern': row.get('sec_pattern', ''),
        })
    return out, settled


# --------------------------------------------------------------------------
# D. マスクヘルパの fan-in
# --------------------------------------------------------------------------

def audit_helpers(idx):
    counts = collections.Counter()
    where = collections.defaultdict(set)
    for (rel, qual), node in idx.funcs.items():
        for callee in called_names(node):
            if callee in FUNC_TO_MASK:
                counts[callee] += 1
                where[callee].add(rel)
    out = []
    for fn, mask in sorted(FUNC_TO_MASK.items(), key=lambda kv: -counts[kv[0]]):
        out.append({'helper': fn, 'mask': mask, 'mask_ja': MASKS[mask][0],
                    'callers': counts[fn], 'files': sorted(where[fn])})
    return out


# --------------------------------------------------------------------------
# 出力
# --------------------------------------------------------------------------

def ja(keys):
    return '/'.join(MASKS[k][0] for k in keys) if keys else 'なし'


def main():
    p = argparse.ArgumentParser(
        description='応答本文が非公開判定(6種)を通っているかをソースから見る')
    p.add_argument('--weko-root', default=None)
    p.add_argument('--full', default=None, help='台帳(既定: $WEKO_API_INVENTORY_DIR)')
    p.add_argument('--depth', type=int, default=4, help='呼び出しを辿る段数(既定4)')
    p.add_argument('--method', default=None,
                   help='台帳の検査を絞る(例: DELETE,PUT,PATCH)')
    p.add_argument('--all', dest='all_stores', action='store_true',
                   help='アイテム/ファイル以外を扱う経路も含める(行列が増える)')
    p.add_argument('--serializers', action='store_true')
    p.add_argument('--factories', action='store_true')
    p.add_argument('--rows', action='store_true')
    p.add_argument('--helpers', action='store_true')
    p.add_argument('--json', dest='json_out', default=None)
    p.add_argument('--gate', action='store_true')
    p.add_argument('--summary-only', action='store_true')
    a = p.parse_args()

    root = a.weko_root or default_weko_root()
    idx = Index(root)
    methods = a.method.split(',') if a.method else None

    ser = audit_serializers(idx, root, a.depth)
    fac = audit_factories(root)
    helpers = audit_helpers(idx)

    rows_res, settled = [], 0
    full = a.full or data_path('weko3_api_list_full.tsv', required=False)
    if full and os.path.exists(full):
        ledger, _H = load_ledger(full)
        rows_res, settled = audit_rows(idx, ledger, a.depth, methods, fac, a.all_stores)

    ser_bad = [s for s in ser if s['resolved'] and s['missing_item_masks']]

    if a.summary_only:
        print(f'応答シリアライザ: {len(ser)} 件 / アイテム4種に1つも届かない: '
              f'{len([s for s in ser_bad if len(s["missing_item_masks"]) == len(ITEM_MASKS)])} 件')
        print(f'None に潰された認可ファクトリ: {len(fac)} 件')
        print(f'本文を返すのにマスクに届かない行: {len(rows_res)} 件'
              f'(ほかに確認済み {settled} 件)')
    else:
        if a.serializers or not (a.factories or a.rows or a.helpers):
            print(f'== A. 応答シリアライザ ({len(ser)} 件) ==')
            for s in ser:
                if not s['resolved']:
                    print(f'  ?  {s["serializer"]}  (解決できず)')
                    continue
                mark = '★' if len(s['missing_item_masks']) == len(ITEM_MASKS) else ' '
                print(f'  {mark}  {s["serializer"]}')
                print(f'       効く: {ja(s["masks"])}'
                      + (f' / 条件付き: {ja(s["masks_conditional"])}'
                         if s['masks_conditional'] else ''))
                print(f'       欠け: {ja(s["missing_item_masks"])}')
            print()
        if a.factories or not (a.serializers or a.rows or a.helpers):
            print(f'== B. None に潰された認可ファクトリ ({len(fac)} 件) ==')
            for f in fac:
                print(f'  {f["file"]}:{f["line"]}  {f["setting"]}')
            print()
        if a.rows or not (a.serializers or a.factories or a.helpers):
            print(f'== C. 本文を返すのにマスクに届かない行 ({len(rows_res)} 件'
                  f' / sec_exposed 記入済みで外した行 {settled} 件) ==')
            for r in rows_res:
                print(f'  no.{r["no"]:<5} {r["method"]:<10} {r["uri"][:62]}')
                print(f'       {r["impl"]}')
                print(f'       効く: {ja(r["masks"])}'
                      + (f' / 条件付き: {ja(r["masks_conditional"])}'
                         if r['masks_conditional'] else ''))
                if r['disabled_by_config']:
                    print('       ★ その条件付きを潰す設定がある: '
                          + ', '.join(r['disabled_by_config']))
            print()
        if a.helpers or not (a.serializers or a.factories or a.rows):
            print('== D. マスクヘルパの fan-in ==')
            for h in helpers:
                print(f'  {h["callers"]:>4}  {h["helper"]:<32} {h["mask_ja"]}')
            print()

    if a.json_out:
        with open(a.json_out, 'w', encoding='utf-8') as f:
            json.dump({'serializers': ser, 'factories': fac,
                       'rows': rows_res, 'helpers': helpers},
                      f, ensure_ascii=False, indent=2)
        print(f'明細を書き出した: {a.json_out}')

    if a.gate and (ser_bad or rows_res):
        sys.exit(1)


if __name__ == '__main__':
    main()
