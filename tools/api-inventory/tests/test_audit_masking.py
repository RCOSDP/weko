# -*- coding: utf-8 -*-
"""audit_masking.py — 応答本文が非公開判定(6種)を通っているかを見る。

この検知が緩む方向に壊れると、**本文をそのまま返している経路が「守られている」
ように見える**。そうなっても件数が減るだけでゲートは緑のまま通るので、
「守られていないと言えること」を固定しておく。

特に `自分のデコレータを直接呼びに数えない` は、実際に一度踏んだ穴。
`ast.walk` は decorator_list も歩くため、factory 名を引数に取る認可デコレータが
直接呼びに混ざり、認可が効いていない経路が行列から消えていた。

フィクスチャは**合成した最小コード**にすること。実在のクラス・設定名で
実際の欠陥を組み立てると、それは検出ロジックではなく所見になる
(`docs/RULE.md` §1「判断するのはファイルではなく内容」)。
"""
import audit_masking as am
from conftest import make_row, run


def _idx(fake_repo, relpath, src):
    fake_repo(relpath, src)
    return am.Index(fake_repo.root)


# --------------------------------------------------------------------------
# マスクの到達
# --------------------------------------------------------------------------

def test_マスク関数の直接呼びを拾う(fake_repo):
    idx = _idx(fake_repo, 'modules/weko-demo/weko_demo/views.py', '''
def show(pid):
    if not check_publish_status(record):
        abort(403)
    return serialize(record)
''')
    direct, cond = idx.masks_from([idx.find('', 'show')], 3)
    assert direct == {'publish'}
    assert cond == set()


def test_数段先のヘルパまで辿る(fake_repo):
    idx = _idx(fake_repo, 'modules/weko-demo/weko_demo/views.py', '''
def show(pid):
    return _render(pid)

def _render(pid):
    return _mask(pid)

def _mask(pid):
    return hide_by_file(pid)
''')
    direct, _ = idx.masks_from([idx.find('', 'show')], 3)
    assert direct == {'file'}
    # 段数を絞れば届かない。段数は引数で変えられることの確認でもある。
    shallow, _ = idx.masks_from([idx.find('', 'show')], 2)
    assert shallow == set()


def test_自分のデコレータは直接呼びに数えない(fake_repo):
    """`ast.walk` が decorator_list も歩くことによる取りこぼしの回帰。

    `need_record_permission` は permission_factory が None なら素通りする。
    「呼び出しが在る」ことは「判定が効く」ことを意味しないので、
    直接呼びと同じ扱いにしてはいけない。
    """
    idx = _idx(fake_repo, 'modules/weko-demo/weko_demo/views.py', '''
def need_record_permission(factory_name):
    def deco(f):
        def wrapper(self, record=None, *a, **kw):
            if permission_factory and record:
                verify_record_permission(permission_factory, record)
            return f(self, record=record, *a, **kw)
        return wrapper
    return deco

def verify_record_permission(factory, record):
    if check_created_id(record):
        return
    check_publish_status(record)

class DemoResource:
    @need_record_permission('edit_permission_factory')
    def edit(self, pid, record):
        return self.make_response(pid, record)
''')
    direct, cond = idx.masks_from([idx.find('', 'DemoResource.edit')], 4)
    assert direct == set(), '素通りしうるデコレータを直接呼びに数えている'
    assert cond == {'owner', 'publish'}


def test_デコレータが読むfactory名を取り出す(fake_repo):
    idx = _idx(fake_repo, 'modules/weko-demo/weko_demo/views.py', '''
def need_record_permission(factory_name):
    pass

class Demo:
    @need_record_permission('edit_permission_factory')
    def put(self, pid, record):
        pass
''')
    assert idx.gate_factories([idx.find('', 'Demo.put')]) == ['edit_permission_factory']


# --------------------------------------------------------------------------
# B. None に潰された認可ファクトリ
# --------------------------------------------------------------------------

def test_factoryをNoneに潰した設定を拾う(fake_repo):
    fake_repo('modules/weko-demo/weko_demo/config.py', '''
DEMO_REST_DEFAULT_EDIT_PERMISSION_FACTORY = None
DEMO_REST_DEFAULT_VIEW_PERMISSION_FACTORY = 'weko_demo.permissions:page'
DEMO_REST_ENDPOINTS = dict(
    demoid=dict(delete_permission_factory_imp=None),
)
''')
    got = am.audit_factories(fake_repo.root)
    names = {d['setting'] for d in got}
    assert 'DEMO_REST_DEFAULT_EDIT_PERMISSION_FACTORY' in names
    assert 'delete_permission_factory_imp' in names
    assert 'DEMO_REST_DEFAULT_VIEW_PERMISSION_FACTORY' not in names, \
        '値が入っている設定まで拾うと、潰された設定が埋もれる'


# --------------------------------------------------------------------------
# A. 応答シリアライザの解決
# --------------------------------------------------------------------------

SERIALIZER_SRC = '''
class Mixin:
    def serialize(self, pid, record, **kw):
        record = hide_by_email(record, True)
        return self.dump(record)

class JSONSerializer(Mixin):
    pass

json_v1 = JSONSerializer(Schema)
json_v1_response = record_responsify(json_v1, 'application/json')
plain_response = json_v1_response
'''


def test_別名と代入をたどってシリアライザを解決する(fake_repo):
    """`a = b` の別名と `f(g, ...)` の代入を辿れないと、シリアライザが
    「解決できず」になり、何を隠しているか分からないまま素通りする。"""
    idx = _idx(fake_repo, 'modules/weko-demo/weko_demo/serializers.py', SERIALIZER_SRC)
    seeds = am.resolve_serializer(idx, 'weko_demo.serializers:plain_response')
    assert seeds, '別名(plain_response → json_v1_response)を辿れていない'
    direct, _ = idx.masks_from(seeds, 3)
    assert direct == {'email'}


def test_添字代入で宣言されたシリアライザも拾う(fake_repo):
    """WEKO は `RECORDS_REST_ENDPOINTS['recid']['record_serializers'] = {...}`
    の形で後から差し替える。辞書リテラルだけ見ていると丸ごと漏れる。"""
    fake_repo('modules/weko-demo/weko_demo/config.py', '''
RECORDS_REST_ENDPOINTS = dict(recid=dict(
    record_serializers={'application/json': 'weko_demo.serializers:a_response'},
))
RECORDS_REST_ENDPOINTS['recid']['record_serializers'] = {
    'text/x-bibliography': 'weko_demo.serializers:b_response',
}
''')
    got = am.collect_serializer_names(fake_repo.root)
    assert 'weko_demo.serializers:a_response' in got
    assert 'weko_demo.serializers:b_response' in got


# --------------------------------------------------------------------------
# C. 台帳の行の絞り込み
# --------------------------------------------------------------------------

def test_本文の無い応答は対象外(fake_repo):
    assert not am.returns_item_body(
        make_row(response='空ボディ(204)', data_store='PostgreSQL:records_metadata'))
    assert not am.returns_item_body(
        make_row(response='なし', data_store='PostgreSQL:records_metadata'))


def test_例外時だけ空ボディの行は対象に残る(fake_repo):
    """「更新後のレコードJSON。例外時は空ボディ500」を全文一致で外すと、
    本文を返す経路を取りこぼす。"""
    assert am.returns_item_body(
        make_row(response='更新後のレコードJSON。例外時は空ボディ500',
                 data_store='PostgreSQL:records_metadata'))


def test_アイテム以外を扱う経路は既定で対象外(fake_repo):
    row = make_row(response='コミュニティのインデックス設定JSON',
                   data_store='PostgreSQL:communities')
    assert not am.returns_item_body(row)
    assert am.returns_item_body(row, all_stores=True), '--all で広げられること'


def test_到達不能と台帳が記録している行は外す(fake_repo):
    idx = _idx(fake_repo, 'modules/weko-demo/weko_demo/views.py', '''
def show(pid):
    return dumps(record)
''')
    row = make_row(no='9', response='レコードJSON',
                   data_store='PostgreSQL:records_metadata',
                   impl_file='modules/weko-demo/weko_demo/views.py', impl_func='show',
                   dynamic_verified='[測定対象外·2026-08-26] 同一ルールの重複登録')
    assert am.audit_rows(idx, [row], 3)[0] == []
    row['dynamic_verified'] = '-'
    assert [r['no'] for r in am.audit_rows(idx, [row], 3)[0]] == ['9']


def test_sec_exposedを書いた行は確認済みとして外す(fake_repo):
    """確認した結果を台帳に書いたら行列から消える、が本スクリプトの前提。
    消えないと毎回同じ行が出続け、誰も読まなくなって --gate も使えない。"""
    idx = _idx(fake_repo, 'modules/weko-demo/weko_demo/views.py', '''
def show(pid):
    return dumps(record)
''')
    row = make_row(no='9', response='レコードJSON',
                   data_store='PostgreSQL:records_metadata',
                   impl_file='modules/weko-demo/weko_demo/views.py', impl_func='show',
                   sec_exposed='非公開アイテムのメタデータ')
    rows, settled = am.audit_rows(idx, [row], 3)
    assert rows == [] and settled == 1, '外した件数を黙って捨てている'


def test_潰されたfactoryに依存する行に印が付く(fake_repo):
    """入口がデコレータ頼みで、そのデコレータが読む factory が None なら、
    その行は何にも守られていない。B と C を突き合わせて初めて言える。"""
    fake_repo('modules/weko-demo/weko_demo/config.py',
              'DEMO_REST_DEFAULT_EDIT_PERMISSION_FACTORY = None\n')
    idx = _idx(fake_repo, 'modules/weko-demo/weko_demo/views.py', '''
def need_record_permission(factory_name):
    pass

class Demo:
    @need_record_permission('edit_permission_factory')
    def put(self, pid, record):
        return dumps(record)
''')
    row = make_row(no='7', method='PUT', response='更新後のレコードJSON',
                   data_store='PostgreSQL:records_metadata',
                   impl_file='modules/weko-demo/weko_demo/views.py',
                   impl_func='Demo.put')
    fac = am.audit_factories(fake_repo.root)
    [got], _settled = am.audit_rows(idx, [row], 3, factories=fac)
    assert got['disabled_by_config'] == ['DEMO_REST_DEFAULT_EDIT_PERMISSION_FACTORY']


# --------------------------------------------------------------------------
# 秘匿の担保
# --------------------------------------------------------------------------

def test_summary_onlyはURIもendpoint名も出さない(fake_repo, full_tsv, tmp_path):
    """public な CI のログ・artifact・PR コメントは誰でも読める。
    件数だけを出すことを、reconcile / detect_routes と同じくここでも固定する。"""
    fake_repo('modules/weko-demo/weko_demo/views.py', 'def show(pid):\n    return dumps(record)\n')
    path = full_tsv([make_row(no='1', uri='/secret/path/<id>',
                              endpoint='weko_demo.secret_endpoint',
                              response='レコードJSON',
                              data_store='PostgreSQL:records_metadata',
                              impl_file='modules/weko-demo/weko_demo/views.py',
                              impl_func='show')])
    from conftest import run
    p = run('audit_masking.py', '--weko-root', fake_repo.root, '--full', path,
            '--summary-only', expect=0)
    assert '/secret/path' not in p.stdout
    assert 'secret_endpoint' not in p.stdout
    assert '1 件' in p.stdout


def test_これはゲートではない(tmp_path, fake_repo):
    """A のシリアライザ表は欠陥一覧ではなく棚卸しで、アイテム4種のマスクに
    届かないシリアライザは常に存在する(アイテム単位の認可は permission factory の
    仕事なので、ゼロにはならない)。そこを落第条件にすると**絶対に緑にならない
    ゲート**になる。実際に一度そう書いてしまったので、戻さないよう固定する。

    行列を詰める強制力は `open_findings.py` のゲート C が持つ。
    """
    fake_repo('modules/weko-demo/weko_demo/views.py',
              'def show(pid):\n    return dumps(record)\n')
    from conftest import write_full
    tsv = write_full(tmp_path / 'full.tsv', [
        make_row(no='1', response='レコードJSON',
                 data_store='PostgreSQL:records_metadata',
                 impl_file='modules/weko-demo/weko_demo/views.py', impl_func='show'),
    ])
    p = run('audit_masking.py', '--weko-root', fake_repo.root, '--full', tsv,
            expect=0)
    assert '本文を返すのにマスクに届かない行' in p.stdout
    assert '--gate' not in p.stdout
