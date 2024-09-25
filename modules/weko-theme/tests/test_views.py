import json
import pytest
from mock import patch, MagicMock
from flask import current_app, make_response, request
from flask_login import current_user
from flask import url_for

from weko_admin.models import SiteInfo
from invenio_accounts.testutils import login_user_via_session
from weko_theme import WekoTheme
from weko_theme.views import (
    index,
    edit,
    get_default_search_setting,
    get_site_info,
    get_init_display_setting
)

# def index():
# .tox/c1/bin/pytest --cov=weko_theme tests/test_views.py::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-theme/.tox/c1/tmp
def test_index(i18n_app, users):
    WekoTheme(i18n_app)

    with i18n_app.test_client() as client:
        res = client.get(url_for("weko_theme.index"))
        assert res.status_code == 200

class Dict2Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
# def index():
# .tox/c1/bin/pytest --cov=weko_theme tests/test_views.py::test_index_community_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-theme/.tox/c1/tmp
def test_index_community_settings(i18n_app, users):
    WekoTheme(i18n_app)
    # テスト用の設定を作成
    db_settings = Dict2Obj(
        title1='DB Title 1',
        title2='DB タイトル 2',
        icon_code='fa fa-handshake-o',
        supplement='Database supplement text'
    )
    # AdminSettings.getをモックする
    with patch("weko_admin.admin.AdminSettings.get", return_value=db_settings):
        # get_languageをモックする
        with patch("weko_theme.views.get_language", return_value='en'):
            with i18n_app.test_client() as client:
                # render_template をモックし、引数をキャプチャする
                mock_render_template = MagicMock(return_value=('<html></html>', 200))
                with patch("weko_theme.views.render_template", mock_render_template):
                    res = client.get(url_for("weko_theme.index"))
                    assert res.status_code == 200
                    # モックされた render_template の引数を検証
                    kwargs = mock_render_template.call_args[1]
                    assert kwargs['lists']['title'] == db_settings.title1
                    assert kwargs['lists']['icon_code'] == db_settings.icon_code
                    assert kwargs['lists']['supplement'] == db_settings.supplement
            # get_languageをモックする
        with patch("weko_theme.views.get_language", return_value='ja'):
            with i18n_app.test_client() as client:
                # render_template をモックし、引数をキャプチャする
                mock_render_template = MagicMock(return_value=('<html></html>', 200))
                with patch("weko_theme.views.render_template", mock_render_template):
                    res = client.get(url_for("weko_theme.index"))
                    assert res.status_code == 200
                    # モックされた render_template の引数を検証
                    kwargs = mock_render_template.call_args[1]
                    assert kwargs['lists']['title'] == db_settings.title2
                    assert kwargs['lists']['icon_code'] == db_settings.icon_code
                    assert kwargs['lists']['supplement'] == db_settings.supplement
    # テスト用の設定を作成
    db_settings = Dict2Obj(
        title1='DB Title 1',
        title2='',
        icon_code='fa fa-handshake-o',
        supplement='Database supplement text'
    )
    # AdminSettings.getをモックする
    with patch("weko_admin.admin.AdminSettings.get", return_value=db_settings):
        # get_languageをモックする
        with patch("weko_theme.views.get_language", return_value='ja'):
            with i18n_app.test_client() as client:
                # render_template をモックし、引数をキャプチャする
                mock_render_template = MagicMock(return_value=('<html></html>', 200))
                with patch("weko_theme.views.render_template", mock_render_template):
                    res = client.get(url_for("weko_theme.index"))
                    assert res.status_code == 200
                    # モックされた render_template の引数を検証
                    kwargs = mock_render_template.call_args[1]
                    assert kwargs['lists']['title'] == db_settings.title1
                    assert kwargs['lists']['icon_code'] == db_settings.icon_code
                    assert kwargs['lists']['supplement'] == db_settings.supplement
    # AdminSettings.getをモックする
    with patch("weko_admin.admin.AdminSettings.get", return_value=None):
        # get_languageを英語でモックする
        with patch("weko_theme.views.get_language", return_value='en'):
            with i18n_app.test_client() as client:
                # render_template をモックし、引数をキャプチャする
                mock_render_template = MagicMock(return_value=('<html></html>', 200))
                with patch("weko_theme.views.render_template", mock_render_template):
                    res = client.get(url_for("weko_theme.index"))
                    assert res.status_code == 200
                    # モックされた render_template の引数を検証
                    kwargs = mock_render_template.call_args[1]
                    assert kwargs["lists"]["title"] == 'Communities'  # 英語ならconfigから英語のデフォルト値を使用
                    assert kwargs["lists"]["icon_code"] == 'fa fa-group'
                    assert kwargs["lists"]["supplement"] == 'created and curated by WEKO3 users'
        # get_languageを日本語でモックする
        with patch("weko_theme.views.get_language", return_value='ja'):
            with i18n_app.test_client() as client:
                # render_template をモックし、引数をキャプチャする
                mock_render_template = MagicMock(return_value=('<html></html>', 200))
                with patch("weko_theme.views.render_template", mock_render_template):
                    res = client.get(url_for("weko_theme.index"))
                    assert res.status_code == 200
                    # モックされた render_template の引数を検証
                    kwargs = mock_render_template.call_args[1]
                    assert kwargs["lists"]["title"] == 'コミュニティ'  # 英語ならconfigから英語のデフォルト値を使用
                    assert kwargs["lists"]["icon_code"] == 'fa fa-group'
                    assert kwargs["lists"]["supplement"] == 'created and curated by WEKO3 users'
                    
# def edit():
# .tox/c1/bin/pytest --cov=weko_theme tests/test_views.py::test_edit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-theme/.tox/c1/tmp
def test_edit(i18n_app, users):
    site_info = MagicMock()
    site_info.favicon = "favicon,favicon"
    site_info.ogp_image = "ogp_image"
    WekoTheme(i18n_app)

    with i18n_app.test_client() as client:
        with patch('weko_theme.views.SiteInfo.get', return_value=site_info):
            # Exception coverage
            try:
                client.get(url_for("weko_theme.edit"))
            except:
                pass

        res = client.get(url_for("weko_theme.edit"))
        assert res.status_code == 200


# def get_default_search_setting():
def test_get_default_search_setting(i18n_app, users):
    with i18n_app.test_client() as client:
        WekoTheme(i18n_app)
        res = client.get(url_for("weko_theme.get_default_search_setting"))
        assert res.status_code == 200


# def get_init_display_setting(settings):
def test_get_init_display_setting(i18n_app, users):
    with i18n_app.test_client() as client:
        WekoTheme(i18n_app)
        get_init_display_setting({})