
import pytest
from invenio_oaiserver.models import OAISet
from invenio_accounts.testutils import create_test_user
from weko_index_tree.models import Index
from invenio_communities.models import Community

from invenio_communities.models import InclusionRequest

from invenio_communities.receivers import inject_provisional_community, destroy_oaipmh_set
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_receivers.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp


#def new_request(sender, request=None, notify=True, **kwargs):
#def inject_provisional_community(sender, json=None, record=None, index=None,
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_receivers.py::test_inject_provisional_community -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_inject_provisional_community(app,db,db_records,communities):
    increq = InclusionRequest(id_community="comm1",id_record=db_records[2].id,id_user=1)
    db.session.add(increq)
    db.session.commit()

    # index is not start with "record-"
    data = {}
    inject_provisional_community(None,data,db_records[2],"not-records-test")
    assert data == {}

    # index is start with "record-"
    data = {}
    inject_provisional_community(None,data,db_records[2])
    assert data == {"provisional_communities":["comm1"]}

#def create_oaipmh_set(mapper, connection, community):
#def destroy_oaipmh_set(mapper, connection, community):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_receivers.py::test_destroy_oaipmh_set -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_destroy_oaipmh_set(app,db):
    user = create_test_user(email='test@test.org')
    user1 = db.session.merge(user)
    ds = app.extensions['invenio-accounts'].datastore
    r = ds.create_role(name='superuser', description='1234')
    ds.add_role_to_user(user1, r)
    ds.commit()
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm1 = Community.create(community_id='comm1', role_id=1,
                         id_user=user1.id, title='Title1',
                         description='Description1',
                         root_node_id=1,
                         group_id=1)

    db.session.commit()

    # exist oaiset
    destroy_oaipmh_set(None,None,comm1)
    assert OAISet.query.filter_by(spec="user-comm1").one_or_none() == None

    # not exist oaiset
    with pytest.raises(Exception) as e:
        destroy_oaipmh_set(None,None,comm1)
    assert str(e.value) == "OAISet for community comm1 is missing"
