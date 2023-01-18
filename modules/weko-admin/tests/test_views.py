import json
from mock import patch, MagicMock
from invenio_accounts.testutils import login_user_via_session


def test_get_email_author_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.FeedbackMail.search_author_mail",
               return_value={}
               ):
        res = client.post('/api/admin/search_email',
                          data=json.dumps({}),
                          content_type="application/json"
                          )
        assert res.status_code == 200


def test_get_email_author_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.FeedbackMail.search_author_mail",
               return_value={}
               ):
        res = client.post('/api/admin/search_email',
                          data=json.dumps({}),
                          content_type="application/json"
                          )
        assert res.status_code == 200


def test_get_email_author_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.FeedbackMail.search_author_mail",
               return_value={}
               ):
        res = client.post('/api/admin/search_email',
                          data=json.dumps({}),
                          content_type="application/json"
                          )
        assert res.status_code == 403


def test_get_email_author_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.FeedbackMail.search_author_mail",
               return_value={}
               ):
        res = client.post('/api/admin/search_email',
                          data=json.dumps({}),
                          content_type="application/json"
                          )
        assert res.status_code == 403


def test_get_email_author_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.FeedbackMail.search_author_mail",
               return_value={}
               ):
        res = client.post('/api/admin/search_email',
                          data=json.dumps({}),
                          content_type="application/json"
                          )
        assert res.status_code == 403


def test_get_email_author_guest(client, users):
    with patch("weko_admin.views.FeedbackMail.search_author_mail",
               return_value={}
               ):
        res = client.post('/api/admin/search_email',
                          data=json.dumps({}),
                          content_type="application/json"
                          )
        assert res.status_code == 302

class MockUsageReport:
    def __init__(self):
        pass

    def get_activities_per_page(self, activities_id, size, page):
        return {}


def test_get_usage_report_activities_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_get_usage_report_activities_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_get_usage_report_activities_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_get_usage_report_activities_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_get_usage_report_activities_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_get_usage_report_activities_guest(client, users):
    mock_usagereport = MagicMock(side_effect=MockUsageReport)
    with patch("weko_admin.views.UsageReport", mock_usagereport):
        res = client.post("/api/admin/restricted_access/"\
                          "get_usage_report_activities",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302


def test_manual_send_site_license_mail_sysadmin(client, users, test_site_license):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_manual_send_site_license_mail_repoadmin(client, users, test_site_license):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_manual_send_site_license_mail_comadmin(client, users, test_site_license):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_manual_send_site_license_mail_cont(client, users, test_site_license):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_manual_send_site_license_mail_gene(client, users, test_site_license):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_manual_send_site_license_mail_guest(client, users, test_site_license):
    with patch("weko_admin.views.QueryCommonReportsHelper.get", return_value={"institution_name":[]}):
        with patch("weko_admin.views.send_site_license_mail"):
            res = client.post("/api/admin/sitelicensesendmail/send/202201/202203",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302


def test_remove_facet_search_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 200


def test_remove_facet_search_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 200


def test_remove_facet_search_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 403


def test_remove_facet_search_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 403


def test_remove_facet_search_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 403


def test_remove_facet_search_guest(client, users):
    data = {"id":[]}
    with patch("weko_admin.views.store_facet_search_query_in_redis", return_value={}):
        res = client.post("api/admin/facet-search/remove",
                          data=json.dumps(data),
                          content_type="application/json")
        assert res.status_code == 302


class Mock_FeedbackMail:
    @classmethod
    def get_mail_data_by_history_id(cls, history_id):
        pass
    
    @classmethod
    def update_history_after_resend(cls, history_id):
        pass


def test_resend_failed_mail_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_resend_failed_mail_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_resend_failed_mail_comadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_resend_failed_mail_cont(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_resend_failed_mail_gene(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403

def test_resend_failed_mail_guest(client, users):
    mock_feedbackmail = MagicMock(side_effect = Mock_FeedbackMail)
    with patch("weko_admin.views.FeedbackMail", mock_feedbackmail):
        with patch("weko_admin.views.StatisticMail.send_mail_to_all", return_value=""):
            res = client.post("/api/admin/resend_failed_mail",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302


def test_save_api_cert_data_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 200


def test_save_api_cert_data_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 200


def test_save_api_cert_data_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_save_api_cert_data_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_save_api_cert_data_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_save_api_cert_data_guest(client, users):
    res = client.post("/api/admin/save_api_cert_data",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 302


def test_save_facet_search_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_save_facet_search_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_save_facet_search_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_save_facet_search_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_save_facet_search_guest(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_save_facet_search_guest(client, users):
    with patch("weko_admin.views.is_exits_facet", return_value=True):
        with patch("weko_admin.views.store_facet_search_query_in_redis", return_value=""):
            res = client.post("/api/admin/facet-search/save",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302


def test_save_lang_list_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200

def test_save_lang_list_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_save_lang_list_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_lang_list_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_lang_list_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_lang_list_guest(client, users):
    with patch("weko_admin.views.update_admin_lang_setting", return_value=""):
        res = client.post("/api/admin/save_lang",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302


def test_save_restricted_access_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_save_restricted_access_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_save_restricted_access_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_restricted_access_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_restricted_access_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_save_restricted_access_guest(client, users):
    with patch("weko_admin.views.update_restricted_access",return_value=True):
        res = client.post("/api/admin/restricted_access/save",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302

def test_send_mail_reminder_usage_report_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 200


def test_send_mail_reminder_usage_report_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 200


def test_send_mail_reminder_usage_report_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_send_mail_reminder_usage_report_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_send_mail_reminder_usage_report_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])

    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 403


def test_send_mail_reminder_usage_report_guest(client, users):
    res = client.post("/api/admin/restricted_access/send_mail_reminder",
                      data=json.dumps({}),
                      content_type="application/json")
    assert res.status_code == 302
def test_update_feedback_mail_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_update_feedback_mail_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200


def test_update_feedback_mail_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_update_feedback_mail_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_update_feedback_mail_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 403


def test_update_feedback_mail_guest(client, users):
    with patch("weko_admin.views.FeedbackMail.update_feedback_email_setting", return_value={}):
        res = client.post("/api/admin/update_feedback_mail",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302


def test_update_site_info_sysadmin(client, users):
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_update_site_info_repoadmin(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 200


def test_update_site_info_comadmin(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_update_site_info_cont(client, users):
    login_user_via_session(client=client, email=users[1]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_update_site_info_gene(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 403


def test_update_site_info_guest(client, users):
    with patch("weko_admin.views.format_site_info_data", return_value=""):
        with patch("weko_admin.views.validation_site_info", return_value={"error":"error"}):
            res = client.post("/api/admin/update_site_info",
                              data=json.dumps({}),
                              content_type="application/json")
            assert res.status_code == 302