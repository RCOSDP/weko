import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch, MagicMock
from elasticsearch_dsl import response, Search

from weko_theme.utils import (
    get_weko_contents,
    get_community_id,
    get_design_layout,
    has_widget_design,
    MainScreenInitDisplaySetting
)


# def get_weko_contents(getargs):
def test_get_weko_contents(i18n_app, users, client_request_args, communities,redis_connect, db):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_weko_contents('comm1')

    with patch("weko_theme.utils.get_index_link_list", return_value=[(11, 'TEST INDEX')]):
        index_style = MagicMock()
        index_style.index_link_enabled = False
        with patch('weko_theme.utils.IndexStyle.get', return_value=index_style):
            result = get_weko_contents('comm1')
            assert result
            assert not result['index_link_list']

            index_style.index_link_enabled = True
            with patch('weko_theme.utils.IndexStyle.get', return_value=index_style):
                result = get_weko_contents('comm1')
                assert result
                assert result['index_link_list']


# def get_community_id(getargs):
def test_get_community_id(i18n_app, communities, db):
    assert get_community_id({'c': 'comm1'})
    assert get_community_id({'c': 'comm2'})


# def get_design_layout(repository_id):
def test_get_design_layout(i18n_app, users, client_request_args, communities):
    assert False in get_design_layout('Root Index')
    assert False in get_design_layout(False)

    with patch('weko_theme.utils.main_design_has_main_widget', return_value=True):
        assert True in get_design_layout('Root Index')


# def has_widget_design(repository_id, current_language):
def test_has_widget_design(i18n_app, users, client_request_args, communities):
    widget_design_setting = {
        "widget-settings": "widget-settings-9999"
    }

    with patch('weko_theme.utils.WidgetDesignServices.get_widget_design_setting', return_value=widget_design_setting):
        assert has_widget_design('Root Index', 'en') == True

    assert has_widget_design('Root Index', 'en') == False

# class MainScreenInitDisplaySetting:
# .tox/c1/bin/pytest --cov=weko_theme tests/test_utils.py::test_get_init_display_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-theme/.tox/c1/tmp
def test_get_init_display_setting(i18n_app, users, client_request_args, communities):
    def dummy_response(data):
        dummy=response.Response(Search(), json.loads(data))
        return dummy

    search_setting = MagicMock()
    search_setting.init_disp_setting = {
        "init_disp_screen_setting": "0",
        "init_disp_index_disp_method": "0",
        "init_disp_index": MagicMock(),
    }
    i18n_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE'] = "schemas/schemaform.json",
    i18n_app.config['WEKO_SEARCH_TYPE_DICT'] = {'INDEX': "WEKO_SEARCH_TYPE_DICT-INDEX"}
    i18n_app.config['COMMUNITIES_SORTING_OPTIONS'] = {'INDEX': "COMMUNITIES_SORTING_OPTIONS-INDEX"}
    test = MainScreenInitDisplaySetting()

    with patch('weko_theme.utils.SearchManagement.get', return_value=search_setting):
        with patch('invenio_search.RecordsSearch.execute', return_value=dummy_response('{"hits": {"hits": [{"_source": {"path": ["44"]}},{"_source": {"path": ["11"]}}]}}')):
            with patch('weko_theme.utils.get_journal_info', return_value="get_journal_info"):
                res = test.get_init_display_setting()
                assert res["index_id"] == "11"

                with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
                    res = test.get_init_display_setting()
                    assert res["index_id"] == "44"

        current_index = MagicMock()
        current_index.display_format = "2"
        with patch('weko_theme.utils.Indexes.get_index', return_value=current_index):
            search_setting.init_disp_setting["init_disp_index_disp_method"] = "1"
            with patch('weko_theme.utils.get_journal_info', return_value="get_journal_info"):
                assert isinstance(test.get_init_display_setting(), dict)

        ranking_settings = MagicMock()
        ranking_settings.statistical_period = "9999"
        ranking_settings.is_show = True
        with patch('weko_theme.utils.RankingSettings.get', return_value=ranking_settings):
            with patch('weko_items_ui.utils.get_ranking', return_value="get_ranking"):
                search_setting.init_disp_setting["init_disp_screen_setting"] = "1"
                assert isinstance(test.get_init_display_setting(), dict)

        search_setting.init_disp_setting["init_disp_screen_setting"] = "2"
        assert isinstance(test.get_init_display_setting(), dict)

    assert isinstance(test.get_init_display_setting(), dict)
