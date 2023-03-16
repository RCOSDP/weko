
from os.path import dirname, join
from flask import url_for,current_app,make_response
from mock import patch
import json
from io import BytesIO

from invenio_accounts.testutils import login_user_via_session

from weko_admin.admin import StyleSettingView,LogAnalysisSettings
from weko_admin.models import AdminSettings,StatisticsEmail,LogAnalysisRestrictedCrawlerList,LogAnalysisRestrictedIpAddress,RankingSettings

# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

#class StyleSettingView(BaseView):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestStyleSettingView:
#    def index(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_index(self,client,users,mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("stylesetting.index")
        current_app.instance_path=dirname(__file__)
        current_app.config.update(
            WEKO_THEME_INSTANCE_DATA_DIR="data"
        )
        mock_render = mocker.patch("weko_admin.admin.StyleSettingView.render",return_value=make_response())
        res = client.get(url)
        mock_render.assert_called_with(
            "weko_admin/admin/block_style.html",
            body_bg="#ffff"
        )
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
            data={"body-bg":"#ffff"}
            mock_render = mocker.patch("weko_admin.admin.StyleSettingView.render",return_value=make_response())
            mock_flash = mocker.patch("weko_admin.admin.flash")
            res = client.post(url,data=data)

#    def upload_editor(self):


#    def get_contents(self, f_path):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView::test_get_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_contents(self,client):
        path = join(current_app.instance_path,dirname(__file__),"data/_variables.scss")
        result = StyleSettingView().get_contents(path)
        test = [
            "$body-bg: #ffff;\n",
            "$panel-bj: #ffff;\n",
            "$footer-default-bg: #0d5f89;\n",
            "$navbar-default-bg: #0d5f89;\n",
            "$panel-default-border: #dddddd;\n",
            "$input-bg-transparent: rgba(255, 255, 255, 0);"
        ]
        assert result == test
        
#    def cmp_files(self, f_path1, f_path2):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestStyleSettingView::test_cmp_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_cmp_files(self,app,client):
        path1=join(current_app.instance_path,dirname(__file__),"data/_variables.scss")
        path2=join(current_app.instance_path,dirname(__file__),"data/actions.json")
        result = StyleSettingView().cmp_files(path1,path2)
        assert result == False
        
        result = StyleSettingView().cmp_files(path1,path1)
        assert result == True
        
            
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
        assert kwargs["emails"] == statistic_email_addrs
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
    def test_index(self,client,users,log_crawler_list,restricted_ip_addr,mocker):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("loganalysissetting.index")
        
        mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
        result = client.get(url)
        assert result.status_code == 200
        mock_render.assert_called_with(
            "weko_admin/admin/log_analysis_settings.html",
            restricted_ip_addresses=restricted_ip_addr,
            shared_crawlers=log_crawler_list
        )
        
        # not shared_crawlers
        LogAnalysisRestrictedCrawlerList.query.delete()
        mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
        result = client.get(url)
        assert result.status_code == 200
        crawler = LogAnalysisRestrictedCrawlerList.query.all()
        mock_render.assert_called_with(
            "weko_admin/admin/log_analysis_settings.html",
            restricted_ip_addresses=restricted_ip_addr,
            shared_crawlers=crawler
        )
        
        # raise Exception
        with patch("weko_admin.admin.LogAnalysisRestrictedIpAddress.get_all",side_effect=Exception("test_error")):
            mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
            mock_flash = mocker.patch("weko_admin.admin.flash")
            result = client.get(url)
            assert result.status_code == 200
            mock_flash.assert_called_with("Could not get restricted data.","error")
            mock_render.assert_called_with(
                "weko_admin/admin/log_analysis_settings.html",
                restricted_ip_addresses=[],
                shared_crawlers=[]
            )
        
        # post
        data = {
            "ip_address_0_id":"1",
            "address_list_0":"123","address_list_0":"456","address_list_0":"789","address_list_0":"012",
            "shared_crawler_0_id":"1","shared_crawler_0_check":"on","shared_crawler_0":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_ip_blacklist.txt",
            "shared_crawler_1_id":"2","shared_crawler_1_check":"on","shared_crawler_1":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_useragent.txt",
        }
        mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
        result = client.post(url,data=data)
        crawler = LogAnalysisRestrictedCrawlerList.query.all()
        addr = LogAnalysisRestrictedIpAddress.query.all()
        mock_render.assert_called_with(
            "weko_admin/admin/log_analysis_settings.html",
            restricted_ip_addresses=addr,
            shared_crawlers=crawler
        )
        
        # raise Exception
        data = {
            "ip_address_0_id":"1",
            "address_list_0":"123","address_list_0":"456","address_list_0":"789","address_list_0":"012",
            "shared_crawler_0_id":"1","shared_crawler_0_check":"on","shared_crawler_0":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_ip_blacklist.txt",
            "shared_crawler_1_id":"2","shared_crawler_1_check":"on","shared_crawler_1":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_useragent.txt",
        }
        with patch("weko_admin.admin.LogAnalysisRestrictedIpAddress.update_table",side_effect=Exception("test_error")):
            mock_render = mocker.patch("weko_admin.admin.LogAnalysisSettings.render",return_value=make_response())
            mock_flash = mocker.patch("weko_admin.admin.flash")
            result = client.post(url,data=data)
            crawler = LogAnalysisRestrictedCrawlerList.query.all()
            addr = LogAnalysisRestrictedIpAddress.query.all()
            mock_render.assert_called_with(
                "weko_admin/admin/log_analysis_settings.html",
                restricted_ip_addresses=addr,
                shared_crawlers=crawler
            )
            mock_flash.assert_called_with("Could not save data.","error")
        
#    def parse_form_data(self, raw_data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_admin.py::TestLogAnalysisSettings::test_parse_form_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_parse_form_data(self):
        from werkzeug.datastructures import ImmutableMultiDict
        raw_data = ImmutableMultiDict([
            ('ip_address_0_id', '1'), ('address_list_0', '123'),
            ('address_list_0', '456'), ('address_list_0', '789'), 
            ('address_list_0', '012'), ('shared_crawler_0_id', '1'), 
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
    mock_render.assert_called_with(
        "weko_admin/admin/ranking_settings.html",
        is_show=True,new_item_period=14,statistical_period=365,display_rank=10,
        rankings=ranking_settings.rankings
    )
    
    # get, ranking_setting is not exist
    with patch("weko_admin.admin.RankingSettings.get",return_value=None):
        mock_render = mocker.patch("weko_admin.admin.RankingSettingsView.render",return_value=make_response())
        result = client.get(url)
        assert result.status_code == 200
        mock_render.assert_called_with(
            "weko_admin/admin/ranking_settings.html",
            is_show=False,new_item_period=14,statistical_period=365,display_rank=10,
            rankings={'most_reviewed_items': False,'most_downloaded_items': False,'created_most_items_user': False,'most_searched_keywords': False,'new_items': False}
        )
    
    # post, submit is not ranking_setting
    data = {
        "is_show":"True","new_item_period":"20","statistical_period":"730","display_rank":"15","most_reviewed_items":"on","most_downloaded_items":"on","created_most_items_user":"on","most_searched_keywords":"off","new_items":"on","submit":"not_save_ranking_settings"
    }
    mock_render = mocker.patch("weko_admin.admin.RankingSettingsView.render",return_value=make_response())
    result = client.post(url,data=data)
    assert result.status_code == 200
    mock_render.assert_called_with(
        "weko_admin/admin/ranking_settings.html",
        is_show=True,new_item_period=14,statistical_period=365,display_rank=10,
        rankings=ranking_settings.rankings
    )
    
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
def test_SearchSettingsView_index(client,users,item_type,admin_settings,index_style,search_management,mocker):
    login_user_via_session(client,email=users[0]["email"])
    url = url_for("searchsettings.index")
    
    # get
    mock_render = mocker.patch("weko_admin.admin.SearchSettingsView.render",return_value=make_response())
    result = client.get(url)
    assert result.status_code == 200
    test = {"init_disp_setting":{"init_disp_index":"","init_disp_screen_setting":"0","init_disp_index_disp_method":"0"},
            "search_author_flg":"name",
            "index_tree_style":{"width_options":["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],"width":"3","height":""}}
    mock_render.assert_called_with(
        "weko_admin/admin/search_management_settings.html",
        widths=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'],
        setting_data=json.dumps(test),
        lists=[item["name"] for item in item_type]
    )
    
    # raise Exception
    with patch("weko_admin.admin.ItemTypes.get_latest",side_effect=BaseException("test_error")):
        result = client.get(url)
        assert result.status_code == 500
    
    # post
    
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
    result = client.post(url,json=data)
    
    

#class SiteLicenseSendMailSettingsView(BaseView):
#    def index(self):
#class FilePreviewSettingsView(BaseView):
#    def index(self):
#class ItemExportSettingsView(BaseView):
#    def index(self):
#    def _get_current_settings(self):
#class SiteInfoView(BaseView):
#    def index(self):
#class IdentifierSettingView(ModelView):
#    def _validator_halfwidth_input(form, field):
#    def validate_form(self, form):
#    def on_model_change(self, form, model, is_created):
#        By default does nothing.
#    def on_form_prefill(self, form, id):
#    def create_form(self, obj=None):
#    def edit_form(self, obj):
#    def _use_append_repository(self, form):
#    def _use_append_repository_edit(self, form):
#    def _get_community_list(self):
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
#    def search_placeholder(self):
#    def create_view(self):
#    def edit_view(self, id=None):
#    def details_view(self, id=None):
#    def delete(self, id=None):
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
