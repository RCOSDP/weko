# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_tasks.py -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp

import json
import pytest

from celery import shared_task
from flask import current_app
from invenio_db import db
from invenio_oaiserver.models import OAISet

from weko_index_tree.tasks import update_oaiset_setting, delete_oaiset_setting
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index

# def update_oaiset_setting(index_info, data):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_tasks.py::test_update_oaiset_setting -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_update_oaiset_setting(i18n_app, indices, db):
    print(Indexes.get_index_tree())
    test_set_one = OAISet(
        id=11,
        spec='test',
        name='test_name_11',
        description='some test description',
        search_pattern='test search'
    )

    test_set_two = OAISet(
        id=22,
        spec='test',
        name='test_name_22',
        description='some test description',
        search_pattern='test search'
    )
    
    test_set_three_child = OAISet(
        id=44,
        spec='test',
        name='test_name_44',
        description='some test description',
        search_pattern='test search'
    )
    
    test_set_private = OAISet(
        id=55,
        spec='test',
        name='test_name_55',
        description='some test description',
        search_pattern='test search'
    )
    
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

    # test 1
    # Doesn't return anything and will pass if there are no errors
    assert not update_oaiset_setting(index_info_one, data_one)

    # test 2
    # Doesn't return anything and will pass if there are no errors
    assert not update_oaiset_setting(index_info_two, data_two)
    
    assert not update_oaiset_setting(index_info_three_child, data_three_child)
    
    assert not update_oaiset_setting(index_info_private, data_private)
    
    # assert not update_oaiset_setting(index_info_three, data_three)


# def delete_oaiset_setting(id_list):
def test_delete_oaiset_setting(i18n_app, indices, db_oaischema):
    test_set_one = OAISet(
        id=33,
        spec='test',
        name='test_name_33',
        description='some test description',
        search_pattern='test search'
    )

    test_set_two = OAISet(
        id=44,
        spec='test',
        name='test_name_44',
        description='some test description',
        search_pattern='test search'
    )
    
    db.session.add(test_set_one)
    db.session.add(test_set_two)

    # Doesn't return anything and will pass if there are no errors
    assert not delete_oaiset_setting([33])