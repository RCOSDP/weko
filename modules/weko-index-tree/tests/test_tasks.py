# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_tasks.py -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp

import json
import pytest

from celery import shared_task
from flask import current_app
from invenio_db import db
from invenio_oaiserver.models import OAISet
from invenio_accounts.testutils import login_user_via_session
from mock import patch

from weko_index_tree.tasks import update_oaiset_setting, delete_oaiset_setting, \
                                    delete_index_handle
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index

# def update_oaiset_setting(index_info, data):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_tasks.py::test_update_oaiset_setting -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_update_oaiset_setting(i18n_app, client_api, indices, db, users, without_oaiset_signals):
    test_set_one = OAISet(
        id=11,
        spec='11',
        name='test_name_11',
        description='some test description',
        search_pattern='test search'
    )

    test_set_two = OAISet(
        id=22,
        spec='22',
        name='test_name_22',
        description='some test description',
        search_pattern='test search'
    )
    
    test_set_three_child = OAISet(
        id=44,
        spec='44',
        name='test_name_44',
        description='some test description',
        search_pattern='test search'
    )
    
    test_set_private = OAISet(
        id=55,
        spec='55',
        name='test_name_55',
        description='some test description',
        search_pattern='test search'
    )
    
    login_user_via_session(client=client_api, email=users[3]["email"])
    index_info_one = Indexes.get_path_name([indices['index_non_dict'].id])
    index_info_two = Indexes.get_path_name([indices['index_non_dict_child'].id])
    index_info_three = Indexes.get_path_name([indices['testIndexThree'].id])
    index_info_three_child = Indexes.get_path_name([indices['testIndexThreeChild'].id])
    index_info_private = Indexes.get_path_name([indices['testIndexThreeChild'].id])
    data_one = indices['index_dict']
    data_two = dict(indices['index_non_dict_child'])
    data_three = dict(indices['testIndexThree'])
    data_three_child = dict(indices['testIndexThreeChild'])
    data_private = dict(indices['testIndexPrivate'])

    db.session.add(test_set_one)
    db.session.add(test_set_two)
    db.session.add(test_set_three_child)
    db.session.add(test_set_private)
    db.session.commit()

    update_oaiset_setting(index_info_one[0], data_one)
    res = OAISet.query.filter_by(id=33).one_or_none()
    assert res.name=="testIndexThree"
    assert res.description=="testIndexThree"
    assert res.search_pattern=='path:"33"'
    assert res.spec=="33"

    update_oaiset_setting(index_info_two[0], data_two)
    res = OAISet.query.filter_by(id=44).one_or_none()
    assert res==None
    
    update_oaiset_setting(index_info_three_child[0], data_three_child)
    res = OAISet.query.filter_by(id=44).one_or_none()
    assert res==None
    
    update_oaiset_setting(index_info_private[0], data_private)
    res = OAISet.query.filter_by(id=55).one_or_none()
    assert res==None

    update_oaiset_setting(index_info_three[0], data_three)
    res = OAISet.query.filter_by(id=33).one_or_none()
    assert res.name=="testIndexThree"
    assert res.description=="testIndexThree"
    assert res.search_pattern=='path:"33"'
    assert res.spec=="33"

    _data = {
        "public_state": True,
        "harvest_public_state": True,
        "parent": "A",
        "id": "33",
        "index_name": "test data"
    }
    update_oaiset_setting(None, _data)
    res = OAISet.query.filter_by(id=33).one_or_none()
    assert res.name=="testIndexThree"
    assert res.description=="testIndexThree"
    assert res.search_pattern=='path:"33"'
    assert res.spec=="33"


# def delete_oaiset_setting(id_list):
def test_delete_oaiset_setting(i18n_app, indices, db_oaischema, without_oaiset_signals):
    test_set_one = OAISet(
        id=33,
        spec='33',
        name='test_name_33',
        description='some test description',
        search_pattern='test search'
    )

    test_set_two = OAISet(
        id=44,
        spec='44',
        name='test_name_44',
        description='some test description',
        search_pattern='test search'
    )
    
    db.session.add(test_set_one)
    db.session.add(test_set_two)

    res = OAISet.query.all()
    assert len(res)==2

    delete_oaiset_setting([])
    res = OAISet.query.all()
    assert len(res)==2

    delete_oaiset_setting([33])
    res = OAISet.query.all()
    assert len(res)==1

    delete_oaiset_setting({})
    res = OAISet.query.all()
    assert len(res)==1

# def delete_index_handle(id_list):
def test_delete_index_handle(i18n_app, indices, db):
    try:
        test_index_one = Index(
            id=999,
            cnri='cnri_999',
            parent=0,
            position=999,
            is_deleted=True
        )

        test_index_two = Index(
            id=1000,
            cnri='cnri_1000',
            parent=0,
            position=1000,
            is_deleted=True
        )

        db.session.add(test_index_one)
        db.session.add(test_index_two)

        with patch("weko_handle.api.Handle.delete_handle", return_value='1234567890/1'):
            delete_index_handle([999, 1000])

        with patch("weko_handle.api.Handle.delete_handle", return_value='1234567890/1'):
            delete_index_handle([10000])
            
        with patch("weko_handle.api.Handle.delete_handle", return_value=None):
            delete_index_handle([999, 1000])

    except Exception as ex:
        current_app.logger.debug(ex)
