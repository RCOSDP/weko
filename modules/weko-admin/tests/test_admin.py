
import os
from os.path import dirname, join
from flask import url_for,current_app,make_response
from flask_admin import Admin
from mock import patch
from mock import MagicMock, patch
import json
from io import BytesIO
import pytest
from datetime import datetime
from wtforms.validators import ValidationError
from werkzeug.datastructures import ImmutableMultiDict

import pytest
from requests import Response

from invenio_accounts.testutils import login_user_via_session
from .test_views import assert_role

from invenio_accounts.testutils import login_user_via_session, create_test_user
from invenio_access.models import ActionUsers
from invenio_communities.models import Community

from weko_index_tree.models import IndexStyle,Index
from weko_admin.admin import StyleSettingView,LogAnalysisSettings,ItemExportSettingsView,IdentifierSettingView,\
    identifier_adminview,facet_search_adminview,FacetSearchSettingView
from weko_admin.models import AdminSettings,StatisticsEmail,LogAnalysisRestrictedCrawlerList,\
                                RankingSettings,SearchManagement, Identifier,FacetSearchSetting

# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

#class StyleSettingView(BaseView):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestStyleSettingView:
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView::test_index -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_index(self,client,users,mocker):
        login_user_via_session(client,email=users[0]["email"])

        url = url_for("stylesetting.index")

        # get
        scss_dir = join(current_app.instance_path, current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'])
        os.makedirs(scss_dir, exist_ok=True)
        scss_file = join(scss_dir, '_variables.scss')
        with open(scss_file, "w") as f:
            f.write("$body-bg: #ffff;\n$panel-bg: #ffff;\n$footer-default-bg: #0d5f89;\n$navbar-default-bg: #0d5f89;\n$panel-default-border: #dddddd;\n$input-bg-transparent: rgba(255, 255, 255, 0);")
        mock_render = mocker.patch("weko_admin.admin.StyleSettingView.render",return_value=make_response())
        res = client.get(url)
        mock_render.assert_called_with(
            "weko_admin/admin/block_style.html",
            body_bg="#ffff"
        )

        # post
        class MockPermission:
            def __init__(self,flg):
                self.flg = flg
            def can(self):
                return self.flg
        with patch("weko_admin.admin.admin_permission_factory",return_value=MockPermission(False)):
            mock_render = mocker.patch("weko_admin.admin.StyleSettingView.render",return_value=make_response())
            mock_flash = mocker.patch("weko_admin.admin.flash")
            res = client.post(url)
            mock_render.assert_called_with(
                "weko_admin/admin/block_style.html",
                body_bg="#ffff"
            )
            mock_flash.assert_called_with("Denied access")
        with patch("weko_admin.admin.admin_permission_factory",return_value=MockPermission(True)):
            data={"body-bg":"#0d5f89"}
            test = ["$body-bg: #0d5f89;\n", "$panel-bg: #ffff;\n", "$footer-default-bg: #0d5f89;\n", "$navbar-default-bg: #0d5f89;\n", "$panel-default-border: #dddddd;\n", "$input-bg-transparent: rgba(255, 255, 255, 0);"]
            mock_render = mocker.patch("weko_admin.admin.StyleSettingView.render",return_value=make_response())
            mock_flash = mocker.patch("weko_admin.admin.flash")
            res = client.post(url,data=data)
            mock_render.assert_called_with(
                "weko_admin/admin/block_style.html",
                body_bg="#0d5f89"
            )
            mock_flash.assert_called_with('Successfully update color.',category="success")
            with open(scss_file, "r") as f:
                new_scss = f.readlines()
                assert new_scss == test
        
        # raise BaseException
        mock_render = mocker.patch("weko_admin.admin.StyleSettingView.render",return_value=make_response())
        current_app.config.update(
            WEKO_THEME_INSTANCE_DATA_DIR="not_exist_dir"
        )
        res = client.get(url)
        assert res.status_code == 200
        mock_render.assert_called_with(
            "weko_admin/admin/block_style.html",
            body_bg="#fff"
        )
        
#    def upload_editor(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView::test_upload_editor -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    @pytest.mark.parametrize("f_or_h,data,result,status_code,res_data",[
        ("footer",{"temp":"footer","content":"<div>this is new content</div>","isEmpty":"True"},"<div>this is contents</div>",200,{"code":0, "msg": "success"}),
        ("footer",{"temp":"footer","content":"<div>this is new content</div>","isEmpty":"False"},"<div>this is new content</div>",200,{"code":0, "msg": "success"}),
        ("header",{"temp":"header","content":"<div>this is new content</div>","isEmpty":"True"},"<div>this is contents</div>",200,{"code":0, "msg": "success"}),
        ("header",{"temp":"header","content":"<div>this is new content</div>","isEmpty":"False"},"<div>this is new content</div>",200,{"code":0, "msg": "success"}),
        ("error",{"temp":"others","content":"<div>this is new content</div>","isEmpty":"True"},None,500,None),
        ("error",{"temp":"header"},None,500,None)
    ])
    def test_upload_editor(self, client, users,f_or_h,data,result,status_code,res_data):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("stylesetting.upload_editor")
        from weko_theme.views import blueprint as theme_bp
        path_to_instance = join("../../../../../",current_app.instance_path)
        
        current_app.config.update(
            THEME_FOOTER_WYSIWYG_TEMPLATE=join(path_to_instance,"footer_wysiwtg_template.html"),
            THEME_HEADER_WYSIWYG_TEMPLATE=join(path_to_instance,"header_wysiwtg_template.html")
        )
        target_file = str()
        if f_or_h == "footer":
            target_file = join(theme_bp.root_path, theme_bp.template_folder, current_app.config["THEME_FOOTER_WYSIWYG_TEMPLATE"])
        elif f_or_h == "header":
            target_file = join(theme_bp.root_path, theme_bp.template_folder, current_app.config["THEME_HEADER_WYSIWYG_TEMPLATE"])
        else:
            pass
        if target_file:
            with open(target_file, "w") as f:
                f.write("<div>this is first contents</div>")
        
        with patch("weko_admin.admin.StyleSettingView.get_contents", side_effect=(["<div>this is contents</div>"])):
            res = client.post(url, json=data)
            assert res.status_code == status_code
            if res_data:
                assert json.loads(res.data) == res_data
                with open(target_file, "r") as f:
                    assert f.read() == result


#    def get_contents(self, f_path):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView::test_get_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_contents(self,client,mocker):
        path = join(current_app.instance_path,dirname(__file__),"data/_variables.scss")
        result = StyleSettingView().get_contents(path)
        test = [
            "$body-bg: #ffff;\n",
            "$panel-bg: #ffff;\n",
            "$footer-default-bg: #0d5f89;\n",
            "$navbar-default-bg: #0d5f89;\n",
            "$panel-default-border: #dddddd;\n",
            "$input-bg-transparent: rgba(255, 255, 255, 0);"
        ]
        assert result == test
        
        # raise Exception
        path = "not_exist_path"
        mock_abort = mocker.patch("weko_admin.admin.abort",return_value=make_response())
        result = StyleSettingView().get_contents(path)
        mock_abort.assert_called_with(500)
        
#    def cmp_files(self, f_path1, f_path2):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView::test_cmp_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_cmp_files(self,app,client,mocker):
        path1=join(current_app.instance_path,dirname(__file__),"data/_variables.scss")
        path2=join(current_app.instance_path,dirname(__file__),"data/actions.json")
        result = StyleSettingView().cmp_files(path1,path2)
        assert result == False
        
        result = StyleSettingView().cmp_files(path1,path1)
        assert result == True
        
        mock_abort = mocker.patch("weko_admin.admin.abort",return_value=make_response())
        path1 = "not_exist_path1"
        path2 = "not_exist_path2"
        result = StyleSettingView().cmp_files(path1,path2)
        mock_abort.assert_called_with(500)
        
            
#class ReportView(BaseView):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestReportView:
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestReportView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_index(self,client,indexes,users,admin_settings,statistic_email_addrs,mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("report.index")
        agg={
            "took": 274,
            "timed_out": False,
            "_shards": {
                "total": 1,
                "successful": 1,
                "skipped": 0,
                "failed": 0
            },
            "hits": {
                "total": 2,
                "max_score": 0.0,
                "hits": [
                ]
            },
            "aggregations": {
                "aggs_public": {
                    "doc_count": 1
                }
            }
        }
        mocker.patch("invenio_stats.utils.get_aggregations",return_value=agg)
        mock_render = mocker.patch("weko_admin.admin.ReportView.render",return_value=make_response())
        test = {
            "total":2,
            "open":1,
            "private":1
        }
        client.get(url)
        args,kwargs = mock_render.call_args
        assert args[0] == "weko_admin/admin/report.html"
        assert kwargs["result"] == test
        assert [email.email_address for email in kwargs["emails"]] == ["test.taro@test.org"] 
        assert kwargs["current_schedule"] == {'frequency': 'daily', 'details': '', 'enabled': False}
        
        with patch("weko_index_tree.api.Indexes.get_public_indexes_list",return_value=[]):
            with patch("invenio_stats.utils.get_aggregations",return_value={}):
                with patch("weko_admin.admin.ReportView.render",side_effect=Exception("test_error")):
                    result = client.get(url)
                    assert result.status_code == 400

#    def get_file_stats_output(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestReportView::test_get_file_stats_output -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_file_stats_output(self,client,users,statistic_email_addrs,mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("report.get_file_stats_output")
        stats_json = {
            "file_download": {"all": [],"all_groups": [],"date": "2022-10","open_access": []},
            "file_preview": {"all": [],"all_groups": [],"date": "2022-10","open_access": []},
            "billing_file_download": {"all": [],"all_groups": [],"date": "2022-10","open_access": []},
            "billing_file_preview": {"all": [],"all_groups": [],"date": "2022-10","open_access": []},
            "detail_view": {
            "all": [
                {
                  "index_names": "人文社会系 (Faculty of Humanities and Social Sciences)",
                  "pid_value": "3",
                  "record_id": "6f8da14f-5a24-4e07-a5cb-04e8ef1c11b3",
                  "record_name": "test_doi",
                  "same_title": "True",
                  "total_all": "2",
                  "total_not_login": "0"
                },
                {
                  "index_names": "コンテンツタイプ (Contents Type)-/-会議発表論文, 人文社会系 (Faculty of Humanities and Social Sciences)",
                  "pid_value": "1",
                  "record_id": "99203669-c376-4f5a-ade3-8139e7785a9d",
                  "record_name": "test full item",
                  "same_title": "True",
                  "total_all": "2",
                  "total_not_login": "1"
                }
            ],
            "date": "2022-10-01-2022-10-31"
            },
            "index_access": {
                "all": [
                  {"index_name": "コンテンツタイプ (Contents Type)-/-会議発表論文","view_count": "2"},
                  {"index_name": "人文社会系 (Faculty of Humanities and Social Sciences)","view_count": "4"}
                ],
                "date": "2022-10",
                "total": "6"
            },
            "file_using_per_user": {
                "all": {},
                "date": "2022-10"
            },
            "top_page_access": {
              "all": {
                "192.168.56.1": {
                  "count": "17",
                  "host": "None",
                  "ip": "192.168.56.1"
                }
              },
              "date": "2022-10"
            },
            "search_count": {
              "all": [],
              "date": "2022-10"
            },
            "user_roles": {
              "all": [
                { "count": "1", "role_name": "Community Administrator" },
                {"count": "1","role_name": "Repository Administrator"},
                  {"count": "1","role_name": "Contributor"},
                  {"count": "1","role_name": "System Administrator"},
                  {"count": "4","role_name": "Registered Users"}
              ]
            },
            "site_access": {
              "date": "2022-10",
              "institution_name": [],
              "other": [
                {
                  "file_download": "0",
                  "file_preview": "0",
                  "record_view": "4",
                  "search": "0",
                  "top_view": "17"
                }
              ],
              "site_license": [
                {
                  "file_download": "0",
                  "file_preview": "0",
                  "record_view": "0",
                  "search": "0",
                  "top_view": "0"
                }
              ]
            }
        }
        data = {
            "report":json.dumps(stats_json),"year":"2022","month":"10","send_email":"False"
        }
        mocker.patch("weko_admin.admin.package_reports",return_value=BytesIO())
        result = client.post(url,data=data)
        assert result.headers["Content-Type"] == "application/x-zip-compressed"
        assert result.headers["Content-Disposition"] == "attachment; filename=logReport_2022-10.zip"
        assert result.data==b""
        
        # send_email is "True"
        data = {
            "report":json.dumps(stats_json),"year":"2022","month":"10","send_email":"True"
        }
        ## send_mail is true
        mock_send = mocker.patch("weko_admin.admin.send_mail",return_value=True)
        mock_flash = mocker.patch("weko_admin.admin.flash")
        mock_redirect = mocker.patch("weko_admin.admin.redirect",return_value=make_response())
        result = client.post(url,data=data)
        mock_flash.assert_called_with(True,"error")
        mock_redirect.assert_called_with("/admin/report/")
        args,kwargs = mock_send.call_args
        assert args[0] == "2022-10 Log report."
        assert args[1] == ["test.taro@test.org"]
        
        ## send_mail is false
        mock_send = mocker.patch("weko_admin.admin.send_mail",return_value=False)
        mock_flash = mocker.patch("weko_admin.admin.flash")
        mock_redirect = mocker.patch("weko_admin.admin.redirect",return_value=make_response())
        result = client.post(url,data=data)
        mock_flash.assert_called_with('Successfully sent the reports to the recepients.')
        mock_redirect.assert_called_with("/admin/report/")
        args,kwargs = mock_send.call_args
        assert args[0] == "2022-10 Log report."
        assert args[1] == ["test.taro@test.org"]
        
        # raise Exception
        mocker.patch("weko_admin.admin.package_reports",side_effect=Exception("test_error"))
        mock_flash = mocker.patch("weko_admin.admin.flash")
        mock_redirect = mocker.patch("weko_admin.admin.redirect",return_value=make_response())
        result = client.post(url,data=data)
        mock_flash.assert_called_with('Unexpected error occurred.',"error")
        mock_redirect.assert_called_with("/admin/report/")
        
        
#    def get_user_report_data(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestReportView::test_get_user_report_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_user_report_data(self,client,users,mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("report.get_user_report_data")
        user_report = {
            "all":[
                {"role_name":"System Administrator","count":1},
                {"role_name":"Repository Administrator","count":2},
                {"role_name":"Contributor","count":1},
                {"role_name":"Community Administrator","count":1},
                {"role_name":"General","count":1},
                {"role_name":"Original Role","count":2},
                {"role_name":"Student","count":1},
                {"role_name":"Registered Users","count":9}
            ],
        }
        mocker.patch("weko_admin.admin.get_user_report",return_value=user_report)
        result = client.get(url)
        assert json.loads(result.data) == user_report

#    def set_email_schedule(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestReportView::test_set_email_schedule -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_set_email_schedule(self,client,users,mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("report.set_email_schedule")
        mocker.patch("weko_admin.admin.redirect",return_value=make_response())
        
        # frequency is daily
        data = {
            "frequency":"daily","monthly_details":"1","weekly_details":"0","dis_enable_schedule":"False"
        }
        test = {"frequency":"daily","details":"","enabled":False}
        result = client.post(url,data=data)
        assert result.status_code == 200
        assert AdminSettings.query.filter_by(name="report_email_schedule_settings").one_or_none().settings == test

        # frequency is weekly
        data = {
            "frequency":"weekly","monthly_details":"1","weekly_details":"0","dis_enable_schedule":"True"
        }
        test = {"frequency":"weekly","details":"0","enabled":True}
        result = client.post(url,data=data)
        assert result.status_code == 200
        assert AdminSettings.query.filter_by(name="report_email_schedule_settings").one_or_none().settings == test
        
        # frequency is monthly
        data = {
            "frequency":"monthly","monthly_details":"1","weekly_details":"0","dis_enable_schedule":"True"
        }
        test = {"frequency":"monthly","details":"1","enabled":True}
        result = client.post(url,data=data)
        assert result.status_code == 200
        assert AdminSettings.query.filter_by(name="report_email_schedule_settings").one_or_none().settings == test
        
        # raise Exception
        with patch("weko_admin.admin.AdminSettings.update",side_effect=Exception("test_error")):
            mock_flash = mocker.patch("weko_admin.admin.flash")
            result = client.post(url,data=data)
            mock_flash.assert_called_with('Could Not Save Changes.',"error")


#    def get_email_address(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestReportView::test_get_email_address -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_email_address(self,client,users,statistic_email_addrs,mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("report.get_email_address")
        data = {"inputEmail":["test.smith@test.org","","not_correct_email_address"]}
        
        mocker.patch("weko_admin.admin.redirect",return_value=make_response())
        mock_flash = mocker.patch("weko_admin.admin.flash")
        result = client.post(url,data=data)
        assert result.status_code == 200
        email_list = [row.email_address for row in StatisticsEmail.query.all()]
        assert "test.smith@test.org" in email_list
        assert "test.taro@test.org" not in email_list
        mock_flash.assert_called_with("Please check email input fields.",category="error")


#class FeedbackMailView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_FeedbackMailView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_FeedbackMailView_index(client,users,mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("feedbackmail.index")
    # get
    mock_render = mocker.patch("weko_admin.admin.FeedbackMailView.render",return_value=make_response())
    result = client.get(url)
    assert result.status_code == 200
    mock_render.assert_called_with("weko_admin/admin/feedback_mail.html")
    
    # post
    mock_render = mocker.patch("weko_admin.admin.FeedbackMailView.render",return_value=make_response())
    result = client.post(url)
    assert result.status_code == 200
    mock_render.assert_called_with("weko_admin/admin/feedback_mail.html")

#class LanguageSettingView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_LanguageSettingView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_LanguageSettingView_index(client,users,mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("language.index")
    # get
    mock_render = mocker.patch("weko_admin.admin.LanguageSettingView.render",return_value=make_response())
    result = client.get(url)
    assert result.status_code == 200
    mock_render.assert_called_with("weko_admin/admin/lang_settings.html")
    
    # post
    mock_render = mocker.patch("weko_admin.admin.LanguageSettingView.render",return_value=make_response())
    result = client.post(url)
    assert result.status_code == 200
    mock_render.assert_called_with("weko_admin/admin/lang_settings.html")


#class WebApiAccount(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_LanguageSettingView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_WebApiAccount_index(client,users,mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("webapiaccount.index")
    # get
    mock_render = mocker.patch("weko_admin.admin.WebApiAccount.render",return_value=make_response())
    result = client.get(url)
    assert result.status_code == 200
    mock_render.assert_called_with("weko_admin/admin/web_api_account.html")
    
    # post
    mock_render = mocker.patch("weko_admin.admin.WebApiAccount.render",return_value=make_response())
    result = client.post(url)
    assert result.status_code == 200
    mock_render.assert_called_with("weko_admin/admin/web_api_account.html")


#class StatsSettingsView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_StatsSettingsView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_StatsSettingsView_index(client,users,admin_settings,mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("statssettings.index")
    # get
    mock_render = mocker.patch("weko_admin.admin.StatsSettingsView.render",return_value=make_response())
    result = client.get(url)
    assert result.status_code == 200
    mock_render.assert_called_with("weko_admin/admin/stats_settings.html",display_stats=False)
    ## not exist admin_setting
    with patch("weko_admin.admin.AdminSettings.get",return_value=None):
        mock_render = mocker.patch("weko_admin.admin.StatsSettingsView.render",return_value=make_response())
        result = client.get(url)
        assert result.status_code == 200
        mock_render.assert_called_with("weko_admin/admin/stats_settings.html",display_stats=True)

    # post
    mock_redirect = mocker.patch("weko_admin.admin.redirect",return_value=make_response())
    data = {"record_stats_radio":"True"}
    result = client.post(url,data=data)
    assert result.status_code == 200
    assert AdminSettings.query.filter_by(name="display_stats_settings").one().settings == {"display_stats":True}
    mock_redirect.assert_called_with(url_for("statssettings.index"))

#class LogAnalysisSettings(BaseView):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestLogAnalysisSettings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestLogAnalysisSettings:
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestLogAnalysisSettings::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_index(self,db,client,users,log_crawler_list,restricted_ip_addr,mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("loganalysissetting.index")
        
        mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
        result = client.get(url)
        assert result.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "weko_admin/admin/log_analysis_settings.html"
        assert kwargs["restricted_ip_addresses"][0].ip_address == "123.456.789.012"
        assert kwargs["shared_crawlers"][0].list_url == "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_ip_blacklist.txt"
        
        
        # not shared_crawlers
        LogAnalysisRestrictedCrawlerList.query.delete()
        db.session.commit()
        mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
        result = client.get(url)
        assert result.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "weko_admin/admin/log_analysis_settings.html"
        assert kwargs["restricted_ip_addresses"][0].ip_address == "123.456.789.012"
        assert [crawler.list_url for crawler in kwargs["shared_crawlers"]] == current_app.config["WEKO_ADMIN_DEFAULT_CRAWLER_LISTS"]

        
        # raise Exception
        with patch("weko_admin.admin.LogAnalysisRestrictedIpAddress.get_all",side_effect=Exception("test_error")):
            mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
            mock_flash = mocker.patch("weko_admin.admin.flash")
            result = client.get(url)
            assert result.status_code == 200
            mock_flash.assert_called_with("Could not get restricted data.","error")
            args, kwargs = mock_render.call_args
            assert args[0] == "weko_admin/admin/log_analysis_settings.html"
            assert kwargs["restricted_ip_addresses"] == []
            assert kwargs["shared_crawlers"] == []
        
        # post
        data = {
            "ip_address_0_id":"1",
            "address_list_0":["987","654","321","098"],
            "shared_crawler_0_id":"1","shared_crawler_0_check":"on","shared_crawler_0":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test2_Crawler-List_ip_blacklist.txt",
            "shared_crawler_1_id":"2","shared_crawler_1_check":"on","shared_crawler_1":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test2_Crawler-List_useragent.txt",
        }
        mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
        result = client.post(url,data=data)
        assert result.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "weko_admin/admin/log_analysis_settings.html"
        assert kwargs["restricted_ip_addresses"][0].ip_address == "987.654.321.098"
        assert [crawler.list_url for crawler in kwargs["shared_crawlers"]] == ["https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test2_Crawler-List_ip_blacklist.txt","https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test2_Crawler-List_useragent.txt"]
        
        # raise Exception
        data = {
            "ip_address_0_id":"1",
            "address_list_0":["123","456","789","012"],
            "shared_crawler_0_id":"1","shared_crawler_0_check":"on","shared_crawler_0":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test2_Crawler-List_ip_blacklist.txt",
            "shared_crawler_1_id":"2","shared_crawler_1_check":"on","shared_crawler_1":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test2_Crawler-List_useragent.txt",
        }
        with patch("weko_admin.admin.LogAnalysisRestrictedIpAddress.update_table",side_effect=Exception("test_error")):
            mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
            mock_flash = mocker.patch("weko_admin.admin.flash")
            result = client.post(url,data=data)
            assert result.status_code == 200
            args, kwargs = mock_render.call_args
            assert args[0] == "weko_admin/admin/log_analysis_settings.html"
            assert kwargs["restricted_ip_addresses"][0].ip_address == "987.654.321.098"
            assert [crawler.list_url for crawler in kwargs["shared_crawlers"]] == ["https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test2_Crawler-List_ip_blacklist.txt","https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test2_Crawler-List_useragent.txt"]
            mock_flash.assert_called_with("Could not save data.","error")

        
#    def parse_form_data(self, raw_data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestLogAnalysisSettings::test_parse_form_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_parse_form_data(self):
        raw_data = ImmutableMultiDict([
            ('ip_address_0_id', '1'), ('address_list_0', '123'),
            ('address_list_0', '456'), ('address_list_0', '789'), 
            ('address_list_0', '012'), ('address_list_1', ''),
            ('address_list_1', ''), ('address_list_1', ''),
            ('address_list_1', ''), ('shared_crawler_0_id', '1'), 
            ('shared_crawler_0_check', 'on'), 
            ('shared_crawler_0', 'https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_ip_blacklist.txt'), 
            ('shared_crawler_1_id', '2'), 
            ('shared_crawler_1_check', 'on'), 
            ('shared_crawler_1', 'https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_useragent.txt')])
        test_crawler=[
            {"id":"1","is_active":True,"list_url":'https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_ip_blacklist.txt'},
            {"id":"2","is_active":True,"list_url":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_useragent.txt"}
        ]
        test_addr = ["123.456.789.012"]
        crawler_list, addr_list = LogAnalysisSettings().parse_form_data(raw_data)
        assert crawler_list == test_crawler
        assert addr_list == test_addr

#class RankingSettingsView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_RankingSettingsView_indes -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_RankingSettingsView_indes(client,users,ranking_settings,mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("rankingsettings.index")

    # get, ranking_setting is exist
    mock_render = mocker.patch("weko_admin.admin.RankingSettingsView.render",return_value=make_response())
    result = client.get(url)
    assert result.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/ranking_settings.html"
    assert kwargs["is_show"] == True
    assert kwargs["new_item_period"] == 14
    assert kwargs["statistical_period"] == 365
    assert kwargs["display_rank"] == 10
    assert kwargs["rankings"] == {"new_items":True,"most_reviewed_items":True,"most_downloaded_items":True,"most_searched_keywords":True,"created_most_items_user":True}
    
    # get, ranking_setting is not exist
    with patch("weko_admin.admin.RankingSettings.get",return_value=None):
        mock_render = mocker.patch("weko_admin.admin.RankingSettingsView.render",return_value=make_response())
        result = client.get(url)
        assert result.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "weko_admin/admin/ranking_settings.html"
        assert kwargs["is_show"] == False
        assert kwargs["new_item_period"] == 14
        assert kwargs["statistical_period"] == 365
        assert kwargs["display_rank"] == 10
        assert kwargs["rankings"] == {'most_reviewed_items': False,'most_downloaded_items': False,'created_most_items_user': False,'most_searched_keywords': False,'new_items': False}
    
    # post, submit is not ranking_setting
    data = {
        "is_show":"True","new_item_period":"20","statistical_period":"730","display_rank":"15","most_reviewed_items":"on","most_downloaded_items":"on","created_most_items_user":"on","most_searched_keywords":"off","new_items":"on","submit":"not_save_ranking_settings"
    }
    mock_render = mocker.patch("weko_admin.admin.RankingSettingsView.render",return_value=make_response())
    result = client.post(url,data=data)
    assert result.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/ranking_settings.html"
    assert kwargs["is_show"] == True
    assert kwargs["new_item_period"] == 14
    assert kwargs["statistical_period"] == 365
    assert kwargs["display_rank"] == 10
    assert kwargs["rankings"] == {"new_items":True,"most_reviewed_items":True,"most_downloaded_items":True,"most_searched_keywords":True,"created_most_items_user":True}

    
    # post
    data = {
        "is_show":"True","new_item_period":"20","statistical_period":"730","display_rank":"15","most_reviewed_items":"on","most_downloaded_items":"on","created_most_items_user":"on","new_items":"on","submit":"save_ranking_settings"
    }
    mock_redirect=mocker.patch("weko_admin.admin.redirect",return_value=make_response())
    mock_flash = mocker.patch("weko_admin.admin.flash")
    result = client.post(url,data=data)
    assert result.status_code==200
    mock_flash.assert_called_with("Successfully Changed Settings.")
    mock_redirect.assert_called_with(url_for('rankingsettings.index'))
    ranking_setting = RankingSettings.query.filter_by(id=0).one()
    assert ranking_setting.new_item_period == 20
    assert ranking_setting.statistical_period == 730
    assert ranking_setting.display_rank == 15
    assert ranking_setting.rankings == {"new_items":True,"most_reviewed_items":True,"most_downloaded_items":True,"most_searched_keywords":False,"created_most_items_user":True}
    
    # not new_item_period<1 or new_item_period > 30
    data = {
        "is_show":"True","new_item_period":"100","statistical_period":"730","display_rank":"15","most_reviewed_items":"on","most_downloaded_items":"on","created_most_items_user":"on","new_items":"on","submit":"save_ranking_settings"
    }
    mock_redirect=mocker.patch("weko_admin.admin.redirect",return_value=make_response())
    mock_flash = mocker.patch("weko_admin.admin.flash")
    result = client.post(url,data=data)
    assert result.status_code==200
    mock_flash.assert_called_with("Failurely Changed Settings.","error")
    mock_redirect.assert_called_with(url_for('rankingsettings.index'))

    # not new_statistical_period<1 or new_statistical_period > 3650
    data = {
        "is_show":"True","new_item_period":"10","statistical_period":"7300","display_rank":"15","most_reviewed_items":"on","most_downloaded_items":"on","created_most_items_user":"on","new_items":"on","submit":"save_ranking_settings"
    }
    mock_redirect=mocker.patch("weko_admin.admin.redirect",return_value=make_response())
    mock_flash = mocker.patch("weko_admin.admin.flash")
    result = client.post(url,data=data)
    assert result.status_code==200
    mock_flash.assert_called_with("Failurely Changed Settings.","error")
    mock_redirect.assert_called_with(url_for('rankingsettings.index'))

    # not new_display_rank<1 or new_display_rank > 100
    data = {
        "is_show":"True","new_item_period":"10","statistical_period":"730","display_rank":"150","most_reviewed_items":"on","most_downloaded_items":"on","created_most_items_user":"on","new_items":"on","submit":"save_ranking_settings"
    }
    mock_redirect=mocker.patch("weko_admin.admin.redirect",return_value=make_response())
    mock_flash = mocker.patch("weko_admin.admin.flash")
    result = client.post(url,data=data)
    assert result.status_code==200
    mock_flash.assert_called_with("Failurely Changed Settings.","error")
    mock_redirect.assert_called_with(url_for('rankingsettings.index'))

#class SearchSettingsView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_SearchSettingsView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_SearchSettingsView_index(client,db,users,item_type,admin_settings,index_style,search_management,mocker):

    login_user_via_session(client,email=users[0]["email"])
    url = url_for("searchsettings.index")
    # get
    mock_render = mocker.patch("weko_admin.admin.SearchSettingsView.render",return_value=make_response())
    result = client.get(url)
    assert result.status_code == 200
    test = {"init_disp_setting":{"init_disp_index":"","init_disp_screen_setting":"0","init_disp_index_disp_method":"0"},
            "search_author_flg":"name",
            "index_tree_style":{"width_options":["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],"width":"3","height":""}}
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/search_management_settings.html"
    assert kwargs["widths"] == ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
    assert kwargs["setting_data"] == json.dumps(test)
    assert [item.name for item in kwargs["lists"]] == ['テストアイテムタイプ1','テストアイテムタイプ2']
    # raise Exception
    with patch("weko_admin.admin.ItemTypes.get_latest",side_effect=BaseException("test_error")):
        result = client.get(url)
        assert result.status_code == 500
    # post
    SearchManagement.query.delete()
    IndexStyle.query.delete()
    db.session.commit()
    # search_author_flg update, index_style create, search_management create
    data = {
        "search_author_flg":"age",
        "index_tree_style":{"width":"5","height":"10"},
        "dlt_dis_num_selected":10,
        "dlt_index_sort_selected":"controlnumber_asc",
        "sort_options":{},
        "detail_condition":{},
        "display_control":{"display_community":{"id":"display_community","status":True},"display_index_tree":{"id":"display_index_tree","status":True},"display_facet_search":{"id":"display_facet_search","status":True}},
        "init_disp_setting":{"init_disp_index":"","init_disp_screen_setting":"0","init_disp_index_disp_method":"0"}
    }
    res = client.post(url,json=data)
    assert res.status_code == 201
    assert json.loads(res.data) == {"status": 201, "message": "Search setting was successfully updated."}
    assert SearchManagement.get().default_dis_num == 10
    assert IndexStyle.get("weko").width == "5"
    assert IndexStyle.get("weko").height == "10"
    # index_style update
    data = {
        "search_author_flg":"age",
        "index_tree_style":{"width":"10","height":"20"},
        "dlt_dis_num_selected":10,
        "dlt_index_sort_selected":"controlnumber_asc",
        "sort_options":{},
        "detail_condition":{},
        "display_control":{"display_community":{"id":"display_community","status":True},"display_index_tree":{"id":"display_index_tree","status":True},"display_facet_search":{"id":"display_facet_search","status":True}},
        "init_disp_setting":{"init_disp_index":"","init_disp_screen_setting":"0","init_disp_index_disp_method":"0"}
    }
    res = client.post(url,json=data)
    assert res.status_code == 201
    assert json.loads(res.data) == {"status": 201, "message": "Search setting was successfully updated."}
    assert SearchManagement.get().default_dis_num == 10
    assert IndexStyle.get("weko").width == "10"
    assert IndexStyle.get("weko").height == "20"
    # not search_author_flg update, not index_style update, search_management update
    data = {
        "dlt_dis_num_selected":20,
        "dlt_index_sort_selected":"controlnumber_asc",
        "sort_options":{},
        "detail_condition":{},
        "display_control":{"display_community":{"id":"display_community","status":True},"display_index_tree":{"id":"display_index_tree","status":True},"display_facet_search":{"id":"display_facet_search","status":True}},
        "init_disp_setting":{"init_disp_index":"","init_disp_screen_setting":"0","init_disp_index_disp_method":"0"}
    }
    res = client.post(url,json=data)
    assert res.status_code == 201
    assert json.loads(res.data) == {"status": 201, "message": "Search setting was successfully updated."}
    assert SearchManagement.get().default_dis_num == 20
    assert IndexStyle.get("weko").width == "10"
    assert IndexStyle.get("weko").height == "20"
    
    # not exist ITEM_SEARCH_FLG in app.config
    items_display_settings = AdminSettings.query.filter_by(id=1).one()
    items_display_settings.settings = {"items_display_email": False, "item_display_open_date": False}
    db.session.merge(items_display_settings)
    db.session.commit()
    current_app.config.pop("ITEM_SEARCH_FLG")
    # raise Exception
    data = {"search_author_flg":"age"}
    with patch("weko_admin.admin.SearchManagement.create",side_effect=BaseException("test_error")):
        res = client.post(url,json=data)
        assert res.status_code == 500
        assert json.loads(res.data) == {"status": 500, "message": "Failed to update search setting."}
    
#class SiteLicenseSettingsView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_SiteLicenseSettingsView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_SiteLicenseSettingsView_index(client,users,item_type,site_license,mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("sitelicensesettings.index")
    response_json = {
        "site_license":[
            {"addresses":[{"finish_ip_address":["987","654","321","098"],"start_ip_address":["123","456","789","012"]}],
             "domain_name":"test_domain",
             "mail_address":"test@mail.com",
             "organization_name":"test data",
             "receive_mail_flag":"T"}
        ],
        "item_type":{"deny":[{"id":"2","name":"テストアイテムタイプ2"}],"allow":[{"id":"1","name":"テストアイテムタイプ1"}]}
    }
    mocker.patch("weko_admin.admin.get_response_json",return_value=response_json)
    mock_render = mocker.patch("weko_admin.admin.SiteLicenseSettingsView.render",return_value=make_response())
    result = client.get(url)
    assert result.status_code == 200
    mock_render.assert_called_with(
        "weko_admin/admin/site_license_settings.html",
        result=json.dumps(response_json)
    )
    
    # raise Exception
    with patch("weko_admin.admin.SiteLicense.get_records",side_effect=BaseException):
        result = client.get(url)
        assert result.status_code == 500
    
    data = {
        "site_license": [{
            "organization_name": "test_organization",
            "mail_address": "test.taro@test.org",
            "domain_name": "test_domain",
            "receive_mail_flag": "F",
            "addresses": [{
                "start_ip_address": ["1","2","3","4"],
                "finish_ip_address": ["5","6","7","8"]
            }]
        }],
        "item_type": {
            "deny": [
                {"id": "31003","name": "利用報告-Data Usage Report"}
            ],
            "allow": [
                {"id": "1","name": "Thesis"}
            ]
        }
    }
    res = client.post(url,json=data)
    assert res.status_code == 201
    assert json.loads(res.data) == {"status": 201, "message": 'Site license was successfully updated.'}
    
    # not exist site_license
    data = {
        "item_type": {
            "deny": [
                {"id": "31003","name": "利用報告-Data Usage Report"}
            ],
            "allow": [
                {"id": "1","name": "Thesis"}
            ]
        }
    }
    res = client.post(url,json=data)
    assert res.status_code == 201
    assert json.loads(res.data) == {"status": 201, "message": 'Site license was successfully updated.'}
    
    # not exist address in license
    data = {
        "site_license": [{}]
    }
    res = client.post(url,json=data)
    assert res.status_code == 500
    assert json.loads(res.data) == {"status": 500, "message": 'Failed to update site license.'}

    # contain "" in address
    data = {
        "site_license": [{
            "addresses": [{
                "start_ip_address": ["","","",""],
                "finish_ip_address": []
            }]
        }]
    }
    res = client.post(url,json=data)
    assert res.status_code == 500
    assert json.loads(res.data) == {"status": 500, "message": 'Failed to update site license.'}

    # raise Exception in ipaddress.ip_address
    data = {
        "site_license": [{
            "addresses": [{
                "start_ip_address": ["a","b"],
                "finish_ip_address": ["a","b"]
            }]
        }]
    }
    res = client.post(url,json=data)
    assert res.status_code == 500
    assert json.loads(res.data) == {"status": 500, "message": 'Failed to update site license.'}



#class SiteLicenseSendMailSettingsView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_SiteLicenseSendMailSettingsView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_SiteLicenseSendMailSettingsView_index(client,users,admin_settings,site_license,mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("sitelicensesendmail.index")

    # get
    mock_render = mocker.patch("weko_admin.admin.SiteLicenseSendMailSettingsView.render",return_value = make_response())
    res = client.get(url)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/site_license_send_mail_settings.html"
    assert kwargs["auto_send"] == False
    assert kwargs["sitelicenses"][0].organization_name == "test data"
    
    # post
    data = {
        "auto_send_flag": True,
        "checked_list": {
            "test data": "F",
            "other data": "T"
        }
    }
    mock_render = mocker.patch("weko_admin.admin.SiteLicenseSendMailSettingsView.render",return_value = make_response())
    res = client.post(url,json=data)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/site_license_send_mail_settings.html"
    assert kwargs["auto_send"] == True
    assert kwargs["sitelicenses"][0].receive_mail_flag == "F"
    
    
#class FilePreviewSettingsView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_FilePreviewSettingsView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_FilePreviewSettingsView_index(client, db, users, admin_settings, mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("filepreview.index")
    # get
    mock_render = mocker.patch("weko_admin.admin.FilePreviewSettingsView.render", return_value = make_response())
    res = client.get(url)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/file_preview_settings.html"
    assert kwargs["settings"].path == "/tmp/file"
    assert kwargs["settings"].pdf_ttl == 1800
    
    # not exist admin_settings
    AdminSettings.query.filter_by(name="convert_pdf_settings").delete()
    db.session.commit()
    mock_render = mocker.patch("weko_admin.admin.FilePreviewSettingsView.render", return_value = make_response())
    res = client.get(url)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/file_preview_settings.html"
    assert kwargs["settings"].path == "/tmp"
    assert kwargs["settings"].pdf_ttl == 3600
    
    # post
    redirect_url = "/admin/filepreview/"
    # not exist submit in data
    data = {}
    mock_flash = mocker.patch("weko_admin.admin.flash")
    mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
    res = client.post(url,data=data)
    assert res.status_code == 200
    mock_flash.assert_called_with("Failurely Changed Settings.", "error")
    mock_redirect.assert_called_with(redirect_url)
    
    # not exist path in data
    data = {
        "submit": "save_settings",
    }
    mock_flash = mocker.patch("weko_admin.admin.flash")
    mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
    res = client.post(url,data=data)
    assert res.status_code == 200
    mock_flash.assert_called_with("Failurely Changed Settings.", "error")
    mock_redirect.assert_called_with(redirect_url)
    
    with patch("weko_admin.admin.remove_dir_with_file"):
        # not exist old_path
        data = {
            "submit": "save_settings",
            "path": "/tmp",
            "pdf_ttl": 3600
        }
        mock_flash = mocker.patch("weko_admin.admin.flash")
        mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
        res = client.post(url,data=data)
        assert res.status_code == 200
        mock_flash.assert_called_with("Successfully Changed Settings.")
        mock_redirect.assert_called_with(redirect_url)
        settings = AdminSettings.get("convert_pdf_settings")
        assert settings.path == "/tmp"
        assert settings.pdf_ttl == 3600
        
        # new_path = old_path
        data = {
            "submit": "save_settings",
            "path": "/new_tmp",
            "pdf_ttl": 7200
        }
        mock_flash = mocker.patch("weko_admin.admin.flash")
        mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
        res = client.post(url,data=data)
        assert res.status_code == 200
        mock_flash.assert_called_with("Successfully Changed Settings.")
        mock_redirect.assert_called_with(redirect_url)
        settings = AdminSettings.get("convert_pdf_settings")
        assert settings.path == "/new_tmp"
        assert settings.pdf_ttl == 7200

    
#class ItemExportSettingsView(BaseView):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestItemExportSettingsView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestItemExportSettingsView:
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestItemExportSettingsView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_index(self, client, users, admin_settings, mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("itemexportsettings.index")
        current_settings = {"allow_item_exporting": True, "enable_contents_exporting": True}
        mocker.patch("weko_admin.admin.ItemExportSettingsView._get_current_settings", return_value=current_settings)
        mocker.patch("weko_admin.admin.str_to_bool",side_effect=lambda x: x.lower() in ["true", "t"])
        # get
        mock_render = mocker.patch("weko_admin.admin.ItemExportSettingsView.render", return_value=make_response())
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "weko_admin/admin/item_export_settings.html"
        assert kwargs["settings"] == current_settings
        
        # post
        data = {
            "item_export_radio": "False",
            "export_contents_radio": "False",
        }
        mock_flash = mocker.patch("weko_admin.admin.flash")
        mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
        res = client.post(url, data=data)
        assert res.status_code == 200
        mock_flash.assert_called_with("Successfully Changed Settings")
        mock_redirect.assert_called_with("/admin/itemexportsettings/")
        settings = AdminSettings.get("item_export_settings")
        assert settings.allow_item_exporting == False
        assert settings.enable_contents_exporting == False

        
        with patch("weko_admin.admin.AdminSettings.update", side_effect=Exception("test_error")):
            data = {
                "item_export_radio": "True",
                "export_contents_radio": "True",
            }
            mock_flash = mocker.patch("weko_admin.admin.flash")
            mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
            res = client.post(url, data=data)
            assert res.status_code == 200
            mock_flash.assert_called_with("Failed To Change Settings", "error")
            mock_redirect.assert_called_with("/admin/itemexportsettings/")
            settings = AdminSettings.get("item_export_settings")
            assert settings.allow_item_exporting == False
            assert settings.enable_contents_exporting == False

        
#    def _get_current_settings(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestItemExportSettingsView::test_get_current_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_current_settings(self, admin_settings):
        result = ItemExportSettingsView()._get_current_settings()
        assert result.allow_item_exporting == True
        assert result.enable_contents_exporting == True


#class SiteInfoView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_SiteInfoView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_SiteInfoView_index(client, users, mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("site_info.index")
    mock_render = mocker.patch("weko_admin.admin.SiteInfoView.render", return_value=make_response())
    res = client.get(url)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/site_info.html"
    assert kwargs["enable_notify"] == False
    
@pytest.fixture()
def setup_view_identifier(admin_app, admin_db):
    admin = Admin(admin_app)
    identifier_adminview_copy = dict(identifier_adminview)
    identifier_model = identifier_adminview_copy.pop("model")
    identifier_view = identifier_adminview_copy.pop("modelview")
    admin.add_view(identifier_view(identifier_model, admin_db.session,**identifier_adminview_copy))
    
    ds = admin_app.extensions['invenio-accounts'].datastore
    sysadmin = create_test_user(email='sysadmin@test.org')
    sysadmin_role = ds.create_role(name='System Administrator')
    ds.add_role_to_user(sysadmin, sysadmin_role)
    action_users = [
            ActionUsers(action='superuser-access', user=sysadmin),
        ]
    admin_db.session.add_all(action_users)
    test_index = Index(
            index_name="testIndexOne",
            browsing_role="Contributor",
            public_state=True,
            id=11,
        )
    admin_db.session.add(test_index)
    comm = Community.create(
        community_id="test_comm",
        role_id=sysadmin_role.id,
        id_user=sysadmin.id,
        title="Test comm",
        description="this is test comm",
        root_node_id=11,
    )
    admin_db.session.add(comm)
    admin_db.session.commit()
    
    return admin_app, admin_db, admin, sysadmin

#class IdentifierSettingView(ModelView):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestIdentifierSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestIdentifierSettingView:
#    def _validator_halfwidth_input(form, field):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestIdentifierSettingView::test_validator_halfwidth_input -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_validator_halfwidth_input(self, setup_view_identifier, mocker):
        app, db, _, _ = setup_view_identifier
        view = IdentifierSettingView(Identifier, db.session)
        data = dict(
                repository="Root Index",
                jalc_flag=True,
                jalc_crossref_flag=True,
                jalc_datacite_flag=True,
                ndl_jalc_flag=True,
                jalc_doi="",
                jalc_crossref_doi="あいうえお",
                jalc_datacite_doi="abcde",
                ndl_jalc_doi="4567",
                suffix="",
            )
        with app.test_request_context(method="POST",data=data):
            create_form = view.create_form()
            # data is None
            validator = create_form.jalc_doi.validators[0]
            validator(create_form, create_form.jalc_doi)
            
            # data is not None
            # validate failed
            validator = create_form.jalc_crossref_doi.validators[0]
            with pytest.raises(ValidationError) as e:
                validator(create_form, create_form.jalc_crossref_doi)
            assert str(e.value) == "Only allow half with 1-bytes character in input"
            
            # validate pass
            validator = create_form.jalc_datacite_doi.validators[0]
            validator(create_form, create_form.jalc_datacite_doi)


#    def validate_form(self, form):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestIdentifierSettingView::test_validate_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_validate_form(self, setup_view_identifier):
        app, db, _, _ = setup_view_identifier
        view = IdentifierSettingView(Identifier, db.session)
        iden = Identifier(
            repository="Root Index",
            jalc_flag=True,
            jalc_crossref_flag=True,
            jalc_datacite_flag=True,
            ndl_jalc_flag=True,
            jalc_doi="1234",
            jalc_crossref_doi="2345",
            jalc_datacite_doi="3456",
            ndl_jalc_doi="4567",
            suffix="test_suffix",
            created_userId="1",
            created_date=datetime(2022,12,1,11,22,33,4444),
            updated_userId="1",
            updated_date=datetime(2022,12,10,11,22,33,4444),
        )
        db.session.add(iden)
        db.session.commit()
        
        
        data = dict(
                repository="test_comm",
                jalc_flag="y",
                jalc_crossref_flag="y",
                jalc_datacite_flag="y",
                ndl_jalc_flag="y",
                jalc_doi="9876",
                jalc_crossref_doi="8765",
                jalc_datacite_doi="7654",
                ndl_jalc_doi="6543",
                suffix="",
            )
        with app.test_request_context(method="POST",data=data):
            create_form = view.create_form()
            result = view.validate_form(create_form)
            result == False
        # already exist repository create
        data = dict(
                repository="Root Index",
                jalc_flag=True,
                jalc_crossref_flag=True,
                jalc_datacite_flag=True,
                ndl_jalc_flag=True,
                jalc_doi="9876",
                jalc_crossref_doi="8765",
                jalc_datacite_doi="7654",
                ndl_jalc_doi="6543",
                suffix="",
            )
        with app.test_request_context(method="POST",data=data):
            create_form = view.create_form()
            result = view.validate_form(create_form)
            assert result == False
        
        # not exist repository
        data = dict(
                repository="New Index",
                jalc_flag=True,
                jalc_crossref_flag=True,
                jalc_datacite_flag=True,
                ndl_jalc_flag=True,
                jalc_doi="9876",
                jalc_crossref_doi="8765",
                jalc_datacite_doi="7654",
                ndl_jalc_doi="6543",
                suffix="",
            )
        with app.test_request_context(method="POST",data=data):
            create_form = view.create_form()
            result = view.validate_form(create_form)
            assert result == False
        

#    def on_model_change(self, form, model, is_created):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestIdentifierSettingView::test_on_model_change -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_on_model_change(self, setup_view_identifier, mocker):
        app, _, _, user = setup_view_identifier
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            # is_created is True
            url = url_for("identifier.create_view")
            data = dict(
                repository="Root Index",
                jalc_flag=True,
                jalc_crossref_flag=True,
                jalc_datacite_flag=True,
                ndl_jalc_flag=True,
                jalc_doi="1234",
                jalc_crossref_doi="2345",
                jalc_datacite_doi="3456",
                ndl_jalc_doi="4567",
                suffix="",
            )
            client.post(url,data=data)
            result = Identifier.query.first()
            assert result.repository == "Root Index"
            assert result.jalc_doi == "1234"
            
            
            # is_created is False
            url = url_for("identifier.edit_view",id=result.id)
            data = dict(
                repository="Root Index",
                jalc_flag="y",
                jalc_crossref_flag="y",
                jalc_datacite_flag="y",
                ndl_jalc_flag="y",
                jalc_doi="9876",
                jalc_crossref_doi="8765",
                jalc_datacite_doi="7654",
                ndl_jalc_doi="6543",
                suffix="",
                repo_selected="Root Index"
            )
            
            client.post(url,data=data)
            result = Identifier.query.first()
            assert result.repository == "Root Index"
            assert result.jalc_doi == "9876"

    
#    def on_form_prefill(self, form, id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestIdentifierSettingView::test_on_form_prefill -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_on_form_prefill(self, setup_view_identifier, mocker):
        app, db, _, user = setup_view_identifier
        iden = Identifier(
            repository="Root Index",
            jalc_flag=True,
            jalc_crossref_flag=True,
            jalc_datacite_flag=True,
            ndl_jalc_flag=True,
            jalc_doi="1234",
            jalc_crossref_doi="2345",
            jalc_datacite_doi="3456",
            ndl_jalc_doi="4567",
            suffix="test_suffix",
            created_userId="1",
            created_date=datetime(2022,12,1,11,22,33,4444),
            updated_userId="1",
            updated_date=datetime(2022,12,10,11,22,33,4444),
        )
        db.session.add(iden)
        db.session.commit()
        
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("identifier.edit_view",id="1",url="/admin/identifier/")
            mock_render = mocker.patch("flask_admin.base.render_template", return_value=make_response())
            res = client.get(url)
            args, kwargs = mock_render.call_args
            assert args[0] == "weko_records_ui/admin/pidstore_identifier_editor.html"
            
#    def create_form(self, obj=None):
#    def edit_form(self, obj):
#    def _use_append_repository(self, form):
#    def _use_append_repository_edit(self, form):
#    def _get_community_list(self):

# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestIdentifierSettingView::test_get_comunity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_comunity_list(self, setup_view_identifier, mocker):
        app, _, _, user = setup_view_identifier
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("identifier.create_view")
            data = dict(
                repository="Root Index",
                jalc_flag=True,
                jalc_crossref_flag=True,
                jalc_datacite_flag=True,
                ndl_jalc_flag=True,
                jalc_doi="1234",
                jalc_crossref_doi="2345",
                jalc_datacite_doi="3456",
                ndl_jalc_doi="4567",
                suffix="",
            )
            with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
                mock_query.return_value.all.side_effect = Exception("test_error")
                mock_render = mocker.patch("flask_admin.base.render_template", return_value=make_response())
                client.post(url,data=data)
                args, kwargs = mock_render.call_args
                assert args[0] == "weko_records_ui/admin/pidstore_identifier_creator.html"

#class RestrictedAccessSettingView(BaseView):
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::test_RestrictedAccessSettingView_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_RestrictedAccessSettingView_index(client, users, admin_settings, mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("restricted_access.index")
    mock_render = mocker.patch("weko_admin.admin.RestrictedAccessSettingView.render", return_value=make_response())
    res = client.get(url)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_admin/admin/restricted_access_settings.html"
    assert json.loads(kwargs["data"]) == {"content_file_download": {"expiration_date": 30,"expiration_date_unlimited_chk": False,"download_limit": 10,"download_limit_unlimited_chk": False,},"usage_report_workflow_access": {"expiration_date_access": 500,"expiration_date_access_unlimited_chk": False,},"terms_and_conditions": []}
    assert kwargs["items_per_page"] == 25
    assert kwargs["maxint"] == 9999999
    
    
@pytest.fixture()
def setup_view_facetsearch(admin_app, admin_db):
    admin = Admin(admin_app)
    facet_adminview_copy = dict(facet_search_adminview)
    facet_model = facet_adminview_copy.pop("model")
    facet_view = facet_adminview_copy.pop("modelview")
    view = facet_view(facet_model, admin_db.session,**facet_adminview_copy)
    admin.add_view(view)
    ds = admin_app.extensions['invenio-accounts'].datastore
    sysadmin = create_test_user(email='sysadmin@test.org')
    sysadmin_role = ds.create_role(name='System Administrator')
    ds.add_role_to_user(sysadmin, sysadmin_role)
    action_users = [
            ActionUsers(action='superuser-access', user=sysadmin),
        ]
    admin_db.session.add_all(action_users)
    admin_db.session.commit()
    
    return admin_app, admin_db, admin, sysadmin, view
#class FacetSearchSettingView(ModelView):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestFacetSearchSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestFacetSearchSettingView:
#    def search_placeholder(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestFacetSearchSettingView::test_search_placeholder -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_search_placeholder(self, setup_view_facetsearch, mocker):
        app, db, admin, user, view = setup_view_facetsearch
        view = FacetSearchSettingView(FacetSearchSetting, db.session)
        assert view.search_placeholder() == "Search"

#    def create_view(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestFacetSearchSettingView::test_create_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create_view(self, setup_view_facetsearch, mocker):
        app, db, admin, user, view = setup_view_facetsearch
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("facet-search.create_view",url="/admin/facet-search/")
            # can_create is True
            mapping_list = ["","path","title"]
            mocker.patch("weko_admin.admin.get_item_mapping_list",return_value=mapping_list)
            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            test = {
                "name_en": "",
                "name_jp": "",
                "mapping": "",
                "active": True,
                "aggregations": [],
                "mapping_list": mapping_list
            }
            client.get(url)
            args, kwargs = mock_render.call_args
            assert args[0] == "weko_admin/admin/facet_search_setting.html"
            assert json.loads(kwargs["data"]) == test
            assert kwargs["type_str"] == "new"
            
            # can_create is False
            view.can_create = False
            mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
            client.get(url)
            mock_redirect.assert_called_with("/admin/facet-search/")

#    def edit_view(self, id=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestFacetSearchSettingView::test_edit_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_edit_view(self, setup_view_facetsearch, mocker):
        app, db, admin, user, view = setup_view_facetsearch
        language = FacetSearchSetting(
            name_en="Data Language",
            name_jp="データの言語",
            mapping="language",
            aggregations=[],
            active=True,
            ui_type="SelectBox",
            display_number=1,
            is_open=True
        )
        db.session.add(language)
        db.session.commit()
        mapping_list = ["","path","title"]
        mocker.patch("weko_admin.admin.get_item_mapping_list",return_value=mapping_list)

        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("facet-search.edit_view",id=1,url="/admin/facet-search/")
            # can_edit is True
            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            test = {
                "name_en": "Data Language",
                "name_jp": "データの言語",
                "mapping": "language",
                "active": True,
                "aggregations": [],
                "mapping_list": mapping_list,
                "display_number":1,
                "is_open":True,
                "ui_type":"SelectBox"
            }
            client.get(url)
            args, kwargs = mock_render.call_args
            assert args[0] == "weko_admin/admin/facet_search_setting.html"
            assert json.loads(kwargs["data"]) == test
            assert kwargs["type_str"] == "edit"
            assert kwargs["id"] == 1

            # can_edit is False
            view.can_edit = False
            mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
            client.get(url)
            mock_redirect.assert_called_with("/admin/facet-search/")

#    def details_view(self, id=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestFacetSearchSettingView::test_details_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_details_view(self, setup_view_facetsearch, mocker):
        app, db, admin, user, view = setup_view_facetsearch
        language = FacetSearchSetting(
            name_en="Data Language",
            name_jp="データの言語",
            mapping="language",
            aggregations=[],
            active=True,
            ui_type="SelectBox",
            display_number=1,
            is_open=True
        )
        db.session.add(language)
        db.session.commit()
        mapping_list = ["","path","title"]
        mocker.patch("weko_admin.admin.get_item_mapping_list",return_value=mapping_list)

        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("facet-search.details_view",id=1,url="/admin/facet-search/")
            # can_edit is True
            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            test = {
                "name_en": "Data Language",
                "name_jp": "データの言語",
                "mapping": "language",
                "active": True,
                "aggregations": [],
                "mapping_list": mapping_list,
                "display_number":1,
                "is_open":True,
                "ui_type":"SelectBox"
            }
            client.get(url)
            args, kwargs = mock_render.call_args
            assert args[0] == "weko_admin/admin/facet_search_setting.html"
            assert json.loads(kwargs["data"]) == test
            assert kwargs["type_str"] == "details"
            assert kwargs["id"] == 1

            # can_edit is False
            view.can_edit = False
            mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
            client.get(url)
            mock_redirect.assert_called_with("/admin/facet-search/")

#    def delete(self, id=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestFacetSearchSettingView::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_delete(self, setup_view_facetsearch, mocker):
        
        app, db, admin, user, view = setup_view_facetsearch
        language = FacetSearchSetting(
            name_en="Data Language",
            name_jp="データの言語",
            mapping="language",
            aggregations=[],
            active=True,
            ui_type="SelectBox",
            display_number=1,
            is_open=True
        )
        db.session.add(language)
        db.session.commit()

        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("facet-search.delete",id=1,url="/admin/facet-search/")
            # can_delete is False
            view.can_delete = False
            mock_redirect = mocker.patch("weko_admin.admin.redirect", return_value=make_response())
            client.get(url)
            mock_redirect.assert_called_with("/admin/facet-search/")
            
            # can_delete is True
            view.can_delete = True
            
            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            test = {
                "name_en": "Data Language",
                "name_jp": "データの言語",
                "mapping": "language",
                "active": True,
                "aggregations": [],
                "display_number":1,
                "is_open":True,
                "ui_type":"SelectBox"
            }
            client.get(url)
            args, kwargs = mock_render.call_args
            assert args[0] == "weko_admin/admin/facet_search_setting.html"
            assert json.loads(kwargs["data"]) == test
            assert kwargs["type_str"] == "delete"
            assert kwargs["id"] == 1
            
            url = url_for("facet-search.delete",url="/admin/facet-search/")

            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            client.get(url,data={"id":1})
            args, kwargs = mock_render.call_args
            assert args[0] == "weko_admin/admin/facet_search_setting.html"
            assert json.loads(kwargs["data"]) == test
            assert kwargs["type_str"] == "delete"
            assert kwargs["id"] == "1"
#    'view_class': StyleSettingView,
#    'view_class': ReportView,
#    'view_class': FeedbackMailView,
#    'view_class': StatsSettingsView,
#    'view_class': LogAnalysisSettings,
#    'view_class': LanguageSettingView,
#    'view_class': WebApiAccount,
#    'view_class': RankingSettingsView,
#    'view_class': SearchSettingsView,
#    'view_class': SiteLicenseSettingsView,
#    'view_class': SiteLicenseSendMailSettingsView,
#    'view_class': FilePreviewSettingsView,
#    'view_class': ItemExportSettingsView,
#    'view_class': SiteInfoView,
#    'view_class': RestrictedAccessSettingView,
#
from flask_babelex import gettext as _
class TestsReindexElasticSearchView:

    @pytest.mark.parametrize("index,is_permission,status_code",[
                            (0,False,200),# sysadmin
                            (1,False,403),# repoadmin
                            (2,False,403),# comadmin
                            (3,False,403),# contributor
                            (4,False,403),# generaluser
                            ])
    def test_ReindexElasticSearchView_index_acl(self, client,users,admin_settings,mocker,index, is_permission ,status_code):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("reindex_es.index")
        # with patch("weko_admin.admin.check_reindex_is_running", return_value="{\"isError\":False ,\"isExecuting\":False,\"disabled_Btn\":False }"):
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker_render = mocker.patch("weko_admin.admin.ReindexElasticSearchView.render",return_value=make_response())
            res = client.get(url)
        assert_role(res,is_permission,status_code)

        if status_code == 200 :
            mocker_render.assert_called_with(
                template='weko_admin/admin/reindex_elasticsearch.html'
                ,isError=False
                ,isExecuting=False
                ,disabled_Btn=False 
            )
        else:
            mocker_render.assert_not_called()


    def test_ReindexElasticSearchView_index_guest(self, client,users,admin_settings,mocker):
        url = url_for("reindex_es.index")
        # with patch("weko_admin.admin.check_reindex_is_running", return_value="{\"isError\":False ,\"isExecuting\":False,\"disabled_Btn\":False }"):
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker_render = mocker.patch("weko_admin.admin.ReindexElasticSearchView.render",return_value=make_response())
            res = client.get(url)
        assert res.status_code == 302
        mocker_render.assert_not_called()
        
    def test_ReindexElasticSearchView_index_raise(self, client,users,admin_settings,mocker):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.index")
        with mocker.patch("weko_admin.admin.is_reindex_running", side_effect=BaseException("test_error")):
            mocker_render = mocker.patch("weko_admin.admin.ReindexElasticSearchView.render",return_value=make_response())
            res = client.get(url)
        assert res.status_code == 500
        mocker_render.assert_not_called()

    @pytest.mark.parametrize("index,is_permission,status_code",[
                            (0,False,200),# sysadmin
                            (1,False,403),# repoadmin
                            (2,False,403),# comadmin
                            (3,False,403),# contributor
                            (4,False,403),# generaluser
                            ])
    def test_ReindexElasticSearchView_reindex_acl(self, client,users,mocker,index,admin_settings, is_permission ,status_code):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("reindex_es.reindex" , is_db_to_es=False)
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker.patch("weko_admin.admin.reindex", return_value='completed')
            res = client.get(url)
            assert res.status_code == 405
            assert res.data != str({"responce" : _('completed')})
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker.patch("weko_admin.admin.reindex", return_value='completed')
            res = client.post(url)
            assert_role(res,is_permission,status_code)
            if res.status_code == 200:
                assert json.loads(res.data) == {"responce" : _('completed')}
            else:
                assert res.data != str({"responce" : _('completed')})

    def test_ReindexElasticSearchView_reindex_guest(self, client,users,admin_settings):
        url = url_for("reindex_es.reindex" , is_db_to_es=False)
        res = client.get(url)
        assert res.status_code == 405
        res = client.post(url)
        assert res.status_code == 302


    def test_ReindexElasticSearchView_reindex_param1(self, client,users,mocker,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.reindex" , is_db_to_es=False)
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker.patch("weko_admin.admin.reindex", return_value='completed')
            res = client.post(url)
            assert res.status_code == 200
            assert json.loads(res.data) == {"responce" : _('completed')}
    def test_ReindexElasticSearchView_reindex_param2(self, client,users,mocker,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.reindex" , is_db_to_es=True)
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker.patch("weko_admin.admin.reindex", return_value='completed')
            res = client.post(url)
            assert res.status_code == 200
            assert json.loads(res.data) == {"responce" : _('completed')}
    def test_ReindexElasticSearchView_reindex_param3(self, client,users,mocker,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.reindex" , is_db_to_es="aaa")
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker.patch("weko_admin.admin.reindex", return_value='completed')
            res = client.post(url)
            assert res.status_code == 200
            assert json.loads(res.data) == {"responce" : _('completed')}
    def test_ReindexElasticSearchView_reindex_param4(self, client,users,mocker,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.reindex" )
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker.patch("weko_admin.admin.reindex", return_value='completed')
            res = client.post(url)
            assert res.status_code == 200
            assert json.loads(res.data) == {"responce" : _('completed')}

    def test_ReindexElasticSearchView_reindex_chk_executing(self, client,users,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.reindex" , is_db_to_es=False)

        with patch("weko_admin.admin.is_reindex_running", return_value=True):
            res = client.post(url)
            assert res.status_code == 400
            assert json.loads(res.data).get("error") ==  _('executing...')

    def test_ReindexElasticSearchView_reindex_chk_err(self, client,users,mocker,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.reindex" , is_db_to_es=False)
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            # patch("weko_admin.admin.reindex", return_value='completed')
            mocker.patch("weko_admin.admin.AdminSettings.get", return_value=dict({"has_errored": True}))
            res = client.post(url)
            assert res.status_code == 400
            assert json.loads(res.data).get("error") == _('haserror')


    def test_ReindexElasticSearchView_reindex_return(self, client,users,mocker,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.reindex" , is_db_to_es=False)

        with mocker.patch("weko_admin.admin.is_reindex_running", side_effect=BaseException("test_error")):
            res = client.post(url)
            assert res.status_code == 500
            assert json.loads(res.data).get("error") != None
            admin_setting = AdminSettings.get('elastic_reindex_settings',False)
            assert True == admin_setting.get('has_errored')
            
    def test_ReindexElasticSearchView_reindex_return2(self, client,users,mocker,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.reindex" , is_db_to_es=False)
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            with mocker.patch("weko_admin.admin.reindex.apply_async", side_effect=BaseException("test_error")):
                res = client.post(url)
                assert res.status_code == 500
                assert json.loads(res.data).get("error") != None
                admin_setting = AdminSettings.get('elastic_reindex_settings',False)
                assert True == admin_setting.get('has_errored')

    @pytest.mark.parametrize("index,is_permission,status_code",[
                            (0,False,200),# sysadmin
                            (1,False,403),# repoadmin
                            (2,False,403),# comadmin
                            (3,False,403),# contributor
                            (4,False,403),# generaluser
                            ])
    def test_ReindexElasticSearchView_check_reindex_is_running_acl(self, client,users,admin_settings,index, is_permission ,status_code):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("reindex_es.check_reindex_is_running")
        with patch("weko_admin.admin.is_reindex_running", return_value=False):
            res = client.get(url)
        assert_role(res,is_permission,status_code)

        if status_code == 200:
            assert json.loads(res.data) == dict({ "isError":False ,"isExecuting":False,"disabled_Btn":False })
        else:
            assert res.data != str(dict({ "isError":False ,"isExecuting":False,"disabled_Btn":False }))

    def test_ReindexElasticSearchView_check_reindex_is_running_running(self, client,users,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.check_reindex_is_running")
        with patch("weko_admin.admin.is_reindex_running", return_value=True):
            res = client.get(url)
            assert res.status_code == 200
            assert json.loads(res.data) == dict({ "isError":False ,"isExecuting":True,"disabled_Btn":True })

    def test_ReindexElasticSearchView_check_reindex_iserror(self, client,users,admin_settings,mocker):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.check_reindex_is_running")
        with mocker.patch("weko_admin.admin.is_reindex_running", return_value=False):
            mocker.patch("weko_admin.admin.AdminSettings.get", return_value=dict({"has_errored": True}))
            res = client.get(url)
            assert res.status_code == 200
            assert json.loads(res.data) == dict({ "isError":True ,"isExecuting":False,"disabled_Btn":True })

    def test_ReindexElasticSearchView_check_reindex_is_running_guest(self, client,users,admin_settings):
        url = url_for("reindex_es.check_reindex_is_running")
        res = client.get(url)
        assert res.status_code == 302
        assert res.data != str(dict({ "isError":False ,"isExecuting":False,"disabled_Btn":False }))

    def test_ReindexElasticSearchView_check_reindex_is_running_err(self, client,users,admin_settings):
        login_user_via_session(client,email=users[0]["email"])# sysadmin
        url = url_for("reindex_es.check_reindex_is_running")
        with patch("weko_admin.admin.AdminSettings.get", side_effect=BaseException("test_error")):
            res = client.get(url)
            assert res.status_code == 500
            assert res.data != str(dict({ "isError":False ,"isExecuting":False,"disabled_Btn":False }))     
