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
def test_update_oaiset_setting(i18n_app, indices, db):
    index_info = Indexes.get_path_name([indices['index_dict']["id"]])
    data = indices['index_dict']
    
    # test 1
    update_oaiset_setting(index_info, data)

    # test 2

# def delete_oaiset_setting(id_list):
def test_delete_oaiset_setting(i18n_app, indices, db):
    set1 = OAISet(
        id=1,
        spec="oaiset1_spec",
        name="oaiset1_name",
    )
    id_list = [Index.get_all()[0]['id']]
    
    # test 1
    delete_oaiset_setting(id_list)

    # test 2
