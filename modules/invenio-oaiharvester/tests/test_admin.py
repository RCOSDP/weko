# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test admin interface."""
import copy
import pytest
import json
from mock import patch
from datetime import datetime
from flask import url_for, make_response
from flask_admin import Admin, menu
from invenio_communities.models import Community
from invenio_db import db
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index

from invenio_oaiharvester.admin import harvest_admin_view,run_stats,control_btns, index_query
from invenio_oaiharvester.models import HarvestSettings,HarvestLogs

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp

def test_admin(app, db):
    """Test Flask-Admin interace."""

    admin = Admin(app, name='Test')

    assert 'model' in harvest_admin_view
    assert 'modelview' in harvest_admin_view

    # Register both models in admin
    copy_adminview = copy.deepcopy(harvest_admin_view)
    model = copy_adminview.pop('model')
    view = copy_adminview.pop('modelview')
    admin.add_view(view(model, db.session, **copy_adminview))

    # Check if generated admin menu contains the correct items
    menu_items = {str(item.name): item for item in admin.menu()}
    assert 'OAI-PMH' in menu_items
    assert menu_items['OAI-PMH'].is_category()

    submenu_items = {
        str(item.name): item for item in menu_items['OAI-PMH'].get_children()
    }
    assert 'Harvesting' in submenu_items
    assert isinstance(submenu_items['Harvesting'], menu.MenuView)

    # Create a test set.
    with app.app_context():
        index = Index()
        db.session.add(index)
        db.session.commit()
        test_set = HarvestSettings(
            id=1,
            repository_name='test_name',
            base_url='test_url',
            metadata_prefix='test_metadata',
            index_id=index.id,
            update_style='0',
            auto_distribution='0')
        db.session.add(test_set)
        db.session.commit()

    with app.test_request_context():
        index_view_url = url_for('harvestsettings.index_view')
        delete_view_url = url_for('harvestsettings.delete_view')
        edit_view_url = url_for('harvestsettings.edit_view', id=1)
        detail_view_url = url_for('harvestsettings.details_view', id=1)

        run_api_url = url_for('harvestsettings.run', id=1)
        pause_api_url = url_for('harvestsettings.pause', id=1)
        clear_api_url = url_for('harvestsettings.clear', id=1)
        get_logs_api_url = url_for('harvestsettings.get_log_detail', id=1)
        get_log_detail_api_url = url_for('harvestsettings.get_log_detail',
                                         id=1)

    with app.test_client() as client:
        # List index view and check record is there.
        res = client.get(index_view_url)
        assert res.status_code == 200

        # List index view and check record is there.
        res = client.get(edit_view_url)
        assert res.status_code == 200

        # API
        # res = client.get(run_api_url)
        # assert res.status_code == 200

        # res = client.get(pause_api_url)
        # assert res.status_code == 200

        # res = client.get(clear_api_url)
        # assert res.status_code == 200

        # res = client.get(get_logs_api_url)
        # assert res.status_code == 200

        # res = client.get(get_log_detail_api_url)
        # assert res.status_code == 200

        # Deletion is forbiden.
        res = client.post(
            delete_view_url, data={'id': 1}, follow_redirects=True)
        assert res.status_code == 200

        # View the deleted record.
        res = client.get(detail_view_url)
        assert res.status_code == 302
        assert 0 == HarvestSettings.query.count()

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::test_run_stats -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_run_stats(app,db):
    index = Index()
    db.session.add(index)
    db.session.commit()
    not_task = HarvestSettings(
        id=1,
        repository_name="test_repo1",
        base_url="http://test1.org/",
        metadata_prefix="test_prefix",
        index_id=index.id,
    )
    resumption = HarvestSettings(
        id=2,
        repository_name="test_repo2",
        base_url="http://test2.org/",
        metadata_prefix="test_prefix",
        index_id=index.id,
        resumption_token="test_token"
    )
    task = HarvestSettings(
        id=3,
        repository_name="test_repo3",
        base_url="http://test3.org/",
        metadata_prefix="test_prefix",
        index_id=index.id,
        task_id="test_task",
        resumption_token="test_token",
        item_processed=1
    )
    db.session.add_all([not_task,resumption,task])
    db.session.commit()
    class MockM:
        def __init__(self,id):
            self.id=id

    test_func = run_stats()
    result = test_func(None,None,MockM(1),None)
    assert result == "Harvesting is not running"

    result = test_func(None,None,MockM(2),None)
    assert result == "Harvesting is paused with resumption token: test_token"

    result = test_func(None,None,MockM(3),None)
    assert result == "Harvesting is running at task id:test_task</br>1 items processed"


# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::test_control_btns -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_control_btns(app,db):
    admin = Admin(app, name='Test')

    # Register both models in admin
    copy_adminview = copy.deepcopy(harvest_admin_view)
    model = copy_adminview.pop('model')
    view = copy_adminview.pop('modelview')
    admin.add_view(view(model, db.session, **copy_adminview))

    index = Index()
    db.session.add(index)
    db.session.commit()
    not_task = HarvestSettings(
        id=1,
        repository_name="test_repo1",
        base_url="http://test1.org/",
        metadata_prefix="test_prefix",
        index_id=index.id,
    )
    resumption = HarvestSettings(
        id=2,
        repository_name="test_repo2",
        base_url="http://test2.org/",
        metadata_prefix="test_prefix",
        index_id=index.id,
        resumption_token="test_token"
    )
    task = HarvestSettings(
        id=3,
        repository_name="test_repo3",
        base_url="http://test3.org/",
        metadata_prefix="test_prefix",
        index_id=index.id,
        task_id="test_task",
        resumption_token="test_token",
        item_processed=1
    )
    db.session.add_all([not_task,resumption,task])
    db.session.commit()

    class MockM:
        def __init__(self,id):
            self.id=id

    test_func = control_btns()
    # task_id is None, resumption_token is None
    result = test_func(None,None,MockM(1),None)
    assert result == '<a id="hvt-btn" class="btn btn-primary" href="http://test_server/admin/harvestsettings/run/?id=1">Run</a>'

    # task_id is None, resumption_token is not None
    result = test_func(None,None,MockM(2),None)
    assert result == '<a id="resume-btn" class="btn btn-primary" href="http://test_server/admin/harvestsettings/run/?id=2">Resume</a>'\
                     '<a id="clear-btn" class="btn btn-danger" href="http://test_server/admin/harvestsettings/clear/?id=2">Clear</a>'

    # task_id is not None, resumption_token is not None
    result = test_func(None,None,MockM(3),None)
    assert result == '<a id="pause-btn" class="btn btn-warning" href="http://test_server/admin/harvestsettings/pause/?id=3">Pause</a>'


@pytest.fixture()
def setup_admin(app,db,users):
    admin = Admin(app, name='Test')

    # Register both models in admin
    copy_adminview = copy.deepcopy(harvest_admin_view)
    model = copy_adminview.pop('model')
    view = copy_adminview.pop('modelview')
    admin.add_view(view(model, db.session, **copy_adminview))
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        yield

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
class TestHarvestSettingView:
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView::test_run -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_run(self,app,db,setup_admin,users,mocker):
        url = url_for("harvestsettings.run",id=1)
        class MockTask:
            @classmethod
            def s(self):
                pass
        mocker.patch("invenio_oaiharvester.admin.link_success_handler",side_effect=MockTask)
        mocker.patch("invenio_oaiharvester.admin.link_error_handler",side_effect=MockTask)
        headers = {
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Referer":"http://test.org"
        }
        with app.test_client() as client:
            mock_run = mocker.patch("invenio_oaiharvester.admin.run_harvesting.apply_async")
            mock_redirect = mocker.patch("invenio_oaiharvester.admin.redirect",return_value=make_response())
            res = client.get(url,headers=headers)
            assert res.status_code == 200
            args, kwargs = mock_run.call_args
            assert kwargs["args"][0] == "1"
            assert kwargs["args"][2] == {"ip_address":"127.0.0.1","user_agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36","user_id":str(users[0]["obj"].id),"session_id":None}
            assert kwargs["args"][3] == {"remote_addr":"127.0.0.1","referrer":"http://test.org","hostname":"test_server","user_id":str(users[0]["obj"].id),"action":"HARVEST"}
            mock_redirect.assert_called_with("/admin/harvestsettings/details/?id=1")

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView::test_pause -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_pause(self,app,db,setup_admin,mocker):
        url = url_for("harvestsettings.pause",id=1)
        index = Index()
        db.session.add(index)
        db.session.commit()
        setting = HarvestSettings(
            id=1,
            repository_name="test_repo1",
            base_url="http://test1.org/",
            metadata_prefix="test_prefix",
            index_id=index.id,
            task_id="test_task"
        )
        db.session.add(setting)
        db.session.commit()

        with app.test_client() as client:
            mock_revoke = mocker.patch("invenio_oaiharvester.admin.celery.current_app.control.revoke")
            mock_redirect = mocker.patch("invenio_oaiharvester.admin.redirect",return_value=make_response())
            res = client.get(url)
            assert res.status_code == 200
            mock_revoke.assert_called_with("test_task",terminate=True)
            mock_redirect.assert_called_with("/admin/harvestsettings/details/?id=1")

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView::test_clear -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_clear(self,app,db,setup_admin,mocker):
        url = url_for("harvestsettings.clear",id=1)
        index = Index()
        db.session.add(index)
        db.session.commit()
        setting = HarvestSettings(
            id=1,
            repository_name="test_repo1",
            base_url="http://test1.org/",
            metadata_prefix="test_prefix",
            index_id=index.id,
            task_id="test_task"
        )
        db.session.add(setting)
        logs = HarvestLogs(
            id=1,harvest_setting_id=1
        )
        db.session.add(logs)
        db.session.commit()

        mocker.patch("invenio_oaiharvester.admin.send_run_status_mail")

        with app.test_client() as client:
            mock_redirect = mocker.patch("invenio_oaiharvester.admin.redirect",return_value=make_response())
            res = client.get(url)
            assert res.status_code == 200
            mock_redirect.assert_called_with("/admin/harvestsettings/details/?id=1")
            harvesting = HarvestSettings.query.filter_by(id=1).first()
            assert harvesting.task_id == None
            logs = HarvestLogs.query.filter_by(id=1).first()
            assert logs.status == "Cancel"

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView::test_get_logs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_get_logs(self,app,db,setup_admin):
        url = url_for("harvestsettings.get_logs",id=1)
        logs1 = HarvestLogs(
            id=1,harvest_setting_id=1,
            start_time=datetime(2021,1,10,11,22,33),
            end_time=datetime(2022,1,10,11,22,33)
        )
        logs2 = HarvestLogs(
            id=2,harvest_setting_id=1,
            start_time=datetime(2021,1,10,11,22,33),
        )
        db.session.add_all([logs1,logs2])
        db.session.commit()

        with app.test_client() as client:
            test = [
                {"counter":{},"end_time":None,"errmsg":None,"harvest_setting_id":1,"id":2,"requrl":None,"setting":{},"start_time":"2021-01-10T20:22:33+09:00","status":"Running"},
                {"counter":{},"end_time":"2022-01-10T20:22:33+09:00","errmsg":None,"harvest_setting_id":1,"id":1,"requrl":None,"setting":{},"start_time":"2021-01-10T20:22:33+09:00","status":"Running"}
            ]
            res = client.get(url)
            result = json.loads(res.data)
            assert result == test

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView::test_get_log_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_get_log_detail(self,app,db,setup_admin):
        url = url_for("harvestsettings.get_log_detail",id=1)
        logs = HarvestLogs(
            id=1,harvest_setting_id=1,
            start_time=datetime(2021,1,10,11,22,33),
            setting={"test_setting":"values"}
        )
        db.session.add(logs)
        db.session.commit()
        with app.test_client() as client:
            res = client.get(url)
            result = json.loads(res.data)
            assert result == {"test_setting":"values"}

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView::test_set_schedule -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_set_schedule(self,app,db,setup_admin,mocker):
        url = url_for("harvestsettings.set_schedule",id=1)
        index = Index()
        db.session.add(index)
        db.session.commit()
        setting = HarvestSettings(
            id=1,
            repository_name="test_repo1",
            base_url="http://test1.org/",
            metadata_prefix="test_prefix",
            index_id=index.id,
            task_id="test_task"
        )
        db.session.add(setting)
        db.session.commit()

        with app.test_client() as client:

            data = {
                "dis_enable_schedule":"True",
                "frequency":"daily"
            }
            mock_redirect = mocker.patch("invenio_oaiharvester.admin.redirect",return_value=make_response())
            res = client.post(url, data=data)
            assert res.status_code == 200
            mock_redirect.assert_called_with("/admin/harvestsettings/edit/?id=1")
            setting = HarvestSettings.query.filter_by(id=1).first()
            assert setting.schedule_enable == True
            assert setting.schedule_frequency == "daily"
            assert setting.schedule_details == 0
            data = {
                "dis_enable_schedule":"False",
                "frequency":"weekly",
                "weekly_details":1
            }
            mock_redirect = mocker.patch("invenio_oaiharvester.admin.redirect",return_value=make_response())
            res = client.post(url, data=data)
            assert res.status_code == 200
            mock_redirect.assert_called_with("/admin/harvestsettings/edit/?id=1")
            setting = HarvestSettings.query.filter_by(id=1).first()
            assert setting.schedule_enable == False
            assert setting.schedule_frequency == "weekly"
            assert setting.schedule_details == 1

            data = {
                "dis_enable_schedule":"True",
                "frequency":"monthly",
                "monthly_details":2
            }
            mock_redirect = mocker.patch("invenio_oaiharvester.admin.redirect",return_value=make_response())
            res = client.post(url, data=data)
            assert res.status_code == 200
            mock_redirect.assert_called_with("/admin/harvestsettings/edit/?id=1")
            setting = HarvestSettings.query.filter_by(id=1).first()
            assert setting.schedule_enable == True
            assert setting.schedule_frequency == "monthly"
            assert setting.schedule_details == 2

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView::test_get_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_get_query(self,app,db,users,mocker):
        copy_adminview = copy.deepcopy(harvest_admin_view)
        model = copy_adminview.pop('model')
        view = copy_adminview.pop('modelview')
        view = view(model, db.session, **copy_adminview)

        index = Index()
        db.session.add(index)
        db.session.commit()
        setting = HarvestSettings(
            id=1,
            repository_name="test_repo1",
            base_url="http://test1.org/",
            metadata_prefix="test_prefix",
            index_id=index.id,
            task_id="test_task"
        )
        db.session.add(setting)
        db.session.commit()

        # super role user
        user = users[0]["obj"]
        mocker.patch("flask_login.utils._get_user",return_value=user)
        query = view.get_query()
        assert query.count() == 1
        assert query.first() == setting

        # community role user with repository
        user = users[2]["obj"]
        repository = Community(root_node_id=index.id)
        mocker.patch("flask_login.utils._get_user",return_value=user)
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[repository])
        mocker.patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[index.id])
        query = view.get_query()
        assert query.count() == 1
        assert query.first() == setting

        # community role user with no repository
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[])
        query = view.get_query()
        assert query.count() == 0

        # community role user with repository but no index
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[repository])
        mocker.patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[])
        query = view.get_query()
        assert query.count() == 0

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::TestHarvestSettingView::test_get_count_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_get_count_query(self,app,db,users,mocker):
        copy_adminview = copy.deepcopy(harvest_admin_view)
        model = copy_adminview.pop('model')
        view = copy_adminview.pop('modelview')
        view = view(model, db.session, **copy_adminview)

        index = Index()
        db.session.add(index)
        db.session.commit()
        setting = HarvestSettings(
            id=1,
            repository_name="test_repo1",
            base_url="http://test1.org/",
            metadata_prefix="test_prefix",
            index_id=index.id,
            task_id="test_task"
        )
        db.session.add(setting)
        db.session.commit()

        # super role user
        user = users[0]["obj"]
        mocker.patch("flask_login.utils._get_user",return_value=user)
        query = view.get_count_query()
        assert query.scalar() == 1

        # community role user with repository
        user = users[2]["obj"]
        repository = Community(root_node_id=index.id)
        mocker.patch("flask_login.utils._get_user",return_value=user)
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[repository])
        mocker.patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[index.id])
        query = view.get_count_query()
        assert query.scalar() == 1

        # community role user with no repository
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[])
        query = view.get_count_query()
        assert query.scalar() == 0

        # community role user with repository but no index
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[repository])
        mocker.patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[])
        query = view.get_count_query()
        assert query.scalar() == 0


# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_admin.py::test_index_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_index_query(app, db, users, mocker):
    with app.app_context():
        index1 = Index(id=1, position=1)
        index2 = Index(id=2, position=2)
        db.session.add(index1)
        db.session.add(index2)
        db.session.commit()

        # super role user
        user = users[0]["obj"]
        mocker.patch("flask_login.utils._get_user",return_value=user)
        result = index_query()
        assert len(result) == 2
        assert index1 in result
        assert index2 in result

        # community role user with repository
        repository = Community(root_node_id=index1.id)
        user = users[2]["obj"]
        mocker.patch("flask_login.utils._get_user",return_value=user)
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user",return_value=[repository])
        mocker.patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[index1.id])
        result = index_query()
        assert len(result) == 1
        assert index1 in result

        # community role user with no repository
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user",return_value=[])
        result = index_query()
        assert len(result) == 0


        # community role user with repository but no index
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user",return_value=[repository])
        mocker.patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[])
        result = index_query()
        assert len(result) == 0

        # get_repositories_by_user raise exception
        mocker.patch("invenio_communities.models.Community.get_repositories_by_user",side_effect=Exception)
        with pytest.raises(Exception):
            result = index_query()

        # get_child_list_recursive raise exception
        mocker.patch("weko_index_tree.api.Indexes.get_child_list_recursive",side_effect=Exception)
        with pytest.raises(Exception):
            result = index_query()
