import shutil
import tempfile
import os
import uuid
import json

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_babelex import Babel, lazy_gettext as _
from flask_menu import Menu
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_accounts.testutils import create_test_user
from invenio_accounts import InvenioAccounts
from invenio_accounts.views.settings import blueprint as invenio_accounts_blueprint
from invenio_db import InvenioDB
from invenio_accounts.models import User, Role
from invenio_accounts.views.settings import blueprint \
    as invenio_accounts_blueprint
from invenio_cache import InvenioCache
from invenio_db import InvenioDB, db as db_
from invenio_stats import InvenioStats
# from weko_records_ui import WekoRecordsUI
from weko_theme import WekoTheme
from weko_workflow import WekoWorkflow
from weko_workflow.models import Activity, Action, ActionStatus, FlowDefine, WorkFlow
from weko_records.models import ItemType, ItemTypeName
from weko_records import WekoRecords
from weko_workflow.views import blueprint as weko_workflow_blueprint
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from weko_records_ui import WekoRecordsUI 

import subprocess
from flask_assets import assets
from invenio_assets import InvenioAssets
from invenio_assets.cli import collect, npm
from flask.cli import ScriptInfo
from click.testing import CliRunner
from weko_workflow.bundles import js_workflow,js_item_link, js_activity_list,js_iframe,js_oa_policy,js_identifier_grant,js_quit_confirmation,js_lock_activity,js_admin_workflow_detail,css_workflow,css_datepicker_workflow,js_admin_flow_detail
from invenio_communities import InvenioCommunities
from invenio_i18n import InvenioI18N
from weko_admin import WekoAdmin
from invenio_admin import InvenioAdmin
@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    print(path)
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        ACCOUNTS_USERINFO_HEADERS=True,
        WEKO_PERMISSION_SUPER_ROLE_USER=['System Administrator',
                                         'Repository Administrator'],
        WEKO_PERMISSION_ROLE_COMMUNITY=['Community Administrator'],
        # THEME_SITEURL = 'https://localhost',
        WEKO_RECORDS_UI_LICENSE_DICT=[
            {
                'name': _('write your own license'),
                'value': 'license_free',
            },
            # version 0
            {
                'name': _(
                    'Creative Commons CC0 1.0 Universal Public Domain Designation'),
                'code': 'CC0',
                'href_ja': 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja',
                'href_default': 'https://creativecommons.org/publicdomain/zero/1.0/',
                'value': 'license_12',
                'src': '88x31(0).png',
                'src_pdf': 'cc-0.png',
                'href_pdf': 'https://creativecommons.org/publicdomain/zero/1.0/'
                            'deed.ja',
                'txt': 'This work is licensed under a Public Domain Dedication '
                    'International License.'
            },
            # version 3.0
            {
                'name': _('Creative Commons Attribution 3.0 Unported (CC BY 3.0)'),
                'code': 'CC BY 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by/3.0/',
                'value': 'license_6',
                'src': '88x31(1).png',
                'src_pdf': 'by.png',
                'href_pdf': 'http://creativecommons.org/licenses/by/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                       ' 3.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-ShareAlike 3.0 Unported '
                    '(CC BY-SA 3.0)'),
                'code': 'CC BY-SA 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-sa/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-sa/3.0/',
                'value': 'license_7',
                'src': '88x31(2).png',
                'src_pdf': 'by-sa.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-sa/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-ShareAlike 3.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)'),
                'code': 'CC BY-ND 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nd/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nd/3.0/',
                'value': 'license_8',
                'src': '88x31(3).png',
                'src_pdf': 'by-nd.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nd/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NoDerivatives 3.0 International License.'

            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial 3.0 Unported'
                    ' (CC BY-NC 3.0)'),
                'code': 'CC BY-NC 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc/3.0/',
                'value': 'license_9',
                'src': '88x31(4).png',
                'src_pdf': 'by-nc.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial 3.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 '
                    'Unported (CC BY-NC-SA 3.0)'),
                'code': 'CC BY-NC-SA 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
                'value': 'license_10',
                'src': '88x31(5).png',
                'src_pdf': 'by-nc-sa.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial-ShareAlike 3.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial-NoDerivs '
                    '3.0 Unported (CC BY-NC-ND 3.0)'),
                'code': 'CC BY-NC-ND 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc-nd/3.0/',
                'value': 'license_11',
                'src': '88x31(6).png',
                'src_pdf': 'by-nc-nd.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial-ShareAlike 3.0 International License.'
            },
            # version 4.0
            {
                'name': _('Creative Commons Attribution 4.0 International (CC BY 4.0)'),
                'code': 'CC BY 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by/4.0/',
                'value': 'license_0',
                'src': '88x31(1).png',
                'src_pdf': 'by.png',
                'href_pdf': 'http://creativecommons.org/licenses/by/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    ' 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-ShareAlike 4.0 International '
                    '(CC BY-SA 4.0)'),
                'code': 'CC BY-SA 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-sa/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-sa/4.0/',
                'value': 'license_1',
                'src': '88x31(2).png',
                'src_pdf': 'by-sa.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-sa/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-ShareAlike 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NoDerivatives 4.0 International '
                    '(CC BY-ND 4.0)'),
                'code': 'CC BY-ND 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nd/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nd/4.0/',
                'value': 'license_2',
                'src': '88x31(3).png',
                'src_pdf': 'by-nd.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nd/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NoDerivatives 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial 4.0 International'
                    ' (CC BY-NC 4.0)'),
                'code': 'CC BY-NC 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc/4.0/',
                'value': 'license_3',
                'src': '88x31(4).png',
                'src_pdf': 'by-nc.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial-ShareAlike 4.0'
                    ' International (CC BY-NC-SA 4.0)'),
                'code': 'CC BY-NC-SA 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'value': 'license_4',
                'src': '88x31(5).png',
                'src_pdf': 'by-nc-sa.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial-ShareAlike 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 '
                    'International (CC BY-NC-ND 4.0)'),
                'code': 'CC BY-NC-ND 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
                'value': 'license_5',
                'src': '88x31(6).png',
                'src_pdf': 'by-nc-nd.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial-ShareAlike 4.0 International License.'
            },
        ],
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE="",
    )
    app_.testing = True
    Babel(app_)
    Menu(app_)
    InvenioAdmin(app_)
    InvenioI18N(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioCache(app_)
    InvenioDB(app_)
    InvenioStats(app_)
    WekoTheme(app_)
    WekoWorkflow(app_)
    WekoRecords(app_)
    
    WekoRecordsUI(app_)
    InvenioCommunities(app_)
    WekoAdmin(app_)
    assets_ext = InvenioAssets(app_)
    app_.jinja_loader.searchpath.append("../invenio-communities/invenio_communities/templates")
    # assets_ext.env.register("invenio_theme_js", js_workflow)
    # assets_ext.env.register("invenio_theme_js", js_item_link)
    # assets_ext.env.register("invenio_theme_js", js_activity_list)
    # assets_ext.env.register("invenio_theme_js", js_iframe)
    # assets_ext.env.register("invenio_theme_js", js_oa_policy)
    # assets_ext.env.register("invenio_theme_js", js_identifier_grant)
    # assets_ext.env.register("invenio_theme_js", js_quit_confirmation)
    # assets_ext.env.register("invenio_theme_js", js_lock_activity)
    # assets_ext.env.register("invenio_theme_js", js_admin_workflow_detail)
    # assets_ext.env.register("invenio_theme_css", css_workflow)
    # assets_ext.env.register("invenio_theme_css", css_datepicker_workflow)
    # assets_ext.env.register("invenio_theme_css", js_admin_flow_detail)
    # WekoRecordsUI(app_)
    app_.register_blueprint(invenio_accounts_blueprint)
    app_.register_blueprint(weko_workflow_blueprint)
    print(app_.instance_path)
    return app_

@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    drop_database(str(db_.engine.url))


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client

@pytest.fixture()
def create_activity(db, users):
    from datetime import datetime
    item_id = uuid.uuid4()
    activity = Activity(
        activity_id = "A-20220420-00001",
        item_id=item_id,
        workflow_id=1,
        flow_id=1,
        action_id=2,
        action_status="F",
        activity_login_user=5,
        activity_update_user=5,
        activity_status="F",
        activity_start=datetime.utcnow(),
        activity_end=datetime.utcnow(),
        activity_confirm_term_of_use=True,
        title="test item01",
        shared_user_id=-1,
        extra_info={},
        action_order=6
    )
    #db.session.add(activity)
    action_status = ActionStatus(
        action_status_id="F",
        action_status_name="action_done",
        action_status_desc="",
        action_scopes="sys,user",
        action_displays="Complete",
    )
    #db.session.add(action_status)
    flow_id = uuid.uuid4()
    flows_id2 = uuid.uuid4()
    flow_define = FlowDefine(
        flow_id=flow_id,
        flow_name="test flow",
        flow_user=5,
        flow_status="A",
        is_deleted=False,
    )
    #db.session.add(flow_define)
    workflow = WorkFlow(
        flows_id=flows_id2,
        flows_name="test workflow",
        itemtype_id=1,
        flow_id=flow_id,
        is_deleted=False,
        open_restricted=True,
        is_gakuninrdm=False,
    )
    #db.session.add(workflow)
    item_type=ItemType(
        name_id=1,
        harvesting_type=True,
        schema={"type": "object"},
        form={"type": "object"},
        render={"type": "object"},
        tag=1,
        version_id=1,
        is_deleted=False
    )
    #db.session.add(item_type)
    item_type_name=ItemTypeName(
        name="test item_type",
        has_site_license=False,
        is_active=True
    )
    #db.session.add(item_type_name)
    actions=list()
    with open("tests/data/actions.json","r") as f:
        action_datas = json.load(f)
        print(action_datas)
    # for action_data in action_datas:
    #     data = action_data
    #     data["action_makedate"] = datetime.utcnow()
    #     data["action_lastdate"] = datetime.utcnow()
    #     action = Action(**data)
    #     db.session.add(action)
    #     actions.append(action)
    data = action_datas[1]
    data["action_makedate"] = datetime.utcnow()
    data["action_lastdate"] = datetime.utcnow()
    action = Action(**action_datas[1])
    # db.session.commit()
    yield {
        "uuid":id,
        "activity":activity,
        # "actions":actions,
        "action":action,
        "action_status":action_status,
        "flow_define":flow_define,
        "workflow":workflow,
        "item_type":item_type,
        "item_type_name":item_type_name
        }

@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user_count = User.query.filter_by(email='test@test.org').count()
    if user_count != 1:
        user = create_test_user(email='test@test.org')
        contributor = create_test_user(email='test2@test.org')
        comadmin = create_test_user(email='test3@test.org')
        repoadmin = create_test_user(email='test4@test.org')
        sysadmin = create_test_user(email='test5@test.org')

    else:
        user = User.query.filter_by(email='test@test.org').first()
        contributor = User.query.filter_by(email='test2@test.org').first()
        comadmin = User.query.filter_by(email='test3@test.org').first()
        repoadmin = User.query.filter_by(email='test4@test.org').first()
        sysadmin = User.query.filter_by(email='test5@test.org').first()

    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        r1 = ds.create_role(name='System Administrator')
        r2 = ds.create_role(name='Repository Administrator')
        r3 = ds.create_role(name='Contributor')
        r4 = ds.create_role(name='Community Administrator')

    else:
        r1 = Role.query.filter_by(name='System Administrator').first()
        r2 = Role.query.filter_by(name='Repository Administrator').first()
        r3 = Role.query.filter_by(name='Contributor').first()
        r4 = Role.query.filter_by(name='Community Administrator').first()

    ds.add_role_to_user(sysadmin, r1)
    ds.add_role_to_user(repoadmin, r2)
    ds.add_role_to_user(contributor, r3)
    ds.add_role_to_user(comadmin, r4)

    # Assign author-access to contributor, comadmin, repoadmin, sysadmin.
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin)
        ]
        db.session.add_all(action_users)
    print(sysadmin.id)
    return [
        {'email': user.email, 'id': user.id,
         'obj': user},
        {'email': contributor.email, 'id': contributor.id,
         'obj': contributor},
        {'email': comadmin.email, 'id': comadmin.id,
         'obj': comadmin},
        {'email': repoadmin.email, 'id': repoadmin.id,
         'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id,
         'obj': sysadmin},
    ]

@pytest.yield_fixture()
def webassets(app):
    """Flask application fixture with assets."""
    initial_dir = os.getcwd()
    os.chdir(app.instance_path)

    script_info = ScriptInfo(create_app=lambda info: app)
    script_info._loaded_app = app

    runner = CliRunner()
    # runner.invoke(npm, obj=script_info)

    # subprocess.call(['npm', 'install'])
    runner.invoke(collect, ['-v'], obj=script_info)
    runner.invoke(assets, ['build'], obj=script_info)

    yield app

    os.chdir(initial_dir)