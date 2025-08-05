
from invenio_communities.serializers.schemas.community import CommunitySchemaV1
from weko_index_tree.models import Index
from invenio_communities.views.api import blueprint
from invenio_communities.models import Community
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_serializers_schema_community.py::test_CommunitySchemaV1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_CommunitySchemaV1(app,db, users):
    index = Index()
    db.session.add(index)
    db.session.commit()

    comm1 = Community.create(community_id='comm1', role_id=1,
                             id_user=users[2]["obj"].id, title='Title1',
                             description='Description1',
                             root_node_id=index.id,
                             group_id=1)
    db.session.commit()
    context = {
        "total":10,
        "urlkwargs":["test_kwargs"]
    }
    with app.test_request_context():
        schema = CommunitySchemaV1(context=context)
        result =schema.dump(comm1)
        assert result.data["title"] == "Title1"
        assert result.data["logo_url"] == None


    comm2 = Community.create(community_id='comm2', role_id=1,
                             id_user=users[2]["obj"].id, title='Title2',
                             description='Description2',
                             root_node_id=1,
                             group_id=1,
                             logo_ext="png",)
    comm3 = Community.create(community_id='comm3', role_id=1,
                             id_user=users[2]["obj"].id, title='Title3',
                             description='Description3',
                             root_node_id=1,
                             group_id=1,
                             logo_ext="jpg")
    db.session.commit()

    page = Community.filter_communities(None,None).paginate(1,2)
    comms = [comm2,comm3]
    context = {
        "total":2,
        "page":page,
        "urlkwargs":{}
    }
    with app.test_request_context():

        schema = CommunitySchemaV1(context=context)
        result =schema.dump(comms,many=True)
        result = result.data
        assert len(result["hits"]["hits"]) == 2
        assert [res["title"] for res in result["hits"]["hits"]] == ["Title2","Title3"]
        assert [res["logo_url"] for res in result["hits"]["hits"]] == ["https://inveniosoftware.org/api/files/00000000-0000-0000-0000-000000000000/comm2/logo.png","https://inveniosoftware.org/api/files/00000000-0000-0000-0000-000000000000/comm3/logo.jpg"]
        assert result["hits"]["total"] == 2
        assert "links" in result
        assert result["links"] == {"self":"http://test_server/api/communities/?page=1","next":"http://test_server/api/communities/?page=2"}

    # page not in context
    context = {
        "total":2,
        "urlkwargs":{}
    }
    with app.test_request_context():
        schema = CommunitySchemaV1(context=context)
        result =schema.dump(comms,many=True)
        result = result.data
        assert len(result["hits"]["hits"]) == 2
        assert [res["title"] for res in result["hits"]["hits"]] == ["Title2","Title3"]
        assert result["hits"]["total"] == 2
        assert "links" not in result
