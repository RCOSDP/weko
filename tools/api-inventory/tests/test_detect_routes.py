# -*- coding: utf-8 -*-
"""detect_routes.py — ソースだけから経路を検知する。

実機 url_map は「今この環境で登録されている経路」しか映さない。config で無効な経路、
プラグイン未導入の経路、設定値が真のときだけ登録される経路は、実機からは見えないのに
API としては存在する。この検知器はそこを埋めるためのもので、**検知源が1つ黙って
死んでも件数が減るだけで気付けない**。だから検知源ごとに「拾えること」を固定する。
"""
import os

import pytest

import detect_routes as dr
from conftest import make_row, write_full


# --------------------------------------------------------------------------
# 検知源ごとの回帰
# --------------------------------------------------------------------------

def _detect(fake_repo, relpath, src):
    fake_repo(relpath, src)
    return dr.detect(fake_repo.root)


def _sources(found, kind):
    return [d for d in found if d['source'] == kind]


def test_route_デコレータを拾う(fake_repo):
    found = _detect(fake_repo, 'modules/weko-demo/weko_demo/views.py', '''
from flask import Blueprint
bp = Blueprint('demo', __name__)

@bp.route('/demo/<int:pk>', methods=['GET', 'POST'])
def show(pk):
    return ''
''')
    [d] = _sources(found, 'route')
    assert d['rule'] == '/demo/<int:pk>'
    assert d['methods'] == ['GET', 'POST']
    assert d['func'] == 'show'


def test_expose_を拾う(fake_repo):
    """Flask-Admin の `@expose`。従来の AST 抽出は route しか見ておらず、
    205件の管理画面ビューがまるごと静的検知から漏れていた。"""
    found = _detect(fake_repo, 'modules/weko-demo/weko_demo/admin.py', '''
from flask_admin import BaseView, expose

class SettingView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        return ''

    @expose('/save', methods=['POST'])
    def save(self):
        return ''
''')
    got = {(d['qual'], d['rule']) for d in _sources(found, 'expose')}
    assert got == {('SettingView.index', '/'), ('SettingView.save', '/save')}


def test_add_url_rule_のas_viewを解決する(fake_repo):
    """config 駆動の登録は `view_func = X.as_view(...)` を挟む。変数名だけ見ると
    どのクラスの経路か分からなくなる(実測: 70件が照合不能になった)。"""
    found = _detect(fake_repo, 'modules/weko-demo/weko_demo/rest.py', '''
def create_blueprint(endpoints):
    for endpoint, options in endpoints.items():
        view_func = DemoResource.as_view(DemoResource.view_name)
        blueprint.add_url_rule(options.get('route'), view_func=view_func,
                               methods=['POST'])
    return blueprint
''')
    [d] = _sources(found, 'add_url_rule')
    assert d['cls'] == 'DemoResource'
    assert d['qual'] == 'DemoResource'
    assert d['rule_expr'] == "options.get('route')"
    assert d['methods'] == ['POST']


def test_add_url_rule_の一括登録は門番から外れる(fake_repo):
    """`add_url_rule(**rule)` は rule も view_func も静的に取れない。
    個々の経路は rest_config 側で拾うので、ここで落とすと常時赤になる。"""
    found = _detect(fake_repo, 'modules/weko-demo/weko_demo/rest.py', '''
def create_blueprint(endpoints):
    for endpoint, options in endpoints.items():
        for rule in build(endpoint, **options):
            blueprint.add_url_rule(**rule)
''')
    [d] = _sources(found, 'add_url_rule')
    assert d['dispatch'] is True


def test_rest_config_の経路定義を拾う(fake_repo):
    found = _detect(fake_repo, 'modules/weko-demo/weko_demo/config.py', '''
DEMO_REST_ENDPOINTS = {
    'demo': {
        'list_route': '/demo/items',
        'item_route': '/demo/items/<pid_value>',
        'record_class': 'weko_demo.api:Demo',
    },
}
''')
    got = {d['rule'] for d in _sources(found, 'rest_config')}
    assert got == {'/demo/items', '/demo/items/<pid_value>'}


def test_modelview_のクラスを拾う(fake_repo):
    found = _detect(fake_repo, 'modules/weko-demo/weko_demo/admin.py', '''
from flask_admin.contrib.sqla import ModelView

class WidgetView(ModelView):
    can_delete = True
''')
    assert [d['cls'] for d in _sources(found, 'modelview')] == ['WidgetView']


def test_entry_point_は経路を生む群だけを見る(fake_repo):
    """`invenio_base.apps` は拡張の登録で、それ自体は経路を作らない。
    混ぜると恒常的な偽陽性になってゲートが形骸化する。"""
    fake_repo('modules/weko-demo/setup.py', '''
setup(entry_points={
    'invenio_base.blueprints': ['weko_demo = weko_demo.views:blueprint'],
    'invenio_base.apps': ['weko_demo_ext = weko_demo:WekoDemo'],
    'invenio_admin.views': ['weko_demo_widget = weko_demo.admin:widget_adminview'],
})
''')
    found = dr.detect(fake_repo.root)
    got = {d['qual'] for d in _sources(found, 'entry_point')}
    assert got == {'weko_demo', 'weko_demo_widget'}


def test_adminview辞書を経由してビュークラスまで辿る(fake_repo):
    """entry point は `module:xxx_adminview` を指すだけ。辞書の中身まで辿らないと
    Flask-Admin の登録名(台帳の endpoint の `.` の手前)が分からない。"""
    fake_repo('modules/weko-demo/weko_demo/admin.py', '''
class SessionActivityView(ModelView):
    pass

session_adminview = {'model': SessionActivity, 'modelview': SessionActivityView}
''')
    fake_repo('modules/weko-demo/setup.py', '''
setup(entry_points={
    'invenio_admin.views': ['demo_session = weko_demo.admin:session_adminview'],
})
''')
    found = dr.detect(fake_repo.root)
    [ep] = _sources(found, 'entry_point')
    assert 'SessionActivityView' in ep.get('via', [])
    assert 'sessionactivity' in dr.admin_prefixes(ep)


def test_テストコードは検知対象から外す(fake_repo):
    fake_repo('modules/weko-demo/tests/test_views.py', '''
@bp.route('/only-in-tests')
def x():
    return ''
''')
    assert dr.detect(fake_repo.root) == []


# --------------------------------------------------------------------------
# 台帳との突き合わせ
# --------------------------------------------------------------------------

@pytest.mark.parametrize('a,b', [
    ('/api/demo', '/demo'), ('/demo/', '/demo'), ('/demo', '/api/demo')])
def test_uri比較はapi前置と末尾スラッシュを吸収する(a, b):
    assert dr.uri_variants(a) & dr.uri_variants(b)


def test_実装一致で照合する(tmp_path, fake_repo):
    src = 'modules/weko-demo/weko_demo/views.py'
    fake_repo(src, "@bp.route('/demo')\ndef show():\n    return ''\n")
    tsv = write_full(tmp_path / 'full.tsv',
                     [make_row(impl_file=src, impl_func='show', uri='/other')])
    led = dr.load_ledger(tsv)
    [d] = dr.detect(fake_repo.root)
    assert dr.match(d, led)[0] == 'impl'


def test_URIだけが一致する場合も照合する(tmp_path, fake_repo):
    """委譲やラッパで impl_func 名が変わることがある。URI でも当てられること。"""
    fake_repo('modules/weko-demo/weko_demo/views.py',
              "@bp.route('/demo')\ndef show():\n    return ''\n")
    tsv = write_full(tmp_path / 'full.tsv',
                     [make_row(impl_file='modules/other/x.py',
                               impl_func='wrapper', uri='/api/demo')])
    led = dr.load_ledger(tsv)
    [d] = dr.detect(fake_repo.root)
    assert dr.match(d, led)[0] == 'uri'


def test_台帳に無い経路は照合できない(tmp_path, fake_repo):
    fake_repo('modules/weko-demo/weko_demo/views.py',
              "@bp.route('/undocumented')\ndef leak():\n    return ''\n")
    tsv = write_full(tmp_path / 'full.tsv', [make_row(uri='/demo')])
    led = dr.load_ledger(tsv)
    [d] = dr.detect(fake_repo.root)
    assert dr.match(d, led)[1] == []


def test_許可リストのキーは行番号に依存しない(tmp_path, fake_repo):
    """行がずれるたびに許可リストを書き直すことになると、いずれ運用されなくなる。"""
    src = 'modules/weko-demo/weko_demo/views.py'
    fake_repo(src, "@bp.route('/x')\ndef f():\n    return ''\n")
    a = dr.detect(fake_repo.root)[0]
    fake_repo(src, "\n\n\n@bp.route('/x')\ndef f():\n    return ''\n")
    b = dr.detect(fake_repo.root)[0]
    assert a['line'] != b['line']
    assert dr.allow_key(a) == dr.allow_key(b)


# --------------------------------------------------------------------------
# ゲートと出力
# --------------------------------------------------------------------------

def _cross(fake_repo, tsv, *extra, expect=None, allow=None):
    from conftest import run
    env = {'WEKO_API_INVENTORY_DIR': os.path.dirname(tsv)} if allow else {}
    return run('detect_routes.py', '--weko-root', fake_repo.root, '--tsv', tsv,
               '--cross-check', *extra, env=env, expect=expect)


def test_未収載があればゲートで落ちる(tmp_path, fake_repo):
    fake_repo('modules/weko-demo/weko_demo/views.py',
              "@bp.route('/undocumented')\ndef leak():\n    return ''\n")
    tsv = write_full(tmp_path / 'full.tsv', [make_row(uri='/demo')])
    p = _cross(fake_repo, tsv, '--gate', expect=1)
    assert '/undocumented' in p.stdout


def test_許可リストに理由を書けばゲートを通る(tmp_path, fake_repo):
    src = 'modules/weko-demo/weko_demo/views.py'
    fake_repo(src, "@bp.route('/undocumented')\ndef leak():\n    return ''\n")
    tsv = write_full(tmp_path / 'full.tsv', [make_row(uri='/demo')])
    import json
    json.dump({f'{src}::leak': 'このサイトでは config で無効'},
              open(tmp_path / 'detect_allow.json', 'w', encoding='utf-8'),
              ensure_ascii=False)
    p = _cross(fake_repo, tsv, '--gate', allow=True, expect=0)
    assert 'このサイトでは config で無効' in p.stdout


def test_summary_onlyは経路名を出さない(tmp_path, fake_repo):
    fake_repo('modules/weko-demo/weko_demo/views.py',
              "@bp.route('/secret/leak/me')\ndef leak():\n    return ''\n")
    tsv = write_full(tmp_path / 'full.tsv', [make_row(uri='/demo')])
    p = _cross(fake_repo, tsv, '--summary-only')
    assert '/secret/leak/me' not in p.stdout
    assert 'leak' not in p.stdout
