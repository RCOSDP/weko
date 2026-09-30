# -*- coding: utf-8 -*-
"""audit_authz.py — 入口の先にある認可の欠陥を拾う。

このスクリプトが守っているのは**判定の線引き**そのものなので、線が動いたら
落ちるようにする。特に

  - 「認可らしき呼び出しが在る」ことを「認可が効いている」と読まないこと
  - 閉包の中にたまたま在る無関係な比較を「突合済み」と読まないこと

の2点は、取り違えると「認可の欠陥がある行」を「問題なし」と判定してしまう。
実際にそれが起きた経緯が非公開側の調査記録にある。合成した最小のソースで固定する。
"""
import json
import textwrap

import pytest

import audit_authz
from conftest import make_row, write_full


def src(text):
    return textwrap.dedent(text).lstrip('\n')


# 「トークンで引いた対象を、URL パスの対象と突き合わせていない」実装の縮図。
# 入口(download)→ 検証(check_download_access)→ トークン照合(check_token_access)の3段で、
# 一番奥までは「トークンを検証している」ようにしか見えない。
VULNERABLE = src('''
    def download(pid, record, filename, **kwargs):
        token = request.args.get('token')
        ok, err = check_download_access(record, filename, token)
        if not ok:
            return abort(403, err)
        return _record_file_factory(pid, record, filename)


    def check_download_access(record, filename, token):
        if not check_token_access(token):
            return False, 'invalid'
        url_obj = convert_token_into_obj(token)
        if url_obj.is_deleted is True:
            return False, 'deleted'
        if url_obj.download_count >= url_obj.download_limit:
            return False, 'over'
        return True, ''


    def check_token_access(token):
        return hashlib.sha256(token.encode()).hexdigest() == token.split('.')[0]
''')

# 同じ実装に突合を1行足したもの。これは検知してはいけない。
FIXED = VULNERABLE.replace(
    "    if url_obj.is_deleted is True:",
    "    if url_obj.record_id != pid_value or url_obj.file_name != filename:\n"
    "        return False, 'mismatch'\n"
    "    if url_obj.is_deleted is True:")
assert FIXED != VULNERABLE, 'FIXED の差し込みに失敗している(テストが無意味になる)'


def repo_with(fake_repo, **files):
    for rel, text in files.items():
        fake_repo(rel, text)
    return fake_repo.root


def ledger(tmp_path, rows, name='full.tsv'):
    return write_full(tmp_path / name, rows)


# --- A. 識別子突合の欠落 --------------------------------------------------

def test_トークンで引いた対象をパスの対象と突き合わせていなければ検知する(fake_repo, tmp_path):
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': VULNERABLE})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/item/<pid_value>/file/<filename>',
        impl_func='download',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    res = audit_authz.audit(root, led)
    assert [d['no'] for d in res['id_binding']] == ['1']


def test_突合を1行足せば検知しなくなる(fake_repo, tmp_path):
    """あるべき修正を入れたら消えること。消えないなら指摘として使えない。"""
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': FIXED})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/item/<pid_value>/file/<filename>',
        impl_func='download',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    assert audit_authz.audit(root, led)['id_binding'] == []


def test_無関係な比較を突合済みと読まない(fake_repo, tmp_path):
    """閉包の奥に `file['filename'] == filename` のような比較はいくらでもある。

    これを突合と数えると、実際に脆弱な行が「問題なし」に落ちる
    (この取り違えで最初の実装は今回の脆弱行を取りこぼした)。
    """
    noise = src('''
        def pick_file(files, filename):
            for f in files:
                if f.get('filename') == filename:
                    return f
            return None
    ''')
    root = repo_with(fake_repo, **{
        'modules/weko-demo/weko_demo/fd.py':
            VULNERABLE.replace('return _record_file_factory(pid, record, filename)',
                               'return pick_file(record.files, filename)') + '\n' + noise})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/item/<pid_value>/file/<filename>',
        impl_func='download',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    assert [d['no'] for d in audit_authz.audit(root, led)['id_binding']] == ['1']


def test_有効期限や回数の検証をいくら重ねても突合とは見なさない(fake_repo, tmp_path):
    """VULNERABLE は is_deleted・download_count・ハッシュ照合を持っている。

    「検証している風」の比較が何本あっても、対象の同一性は担保されない。
    """
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': VULNERABLE})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/item/<pid_value>/file/<filename>',
        impl_func='download',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    d = audit_authz.audit(root, led)['id_binding'][0]
    assert 'convert_token_into_obj' in ' '.join(d['fetched_by'])


def test_段数を1にすると入口しか見ないので取りこぼす(fake_repo, tmp_path):
    """欠陥は入口から2段目にある。段数を絞れば拾えないことを明示しておく
    (「入口だけ見る」調査が取りこぼした構図そのもの)。"""
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': VULNERABLE})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/item/<pid_value>/file/<filename>',
        impl_func='download',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    assert audit_authz.audit(root, led, depth=1)['id_binding'] == []
    assert audit_authz.audit(root, led, depth=2)['id_binding'] != []


def test_委譲表記の実体側の関数も辿る(fake_repo, tmp_path):
    """`impl_func` の `A→B` は「A が入口、B が実体」。B を見ないと届かない。"""
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': VULNERABLE})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/item/<pid_value>/file/<filename>',
        impl_func='entry→check_download_access',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    assert [d['no'] for d in audit_authz.audit(root, led)['id_binding']] == ['1']


# --- B. 認可入力汚染 ------------------------------------------------------

AUTHZ = src('''
    def check_actor_permission(draft_id, action_id):
        draft = get_draft(draft_id)
        shared = draft.editor_ids or []
        if int(current_user.get_id()) in shared:
            return 0
        if draft.approver == current_user.email:
            return 0
        return 1
''')

WRITER = src('''
    def save_draft():
        save_draft_data(request.get_json())
        return jsonify(code=0)
''')


def test_認可判定が読むフィールドを書けるエンドポイントを検知する(fake_repo, tmp_path):
    root = repo_with(fake_repo, **{
        'modules/weko-demo/weko_demo/views.py': AUTHZ + '\n' + WRITER})
    led = ledger(tmp_path, [make_row(
        no='1', method='POST', uri='/board/save_draft',
        impl_func='save_draft', impl_file='modules/weko-demo/weko_demo/views.py',
        body_params='draft_id(必須);title;editor_ids(必須);approver')])
    hit = audit_authz.audit(root, led)['authz_input']
    assert [d['no'] for d in hit] == ['1']
    assert 'editor_ids' in hit[0]['fields'] and 'approver' in hit[0]['fields']
    assert any('check_actor_permission' in w for w in hit[0]['read_by'])


def test_認可判定と関係ない項目しか書けなければ検知しない(fake_repo, tmp_path):
    root = repo_with(fake_repo, **{
        'modules/weko-demo/weko_demo/views.py': AUTHZ + '\n' + WRITER})
    led = ledger(tmp_path, [make_row(
        no='1', method='POST', uri='/demo', impl_func='save_draft',
        impl_file='modules/weko-demo/weko_demo/views.py',
        body_params='comment;subject')])
    assert audit_authz.audit(root, led)['authz_input'] == []


def test_参照系は認可入力汚染の対象にしない(fake_repo, tmp_path):
    """書けないなら汚染できない。GET を混ぜると件数が無意味に膨らむ。"""
    root = repo_with(fake_repo, **{
        'modules/weko-demo/weko_demo/views.py': AUTHZ + '\n' + WRITER})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/demo', impl_func='save_draft',
        impl_file='modules/weko-demo/weko_demo/views.py',
        body_params='editor_ids')])
    assert audit_authz.audit(root, led)['authz_input'] == []


# --- C. 認可ヘルパの fan-in ----------------------------------------------

def test_認可ヘルパを参照本数の多い順に並べる(fake_repo, tmp_path):
    """1000本のエンドポイントを個別に追う代わりに、ここを上から潰すための出力。"""
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': VULNERABLE})
    led = ledger(tmp_path, [
        make_row(no='1', method='GET', uri='/a', impl_func='download',
                 impl_file='modules/weko-demo/weko_demo/fd.py'),
        make_row(no='2', method='GET', uri='/b', impl_func='check_download_access',
                 impl_file='modules/weko-demo/weko_demo/fd.py'),
    ])
    helpers = dict((k.split(':')[-1], v) for k, v in audit_authz.audit(root, led)['helpers'])
    # no=1 は入口から辿って届き、no=2 は自分自身が check_download_access
    assert helpers['check_download_access'] == ['1', '2']
    assert helpers['check_token_access'] == ['1', '2']
    # 参照本数の多い順に並ぶ(ここが精査の順番になる)
    counts = [len(v) for _k, v in audit_authz.audit(root, led)['helpers']]
    assert counts == sorted(counts, reverse=True)


# --- add_authmech.py から使う入口 ----------------------------------------

def test_id_bindingは突合の有無でokとmissingを返す():
    assert audit_authz.id_binding(VULNERABLE) == 'missing'
    assert audit_authz.id_binding(FIXED) == 'ok'


@pytest.mark.parametrize('src_text', ['', '   ', 'def f(:\n  pass'])
def test_読めないソース片は判断しない(src_text):
    """構文が壊れているセルで `missing` を返すと、静かに誤指摘が増える。"""
    assert audit_authz.id_binding(src_text) == 'n/a'


def test_対象を引いていない関数は判断しない():
    assert audit_authz.id_binding(src('''
        def index():
            return render_template('index.html')
    ''')) == 'n/a'


# --- CLI ------------------------------------------------------------------

def test_コマンドとして回ると件数と明細が出る(fake_repo, tmp_path):
    from conftest import run as _run
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': VULNERABLE})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/item/<pid_value>/file/<filename>',
        impl_func='download',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    out = tmp_path / 'a.json'
    p = _run('audit_authz.py', '--root', root, '--full', led, '--json', out, expect=0)
    assert '識別子突合の欠落 | 1' in p.stdout
    assert json.load(open(out, encoding='utf-8'))['id_binding'][0]['no'] == '1'


def test_gateは検知があれば異常終了する(fake_repo, tmp_path):
    """CI に置くための線。検知があるのに 0 で返すと誰も気付かない。"""
    from conftest import run as _run
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': VULNERABLE})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/x/<pid_value>/<filename>',
        impl_func='download',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    _run('audit_authz.py', '--root', root, '--full', led, '--gate', expect=1)
    led_ok = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/x', impl_func='index',
        impl_file='modules/weko-demo/weko_demo/fd.py')], name='ok.tsv')
    _run('audit_authz.py', '--root', root, '--full', led_ok, '--gate', expect=0)


def test_summary_onlyは経路名を出さない(fake_repo, tmp_path):
    """public リポジトリの CI ログは誰でも読める。件数だけに絞れること。"""
    from conftest import run as _run
    root = repo_with(fake_repo, **{'modules/weko-demo/weko_demo/fd.py': VULNERABLE})
    led = ledger(tmp_path, [make_row(
        no='1', method='GET', uri='/item/<pid_value>/file/<filename>',
        impl_func='download',
        impl_file='modules/weko-demo/weko_demo/fd.py')])
    p = _run('audit_authz.py', '--root', root, '--full', led, '--summary-only', expect=0)
    assert '識別子突合の欠落 | 1' in p.stdout
    assert 'file/secret' not in p.stdout
    assert 'download' not in p.stdout
