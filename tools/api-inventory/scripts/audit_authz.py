# -*- coding: utf-8 -*-
"""入口の**先**にある認可の欠陥を、ソース(AST)だけから拾う。

    python3 audit_authz.py                    # 3つの検知のサマリ
    python3 audit_authz.py --helpers          # 認可ヘルパを fan-in 順に並べる
    python3 audit_authz.py --id-binding       # 識別子突合の欠落(明細)
    python3 audit_authz.py --authz-input      # 認可判定の入力を書き換えられる経路(明細)
    python3 audit_authz.py --json out.json    # 明細を JSON で
    python3 audit_authz.py --gate             # 検知があれば exit 1
    python3 audit_authz.py --summary-only     # 件数だけ(public CI 用)

## なぜ要るか

台帳の `auth_method` / `auth_mechanism` / `bola_risk` は**エンドポイントの入口**を見る。
「デコレータが付いているか」「認可らしき関数を呼んでいるか」までは機械で分かるが、
**呼んだ先が何を検証しているか**は見ていない。これは意図した割り切りだった
(エンドポイントが1000本あり、全部の呼び出し先まで追う時間は無い)。

その割り切りは実際に穴になった。認可の判断が入口から数段先のヘルパに置かれて
いると、入口の近くを読んだだけでは「認可している」ようにしか見えない。呼び出しが
確かに在るからである。**呼び出しの存在は、その呼び出しが何を保証しているかを
何も語らない。** 具体的な事例は非公開側の調査記録にある。

そこで本スクリプトは「認可らしき呼び出しが**在るか**」ではなく、
**その認可が何と何を結び付けているか**を見る。全エンドポイントを人手で深追い
する代わりに、次の3つに絞って機械で拾う。

| 検知 | 何を見るか |
|---|---|
| A. 識別子突合の欠落 | リクエスト由来の値で対象を引きながら、引いた対象とリクエストの識別子を照合していない |
| B. 認可入力汚染 | 認可判定関数が読むフィールドを、別のエンドポイントが書ける |
| C. 認可ヘルパの fan-in | エンドポイントから到達する認可ヘルパを参照本数順に並べる |

C は指摘ではなく**精査の順番**を出す。1048 本のエンドポイントを個別に追うのは
無理でも、そこから到達する認可ヘルパは数十本に収束する。参照本数の多い順に
ヘルパ側をレビューすれば、同じ工数で覆う範囲がまるで変わる。

## 精度について

A・B はヒューリスティックで、**偽陽性を許して取りこぼしを減らす**側に振っている
(`detect_routes.py` と同じ思想)。出力は「指摘」ではなく**確認待ちの行列**であり、
確認した結果を台帳の `sec_pattern` / `sec_detail` に書くことで消える。
`--gate` を CI で使うときは、確認済みの行を許可リストに登録して差分だけを見ること。
"""
import argparse
import ast
import collections
import json
import os
import re
import sys
import textwrap
import warnings

warnings.filterwarnings('ignore', category=SyntaxWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
from snapshot import default_weko_root  # noqa: E402

SKIP_DIRS = ('/tests', '/examples', '/.tox', '/node_modules', '/cookiecutter',
             '/docs/', '/build/', '/.git/')

# 認可の判断をしている関数の名前。ヘルパの棚卸し(C)と、認可判定が読む
# フィールドの収集(B)の両方で使う。
AUTHZ_FUNC = re.compile(
    r'^(check_[a-z_]*(authority|permission|access|owner|created)'
    r'|can_[a-z_]+'
    r'|is_[a-z_]*(permitted|accessible|owner|admin|editable)'
    r'|has_[a-z_]*permission'
    r'|validate_[a-z_]*(token|access|permission|url|download|authority)'
    r'|verify_[a-z_]+'
    r'|[a-z_]*permission_factory'
    r'|[a-z_]*_authority[a-z_]*'
    r'|authorize[a-z_]*)$')

# 「対象をリクエスト由来の値から引く」呼び出し。引いた時点では、その対象が
# リクエスト元に属するものかはまだ確かめられていない。
FETCH_BY_ID = re.compile(
    r'^(get_by_id|get_or_404|get_record|get_activity|get_by_token'
    r'|get_onetime_download|get_secret_download|get_by_key'
    r'|parse_[a-z_]*token|convert_token_into_obj'
    r'|filter_by|get_by_object_version|resolve)$')

# 持っているだけで通る値(ケイパビリティ)。トークン、発行済みURLの行 ID など。
# 「本人であること」ではなく「この値を持っていること」しか示さないので、
# **何に対する権利なのか**を別途確かめないと対象を差し替えられる。
CAPABILITY = re.compile(r'^([a-z_]*token|[a-z_]*_url_id|secret_url_id|onetime_url_id)$')

# トークンを解いて中身を取り出す呼び出し。左辺に出てくる値は、パス由来では
# なく**トークン由来**として扱う。
TOKEN_CALL = re.compile(
    r'^(parse_[a-z_]*token|decode_[a-z_]*token|convert_token_into_obj|get_by_token)$')

# URL パス・クエリ・ボディから来る識別子。**実際に配信/更新される対象**を決める。
REQUEST_ID = re.compile(
    r'^(pid|pid_value|recid|record_id|rec_id|filename|file_name|key'
    r'|activity_id|item_id|bucket_id|object_version|version_id'
    r'|community_id|index_id|group_id|user_id|token|secret_token'
    r'|guest_mail|user_mail|email)$')

# 突合に使われていれば「引いた対象とリクエストが結び付いている」と読める属性名。
BOUND_ATTR = re.compile(
    r'^(record_id|rec_id|file_name|filename|pid_value|recid|id'
    r'|user_mail|guest_mail|email|owner|owner_id|owners|created_by'
    r'|user_id|activity_id|item_id|bucket_id|key)$')

# request.* / kwargs.* から値を取り出す入れ物。
REQUEST_HOLDER = re.compile(
    r'^(kwargs|request|post_data|json_data|data|payload|form|args|values|body)$')

# 認可判定が読んでいても「フィールド」とは呼べない名前。B の収集から外す。
FIELD_STOPWORDS = {
    'get', 'json', 'query', 'config', 'app', 'current_app', 'session', 'id',
    'items', 'keys', 'values', 'append', 'update', 'format', 'split', 'strip',
    'lower', 'upper', 'join', 'filter_by', 'first', 'one', 'all', 'count',
    'name', 'value', 'type', 'data', 'result', 'error', 'message', 'status',
}


# --------------------------------------------------------------------------
# ソースの索引
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


class Index:
    """`modules/` 配下の関数を1度だけ読み、名前で引けるようにする。

    台帳の1048行が指す実装から呼び出しを辿るので、ファイルを何度も開かない。
    """

    def __init__(self, root):
        self.root = root
        self.funcs = {}          # (rel, qualname) -> FunctionDef
        self.by_name = collections.defaultdict(list)   # 単純名 -> [(rel, qual)]
        for path in iter_py(root):
            rel = os.path.relpath(path, root)
            try:
                tree = ast.parse(open(path, encoding='utf-8', errors='replace').read())
            except Exception:
                continue
            self._collect(rel, tree, prefix='')

    def _collect(self, rel, node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                self._collect(rel, child, prefix + child.name + '.')
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = prefix + child.name
                self.funcs[(rel, qual)] = child
                self.by_name[child.name].append((rel, qual))
                # ネストした関数も拾う(認可判定を内側の関数に書く実装がある)
                self._collect(rel, child, qual + '.')

    def find(self, rel, name):
        """(ファイル, 関数名) で引く。同名が複数あるときは同一ファイルを優先する。"""
        for qual in (name, ):
            if (rel, qual) in self.funcs:
                return rel, qual, self.funcs[(rel, qual)]
        for r, qual in self.by_name.get(name.split('.')[-1], []):
            if r == rel:
                return r, qual, self.funcs[(r, qual)]
        cands = self.by_name.get(name.split('.')[-1], [])
        if len(cands) == 1:
            r, qual = cands[0]
            return r, qual, self.funcs[(r, qual)]
        return None

    def closure(self, rel, name, depth):
        """実装関数から `depth` 段だけ呼び出しを辿り、到達した関数を返す。

        「入口だけ見て終わりにしない」ための唯一の仕掛けなので、段数は
        引数で変えられるようにしてある(既定3段)。段数を増やすほど
        取りこぼしは減るが、無関係なユーティリティまで混ざる。
        """
        start = self.find(rel, name)
        if not start:
            return []
        seen = {(start[0], start[1])}
        out = [start]
        frontier = [start]
        for _ in range(max(0, depth - 1)):
            nxt = []
            for r, _qual, node in frontier:
                for callee in called_names(node):
                    got = self.find(r, callee)
                    if got and (got[0], got[1]) not in seen:
                        seen.add((got[0], got[1]))
                        out.append(got)
                        nxt.append(got)
            frontier = nxt
            if not frontier:
                break
        return out


# --------------------------------------------------------------------------
# 関数から読み取る事実
# --------------------------------------------------------------------------

def call_name(node):
    """呼び出しの末尾の名前を返す。`a.b.c()` なら `c`。"""
    f = node.func if isinstance(node, ast.Call) else node
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ''


def called_names(fn):
    return {call_name(n) for n in ast.walk(fn) if isinstance(n, ast.Call)}


def request_names(fn):
    """URL パス・クエリ・ボディから受け取る識別子の名前を集める。

    これが「**攻撃者が選ぶ配信対象**」の側。
      - 引数名 (`def download(pid, record, filename, **kwargs)`)
      - `kwargs.get('filename')` / `request.args.get('pid_value')` の取り出し

    トークンを解いて出てきた値は**ここに入れない**(`capability_names` が持つ)。
    両方を「リクエスト由来」として一緒くたにすると、片方でもう片方を検証した
    ことにしてしまい、今回の欠陥がそのまま「突合済み」に見える。
    """
    names = set()
    for a in list(fn.args.args) + list(fn.args.kwonlyargs):
        if REQUEST_ID.match(a.arg):
            names.add(a.arg)
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and call_name(n) == 'get':
            base = n.func.value if isinstance(n.func, ast.Attribute) else None
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name) and REQUEST_HOLDER.match(base.id):
                for arg in n.args[:1]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        names.add(arg.value)
    return names


def capability_names(fn):
    """「持っているだけで通る値」と、そこから解けた値の名前を集める。

        owner_id, mail, date, sig = parse_download_token(token)

    左辺の `owner_id` は URL パスの値ではなく**トークンの中身**で、攻撃者が
    正規に発行を受けた自分のトークンに由来する。配信対象を決めるパス側の
    識別子とは出どころが違う。
    """
    caps = {a.arg for a in list(fn.args.args) + list(fn.args.kwonlyargs)
            if CAPABILITY.match(a.arg)}
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) \
                and TOKEN_CALL.match(call_name(n.value)):
            for t in n.targets:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name):
                        caps.add(sub.id)
    return caps


def fetched_objects(fn, caps):
    """ケイパビリティから引いた対象が、どの変数に入ったかを返す。

    `url_obj = convert_token_into_obj(token, is_secret_url)` の `url_obj`。
    引数にトークンや発行済み URL の行 ID を渡している呼び出しだけを対象にする。
    パスの ID だけで引く素朴な参照は、所有者チェックの有無の問題(`bola_risk`)
    であって、ここで見たい「ケイパビリティと対象の食い違い」ではない。
    """
    out = {}
    for n in ast.walk(fn):
        if not isinstance(n, ast.Assign):
            continue
        fetch = None
        for sub in ast.walk(n.value):
            if not (isinstance(sub, ast.Call) and FETCH_BY_ID.match(call_name(sub))):
                continue
            used = {x.id for x in ast.walk(sub) if isinstance(x, ast.Name)}
            used |= {k.arg for k in sub.keywords if k.arg}
            if TOKEN_CALL.match(call_name(sub)) or (used & caps) \
                    or any(CAPABILITY.match(u) for u in used):
                fetch = call_name(sub)
                break
        if not fetch:
            continue
        for t in n.targets:
            for sub in ast.walk(t):
                if isinstance(sub, ast.Name):
                    out[sub.id] = fetch
    return out


def binding_compares(fn, objs, path_ids):
    """「ケイパビリティで引いた対象」と「パスで指定された対象」の突合を返す。

    `obj.owner_id == pid.pid_value` のように、**引いた対象の属性**と
    **パス由来の識別子**が同じ比較式に現れるものだけを数える。トークンの
    ハッシュ照合・有効期限・ダウンロード回数の比較はいくらあっても対象の
    同一性を担保しないので、ここには入らない。

    対象の変数名で縛るのは、無関係なヘルパの中にたまたまある
    `file.get('filename') == file_name` のような比較を「突合済み」と
    読んでしまうのを防ぐため(実際にこれで今回の脆弱行を取りこぼした)。
    """
    hits = []
    for n in ast.walk(fn):
        if not isinstance(n, ast.Compare) or not any(
                isinstance(o, (ast.Eq, ast.NotEq, ast.In, ast.NotIn)) for o in n.ops):
            continue
        bound, from_path = set(), set()
        for s in [n.left] + list(n.comparators):
            for sub in ast.walk(s):
                if isinstance(sub, ast.Attribute):
                    base = sub.value
                    if isinstance(base, ast.Name) and base.id in objs \
                            and BOUND_ATTR.match(sub.attr):
                        bound.add(f'{base.id}.{sub.attr}')
                    elif sub.attr in path_ids:
                        from_path.add(sub.attr)
                elif isinstance(sub, ast.Name) and sub.id in path_ids:
                    from_path.add(sub.id)
                elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) \
                        and sub.value in path_ids:
                    from_path.add(sub.value)
        if bound and from_path:
            hits.append(f'{sorted(bound)[0]} ↔ {sorted(from_path)[0]}')
    return hits


def authz_fields(fn):
    """認可判定関数が読んでいるフィールド名を集める(検知 B の素材)。

    `obj.editor_ids` / `meta.json.get('reviewer')` のような
    「判定材料」を拾う。名前だけでは判定材料かどうか決まらないので、
    ここは広めに取り、台帳の `body_params`(=実際に外から書ける項目)と
    突き合わせて絞る。
    """
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Attribute) and not n.attr.startswith('_'):
            out.add(n.attr)
        if isinstance(n, ast.Call) and call_name(n) == 'get':
            for arg in n.args[:1]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    out.add(arg.value)
    return {f for f in out
            if f not in FIELD_STOPWORDS and len(f) > 3 and re.match(r'^[a-z][a-z0-9_]*$', f)}


# --------------------------------------------------------------------------
# add_authmech.py から使う入口(ソース片1つを judge する)
# --------------------------------------------------------------------------

def id_binding(src):
    """関数のソース片を見て `ok` / `missing` / `n/a` を返す。

    `add_authmech.py` が `bola_risk` を決めるときに使う。「所有者チェックらしき
    呼び出しが在る」ことと「それが効いている」ことを区別するための判定で、
    ソース片が構文として読めなければ `n/a`(判断しない)。
    """
    if not src or not src.strip():
        return 'n/a'
    for text in (src, textwrap.dedent(src)):
        try:
            tree = ast.parse(text)
            break
        except SyntaxError:
            tree = None
    if tree is None:
        return 'n/a'
    funcs = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    path_ids, caps = set(), set()
    for node in funcs:
        path_ids |= request_names(node)
        caps |= capability_names(node)
    objs, comp = {}, []
    for node in funcs:
        objs.update(fetched_objects(node, caps))
    for node in funcs:
        comp += binding_compares(node, objs, path_ids)
    if not objs or not path_ids:
        return 'n/a'
    return 'ok' if comp else 'missing'


# --------------------------------------------------------------------------
# 台帳
# --------------------------------------------------------------------------

# `A→B` は委譲(A が入口、B が実体)、`A/B` は同一実装の別名、`f(...)` の
# 括弧内は経路の内訳。いずれも実体の関数名を取り出す。
IMPL_SPLIT = re.compile(r'[→/;,]')


def impl_names(value):
    out = []
    for part in IMPL_SPLIT.split(value or ''):
        part = re.sub(r'\(.*', '', part).strip()
        if part and part not in ('-', 'TODO') and re.match(r'^[A-Za-z_][\w.]*$', part):
            out.append(part)
    return out


def load_ledger(path):
    rows = [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8')
            if l.rstrip('\n')]
    return rows[0], rows[1:], {n: i for i, n in enumerate(rows[0])}


def cell(row, H, name):
    i = H.get(name)
    return row[i] if i is not None and len(row) > i else ''


def body_fields(value):
    """`body_params` を項目名の集合にする。`editor_ids(必須)` → `editor_ids`。"""
    out = set()
    for part in re.split(r'[;,、]', value or ''):
        part = re.sub(r'[(（※].*', '', part).strip()
        if part and re.match(r'^[a-z][a-z0-9_]*$', part):
            out.add(part)
    return out


WRITE_METHODS = {'POST', 'PUT', 'DELETE', 'PATCH'}

NON_SOURCE_IMPL = re.compile(r'^\((provider|site-packages|framework)|^Flask-Admin ModelView')


# --------------------------------------------------------------------------
# 検知
# --------------------------------------------------------------------------

def audit(root, ledger_path, depth=3):
    idx = Index(root)
    hdr, rows, H = load_ledger(ledger_path)

    # --- 認可判定関数が読むフィールド(B の素材) -------------------------
    fields_read = collections.defaultdict(set)      # field -> {関数の所在}
    for (rel, qual), node in idx.funcs.items():
        if AUTHZ_FUNC.match(qual.split('.')[-1]):
            for f in authz_fields(node):
                fields_read[f].add(f'{rel}:{qual}')

    id_missing, authz_input, helper_fanin = [], [], collections.defaultdict(set)

    for row in rows:
        no = cell(row, H, 'no')
        uri = cell(row, H, 'uri')
        impl_file = cell(row, H, 'impl_file')
        if NON_SOURCE_IMPL.match(impl_file or '-'):
            continue
        methods = {m.strip().upper() for m in cell(row, H, 'method').split(',')}

        reached = []
        for name in impl_names(cell(row, H, 'impl_func')):
            reached += idx.closure(impl_file, name, depth)
        if not reached:
            continue

        # --- C. 認可ヘルパの fan-in -----------------------------------
        for rel, qual, _node in reached:
            if AUTHZ_FUNC.match(qual.split('.')[-1]):
                helper_fanin[f'{rel}:{qual}'].add(no)

        # --- A. 識別子突合の欠落 --------------------------------------
        path_ids, caps = set(), set()
        for _rel, _qual, node in reached:
            path_ids |= request_names(node)
            caps |= capability_names(node)
        objs, where, comp = {}, {}, []
        for rel, qual, node in reached:
            got = fetched_objects(node, caps)
            objs.update(got)
            for v in got:
                where[v] = f'{rel}:{qual}'
        for _rel, _qual, node in reached:
            comp += binding_compares(node, objs, path_ids)
        if objs and path_ids and not comp:
            id_missing.append({
                'no': no, 'uri': uri, 'method': ','.join(sorted(methods)),
                'impl': f"{impl_file}:{cell(row, H, 'impl_line')}",
                'fetched_by': sorted(f'{v}={c}' for v, c in objs.items()),
                'request_ids': sorted(path_ids),
                'where': sorted(set(where.values())),
                'sec_pattern': cell(row, H, 'sec_pattern'),
            })

        # --- B. 認可入力汚染 ------------------------------------------
        if methods & WRITE_METHODS:
            hit = sorted(body_fields(cell(row, H, 'body_params')) & set(fields_read))
            if hit:
                authz_input.append({
                    'no': no, 'uri': uri, 'method': ','.join(sorted(methods & WRITE_METHODS)),
                    'impl': f"{impl_file}:{cell(row, H, 'impl_line')}",
                    'fields': hit,
                    'read_by': sorted({w for f in hit for w in fields_read[f]})[:4],
                    'auth_method': cell(row, H, 'auth_method'),
                    'sec_pattern': cell(row, H, 'sec_pattern'),
                })

    helpers = sorted(((k, sorted(v)) for k, v in helper_fanin.items()),
                     key=lambda kv: (-len(kv[1]), kv[0]))
    return {'id_binding': id_missing, 'authz_input': authz_input,
            'helpers': helpers, 'rows': len(rows)}


# --------------------------------------------------------------------------
# 出力
# --------------------------------------------------------------------------

def render(res, a):
    L = ['# 認可の中身の検査 (audit_authz.py)', '',
         f"- 台帳: {res['rows']} 行", f'- 呼び出しを辿った段数: {a.depth}', '']
    L += ['| 検知 | 件数 |', '|---|---:|',
          f"| A. 識別子突合の欠落 | {len(res['id_binding'])} |",
          f"| B. 認可入力汚染 | {len(res['authz_input'])} |",
          f"| C. 認可ヘルパ(fan-in 順) | {len(res['helpers'])} |", '']
    if a.summary_only:
        return '\n'.join(L)

    show_all = not (a.id_binding or a.authz_input or a.helpers)

    if (a.id_binding or show_all) and res['id_binding']:
        L += ['## A. 識別子突合の欠落', '',
              'リクエスト由来の値で対象を引きながら、引いた対象とリクエストの',
              '識別子を照合していない。有効なトークン/ID を1つ持っていれば、',
              '対象だけ差し替えて別リソースに届きうる。', '']
        for d in res['id_binding'][:a.limit]:
            L.append(f"- no={d['no']} `{d['method']} {d['uri'][:64]}` — "
                     f"{d['impl']}\n"
                     f"    - 対象の引き方: {', '.join(d['fetched_by'][:4])}"
                     f" ({', '.join(d['where'][:2])})\n"
                     f"    - リクエスト由来の識別子: {', '.join(d['request_ids'][:6])}")
        if len(res['id_binding']) > a.limit:
            L.append(f"- … 他 {len(res['id_binding']) - a.limit} 行")
        L.append('')

    if (a.authz_input or show_all) and res['authz_input']:
        L += ['## B. 認可入力汚染', '',
              '認可判定関数が読んでいるフィールドを、このエンドポイントが',
              'リクエストボディで書き換えられる。入口の認可は通っていても、',
              '以降のアクションの認可判定が汚染される。', '']
        for d in res['authz_input'][:a.limit]:
            L.append(f"- no={d['no']} `{d['method']} {d['uri'][:64]}` — {d['impl']}\n"
                     f"    - 書ける項目: {', '.join(d['fields'])}\n"
                     f"    - 判定に読んでいる側: {', '.join(d['read_by'])}\n"
                     f"    - この行の認可: {d['auth_method'][:60]}")
        if len(res['authz_input']) > a.limit:
            L.append(f"- … 他 {len(res['authz_input']) - a.limit} 行")
        L.append('')

    if (a.helpers or show_all) and res['helpers']:
        L += ['## C. 認可ヘルパ(参照本数の多い順)', '',
              'エンドポイントを1本ずつ深追いする代わりに、ここを上から潰す。',
              '1本のヘルパの欠陥が、そのまま右列の本数ぶんの経路に効く。', '']
        L += ['| ヘルパ | 参照するエンドポイント数 |', '|---|---:|']
        for name, nos in res['helpers'][:a.limit]:
            L.append(f'| `{name}` | {len(nos)} |')
        if len(res['helpers']) > a.limit:
            L.append(f"| … 他 {len(res['helpers']) - a.limit} 本 | |")
        L.append('')
    return '\n'.join(L)


def main():
    p = argparse.ArgumentParser(description='入口より深い認可の欠陥を AST で拾う')
    p.add_argument('--root', default=None, help='解析対象の WEKO3 チェックアウト')
    p.add_argument('--full', default=None,
                   help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--depth', type=int, default=3, help='呼び出しを辿る段数(既定 3)')
    p.add_argument('--limit', type=int, default=40, help='明細の表示件数')
    p.add_argument('--id-binding', action='store_true', help='A だけ出す')
    p.add_argument('--authz-input', action='store_true', help='B だけ出す')
    p.add_argument('--helpers', action='store_true', help='C だけ出す')
    p.add_argument('--json', default=None)
    p.add_argument('--out', default=None)
    p.add_argument('--summary-only', action='store_true', help='件数のみ(public CI 用)')
    p.add_argument('--gate', action='store_true', help='A または B の検知があれば exit 1')
    a = p.parse_args()

    root = a.root or default_weko_root()
    full = a.full or data_path('weko3_api_list_full.tsv')
    res = audit(root, full, depth=a.depth)

    md = render(res, a)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(md + '\n')
        print(f'{a.out} を書き出しました')
    else:
        print(md)
    if a.json:
        json.dump({'meta': {'weko_root': root, 'depth': a.depth}, **res},
                  open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'{a.json} を書き出しました')

    if a.gate and (res['id_binding'] or res['authz_input']):
        sys.exit(1)


if __name__ == '__main__':
    main()
