# -*- coding: utf-8 -*-
"""refresh_callers.py — inproc_callers(プロセス内の呼び出し元)を引き直す。

この列は「経路を塞いだら何が道連れになるか」の判断材料で、**`なし` を誤って
出すのが一番まずい**。2026-08-26 の nginx 遮断では「実呼び出しなし」と分類した
3経路を塞いでウィジェットのファイルアップロードとファイル置換が止まっている。

そこで次の2点を固定する:

  - 同名の別モジュールの関数と取り違えないこと(import を辿る)
  - 解決できなかったものを `なし` に落とさないこと(`未調査` として残す)
"""
import textwrap

import pytest

import refresh_callers
from conftest import FULL_HEADER, make_row, run, write_full

H = {n: i for i, n in enumerate(FULL_HEADER)}

TARGET = 'modules/weko-demo/weko_demo/views.py'
OTHER = 'modules/weko-other/weko_other/caller.py'


def src(text):
    return textwrap.dedent(text).lstrip('\n')


@pytest.fixture
def repo(fake_repo):
    """`weko_demo` と `weko_other` の2パッケージを持つ最小リポジトリ。"""
    fake_repo('modules/weko-demo/weko_demo/__init__.py', '')
    fake_repo('modules/weko-other/weko_other/__init__.py', '')
    return fake_repo


def callers(tmp_path, repo, target_src, other_src='', impl_func='soft_delete',
            impl_file=TARGET, **over):
    """1行の台帳に refresh_callers.py を掛けて inproc_callers を返す。"""
    repo(TARGET, target_src)
    if other_src:
        repo(OTHER, other_src)
    row = make_row(impl_func=impl_func, impl_file=impl_file, impl_line='1',
                   inproc_callers='-', **over)
    tsv = write_full(tmp_path / 'full.tsv', [row])
    run('refresh_callers.py', '--root', repo.root, '--full', tsv, '--write',
        expect=0)
    line = open(tsv, encoding='utf-8').read().rstrip('\n').split('\n')[1].split('\t')
    return line[H['inproc_callers']]


TARGET_SRC = src('''
    def soft_delete(recid):
        return recid
''')


# --- 名前解決 --------------------------------------------------------------

def test_importを辿って呼び出し元を特定する(tmp_path, repo):
    v = callers(tmp_path, repo, TARGET_SRC, src('''
        from weko_demo.views import soft_delete


        def purge(x):
            soft_delete(x)
    '''))
    assert v == f'位置引数:{OTHER}:5'


def test_同名の別モジュールの関数と取り違えない(tmp_path, repo):
    """`soft_delete` は v2.0.4 時点で3箇所に定義がある。名前だけで突き合わせると
    別モジュールの呼び出しを拾い、「呼び出し元あり」が嘘になる。"""
    v = callers(tmp_path, repo, TARGET_SRC, src('''
        from weko_somewhere.utils import soft_delete


        def purge(x):
            soft_delete(x)
    '''))
    assert v == refresh_callers.NONE


def test_関数ローカルのimportも拾う(tmp_path, repo):
    """実際の呼び出し元は循環 import を避けて関数の中で import している。"""
    v = callers(tmp_path, repo, TARGET_SRC, src('''
        def purge(x):
            from weko_demo.views import soft_delete
            soft_delete(x)
    '''))
    assert v == f'位置引数:{OTHER}:3'


def test_相対importも拾う(tmp_path, repo):
    repo('modules/weko-demo/weko_demo/other.py', src('''
        from .views import soft_delete


        def purge(x):
            soft_delete(x)
    '''))
    v = callers(tmp_path, repo, TARGET_SRC)
    assert v == '位置引数:modules/weko-demo/weko_demo/other.py:5'


def test_モジュールを丸ごとimportした呼び出しも拾う(tmp_path, repo):
    v = callers(tmp_path, repo, TARGET_SRC, src('''
        import weko_demo.views


        def purge(x):
            weko_demo.views.soft_delete(x)
    '''))
    assert v == f'位置引数:{OTHER}:5'


def test_自分のファイル内の呼び出しは数えない(tmp_path, repo):
    """同じファイルの中で呼び合っているのは「別の経路から使われている」ではない。"""
    v = callers(tmp_path, repo, TARGET_SRC + src('''

        def wrapper(x):
            return soft_delete(x)
    '''))
    assert v == refresh_callers.NONE


# --- 区分 ------------------------------------------------------------------

@pytest.mark.parametrize('call,kind', [
    ('soft_delete(x)', '位置引数'),
    ('soft_delete(recid=x)', 'キーワード引数'),
    ('register(view_func=soft_delete)', '参照のみ'),
])
def test_呼び出しの形を区分として記録する(tmp_path, repo, call, kind):
    v = callers(tmp_path, repo, TARGET_SRC, src(f'''
        from weko_demo.views import soft_delete


        def purge(x):
            {call}
    '''))
    assert v.startswith(kind + ':'), v


# --- クラスメソッド --------------------------------------------------------

CLASS_SRC = src('''
    class QueryRecordViewCount(object):
        def get(self, record_id):
            return record_id
''')


def test_クラスメソッドはレシーバを確かめる(tmp_path, repo):
    """`.get(` はどこにでもある。クラスを import しているだけのファイルで
    素朴に数えると、実データで1行に 319 件付いた。"""
    v = callers(tmp_path, repo, CLASS_SRC, src('''
        from weko_demo.views import QueryRecordViewCount


        def run(d):
            return d.get('key')          # 無関係な dict.get
    '''), impl_func='QueryRecordViewCount.get')
    assert v == refresh_callers.NONE


def test_インスタンス経由のメソッド呼び出しは拾う(tmp_path, repo):
    v = callers(tmp_path, repo, CLASS_SRC, src('''
        from weko_demo.views import QueryRecordViewCount


        def run(rid):
            res = QueryRecordViewCount()
            return res.get(rid)
    '''), impl_func='QueryRecordViewCount.get')
    assert v.startswith('メソッド呼び出し:')


# --- 解決できなかったもの --------------------------------------------------

def test_実ファイルを持たない行は未調査(tmp_path, repo):
    """ModelView / framework 自動生成 / pip 由来は AST で追えない。"""
    v = callers(tmp_path, repo, TARGET_SRC,
                impl_file='Flask-Admin ModelView(自動生成)')
    assert v == refresh_callers.UNKNOWN


def test_実体を見つけられない行はなしにせず未調査にする(tmp_path, repo):
    """`なし` にすると「呼び出し元が無い」と読める。調べられなかったことと
    調べて無かったことは、この列では結論が正反対になる。"""
    v = callers(tmp_path, repo, TARGET_SRC, impl_func='create_blueprint.<locals>.index')
    assert v == refresh_callers.UNKNOWN


def test_呼び出し元が無ければなし(tmp_path, repo):
    assert callers(tmp_path, repo, TARGET_SRC) == refresh_callers.NONE


# --- 運用 ------------------------------------------------------------------

def test_二度流しても結果が変わらない(tmp_path, repo):
    """バージョンアップのたびに回す列なので、冪等でないと差分が出続ける。"""
    repo(TARGET, TARGET_SRC)
    repo(OTHER, src('''
        from weko_demo.views import soft_delete


        def purge(x):
            soft_delete(x)
    '''))
    tsv = write_full(tmp_path / 'full.tsv', [
        make_row(impl_func='soft_delete', impl_file=TARGET, impl_line='1',
                 inproc_callers='-')])
    run('refresh_callers.py', '--root', repo.root, '--full', tsv, '--write', expect=0)
    once = open(tsv, encoding='utf-8').read()
    p = run('refresh_callers.py', '--root', repo.root, '--full', tsv, '--write', expect=0)
    assert open(tsv, encoding='utf-8').read() == once
    assert '変更 0 行' in p.stdout


def test_writeを付けなければ書き換えない(tmp_path, repo):
    repo(TARGET, TARGET_SRC)
    tsv = write_full(tmp_path / 'full.tsv', [
        make_row(impl_func='soft_delete', impl_file=TARGET, impl_line='1',
                 inproc_callers='-')])
    before = open(tsv, encoding='utf-8').read()
    p = run('refresh_callers.py', '--root', repo.root, '--full', tsv, expect=0)
    assert open(tsv, encoding='utf-8').read() == before
    assert '--write' in p.stdout


def test_列が無い台帳では列の追加を促して止まる(tmp_path, repo):
    """勝手に列を足すと schema.py と README が置いていかれる。"""
    repo(TARGET, TARGET_SRC)
    hdr = [c for c in FULL_HEADER if c != 'inproc_callers']
    tsv = tmp_path / 'no_column.tsv'
    with open(tsv, 'w', encoding='utf-8') as f:
        f.write('\t'.join(hdr) + '\n')
        f.write('\t'.join('-' for _ in hdr) + '\n')
    p = run('refresh_callers.py', '--root', repo.root, '--full', tsv, expect=1)
    assert 'schema.py' in p.stdout + p.stderr


# --- CI 用のゲート ---------------------------------------------------------

CALLER_SRC = src('''
    from weko_demo.views import soft_delete

    def prepare(value):
        return soft_delete(value)
''')


def _one_row_ledger(tmp_path, repo, recorded='-'):
    """呼び出し元が1つあるソースと、台帳1行を用意する。"""
    repo(TARGET, TARGET_SRC)
    repo(OTHER, CALLER_SRC)
    row = make_row(impl_func='soft_delete', impl_file=TARGET, impl_line='1',
                   uri='/secret/path/<id>', endpoint='weko_demo.secret_endpoint',
                   inproc_callers=recorded)
    return write_full(tmp_path / 'full.tsv', [row])


def test_gateは台帳とソースがずれていれば1で落ちる(tmp_path, repo):
    """認可を足す PR で、HTTP 以外の入口を持つビューを素通りさせないためのゲート。
    落ちなくなると、第二の入口を見落としたまま緑で通る。"""
    tsv = _one_row_ledger(tmp_path, repo)
    run('refresh_callers.py', '--root', repo.root, '--full', tsv,
        '--summary-only', '--gate', expect=1)


def test_gateは台帳が追いついていれば0で通る(tmp_path, repo):
    tsv = _one_row_ledger(tmp_path, repo)
    run('refresh_callers.py', '--root', repo.root, '--full', tsv, '--write',
        expect=0)
    run('refresh_callers.py', '--root', repo.root, '--full', tsv,
        '--summary-only', '--gate', expect=0)


def test_summary_onlyは経路名もファイル名も出さない(tmp_path, repo):
    """public な CI のログ・artifact・PR コメントは誰でも読める。
    件数だけを出すことを、reconcile / detect_routes と同じくここでも固定する。"""
    tsv = _one_row_ledger(tmp_path, repo)
    p = run('refresh_callers.py', '--root', repo.root, '--full', tsv,
            '--summary-only', '--gate', expect=1)
    for leaked in ('/secret/path', 'secret_endpoint', 'views.py', 'caller.py',
                   str(tsv), 'no='):
        assert leaked not in p.stdout, f'{leaked} が出ている'
