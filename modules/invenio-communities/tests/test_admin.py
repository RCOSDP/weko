# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp

from flask import url_for, current_app, make_response
from flask_admin import Admin
import pytest
from mock import patch
from invenio_accounts.testutils import login_user_via_session, create_test_user
from invenio_access.models import ActionUsers
from invenio_communities.models import Community
from weko_index_tree.models import IndexStyle,Index
from invenio_accounts.testutils import login_user_via_session
from invenio_communities.admin import community_adminview,request_adminview,featured_adminview

@pytest.fixture()
def setup_view_community(app,db,users):
    sysadmin = users[2]["obj"]
    test_index = Index(
            index_name="testIndexOne",
            browsing_role="Contributor",
            public_state=True,
            id=11,
        )
    db.session.add(test_index)
    db.session.commit()
    comm = Community(
        id="test_comm",
        id_role=1,root_node_id=11,
        title="Test comm",
        description="this is test comm",
        id_user=1
    )
    db.session.add(comm)
    db.session.commit()
    
    admin = Admin(app)
    community_adminview_copy = dict(community_adminview)
    community_model = community_adminview_copy.pop("model")
    community_view = community_adminview_copy.pop("modelview")
    view = community_view(community_model,db.session,**community_adminview_copy)
    admin.add_view(view)
    return app, db, admin, sysadmin, view

# def _(x):
# class CommunityModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionRequestModelView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestCommunityModelView():
    def test_index_view_acl_guest(self,app,setup_view_community,client):
        url = url_for('community.index_view')
        res = client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_index_view_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_index_view_acl(self,app,client,setup_view_community,users,id,status_code):
        url = url_for('community.index_view')
        with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
            # login_user_via_session(client,email=users[id]["email"])
            res = client.get(url)
            assert res.status_code == status_code

    # def on_model_change(self, form, model, is_created):
    # def _validate_input_id(self, field):
    # def role_query_cond(self, role_ids):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_role_query_cond -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_role_query_cond(self, setup_view_community, users):
        _, _, _, user, view = setup_view_community
        with patch("flask_login.utils._get_user", return_value=user):
            # role_ids is false
            result = view.role_query_cond([])
            assert result == None
            
            # role_idss is true
            result = view.role_query_cond([1,2])
            assert str(result) == "communities_community.id_role IN (:id_role_1, :id_role_2) OR communities_community.id_user = :id_user_1"
    
    # def get_query(self): 
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_get_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_query(self,setup_view_community,users):
        _, _, _, user, view = setup_view_community
        # min(role_ids) <= 2
        with patch("flask_login.utils._get_user", return_value=user):
            result = view.get_query()
            assert "WHERE" not in str(result)
        
        # min(role_ids) > 2
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            result = view.get_query()
            assert "WHERE communities_community.id_role IN (?) OR communities_community.id_user = ?" in str(result)
            
    # def get_count_query(self):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_get_count_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_count_query(self,setup_view_community,users):
        app, _, _, user, view = setup_view_community
        # min(role_ids) <= 2
        with patch("flask_login.utils._get_user", return_value=user):
            result = view.get_count_query()
            assert "WHERE" not in str(result)
            
        # min(role_ids) > 2
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            result = view.get_count_query()
            assert "WHERE communities_community.id_role IN (?) OR communities_community.id_user = ?" in str(result)

    # def edit_form(self, obj):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_edit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_edit(self,setup_view_community,users,mocker):
        app, _, _, user, _ = setup_view_community
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("community.edit_view",id="test_comm",url="/admin/community/")
            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            # get
            res = client.get(url)
            assert res.status_code == 200
            login_user_via_session(client,email=users[0]["email"])
            res = client.get(url)
            assert res.status_code == 200
            
            login_user_via_session(client,email=user.email)
            # post
            # first character is not alphabet,"-","_"
            data = {
                "id": "111",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1."
            }
            res = client.post(url,data=data)
            assert res.status_code == 200
            assert "The first character cannot be a number or special character. It should be an alphabet character, &#34;-&#34; or &#34;_&#34;" in str(res.data)
            
            # first character is alphabet,"-","_"  negative number
            data = {
                "id": "-1",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1."
            }
            res = client.post(url,data=data)
            assert res.status_code == 200
            assert "Cannot set negative number to ID." in str(res.data)
            
            # special character
            data = {
                "id": "a-1^^^",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1."
            }
            res = client.post(url,data=data)
            assert res.status_code == 200
            assert "Don&#39;t use space or special character except `-` and `_`." in str(res.data)
            
            # correct_data
            data = {
                "id": "a-123456789",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1."
            }
            res = client.post(url,data=data)
            assert res.status_code == 302
            comm = Community.query.filter_by(id="a-123456789").one()
            assert comm
            assert comm.title == "Test comm after"
            assert comm.description == "this is description of community1."

    # def _use_append_repository_edit(self, form, index_id: str):
    # def _get_child_index_list(self):



# class FeaturedCommunityModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestFeaturedCommunityModelView():
    def test_index_view_acl_guest(self,app,db,client):
        admin = Admin(app)
        featured_adminview_copy = dict(featured_adminview)
        featured_model = featured_adminview_copy.pop("model")
        featured_view = featured_adminview_copy.pop("modelview")
        view = featured_view(featured_model,db.session,**featured_adminview_copy)
        admin.add_view(view)

        url = url_for('featuredcommunity.index_view')
        res = client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionfeaturedModelView::test_index_view_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_index_view_acl(self,app,db,client,users,id,status_code):
        admin = Admin(app)
        featured_adminview_copy = dict(featured_adminview)
        featured_model = featured_adminview_copy.pop("model")
        featured_view = featured_adminview_copy.pop("modelview")
        view = featured_view(featured_model,db.session,**featured_adminview_copy)
        admin.add_view(view)
        url = url_for('featuredcommunity.index_view')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code
    
    
# class InclusionRequestModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionRequestModelView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestInclusionRequestModelView():
    def test_index_view_acl_guest(self,app,client,db):
        admin = Admin(app)
        request_adminview_copy = dict(request_adminview)
        request_model = request_adminview_copy.pop("model")
        request_view = request_adminview_copy.pop("modelview")
        view = request_view(request_model,db.session,**request_adminview_copy)
        admin.add_view(view)
        url = url_for('inclusionrequest.index_view')
        res = client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionRequestModelView::test_index_view_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_index_view_acl(self,app,client,db,users,id,status_code):
        admin = Admin(app)
        request_adminview_copy = dict(request_adminview)
        request_model = request_adminview_copy.pop("model")
        request_view = request_adminview_copy.pop("modelview")
        view = request_view(request_model,db.session,**request_adminview_copy)
        admin.add_view(view)

        url = url_for('inclusionrequest.index_view')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code
