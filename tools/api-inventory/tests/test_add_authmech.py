# -*- coding: utf-8 -*-
"""add_authmech.py — auth_mechanism と bola_risk を機械付与する。

`bola_risk` は OWASP API1(BOLA)の一次判定で、**どの行を深追いするか**を
決める。ここが「安全」と言い切った行は誰も見に行かないので、判定を緩める
方向の変更は静かに調査の穴になる。実際、次の2つで穴が空いた:

  - 対象を指す ID が URL パスにしか無いものとして扱い、body で対象を指定する
    経路を「リソースID無し」で検査対象から外していた
  - 所有者チェックらしき語が実装に**出現するだけ**で「認可あり」としていた

どちらも実際に見落としを生んだ形である。合成したソースで線を固定する。
"""
import textwrap

from conftest import FULL_HEADER, make_row, run, write_full

H = {n: i for i, n in enumerate(FULL_HEADER)}


def src(text):
    return textwrap.dedent(text).lstrip('\n')


def bola(tmp_path, fake_repo, source, **over):
    """1行の台帳に add_authmech.py を掛けて bola_risk を返す。"""
    rel = 'modules/weko-demo/weko_demo/views.py'
    fake_repo(rel, source)
    row = make_row(impl_file=rel, impl_line='1', bola_risk='-',
                   auth_mechanism='-', **over)
    tsv = write_full(tmp_path / 'full.tsv', [row])
    run('add_authmech.py', tsv, env={'WEKO_ROOT': fake_repo.root}, expect=0)
    line = open(tsv, encoding='utf-8').read().rstrip('\n').split('\n')[1].split('\t')
    return line[H['bola_risk']]


# 所有者チェックらしき呼び出しは在るが、引いた対象とパスの対象を照合していない。
NO_BINDING = src('''
    def download(pid, filename, token):
        if not check_created_id(record):
            return abort(403)
        url_obj = convert_token_into_obj(token)
        if url_obj.is_deleted:
            return abort(403)
        return serve(pid, filename)
''')

WITH_BINDING = src('''
    def download(pid, filename, token):
        if not check_created_id(record):
            return abort(403)
        url_obj = convert_token_into_obj(token)
        if url_obj.file_name != filename:
            return abort(403)
        return serve(pid, filename)
''')


def test_突合が見えない行を認可ありと断じない(tmp_path, fake_repo):
    """`check_created_id` は呼ばれている。呼び出しの有無だけを見ると
    「所有者チェックあり」に見えるが、トークンで引いた対象は照合していない。"""
    v = bola(tmp_path, fake_repo, NO_BINDING,
             uri='/item/<pid_value>/file/<filename>')
    assert v.startswith('★'), v
    assert '突合' in v


def test_突合があれば認可ありと判定する(tmp_path, fake_repo):
    v = bola(tmp_path, fake_repo, WITH_BINDING,
             uri='/item/<pid_value>/file/<filename>')
    assert v == 'object-level認可あり(所有者/対象単位)'


def test_bodyで対象を指定する経路をリソースID無しにしない(tmp_path, fake_repo):
    """対象をボディで受ける経路がある。URI だけを見ると
    「リソースID無し」になり、検査対象から外れる。"""
    v = bola(tmp_path, fake_repo, src('''
        def start_guest_request():
            post_data = request.get_json()
            return start_request(post_data)
    '''), method='POST', uri='/request/start',
        body_params='guest_mail;record_id;file_name')
    assert v != 'N/A(リソースID無し)'
    assert v.startswith('★') and 'body' in v


def test_対象を指すIDがどこにも無ければ従来どおり対象外(tmp_path, fake_repo):
    """「ID があるのに見落とす」を直すために「ID が無いのに拾う」を
    招いてはいけない。件数が膨らめば誰も見なくなる。"""
    v = bola(tmp_path, fake_repo, src('''
        def ping():
            return 'ok'
    '''), method='GET', uri='/ping', body_params='-')
    assert v == 'N/A(リソースID無し)'
