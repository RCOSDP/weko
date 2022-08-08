from invenio_oaiserver.response import is_pubdate_in_future
import pytest
from datetime import datetime,timedelta,timezone
from flask_babelex import Babel

# def envelope(**kwargs):
# def error(errors, **kwargs):
# def verb(**kwargs):
# def identify(**kwargs):
# def resumption_token(parent, pagination, **kwargs):
# def listsets(**kwargs):
# def listmetadataformats(**kwargs):
# def header(parent, identifier, datestamp, sets=[], deleted=False):
# def extract_paths_from_sets(sets):
# def is_deleted_workflow(pid):
# def is_private_workflow(record):
# def is_pubdate_in_future(record):

def test_is_pubdate_in_future():
    from flask import Flask, session
    app = Flask('test')
    Babel(app)
    app.config['BABEL_DEFAULT_TIMEZONE']='Asia/Tokyo'
    with app.test_request_context():    
        # offset-naive
        now = datetime.utcnow()
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==False

        # offset-naive
        now = datetime.utcnow() + timedelta(days=1)
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==True

        # offset-naive
        now = datetime.utcnow() + timedelta(days=10)
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==True

                # offset-naive
        now = datetime.utcnow() - timedelta(days=1)
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==False

        # offset-naive
        now = datetime.utcnow() - timedelta(days=10)
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==False
    

# def is_private_index(record):
# def is_private_index_by_public_list(item_path, public_index_ids):
# def set_identifier(param_record, param_rec):
# def is_exists_doi(param_record):
# def getrecord(**kwargs):
# def listidentifiers(**kwargs):
# def listrecords(**kwargs):
# def get_error_code_msg(code=''):
# def create_identifier_index(root, **kwargs):
# def check_correct_system_props_mapping(object_uuid, system_mapping_config):
# def combine_record_file_urls(record, object_uuid, meta_prefix):
# def create_files_url(root_url, record_id, filename):
# def get_identifier(record):