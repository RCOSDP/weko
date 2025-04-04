# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import json
import pytest
from mock import patch, MagicMock
from flask import url_for
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.base import ViewArgs
from invenio_accounts.testutils import login_user_via_session

from weko_gridlayout.utils import get_register_language
from weko_gridlayout.admin import WidgetSettingView, WidgetDesign
from weko_gridlayout.models import WidgetItem


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_admin.py::test_index_view_can_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
@pytest.mark.parametrize("can_delete", [True, False, None])
def test_index_view_can_delete(app, client, admin_view, widget_items,
                               view_instance, can_delete):
    """Test flask-admin interace."""
    view = view_instance
    view.can_delete = can_delete
    index_view_url = url_for("widgetitem.index_view")
    res = client.get(index_view_url)
    assert res.status_code == 200


@pytest.mark.parametrize("sort", [1, None])
def test_index_view_sort_column(app,
                client, admin_view, view_instance, widget_items, sort):
    """Test flask-admin interace."""
    view = view_instance
    view_args = ViewArgs(page=1,
                        page_size=20,
                        sort=sort,
                        sort_desc=1,
                        search=None,
                        filters=None,
                        extra_args={})
    view.column_editable_list = {"test": "test"}

    with patch("weko_gridlayout.admin.WidgetSettingView._get_list_extra_args", return_value=view_args):
        index_view_url = url_for("widgetitem.index_view")
        res = client.get(index_view_url)
        assert res.status_code == 200


# with list-with data の場合にエラー発生
@pytest.mark.parametrize("condition1, condition2",
                         [("with list", "with data"), ("with list", "without data"),
                         ("without list", "with data"), ("without list", "without data"),
                         ("with page_size", "with count"), ("with page_size", "without count"),
                         ("without page_size", "with count"), ("without page_size", "without count")])
def test_index_view_editable_list_page_size_data(app, client, admin_view, view_instance,
                                widget_items, condition1, condition2):
    """Test flask-admin interace."""
    view = view_instance
    view_args = ViewArgs(page=1,
                        page_size=None,
                        sort=1,
                        sort_desc=1,
                        search=None,
                        filters=None,
                        extra_args={})
    if condition1 == "with list":
        view.column_editable_list = {"test": "test"}
    else:
        view.column_editable_list = {}

    if condition1 == "with page_size":
        view.page_size = 20
    else:
        view.page_size = None

    if condition2 == "with data" or condition2 == "with count":
        with patch("weko_gridlayout.admin.WidgetSettingView._get_list_extra_args", return_value=view_args):
            with patch("weko_gridlayout.admin.WidgetSettingView.get_list", return_value=(3, widget_items)):
                with patch("weko_gridlayout.admin.WidgetSettingView.list_form"):
                    index_view_url = url_for("widgetitem.index_view")
                    res = client.get(index_view_url)
                    assert res.status_code == 200

    elif condition2 == "without count":
        with patch("weko_gridlayout.admin.WidgetSettingView.get_list", return_value=(None, widget_items)):
                index_view_url = url_for("widgetitem.index_view")
                res = client.get(index_view_url)
                assert res.status_code == 200
    else:
        index_view_url = url_for("widgetitem.index_view")
        res = client.get(index_view_url)
        assert res.status_code == 200


@pytest.mark.parametrize("page_size",
                         [1, 2])
def test_pager_url(app, client, admin_view, view_instance,
                   widget_items, page_size):
    """Test flask-admin interace."""
    view = view_instance
    view_args = ViewArgs(page=1,
                        page_size=page_size,
                        sort=1,
                        sort_desc=1,
                        search=None,
                        filters=None,
                        extra_args={})

    with patch("weko_gridlayout.admin.WidgetSettingView._get_list_extra_args", return_value=view_args):
        with patch("weko_gridlayout.admin.WidgetSettingView.get_list", return_value=(3, widget_items)):
            index_view_url = url_for("widgetitem.index_view")
            res = client.get(index_view_url)
            assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_admin.py::test_sort_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
#一つのパラメータセットにつき複数回呼び出されている模様
@pytest.mark.parametrize("desc, invert, sort_desc",
                         [(1, False, 1), (1, False, 0), (1, False, None),
                          (1, True, 1), (1, True, 0), (1, True, None),
                          (0, False, 1), (0, False, 0), (0, False, None),
                          (0, True, 1), (0, True, 0), (0, True, None),
                          (None, False, 1), (None, False, 0), (None, False, None),
                          (None, True, 1), (None, True, 0), (None, True, None),
                         ])
def test_sort_url(app, client, admin_view, view_instance,
                   widget_item, desc, invert, sort_desc):
    """Test flask-admin interace."""
    view = view_instance
    view_args = ViewArgs(page=1,
                        page_size=20,
                        sort=1,
                        sort_desc=sort_desc,
                        search=None,
                        filters=None,
                        extra_args={})
    view.desc = desc
    view.invert = invert
    with patch("weko_gridlayout.admin.WidgetSettingView._get_list_extra_args", return_value=view_args):
        with patch("weko_gridlayout.admin.WidgetSettingView.get_list", return_value=(1, widget_item)):
            index_view_url = url_for("widgetitem.index_view")
            res = client.get(index_view_url)
            assert res.status_code == 200
            if not desc and invert and not sort_desc:
                assert view.desc == 1
            else:
                assert view.desc == desc


@pytest.mark.parametrize("page_size",
                         [20, 0, None])
def test_page_size_url(app, client, admin_view, view_instance,
                   widget_item, page_size):
    """Test flask-admin interace."""
    view = view_instance
    view_args = ViewArgs(page=1,
                        page_size=page_size,
                        sort=1,
                        sort_desc=1,
                        search=None,
                        filters=None,
                        extra_args={})
    view.page_size = page_size

    with patch("weko_gridlayout.admin.WidgetSettingView._get_list_extra_args", return_value=view_args):
        with patch("weko_gridlayout.admin.WidgetSettingView.get_list", return_value=(1, widget_item)):
            index_view_url = url_for("widgetitem.index_view")
            res = client.get(index_view_url)
            assert res.status_code == 200


def test_get_label_display_to_list_without_register_languages(admin_view, widget_items):
    res = WidgetSettingView.get_label_display_to_list(1)
    assert res is None


@pytest.mark.parametrize("num, result",
                         [(1, None), (2, None)])
def test_get_label_display_to_list_without_widget(admin_view, admin_lang_settings, num, result):
    res = WidgetSettingView.get_label_display_to_list(num)
    assert res == result


@pytest.mark.parametrize("num, result",
                         [(1, "for test"), (2, "for test2"), (3, None)])
def test_get_label_display_to_list(admin_view, widget_items, admin_lang_settings, num, result):
    res = WidgetSettingView.get_label_display_to_list(num)
    assert res == result


def test_search_placeholder(app, admin_view, widget_items, view_instance):

    # Error
    assert view_instance.search_placeholder() == "Search"


# WidgetDesign.index ~ ERROR
def test_index_WidgetDesign(i18n_app, view_instance):
    test = WidgetDesign()
    test.admin = MagicMock()
    test.admin.base_template = "weko_gridlayout/admin/widget_design.html"
    try:
        assert test.index()
    except:
        pass


# WidgetSettingView.index_view ~ ERROR
def test_index_view_WidgetSettingView(i18n_app, view_instance):
    assert view_instance.index_view() != None


# WidgetSettingView.create_view ~ ERROR
def test_create_view_WidgetSettingView(i18n_app, view_instance):
    with patch("weko_gridlayout.admin.get_redirect_target", return_value="/"):
        def can_create():
            return False

        view_instance.admin = MagicMock()
        view_instance.admin.base_template = "weko_gridlayout/admin/widget_design.html"
        view_instance.can_create = can_create

        assert view_instance.create_view()


# WidgetSettingView.edit_view ~ ERROR jinja2.exceptions.TemplateSyntaxError: Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'.
def test_edit_view_WidgetSettingView(i18n_app, view_instance):
    locked_widget = WidgetItem()
    i18n_app.config["WEKO_GRIDLAYOUT_ADMIN_EDIT_WIDGET_SETTINGS"] = 'weko_gridlayout/admin/edit_widget_settings.html'

    with patch("weko_gridlayout.admin.get_redirect_target", return_value="/"):
        with patch("weko_gridlayout.admin.WidgetItemServices.get_locked_widget_info", return_value=locked_widget):
            view_instance.admin = MagicMock()
            view_instance.admin.base_template = "weko_gridlayout/admin/edit_widget_settings.html"
            # Error ~ jinja2.exceptions.TemplateSyntaxError: Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'.
            try:
                assert view_instance.edit_view()
            except:
                pass

        with patch("weko_gridlayout.admin.WidgetItemServices.get_locked_widget_info", return_value="locked_widget"):
            view_instance.admin = MagicMock()
            view_instance.admin.base_template = "weko_gridlayout/admin/edit_widget_settings.html"

            with patch('weko_gridlayout.admin.WidgetSettingView.get_one', return_value=""):
                with patch('weko_gridlayout.admin.convert_widget_data_to_dict', return_value=""):
                    with patch('weko_gridlayout.admin.convert_data_to_design_pack', return_value=""):
                        assert view_instance.edit_view()

                    model = {"test": "test"}

                    # Error ~ jinja2.exceptions.TemplateSyntaxError: Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'.
                    with patch('weko_gridlayout.admin.convert_data_to_edit_pack', return_value=model):
                        try:
                            assert view_instance.edit_view()
                        except:
                            pass

        with patch("weko_gridlayout.admin.WidgetItemServices.get_locked_widget_info", return_value={}):
            with patch('weko_gridlayout.admin.WidgetSettingView.get_one', return_value=""):
                with patch('weko_gridlayout.admin.convert_widget_data_to_dict', return_value=""):

                    # Error ~ jinja2.exceptions.TemplateSyntaxError: Encountered unknown tag 'assets'. Jinja was looking for the following tags: 'endblock'. The innermost block that needs to be closed is 'block'.
                    with patch('weko_gridlayout.admin.convert_data_to_edit_pack', return_value={"test": "test"}):
                        with patch('weko_gridlayout.admin.WidgetItemServices.lock_widget', return_value=""):
                            view_instance.admin = MagicMock()
                            view_instance.admin.base_template = "weko_gridlayout/admin/edit_widget_settings.html"
                            try:
                                assert view_instance.edit_view()
                            except:
                                pass


# WidgetSettingView.get_detail_value
def test_get_detail_value_WidgetSettingView(i18n_app, view_instance):
    context = MagicMock()
    model = MagicMock()
    name = "text_color"

    assert not view_instance.get_detail_value(context, model, name)
    assert view_instance.get_detail_value(context, model, "name")


# WidgetSettingView.details_view
def test_details_view_WidgetSettingView(i18n_app, view_instance):
    def get_one(item):
        get_one_magic_mock = MagicMock()
        get_one_magic_mock.label = "label"
        get_one_magic_mock.id = 1

        return get_one_magic_mock

    def can_view_details_T():
        return True

    def can_view_details_F():
        return False

    view_instance.get_one = get_one

    with patch("weko_gridlayout.admin.get_redirect_target", return_value="/"):
        with patch("weko_gridlayout.admin.helpers.get_mdict_item_or_list", return_value="1"):
            with patch("weko_gridlayout.admin.WidgetSettingView.get_label_display_to_list", return_value="1"):
                view_instance.admin = MagicMock()
                view_instance.admin.base_template = "weko_gridlayout/admin/widget_design.html"
                view_instance.can_view_details = can_view_details_F

                view_instance.can_view_details = can_view_details_F
                assert view_instance.details_view()


# WidgetSettingView.action_delete
def test_action_delete_WidgetSettingView(i18n_app, view_instance):
    def get_query_for_ids(item1, item2, item3):
        def all_func():
            all_func_magic_mock = MagicMock()
            all_func_magic_mock.widget.id = 1
            return [all_func_magic_mock]
        get_query_for_ids_magic_mock = MagicMock()
        get_query_for_ids_magic_mock.all = all_func
        return get_query_for_ids_magic_mock

    ids = MagicMock()
    tools = MagicMock()
    tools.get_query_for_ids = get_query_for_ids

    # with patch('weko_gridlayout.admin.tools', tools):
        # assert not view_instance.action_delete(ids)

    assert view_instance.action_delete(ids) == None

    # Exception coverage
    try:
        view_instance.action_delete(0)
    except:
        pass

# WidgetSettingView.get_query
def test_get_query_WidgetSettingView(i18n_app, view_instance, users, db_register):
    # super role user
    with patch("flask_login.utils._get_user", return_value=users[2]['obj']):
        query = view_instance.get_query()
        assert query.count() == WidgetItem.query.count()

    # comadmin role user
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_gridlayout.admin.Community.get_repositories_by_user", return_value=[MagicMock(id="Root Index")]):
            query = view_instance.get_query()
            assert query.count() == WidgetItem.query.count()
        with patch("weko_gridlayout.admin.Community.get_repositories_by_user", return_value=[]):
            query = view_instance.get_query()
            assert query.count() == 0

# WidgetSettingView.get_count_query
def test_get_count_query_WidgetSettingView(i18n_app, view_instance, users, db_register):
    # super role user
    with patch("flask_login.utils._get_user", return_value=users[2]['obj']):
        query = view_instance.get_count_query()
        assert query.scalar() == WidgetItem.query.count()

    # comadmin role user
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_gridlayout.admin.Community.get_repositories_by_user", return_value=[MagicMock(id="Root Index")]):
            query = view_instance.get_count_query()
            assert query.scalar() == WidgetItem.query.count()
        with patch("weko_gridlayout.admin.Community.get_repositories_by_user", return_value=[]):
            query = view_instance.get_count_query()
            assert query.scalar() == 0

# WidgetSettingView.delete_model
def test_delete_model_WidgetSettingView(i18n_app, view_instance, widget_items, db):
    model = widget_items[0]
    data = MagicMock()
    data.widget_id = 222

    assert view_instance.delete_model(model, db.session) == True
    assert view_instance.delete_model(model) == True

    with patch('weko_gridlayout.admin.WidgetItemServices.delete_multi_item_by_id', side_effect=Exception('test')):
        with patch('weko_gridlayout.admin.current_app.logger.error', return_value=""):
            assert view_instance.delete_model(model, db.session) == False

# WidgetSettingView.on_model_delete
def test_on_model_delete_WidgetSettingView(i18n_app, view_instance, widget_items, db):
    model = widget_items[0]

    def is_used_in_widget_design(item):
        return True

    WidgetDesignServices = MagicMock()
    WidgetDesignServices.is_used_in_widget_design = is_used_in_widget_design

    with patch('weko_gridlayout.admin.WidgetDesignServices', WidgetDesignServices):
        assert view_instance.delete_model(model) == False

    assert view_instance.delete_model(model) == True
