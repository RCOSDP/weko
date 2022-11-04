from os.path import dirname
from flask import url_for,current_app,make_response
from mock import patch

from invenio_accounts.testutils import login_user_via_session


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
        #with patch("weko_admin.admin.admin_permission_factory",return_value=MockPermission(True)):
        #    mock_render = mocker.patch("weko_admin.admin.StyleSettingView.render",return_value=make_response())
        #    mock_flash = mocker.patch("weko_admin.admin.flash")
        #    res = client.post(url,data={"body-bg":"#ffff"})
        #    mock_flash.assert_called_with("Successfully update color.",category="success")

#    def upload_editor(self):
#    def get_contents(self, f_path):
#    def cmp_files(self, f_path1, f_path2):
#class ReportView(BaseView):
#    def index(self):
#    def get_file_stats_output(self):
#    def get_user_report_data(self):
#    def set_email_schedule(self):
#    def get_email_address(self):
#class FeedbackMailView(BaseView):
#    def index(self):
#class LanguageSettingView(BaseView):
#    def index(self):
#class WebApiAccount(BaseView):
#    def index(self):
#class StatsSettingsView(BaseView):
#    def index(self):
#class LogAnalysisSettings(BaseView):
#    def index(self):
#    def parse_form_data(self, raw_data):
#class RankingSettingsView(BaseView):
#    def index(self):
#class SearchSettingsView(BaseView):
#    def index(self):
#class SiteLicenseSettingsView(BaseView):
#    def index(self):
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
