# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp

from flask import url_for
import pytest
from mock import patch
from invenio_accounts.testutils import login_user_via_session

# def _(x):
# class CommunityModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionRequestModelView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestCommunityModelView():
    def test_index_view_acl_guest(self,app,client):
        url = url_for('community.index_view')
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
    def test_index_view_acl(self,app,client,users,id,status_code):
        url = url_for('community.index_view')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code

    # def on_model_change(self, form, model, is_created):
    # def _validate_input_id(self, field):
    # def role_query_cond(self, role_ids):
    # def get_query(self): 
    def test_get_query(self):
        assert self.get_query()
    # def get_count_query(self):
    def test_get_count_query(self):
        assert self.get_count_query()
    # def edit_form(self, obj):
    # def _use_append_repository_edit(self, form, index_id: str):
    # def _get_child_index_list(self):
    def test__get_child_index_list(self):
        assert self._get_child_index_list()



# class FeaturedCommunityModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestFeaturedCommunityModelView():
    def test_index_view_acl_guest(self,app,client):
        url = url_for('featuredcommunity.index_view')
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
    def test_index_view_acl(self,app,client,users,id,status_code):
        url = url_for('featuredcommunity.index_view')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code
    
    
# class InclusionRequestModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionRequestModelView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestInclusionRequestModelView():
    def test_index_view_acl_guest(self,app,client):
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
    def test_index_view_acl(self,app,client,users,id,status_code):
        url = url_for('inclusionrequest.index_view')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code
