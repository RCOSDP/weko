# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Admin api tests."""

from flask import session,make_response
from flask_login.utils import login_user, logout_user

from invenio_accounts.testutils import login_user_via_session

from weko_user_profiles.admin import UserProfileView
from weko_user_profiles.models import UserProfile

from tests.helpers import login,logout
# def test_admin(app):
#     """Test flask-admin interace."""
#     WekoUserProfiles(app)
# 
#     assert isinstance(user_profile_adminview, dict)
# 
#     assert 'model' in user_profile_adminview
#     assert 'modelview' in user_profile_adminview
# 
#     admin = Admin(app, name="Test")
# 
#     user_model = user_profile_adminview.pop('model')
#     user_view = user_profile_adminview.pop('modelview')
#     admin.add_view(user_view(user_model, db.session,
#                              **user_profile_adminview))
# 
#     with app.test_request_context():
#         request_url = url_for('userprofile.index_view')
# 
#     with app.app_context():
#         with app.test_client() as client:
#             res = client.get(
#                 request_url,
#                 follow_redirects=True
#             )
#             # assert res.status_code == 200
#             # assert b'Username' in (res.get_data())
#             # assert b'Full Name' in (res.get_data())

#class UserProfileView(ModelView):
class TestUserProfileView:
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_admin.py::TestUserProfileView::test_search_placeholder -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
#    def search_placeholder(self):
    def test_search_placeholder(self,req_context):
        assert UserProfileView(UserProfile,session).search_placeholder() == "Search"


#    def on_form_prefill(self, form, id):
    def test_on_form_prefill(self):
        pass


#    def index_view(self):
#        def pager_url(p):
#        def sort_url(column, invert=False, desc=None):
#        def page_size_url(s):
#            default_page_size=self.page_size,
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_admin.py::TestUserProfileView::test_index_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
    def test_index_view(self,app,admin_app,client,users,mocker):
        url = "/admin/userprofile/"
        login_user_via_session(client,email=users[0]["email"])
        mock_render = mocker.patch("weko_user_profiles.admin.UserProfileView.render",return_value=make_response())
        client.get(url)
        logout(app,client)
        # can_delete is false
        login(app,client,obj=users[1]["obj"])
        client.get(url)
        logout(app,client)


#    def edit_view(self):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_admin.py::TestUserProfileView::test_edit_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
    def test_edit_view(self,app,admin_app,client,users,user_profiles,mocker):
        url_base = "/admin/userprofile/edit/"
        # not self.can_edit
        login(app,client,obj=users[1]["obj"])
        mock_redirect = mocker.patch("weko_user_profiles.admin.redirect",return_value=make_response())
        res = client.post(url_base)
        mock_redirect.assert_called_with("/admin/userprofile/")
        logout(app,client)
        login(app,client,obj=users[0]["obj"])
        # not exist args
        mock_redirect = mocker.patch("weko_user_profiles.admin.redirect",return_value=make_response())
        res = client.post(url_base)
        mock_redirect.assert_called_with("/admin/userprofile/")
        
        # model is none
        url = url_base+"?id=1"
        mock_redirect = mocker.patch("weko_user_profiles.admin.redirect",return_value=make_response())
        mock_flash = mocker.patch("weko_user_profiles.admin.flash")
        res = client.post(url)
        mock_redirect.assert_called_with("/admin/userprofile/")
        mock_flash.assert_called_with("Record does not exist.","error")
        
        # not validate_form
        url = url_base+"?id={}".format(user_profiles[2].user_id)
        mock_render = mocker.patch("weko_user_profiles.admin.UserProfileView.render",return_value=make_response())
        res = client.post(url)
        args,_ = mock_render.call_args
        assert args[0] == "admin/model/edit.html"
        #mock_redirect.assert_called_with("/admin/userprofile/")
        
        # _add_another exist
        url = url_base+"?id={}".format(user_profiles[0].user_id)
        mock_redirect = mocker.patch("weko_user_profiles.admin.redirect",return_value=make_response())
        mock_flash = mocker.patch("weko_user_profiles.admin.flash")
        res = client.post(url,data={"_add_another":"value"})
        mock_redirect.assert_called_with("/admin/userprofile/new/?url=%2Fadmin%2Fuserprofile%2F")
        mock_flash.assert_called_with('Record was successfully saved.',"success")
        
        # _continue_editing exist
        url = url_base+"?id={}".format(user_profiles[0].user_id)
        mock_redirect = mocker.patch("weko_user_profiles.admin.redirect",return_value=make_response())
        mock_flash = mocker.patch("weko_user_profiles.admin.flash")
        res = client.post(url,data={"_continue_editing":"value"})
        mock_redirect.assert_called_with("http://TEST_SERVER.localdomain/admin/userprofile/edit/?id=5")
        mock_flash.assert_called_with('Record was successfully saved.',"success")
        
        # _add_another not exist, _continue_editing not exist
        url = url_base+"?id={}".format(user_profiles[0].user_id)
        mock_redirect = mocker.patch("weko_user_profiles.admin.redirect",return_value=make_response())
        mock_flash = mocker.patch("weko_user_profiles.admin.flash")
        res = client.post(url,data={})
        mock_redirect.assert_called_with("/admin/userprofile/")
        mock_flash.assert_called_with('Record was successfully saved.',"success")


#    def can_delete(self):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_admin.py::TestUserProfileView::test_can_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
    def test_can_delete(self,req_context,users):
        login_user(users[1]["obj"])
        result = UserProfileView(UserProfile,session).can_edit
        assert result == False
        logout_user()
        
        login_user(users[0]["obj"])
        result = UserProfileView(UserProfile,session).can_edit
        assert result == True


#    def can_edit(self):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_admin.py::TestUserProfileView::test_can_edit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
    def test_can_edit(self,req_context,users):
        login_user(users[1]["obj"])
        result = UserProfileView(UserProfile,session).can_edit
        assert result == False
        logout_user()
        
        login_user(users[0]["obj"])
        result = UserProfileView(UserProfile,session).can_edit
        assert result == True
