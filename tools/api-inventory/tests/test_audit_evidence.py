# -*- coding: utf-8 -*-
"""audit_evidence.py — 台帳に書いたことがソースと合っているかを突き合わせる。

台帳の検査は**形と語彙しか見ていない**。`sec_evidence` の行番号を実在しない値に
しても、`data_op` の削除を誤った値にしても、57 本のテストと 3 本のゲートを全部
通る(実験で確認済み)。ここはその穴を塞ぐ検知なので、**検知が鳴ることそのもの**を
固定する。鳴らなくなっても件数が減るだけで、誰も気付かない。
"""
import json

import audit_evidence as ae
from conftest import make_row, run, write_full


def ledger(tmp_path, rows, name='full.tsv'):
    return write_full(tmp_path / name, rows)


def allow(tmp_path, refs=None, dataop=None, name='evidence_allow.json'):
    p = tmp_path / name
    json.dump({'refs': refs or {}, 'dataop': dataop or {}},
              open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return str(p)


SRC = 'modules/weko-demo/weko_demo/views.py'


# --- A. 位置参照のずれ -----------------------------------------------------

def test_存在しないファイルへの参照を検知する(fake_repo, tmp_path):
    fake_repo(SRC, 'def show():\n    return 1\n')
    rows = [make_row(no='1', sec_evidence='modules/weko-demo/weko_demo/ない.py:10')]
    bad, _ = ae.audit_refs([r for r in rows], fake_repo.root)
    assert [d['no'] for d in bad] == ['1']
    assert 'ファイルが無い' in bad[0]['why']


def test_行番号がファイルの範囲外なら検知する(fake_repo):
    """バージョンが変われば必ずずれる。`impl_line` には検査があるのに
    `sec_evidence` には無かった、というのがこの検知を足した理由。"""
    fake_repo(SRC, 'a = 1\nb = 2\n')
    bad, _ = ae.audit_refs([make_row(no='1', sec_evidence=f'{SRC}:99')],
                           fake_repo.root)
    assert len(bad) == 1 and '範囲外' in bad[0]['why']


def test_範囲の終端も見る(fake_repo):
    fake_repo(SRC, 'a = 1\nb = 2\n')
    bad, _ = ae.audit_refs([make_row(no='1', sec_evidence=f'{SRC}:1-99')],
                           fake_repo.root)
    assert len(bad) == 1


def test_範囲に収まっていれば通す(fake_repo):
    fake_repo(SRC, 'a = 1\nb = 2\nc = 3\n')
    bad, _ = ae.audit_refs([make_row(no='1', sec_evidence=f'{SRC}:1-3')],
                           fake_repo.root)
    assert bad == []


def test_sec_detailの参照も見る(fake_repo):
    """位置は sec_evidence だけでなく sec_detail にも書かれる。"""
    fake_repo(SRC, 'a = 1\n')
    bad, _ = ae.audit_refs([make_row(no='1', sec_detail=f'{SRC}:50 が原因')],
                           fake_repo.root)
    assert len(bad) == 1


def test_ファイル名だけの参照は検知ではなく別枠で数える(fake_repo):
    """`rest.py:309-313` はどのモジュールか分からず機械では追えない。
    落とすのではなく、解決できない参照として件数だけ出す。"""
    fake_repo(SRC, 'a = 1\n')
    bad, unresolved = ae.audit_refs([make_row(no='1', sec_evidence='rest.py:309-313')],
                                    fake_repo.root)
    assert bad == [] and unresolved == 1


# --- B. data_op と実装の矛盾 -----------------------------------------------

def _dataop(fake_repo, src, data_op='削除', **over):
    fake_repo(SRC, src)
    idx = ae.Index(fake_repo.root)
    row = make_row(no='1', impl_file=SRC, impl_func='act', data_op=data_op, **over)
    return ae.audit_dataop([row], fake_repo.root, idx, 3)


def test_data_opに削除があるのに実装に無ければ検知する(fake_repo):
    """ある設定画面が `更新,削除` と書かれていたが、呼んでいるのは設定の get と
    update だけだった、という実例がある。"""
    out = _dataop(fake_repo, 'def act():\n    return Settings.update(x)\n')
    assert [d['no'] for d in out] == ['1']


def test_実装に削除があれば検知しない(fake_repo):
    out = _dataop(fake_repo, 'def act():\n    db.session.delete(obj)\n')
    assert out == []


def test_論理削除の書き方も削除とみなす(fake_repo):
    out = _dataop(fake_repo, 'def act():\n    obj.is_deleted = True\n')
    assert out == []


def test_ファイル実体の削除も削除とみなす(fake_repo):
    """DB の行とは限らない。サムネイル画像を os.remove する実装がある。"""
    out = _dataop(fake_repo, 'def act():\n    os.remove(filename)\n')
    assert out == []


def test_委譲先の削除も辿る(fake_repo):
    out = _dataop(fake_repo,
                  'def act():\n    return _do()\n\ndef _do():\n    db.session.delete(o)\n')
    assert out == []


def test_data_opに削除が無ければ見ない(fake_repo):
    """逆向き(実装は消しているのに data_op に無い)は見ない。副作用として
    消える実装が多く、主たる操作を何と呼ぶかは人の判断だから。"""
    out = _dataop(fake_repo, 'def act():\n    db.session.delete(o)\n', data_op='取得')
    assert out == []


def test_実ファイルを持たない行は対象外(fake_repo):
    fake_repo(SRC, 'a = 1\n')
    idx = ae.Index(fake_repo.root)
    row = make_row(no='1', impl_file='Flask-Admin ModelView', impl_func='delete',
                   data_op='削除')
    assert ae.audit_dataop([row], fake_repo.root, idx, 3) == []


# --- 許可リスト ------------------------------------------------------------

def test_理由つきの許可で検知から外れる(fake_repo, tmp_path):
    fake_repo(SRC, 'def act():\n    return Settings.update(x)\n')
    tsv = ledger(tmp_path, [make_row(no='1', impl_file=SRC, impl_func='act',
                                     data_op='削除')])
    run('audit_evidence.py', '--full', tsv, '--weko-root', fake_repo.root,
        '--allow', allow(tmp_path, dataop={'1': 'celery 越しで AST が届かない'}),
        '--gate', expect=0)


def test_理由が空の許可は効かない(fake_repo, tmp_path):
    """`reconcile_allow.json` と同じ規約。理由を読めない許可は形骸化する。"""
    fake_repo(SRC, 'def act():\n    return Settings.update(x)\n')
    tsv = ledger(tmp_path, [make_row(no='1', impl_file=SRC, impl_func='act',
                                     data_op='削除')])
    run('audit_evidence.py', '--full', tsv, '--weko-root', fake_repo.root,
        '--allow', allow(tmp_path, dataop={'1': '   '}), '--gate', expect=1)


# --- ゲートと秘匿 ----------------------------------------------------------

def test_検知があればゲートが落ちる(fake_repo, tmp_path):
    fake_repo(SRC, 'a = 1\n')
    tsv = ledger(tmp_path, [make_row(no='1', sec_evidence=f'{SRC}:99')])
    run('audit_evidence.py', '--full', tsv, '--weko-root', fake_repo.root,
        '--allow', allow(tmp_path), '--gate', expect=1)


def test_summary_onlyは経路名もファイル位置も出さない(fake_repo, tmp_path):
    """public な CI のログは誰でも読める。出してよいのは件数だけ。"""
    fake_repo(SRC, 'a = 1\n')
    tsv = ledger(tmp_path, [make_row(no='1', uri='/secret/path/<id>',
                                     endpoint='weko_demo.secret_endpoint',
                                     sec_evidence=f'{SRC}:99')])
    p = run('audit_evidence.py', '--full', tsv, '--weko-root', fake_repo.root,
            '--allow', allow(tmp_path), '--summary-only', '--gate', expect=1)
    for leaked in ('/secret/path', 'secret_endpoint', 'views.py', 'no='):
        assert leaked not in p.stdout, f'{leaked} が出ている'
    assert '1 件' in p.stdout
