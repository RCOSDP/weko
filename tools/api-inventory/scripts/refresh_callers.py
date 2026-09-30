# -*- coding: utf-8 -*-
"""inproc_callers を現在のソースから引き直す。

    python3 refresh_callers.py                        # 差分を表示するだけ
    python3 refresh_callers.py --write                # 台帳に書き戻す
    python3 refresh_callers.py --summary-only --gate  # CI 用。ずれがあれば exit 1

**`refresh_impl.py` の後に回すこと。** 記録するのが `ファイル:行番号` なので、
バージョンが変われば必ずずれる(`impl_line` と同じ性質)。

## この列が答えるもの

HTTP 経路として登録されている関数が、**同じプロセスの Python コードからも
直接呼ばれているか**。`weko_items_ui/views.py` が
`from weko_records_ui.views import soft_delete` して `soft_delete(del_value)` を
呼ぶ、という形が該当する。経路を塞いだときに何が道連れになるかの判断材料。

## この列が答えないもの ★

**`なし` は「未使用」という意味ではない。** 呼び出し元は3系統あり、この列が
見るのは1系統目だけである。

| 系統 | 台帳 |
|---|---|
| 1. プロセス内の Python コード | **この列** |
| 2. ブラウザの JS | 持っていない |
| 3. 外部クライアント | 持っていない |

2 を見落として遮断判断に進むと機能が止まる。2026-08-26 の nginx 遮断では
「実呼び出しなし」と分類した3経路(no=301/302/503)を塞いだ結果、ウィジェットの
ファイルアップロードとファイル置換が停止した。いずれも JS から叩かれていた。
**この列だけで「未使用」を判定しないこと。**

## 値

| 値 | 意味 |
|---|---|
| `<区分>:<file>:<line>` を `;` 連結 | 調査済み・プロセス内に呼び出し元あり |
| `なし` | 調査済み・プロセス内に呼び出し元なし(未使用の意味ではない) |
| `未調査` | 調べていない。実ファイルを持たない行(ModelView / framework 自動生成 / pip 由来)と、impl_func を impl_file 内に見つけられなかった行 |

区分は `位置引数` / `キーワード引数` / `参照のみ`(呼ばずに値として渡している)/
`メソッド呼び出し`(クラスメソッド。下記のとおり確度が一段低い)。

## 名前解決

同名の関数が複数のモジュールにあるので、**import を辿らないと解決できない**。
`soft_delete` は v2.0.4 時点で3箇所に定義があり、呼び出し元2箇所はいずれも
直前で `from weko_records_ui.views import soft_delete` している。関数ローカルの
import も相対 import も拾う。

クラスメソッド(`Class.method`)だけは、レシーバまで追わない。クラスを import
しているファイルの中の `.method(` 呼び出しを拾う。関数より確度が低く、
**多めに拾う側**に倒してある(`なし` を誤って出すより安全なため)。
"""
import argparse
import ast
import collections
import os
import re
import sys
import warnings

warnings.filterwarnings('ignore', category=SyntaxWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
from changed_rows import default_weko_root  # noqa: E402

SKIP_DIRS = ('/tests', '/examples', '/.tox', '/node_modules', '/cookiecutter',
             '/docs/', '/build/', '/.git/')

# 実ファイルを持たない実装の総称表記。AST では追えない。
NON_SOURCE_IMPL = re.compile(r'^\((provider|site-packages|framework)|^Flask-Admin ModelView')

NONE = 'なし'
UNKNOWN = '未調査'

# 1セルに並べる件数の上限。超えた分は件数だけ残す(セルが読めなくなるため)。
MAX_SITES = 6


def iter_py(root, sub='modules'):
    base = os.path.join(root, sub)
    for dp, dn, fn in os.walk(base):
        if any(s in dp.replace(os.sep, '/') + '/' for s in SKIP_DIRS):
            dn[:] = []
            continue
        for f in sorted(fn):
            if f.endswith('.py'):
                yield os.path.join(dp, f)


def module_name(root, rel):
    """`modules/weko-records-ui/weko_records_ui/views.py` → `weko_records_ui.views`

    `__init__.py` がある限り上へ辿る。配布名(`weko-records-ui`)は
    パッケージ名ではないので、そこで止まる。
    """
    base = os.path.basename(rel)[:-3]
    names = [] if base == '__init__' else [base]
    d = os.path.dirname(os.path.join(root, rel))
    while os.path.isfile(os.path.join(d, '__init__.py')):
        names.append(os.path.basename(d))
        d = os.path.dirname(d)
    return '.'.join(reversed(names))


def import_map(tree, self_mod):
    """このファイル内の名前 → 完全修飾名。関数ローカル・相対 import も拾う。"""
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            mod = n.module or ''
            if n.level:
                base = self_mod.split('.')[:-n.level]
                mod = '.'.join([x for x in base + ([mod] if mod else []) if x])
            for a in n.names:
                out[a.asname or a.name] = f'{mod}.{a.name}' if mod else a.name
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.asname:
                    out[a.asname] = a.name
                else:
                    head = a.name.split('.')[0]
                    out.setdefault(head, head)
    return out


def dotted(node):
    """`a.b.c` 形式の参照を文字列で返す。それ以外は None。"""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return '.'.join(reversed(parts))


def resolve(name, imap):
    """import 表を使って完全修飾名に直す。一番長い接頭辞から当てる。"""
    segs = name.split('.')
    for i in range(len(segs), 0, -1):
        head = '.'.join(segs[:i])
        if head in imap:
            return '.'.join([imap[head]] + segs[i:])
    return None


def scan(root, wanted):
    """ソース全体を1度だけ読み、参照表を作る。

    `wanted` は台帳が使う末尾名(関数名・クラス名・メソッド名)の集合。
    ここで絞らないと、全モジュールの全参照を抱えることになる。

    戻り値:
      refs       完全修飾名 → [(rel, lineno, 区分)]
      attr_calls rel → {属性名: [lineno]}     … クラスメソッド用
    """
    refs = collections.defaultdict(list)
    attr_calls = collections.defaultdict(lambda: collections.defaultdict(list))
    inst = collections.defaultdict(dict)
    for path in iter_py(root):
        rel = os.path.relpath(path, root)
        try:
            tree = ast.parse(open(path, encoding='utf-8', errors='replace').read())
        except Exception:
            continue
        imap = import_map(tree, module_name(root, rel))

        # `res = ItemResource(...)` のような束縛。`.method(` のレシーバが
        # そのクラスのものかを判定するために要る。
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
                cls = dotted(n.value.func)
                if cls:
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            inst[rel][t.id] = cls.rsplit('.', 1)[-1]

        def record(node, kind):
            d = dotted(node)
            full = resolve(d, imap) if d else None
            if full and full.rsplit('.', 1)[-1] in wanted:
                refs[full].append((rel, node.lineno, kind))

        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            if isinstance(n.func, ast.Attribute) and n.func.attr in wanted:
                recv = dotted(n.func.value)
                attr_calls[rel][n.func.attr].append((n.lineno, recv))
            record(n.func, 'キーワード引数' if n.keywords else '位置引数')
            # 呼ばずに値として渡しているもの(`add_url_rule(..., view_func=f)` 等)。
            # 名前の出現を全部拾うと雑音になるので、引数として渡している場合に限る。
            for x in list(n.args) + [k.value for k in n.keywords]:
                if isinstance(x, (ast.Name, ast.Attribute)):
                    record(x, '参照のみ')
    return refs, attr_calls, inst


def impl_names(value):
    """impl_func から候補名を取り出す。`A→B` は委譲、`A/B` は別名、`f(...)` は内訳。"""
    out = []
    for part in re.split(r'[→/;,]', value or ''):
        part = re.sub(r'\(.*', '', part).strip()
        if part and re.match(r'^[A-Za-z_][\w.]*$', part):
            out.append(part)
    return out


def defs_in(path):
    """ファイル内の定義名を {name, Class.method} で返す。"""
    try:
        tree = ast.parse(open(path, encoding='utf-8', errors='replace').read())
    except Exception:
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(n.name)
        if isinstance(n, ast.ClassDef):
            out.add(n.name)
            for sub in n.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.add(f'{n.name}.{sub.name}')
    return out


def callers_for(root, row_file, row_func, refs, attr_calls, inst, defs):
    """1行ぶんの呼び出し元を返す。impl_file 内に実体が無ければ None(=未調査)。

    `A→B` の委譲で B が別ファイルにある行は、impl_file のモジュール名で
    引いても当たらない。黙って `なし` にすると「呼び出し元が無い」と読めて
    しまうので、解決できなかったことを `未調査` として残す。
    """
    mod = module_name(root, row_file)
    names = [n for n in impl_names(row_func) if n in defs
             or n.rsplit('.', 1)[-1] in defs]
    if not mod or not names:
        return None
    sites = set()
    for name in names:
        if '.' in name:                       # Class.method
            # レシーバまで確かめる。`.get(` のような一般的なメソッド名は、
            # クラスを import しているだけのファイルで大量に当たるため
            # (no=113 は素朴に数えると 319 件になった)。
            cls, meth = name.rsplit('.', 1)
            for rel, _ln, _k in refs.get(f'{mod}.{cls}', []):
                if rel == row_file:
                    continue
                for ln, recv in attr_calls.get(rel, {}).get(meth, []):
                    if recv is None or recv == 'self':
                        continue
                    tail = recv.rsplit('.', 1)[-1]
                    if tail == cls or inst.get(rel, {}).get(tail) == cls:
                        sites.add((rel, ln, 'メソッド呼び出し'))
        else:
            for rel, ln, kind in refs.get(f'{mod}.{name}', []):
                if rel != row_file:
                    sites.add((rel, ln, kind))
    return sorted(sites, key=lambda s: (s[0], s[1], s[2]))


def format_sites(sites):
    if not sites:
        return NONE
    head = sites[:MAX_SITES]
    out = ';'.join(f'{k}:{rel}:{ln}' for rel, ln, k in head)
    if len(sites) > MAX_SITES:
        out += f';…(他{len(sites) - MAX_SITES}件)'
    return out


def main():
    p = argparse.ArgumentParser(description='inproc_callers を引き直す')
    p.add_argument('--full', default=None,
                   help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--root', default=None, help='解析対象の WEKO3 チェックアウト')
    p.add_argument('--write', action='store_true', help='台帳に書き戻す')
    p.add_argument('--summary-only', action='store_true',
                   help='件数だけ出す(public な CI 用。no も経路名もファイル名も出さない)')
    p.add_argument('--gate', action='store_true',
                   help='台帳とソースがずれていれば終了コード1')
    a = p.parse_args()

    tsv = a.full or data_path('weko3_api_list_full.tsv')
    root = a.root or default_weko_root()
    rows = [l.rstrip('\n').split('\t') for l in open(tsv, encoding='utf-8') if l.rstrip('\n')]
    head = {n: i for i, n in enumerate(rows[0])}
    if 'inproc_callers' not in head:
        sys.exit('台帳に inproc_callers 列がありません。'
                 '列の追加は schema.py と README を直してから行ってください。')
    col = head['inproc_callers']

    # 台帳が使う末尾名だけを集めてから走査する(全参照を抱えないため)
    wanted = set()
    for r in rows[1:]:
        for name in impl_names(r[head['impl_func']] if len(r) > head['impl_func'] else ''):
            wanted.add(name.rsplit('.', 1)[-1])
            if '.' in name:
                wanted.add(name.split('.')[0])       # クラス名
    refs, attr_calls, inst = scan(root, wanted)

    changed, found, none_, unknown, unresolved = [], 0, 0, 0, []
    defcache = {}
    for r in rows[1:]:
        r += [''] * (len(rows[0]) - len(r))
        f = r[head['impl_file']]
        if f == '-' or NON_SOURCE_IMPL.match(f) or not os.path.isfile(os.path.join(root, f)):
            new = UNKNOWN                      # AST で追えない行
        else:
            full_path = os.path.join(root, f)
            if full_path not in defcache:
                defcache[full_path] = defs_in(full_path)
            sites = callers_for(root, f, r[head['impl_func']], refs, attr_calls,
                                inst, defcache[full_path])
            if sites is None:
                new = UNKNOWN
                unresolved.append((r[0], f, r[head['impl_func']]))
            else:
                new = format_sites(sites)
        if new == UNKNOWN:
            unknown += 1
        elif new == NONE:
            none_ += 1
        else:
            found += 1
        if r[col] != new:
            changed.append((r[0], r[col][:40], new[:60]))
            r[col] = new

    if a.summary_only:
        print(f'inproc_callers: 呼び出し元あり {found} / なし {none_} / '
              f'未調査 {unknown} / 台帳とのずれ {len(changed)} 行')
    else:
        print(f'{tsv}: 呼び出し元あり {found} / なし {none_} / 未調査 {unknown} '
              f'(変更 {len(changed)} 行)')
        for c in changed[:30]:
            print(f'  no={c[0]:<5} {c[1] or "(空)"} -> {c[2]}')
        if len(changed) > 30:
            print(f'  ... 他 {len(changed) - 30} 件')
        for u in unresolved[:10]:
            print(f'  ★impl_func を impl_file 内に見つけられない no={u[0]:<5} {u[1]}  {u[2]}')
        if len(unresolved) > 10:
            print(f'  ... 他 {len(unresolved) - 10} 件')

    if a.write and changed:
        open(tsv, 'w', encoding='utf-8').write(
            '\n'.join('\t'.join(x) for x in rows) + '\n')
        print(f'  → {len(changed)} 行の inproc_callers を書き戻した')
    elif not a.write and not a.summary_only:
        print('  (--write を付けると書き戻す)')

    # 認可を足す PR で、HTTP 以外の入口を持つビューを素通りさせないためのゲート。
    # add_inproc_callers.py が持っていた --check --gate の後継。あちらは
    # 「台帳に無い呼び出し元が現れた」方向だけを見ていたが、こちらは消えた方向も
    # ずれとして数える。台帳を更新せずにソースを変えたことを止めるのが目的なので、
    # 向きで区別しない。
    if a.gate and changed:
        sys.exit(1)


if __name__ == '__main__':
    main()
