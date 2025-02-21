
from flask import url_for

from invenio_communities.models import Community
from weko_index_tree.models import Index
from mock import patch
from invenio_accounts.testutils import create_test_user
from invenio_communities.views.api import blueprint, dbsession_clean

# class CommunitiesResource(ContentNegotiatedMethodView):
#     def __init__(self, serializers=None, *args, **kwargs):
#     def get(self, query, sort, page, size):

# class CommunityDetailsResource(ContentNegotiatedMethodView):
class TestCommunityDetailsResource:
#     def __init__(self, serializers=None, *args, **kwargs):
#     def get(self, community_id):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_api.py::TestCommunityDetailsResource::test_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get(self,client,app,db,communities):
        app.register_blueprint(blueprint)
        url = url_for("invenio_communities_rest.communities_item",community_id="not_exist_comm")
        res = client.get(url)
        assert res.status_code==404


# def dbsession_clean(exception):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_api.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_dbsession_clean(app, db):
    user = create_test_user(email='test@test.org')
    user1 = db.session.merge(user)
    ds = app.extensions['invenio-accounts'].datastore
    r = ds.create_role(name='superuser', description='1234')
    ds.add_role_to_user(user1, r)
    ds.commit()
    index = Index()
    db.session.add(index)
    db.session.commit()
    # exist exception
    com1 = Community(id=1,id_role=1,id_user=1,root_node_id=1,title="com1",page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False)
    db.session.add(com1)
    dbsession_clean(None)
    assert Community.query.filter_by(id=1).first().title =="com1"

    # raise Exception
    com2 = Community(id=2,id_role=1,id_user=1,root_node_id=1,title="com2",page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False)
    db.session.add(com2)
    with patch("invenio_mail.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert Community.query.filter_by(id=2).first() is None

    # not exist exception
    config3 = Community(id=3,id_role=1,id_user=1,root_node_id=1,title="com3",page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False)
    db.session.add(config3)
    dbsession_clean(Exception)
    assert Community.query.filter_by(id=3).first() is None
