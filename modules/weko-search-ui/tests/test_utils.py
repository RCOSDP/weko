# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp

import copy
import json
import os
import re
import tempfile
import time
import unittest
import uuid
import zipfile
from datetime import datetime, timedelta
import redis
import bagit
from io import StringIO

import pytest
from unittest.mock import MagicMock, patch, mock_open

from flask import current_app, make_response, request
from flask_login import current_user
from werkzeug.exceptions import BadRequest, NotFound
from elasticsearch import helpers, ElasticsearchException, NotFoundError
from elasticsearch_dsl import Search
from sqlalchemy.exc import SQLAlchemyError

from invenio_db import db as iv_db
from invenio_files_rest.models import FileInstance,Location
from invenio_i18n.babel import set_locale
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.errors import PIDDoesNotExistError

from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS
from weko_admin.api import TempDirInfo
from weko_deposit.api import WekoDeposit, WekoIndexer, WekoRecord as d_wekorecord
from weko_authors.models import AuthorsPrefixSettings, AuthorsAffiliationSettings
from weko_records.api import ItemsMetadata, JsonldMapping, WekoRecord
from weko_records.models import ItemType
from weko_redis.redis import RedisConnection
from weko_schema_ui.config import WEKO_SCHEMA_RELATION_TYPE
from weko_workflow.errors import WekoWorkflowException
from weko_workflow.headless.activity import HeadlessActivity
from weko_workflow.models import Activity, WorkFlow


from weko_search_ui.config import (
    ACCESS_RIGHT_TYPE_URI,
    RESOURCE_TYPE_URI,
    VERSION_TYPE_URI,
    WEKO_SEARCH_UI_BULK_EXPORT_URI,
    WEKO_SEARCH_UI_BULK_EXPORT_TASK,
)
from weko_search_ui.utils import (
    DefaultOrderedDict,
    cancel_export_all,
    check_jsonld_import_items,
    check_tsv_import_items,
    check_xml_import_items,
    check_index_access_permissions,
    check_permission,
    check_provide_in_system,
    check_sub_item_is_system,
    check_terms_in_system,
    clean_thumbnail_file,
    create_deposit,
    create_flow_define,
    create_work_flow,
    defaultify,
    define_default_dict,
    delete_exported_file,
    delete_exported,
    delete_items_with_activity,
    delete_task_id_cache_on_missing_meta,
    delete_records,
    execute_search_with_pagination,
    export_all,
    get_retry_info,
    generate_metadata_from_jpcoar,
    get_change_identifier_mode_content,
    get_content_workflow,
    get_current_language,
    get_data_by_property,
    get_data_in_deep_dict,
    get_doi_link,
    get_doi_prefix,
    get_export_status,
    get_file_name,
    get_filenames_from_metadata,
    get_item_type,
    get_journal_info,
    get_key_by_property,
    get_lifetime,
    get_list_key_of_iso_date,
    get_root_item_option,
    get_sub_item_option,
    get_system_data_uri,
    get_thumbnail_key,
    get_tree_items,
    getEncode,
    handle_check_and_prepare_feedback_mail,
    handle_check_and_prepare_request_mail,
    handle_check_and_prepare_item_application,
    check_exists_file_name,
    check_terms_in_system_for_item_application,
    handle_check_and_prepare_index_tree,
    handle_check_and_prepare_publish_status,
    handle_check_cnri,
    handle_check_consistence_with_mapping,
    handle_check_date,
    handle_check_doi,
    handle_check_doi_indexes,
    handle_check_doi_ra,
    handle_check_duplication_item_id,
    handle_check_duplicate_item_link,
    handle_check_duplicate_record,
    handle_check_exist_record,
    handle_check_file_content,
    handle_check_file_metadata,
    handle_check_file_path,
    handle_check_filename_consistence,
    handle_check_id,
    handle_check_item_is_locked,
    handle_check_item_link,
    handle_check_metadata_not_existed,
    handle_check_restricted_access_property,
    handle_check_thumbnail,
    handle_check_thumbnail_file_type,
    handle_check_authors_prefix,
    handle_check_authors_affiliation,
    handle_convert_validate_msg_to_jp,
    handle_metadata_amend_by_doi,
    handle_metadata_by_doi,
    handle_doi_required_check,
    handle_fill_system_item,
    handle_generate_key_path,
    handle_get_all_id_in_item_type,
    handle_get_all_sub_id_and_name,
    handle_item_title,
    handle_remove_es_metadata,
    handle_save_bagit,
    handle_set_change_identifier_flag,
    handle_shared_ids,
    handle_validate_item_import,
    handle_workflow,
    handle_flatten_data_encode_filename,
    handle_check_operation_flags,
    import_items_to_activity,
    import_items_to_system,
    make_file_by_line,
    make_file_info,
    make_stats_file,
    parse_to_json_form,
    prepare_doi_link,
    prepare_doi_setting,
    read_jpcoar_xml_file,
    read_stats_file,
    register_item_doi,
    register_item_handle,
    register_item_metadata,
    register_item_update_publish_status,
    represents_int,
    send_item_created_event_to_es,
    set_nested_item,
    unpackage_import_file,
    up_load_file,
    update_publish_status,
    validation_date_property,
    validation_file_open_date,
    write_files,
    combine_aggs,
    result_download_ui,
    search_results_to_tsv,
    create_tsv_row,
    get_priority,
    get_record_ids
)


from .helpers import json_data


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


class MockRecordsSearch:
    class MockQuery:
        class MockExecute:
            def __init__(self):
                pass

            def to_dict(self):
                raise NotFoundError

        def __init__(self):
            pass

        def execute(self):
            return self.MockExecute()

    def __init__(self, index=None):
        pass

    def update_from_dict(self, query=None):
        return self.MockQuery()


# class DefaultOrderedDict(OrderedDict):
def test_DefaultOrderDict_deepcopy():
    import copy

    data = {
        "key0": "value0",
        "key1": "value1",
        "key2": {"key2.0": "value2.0", "key2.1": "value2.1"},
    }
    dict1 = defaultify(data)
    dict2 = copy.deepcopy(dict1)

    for i, d in enumerate(dict2):
        if i in [0, 1]:
            assert d == "key" + str(i)
            assert dict2[d] == "value" + str(i)
        else:
            assert d == "key" + str(i)
            assert isinstance(dict2[d], DefaultOrderedDict)
            for s, dd in enumerate(dict2[d]):
                assert dd == "key{}.{}".format(i, s)
                assert dict2[d][dd] == "value{}.{}".format(i, s)

class MockSearchPerm:
    def __init__(self):
        pass

    def can(self):
        return True

def clear_test_data():
    Redirect.query.delete()
    iv_db.session.commit()

    PersistentIdentifier.query.delete()
    iv_db.session.commit()


# def execute_search_with_pagination(search_instance, get_all=False, size=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_execute_search_with_pagination -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_execute_search_with_pagination(i18n_app, indices, users, db_records, mocker, esindex):
    i18n_app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    i18n_app.config['OAISERVER_ES_MAX_CLAUSE_COUNT'] = 1
    i18n_app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS

    mocker.patch("weko_search_ui.query.search_permission",side_effect=MockSearchPerm)

    def _generate_es_data(num, start_datetime=datetime.now()):
        for i in range(num):
            doc = {
                "_index": i18n_app.config.get("INDEXER_DEFAULT_INDEX", "test-weko-item-v1.0.0"),
                "_type": "item-v1.0.0",
                "_id": f"2d1a2520-9080-437f-a304-230adc8{i:05d}",
                "_source": {
                    "_item_metadata": {
                        "title": [f"test_title_{i}"],
                    },
                    "relation_version_is_last": True,
                    "path": ["66"],
                    "control_number": f"{i:05d}",
                    "_created": (start_datetime + timedelta(seconds=i)).isoformat(),
                    "publish_status": "0",
                },
                "sort": i,
            }
            yield doc

    generate_data_num = 20005
    preset_records_num = len(db_records)
    expected_data_num = generate_data_num + preset_records_num + 3
    helpers.bulk(esindex, _generate_es_data(generate_data_num), refresh='true')
    i18n_app.config['RECORDS_REST_SORT_OPTIONS'] = {"test-weko":{"controlnumber":{"title":"ID","fields": ["control_number"],"default_order": "asc","order": 2}}}
    search = Search(using=esindex)
    search._sort.append( {"_created": {"order": "asc", "unmapped_type": "long"}})

    with i18n_app.test_request_context(query_string={"sort": "control_number", "q": "66"}):
        with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
            # max_result_size < 0
            assert len(execute_search_with_pagination(search, max_result_size=-1)) == expected_data_num
            # max_result_size   default
            assert len(execute_search_with_pagination(search)) == 10000
            # max_result_size = 1
            assert len(execute_search_with_pagination(search, max_result_size=1)) == 1
            # max_result_size = 15000
            assert len(execute_search_with_pagination(search, max_result_size=15000)) == 15000
            # max_result_size = 30000
            assert len(execute_search_with_pagination(search, max_result_size=30000)) == expected_data_num


# def execute_search_with_pagination(search_instance, get_all=False, size=None):
# def get_tree_items(index_tree_id): ERROR ~ AttributeError: '_AppCtxGlobals' object has no attribute 'identity'
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_get_tree_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_tree_items(i18n_app, indices, users, mocker, esindex):
    i18n_app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    i18n_app.config['OAISERVER_ES_MAX_CLAUSE_COUNT'] = 1
    i18n_app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS

    mocker.patch("weko_search_ui.query.search_permission",side_effect=MockSearchPerm)
    #search_instance = {"size": 1, "query": {"bool": {"filter": [{"bool": {"must": [{"match": {"publish_status": "0"}}, {"range": {"publish_date": {"lte": "now/d"}}}, {"terms": {"path": ["1031", "1029", "1025", "952", "953", "943", "940", "1017", "1015", "1011", "881", "893", "872", "869", "758", "753", "742", "530", "533", "502", "494", "710", "702", "691", "315", "351", "288", "281", "759", "754", "744", "531", "534", "503", "495", "711", "704", "692", "316", "352", "289", "282", "773", "771", "767", "538", "539", "519", "510", "756", "745", "733", "337", "377", "308", "299", "2063", "2061", "2057", "1984", "1985", "1975", "1972", "2049", "2047", "2043", "1913", "1925", "1904", "1901", "1790", "1785", "1774", "1562", "1565", "1534", "1526", "1742", "1734", "1723", "1347", "1383", "1320", "1313", "1791", "1786", "1776", "1563", "1566", "1535", "1527", "1743", "1736", "1724", "1348", "1384", "1321", "1314", "1805", "1803", "1799", "1570", "1571", "1551", "1542", "1788", "1777", "1765", "1369", "1409", "1340", "1331", "4127", "4125", "4121", "4048", "4049", "4039", "4036", "4113", "4111", "4107", "3977", "3989", "3968", "3965", "3854", "3849", "3838", "3626", "3629", "3598", "3590", "3806", "3798", "3787", "3411", "3447", "3384", "3377", "3855", "3850", "3840", "3627", "3630", "3599", "3591", "3807", "3800", "3788", "3412", "3448", "3385", "3378", "3869", "3867", "3863", "3634", "3635", "3615", "3606", "3852", "3841", "3829", "3433", "3473", "3404", "3395", "1631495207665", "1631495247023", "1631495289664", "1631495340640", "1631510190230", "1631510251689", "1631510324260", "1631510380602", "1631510415574", "1631511387362", "1631511432362", "1631511521954", "1631511525655", "1631511606115", "1631511735866", "1631511740808", "1631511841882", "1631511874428", "1631511843164", "1631511845163", "1631512253601", "1633380618401", "1638171727119", "1638171753803", "1634120530242", "1636010714174", "1636010749240", "1638512895916", "1638512971664"]}}, {"bool": {"must": [{"match": {"publish_status": "0"}}, {"match": {"relation_version_is_last": "true"}}]}}, {"bool": {"should": [{"nested": {"query": {"multi_match": {"query": "simple", "operator": "and", "fields": ["content.attachment.content"]}}, "path": "content"}}, {"query_string": {"query": "simple", "default_operator": "and", "fields": ["search_*", "search_*.ja"]}}]}}]}}], "must": [{"match_all": {}}]}}, "aggs": {"Data Language": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Data Language": {"terms": {"field": "language", "size": 1000}}}}, "Access": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Access": {"terms": {"field": "accessRights", "size": 1000}}}}, "Location": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Location": {"terms": {"field": "geoLocation.geoLocationPlace", "size": 1000}}}}, "Temporal": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Temporal": {"terms": {"field": "temporal", "size": 1000}}}}, "Topic": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Topic": {"terms": {"field": "subject.value", "size": 1000}}}}, "Distributor": {"filter": {"bool": {"must": [{"term": {"contributor.@attributes.contributorType": "Distributor"}}, {"term": {"publish_status": "0"}}]}}, "aggs": {"Distributor": {"terms": {"field": "contributor.contributorName", "size": 1000}}}}, "Data Type": {"filter": {"bool": {"must": [{"term": {"description.descriptionType": "Other"}}, {"term": {"publish_status": "0"}}]}}, "aggs": {"Data Type": {"terms": {"field": "description.value", "size": 1000}}}}}, "sort": [{"_id": {"order": "desc", "unmapped_type": "long"}}], "_source": {"excludes": ["content"]}}
    execute_result = {"hits":{"hits":{"hits_data":"data"}}}
    class MockRecordsSearch:
        class MockExecute:
            def __init__(self,data):
                self.data = data
            def to_dict(self):
                return self.data
        def __init__(self,data):
            self.data=data
        def extra(self,size):
            return self
        def execute(self):
            return self.MockExecute(self.data)
    def mock_search_factory(self, search,index_id=None):
        return MockRecordsSearch(execute_result),"test_data"
    with patch(
        "weko_search_ui.utils.item_path_search_factory", side_effect=mock_search_factory
    ):
        # with patch("weko_search_ui.query.item_path_search_factory", return_value="{'abc': 123}"):
        assert get_tree_items(33)

    def _generate_es_data(num, start_datetime=datetime.now()):
        for i in range(num):
            doc = {
                "_index": i18n_app.config.get("INDEXER_DEFAULT_INDEX", "test-weko-item-v1.0.0"),
                "_type": "item-v1.0.0",
                "_id": f"2d1a2520-9080-437f-a304-230adc8{i:05d}",
                "_source": {
                    "_item_metadata": {
                        "title": [f"test_title_{i}"],
                    },
                    "relation_version_is_last": True,
                    "path": ["66"],
                    "control_number": f"{i:05d}",
                    "_created": (start_datetime + timedelta(seconds=i)).isoformat(),
                    "publish_status": "0",
                },
            }
            yield doc

    generate_data_num = 20005
    helpers.bulk(esindex, _generate_es_data(generate_data_num), refresh='true')
    i18n_app.config['RECORDS_REST_SORT_OPTIONS'] = {"test-weko":{"controlnumber":{"title":"ID","fields": ["control_number"],"default_order": "asc","order": 2}}}

    with i18n_app.test_request_context(query_string={"sort": "control_number", "q": "66"}):
        with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
            # max_result_size < 0
            assert len(get_tree_items(66, max_result_size=-1)) == generate_data_num
            # max_result_size   default
            assert len(get_tree_items(66)) == 10000
            # max_result_size = 1
            assert len(get_tree_items(66, max_result_size=1)) == 1
            # max_result_size = 15000
            assert len(get_tree_items(66, max_result_size=15000)) == 15000
            # max_result_size = 30000
            assert len(get_tree_items(66, max_result_size=30000)) == generate_data_num


# def delete_records(index_tree_id, ignore_items):
def test_delete_records(i18n_app, db_activity):
    with open("tests/data/search_result_2.json", "r") as json_file:
        search_result = json.load(json_file)

        with patch("weko_search_ui.utils.get_tree_items", return_value=[search_result]):
            with patch(
                "invenio_records.api.Record.get_record",
                return_value=db_activity["record"],
            ):
                with patch(
                    "weko_deposit.api.WekoIndexer.update_es_data",
                    return_value=db_activity["record"],
                ):
                    with patch(
                        "weko_deposit.api.WekoDeposit.delete_by_index_tree_id",
                        return_value="",
                    ):
                        with patch(
                            "invenio_records.api.Record.delete", return_value=""
                        ):
                            assert delete_records(33, ignore_items=[])
                            assert delete_records(1, ignore_items=[])


# def get_journal_info(index_id=0):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_get_journal_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_journal_info(i18n_app, indices, client_request_args, mocker):
    journal = {"publisher_name": "key", "is_output": True, "title_url": "title"}

    with patch(
        "weko_indextree_journal.api.Journals.get_journal_by_index_id",
        return_value=journal,
    ):
        assert get_journal_info(33)

    assert not get_journal_info(0)

    with patch(
        "weko_indextree_journal.api.Journals.get_journal_by_index_id",
        return_value=journal,
    ):
        del journal["title_url"]
        mock_abort = mocker.patch("weko_search_ui.utils.abort",return_value=make_response())
        # Will result in an error for coverage of the except part
        assert get_journal_info(33)
        mock_abort.assert_called_with(500)

    with patch(
        "weko_indextree_journal.api.Journals.get_journal_by_index_id",
        return_value=None,
    ):
        assert get_journal_info(33) == None


# def check_permission():
def test_check_permission(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        assert check_permission()


# def get_content_workflow(item):
def test_get_content_workflow():
    item = MagicMock()

    item.flowname = "flowname"
    item.id = "id"
    item.flow_id = "flow_id"
    item.flow_define.flow_name = "flow_name"
    item.itemtype.item_type_name.name = "item_type_name"

    assert get_content_workflow(item)


# def set_nested_item(data_dict, map_list, val):
def test_set_nested_item(i18n_app):
    data_dict = {"1": {"a": "aa"}}
    map_list = ["test"]
    val = None

    assert set_nested_item(data_dict, map_list, val)


# def convert_nested_item_to_list(data_dict, map_list):
# def test_convert_nested_item_to_list(i18n_app):
#     data_dict = {'a': 'aa'}
#     map_list = [1,2,3,4]

#     assert convert_nested_item_to_list(data_dict, map_list)


# def define_default_dict(): *** not yet done
def test_define_default_dict(i18n_app):
    # Test 1
    assert not define_default_dict()


# def defaultify(d: dict) -> dict: *** not yet done
def test_defaultify():
    # Test 1
    assert not defaultify({})


# def handle_generate_key_path(key) -> list:
def test_handle_generate_key_path():
    assert handle_generate_key_path("key")


# def parse_to_json_form(data: list, item_path_not_existed=[], include_empty=False):
def test_parse_to_json_form(i18n_app, record_with_metadata):
    data = record_with_metadata[0].items()

    assert parse_to_json_form(data)


# def check_tsv_import_items(file, is_change_identifier: bool, is_gakuninrdm=False,
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_tsv_import_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_tsv_import_items(i18n_app):
    # test is_gakuninrdm = False
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_name = "sample_file.zip"
    file_path = os.path.join(current_path, "data", "sample_file", file_name)

    ret = check_tsv_import_items(file_path, True)
    prefix = current_app.config["WEKO_SEARCH_UI_IMPORT_TMP_PREFIX"]
    assert ret
    assert ret["data_path"].startswith(f'/var/tmp/{prefix}')

    # test case is_gakuninrdm = True
    ret = check_tsv_import_items(file_path, True, True)
    assert ret["data_path"].startswith('/var/tmp/deposit_activity_')

    # current_pathがdict
    class TestFile(object):
        @property
        def filename(self):
            return 'test_file.txt'

    file = TestFile()
    assert check_tsv_import_items(file, True, True)

    time.sleep(0.1)
    file_name = "sample_file.zip"
    file_path = os.path.join(current_path, "data", "sample_file", file_name)
    prefix = current_app.config["WEKO_SEARCH_UI_IMPORT_TMP_PREFIX"]

    with patch("weko_search_ui.utils.chardet.detect", return_value = {'encoding': 'cp932'}):
        ret = check_tsv_import_items(file_path, True)
        assert ret

    with patch("weko_search_ui.utils.chardet.detect", return_value = {'encoding': 'cp437'}):
        ret = check_tsv_import_items(file_path, True)
        assert ret

        with patch("weko_search_ui.utils.os") as o:
            type(o).sep = "_"
            ret = check_tsv_import_items(file_path, True)
            assert ret


@pytest.mark.parametrize('order_if', [1,2,3,4,5,6,7,8,9])
#def check_tsv_import_items(file, is_change_identifier: bool, is_gakuninrdm=False):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_tsv_import_items2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_tsv_import_items2(app,test_importdata,mocker,db, order_if):
    app.config['WEKO_SEARCH_UI_IMPORT_TMP_PREFIX'] = 'importtest'
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_map.json")
    print("")
    with open(filepath,encoding="utf-8") as f:
        item_map = json.load(f)

    mocker.patch("weko_records.serializers.utils.get_mapping",return_value=item_map)
    with app.test_request_context():
        with set_locale('en'):
            mocker.patch("weko_search_ui.utils.unpackage_import_file", return_value=[{"item_type_id":1}])
            mocker.patch("weko_search_ui.utils.handle_check_exist_record", return_value=[{"item_type_id":1}])
            mocker.patch("weko_search_ui.utils.handle_item_title")
            mocker.patch("weko_search_ui.utils.handle_check_date", return_value=[{"item_type_id":1}])
            mocker.patch("weko_search_ui.utils.handle_check_id")
            mocker.patch("weko_search_ui.utils.handle_check_and_prepare_index_tree")
            mocker.patch("weko_search_ui.utils.handle_check_and_prepare_publish_status")
            mocker.patch("weko_search_ui.utils.handle_check_and_prepare_feedback_mail")
            check_request_mail = mocker.patch("weko_search_ui.utils.handle_check_and_prepare_request_mail")
            mocker.patch("weko_search_ui.utils.handle_check_file_metadata")
            mocker.patch("weko_search_ui.utils.handle_check_cnri")
            mocker.patch("weko_search_ui.utils.handle_check_doi_indexes")
            mocker.patch("weko_search_ui.utils.handle_check_doi_ra")
            mocker.patch("weko_search_ui.utils.handle_check_doi")
            mocker.patch("weko_search_ui.utils.handle_check_authors_prefix")
            mocker.patch("weko_search_ui.utils.handle_check_authors_affiliation")

            for file in test_importdata:

                # for exception
                if order_if == 1:
                    with patch("weko_search_ui.utils.zipfile.ZipFile.infolist",return_value=[1,2]):
                        ret = check_tsv_import_items(file, False, False)

                # for badzipfile exception
                if order_if == 2:
                    with patch("weko_search_ui.utils.zipfile.ZipFile",side_effect=zipfile.BadZipFile):
                        ret = check_tsv_import_items(file, False, False)
                        assert ret["error"] == 'The format of the specified file import00.zip does not support import. Please specify one of the following formats: zip, tar, gztar, bztar, xztar.'

                # for FileNotFoundError
                if order_if == 3:
                    with patch("weko_search_ui.utils.list",return_value=None):
                        ret = check_tsv_import_items(file, False, False)
                        assert ret["error"]=='The csv/tsv file was not found in the specified file import00.zip. Check if the directory structure is correct.'

                # for UnicodeDecodeError
                if order_if == 4:
                    with patch("weko_search_ui.utils.zipfile.ZipFile",side_effect=UnicodeDecodeError("uni", b'\xe3\x81\xad\xe3\x81\x93',2,4,"cp932 cant decode")):
                        ret = check_tsv_import_items(file, False, False)

                # for error is ex.args
                if order_if == 5:
                    with patch("weko_search_ui.utils.zipfile.ZipFile",side_effect=Exception({"error_msg":"エラーメッセージ"})):
                        ret = check_tsv_import_items(file, False, False)

                # for tsv
                if order_if == 6:
                    with patch("weko_search_ui.utils.list",return_value=['items.tsv']):
                        ret = check_tsv_import_items(file,False,False)
                        assert "error" not in ret

                # for gakuninrdm is False
                if order_if == 7:
                    ret = check_tsv_import_items(file,False,False)
                    assert "error" not in ret
                # for gakuninrdm is True
                if order_if == 8:
                    ret = check_tsv_import_items(file,False,True)
                    assert "error" not in ret

                # for os.sep is not "/"
                if order_if == 9:
                    with patch("weko_search_ui.utils.os") as o:
                        with patch("weko_search_ui.utils.zipfile.ZipFile.infolist", return_value = [zipfile.ZipInfo(filename = filepath.replace("/","\\"))]):
                            type(o).sep = "\\"
                            ret = check_tsv_import_items(file,False,False)
                            assert ret["error"]

# def check_xml_import_items(file, item_type_id, is_gakuninrdm=False)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_xml_import_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_xml_import_items(i18n_app, db_itemtype_jpcoar):
    file_name = "sample_file_jpcoar_xml.zip"
    file_path = os.path.join('tests', "data", "jpcoar", "v2", file_name)

    item_type = db_itemtype_jpcoar["item_type_multiple"]

    # Case01: Call with file path as argument
    with i18n_app.test_request_context():
        result = check_xml_import_items(file_path, item_type.id)
        print(result["data_path"])
        assert re.fullmatch(r'^/var/tmp/weko_import_\d{17}', result['data_path']) is not None
        assert 'error' not in result
        assert 'list_record' in result

    # Case02: Call with if is_gakuninrdm = True
    with i18n_app.test_request_context():
        result = check_xml_import_items(file_path, item_type.id, is_gakuninrdm=True)
        assert re.fullmatch(r'^/var/tmp/deposit_activity_\d{17}', result['data_path']) is not None
        assert 'error' not in result
        assert 'list_record' in result

    # Case03: zip files is broken
    with i18n_app.test_request_context():
        broken_file_name = "sample_zip_broken.zip"
        broken_file_path = os.path.join('tests', "data", "jpcoar", "v2", broken_file_name)
        time.sleep(0.1)
        result = check_xml_import_items(broken_file_path, item_type.id)
        assert result["error"] == "The format of the specified file sample_zip_broken.zip does not support import." \
            " Please specify one of the following formats: zip, tar, gztar, bztar, xztar."

    # Case04: Xml files not included
    with i18n_app.test_request_context():
        zip_file_path = os.path.join('tests', "data", "helloworld.zip")
        time.sleep(0.1)
        result = check_xml_import_items(zip_file_path, item_type.id)
        assert result["error"] ==  "The xml file was not found in the specified file helloworld.zip." \
            " Check if the directory structure is correct."

    with i18n_app.test_request_context():
        failed_file_name = "no_jpcoar_xml_file.zip"
        failed_file_path = os.path.join('tests', "data", "jpcoar", "v2", failed_file_name)
        time.sleep(0.1)
        print("Case04")
        result = check_xml_import_items(failed_file_path, item_type.id)
        assert result["error"] ==  "The xml file was not found in the specified file no_jpcoar_xml_file.zip." \
            " Check if the directory structure is correct."


    # Case05: UnicodeDecodeError occured
    with i18n_app.test_request_context():
        with patch("weko_search_ui.utils.handle_check_file_metadata", side_effect=lambda x,y: "foo".encode('utf-16').decode('utf-8')):
            time.sleep(0.1)
            result = check_xml_import_items(file_path, item_type.id)
            assert result["error"] == "invalid start byte"

    # Case06: Other exception occured (without args)
    with i18n_app.test_request_context():
        with patch("weko_search_ui.utils.handle_check_file_metadata", side_effect=Exception()):
            time.sleep(0.1)
            result = check_xml_import_items(file_path, item_type.id)
            assert result["error"] == "Internal server error"

    # Case07: Other exception occured (with args)
    with i18n_app.test_request_context():
        with patch("weko_search_ui.utils.handle_check_file_metadata", side_effect=Exception({"error_msg": "error_msg_sample"})):
            time.sleep(0.1)
            result = check_xml_import_items(file_path, item_type.id)
            assert result["error"] == "error_msg_sample"

    # Case08: item_type is not found
    with i18n_app.test_request_context():
        result = check_xml_import_items(file_path, 9999)
        assert result["error"] == "The item type of the item to be imported is missing or has already been deleted."

    # Case09: item_type has been already deleted
    with i18n_app.test_request_context():
        item_type = MagicMock(spec=ItemType)
        item_type.is_deleted = True

        with patch("weko_search_ui.utils.ItemTypes.get_by_id", return_value=item_type):
            result = check_xml_import_items(file_path, 9999)
            assert result["error"] == "The item type of the item to be imported is missing or has already been deleted."


# def unpackage_import_file(data_path: str, file_name: str, file_format: str, force_new=False):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_unpackage_import_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_unpackage_import_file(app, db,mocker, mocker_itemtype):
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "item_map.json"
    )
    with open(filepath, encoding="utf-8") as f:
        item_map = json.load(f)
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "item_type_mapping.json"
    )
    with open(filepath, encoding="utf-8") as f:
        item_type_mapping = json.load(f)
    mocker.patch("weko_records.serializers.utils.get_mapping", return_value=item_map)
    mocker.patch("weko_records.api.Mapping.get_record", return_value=item_type_mapping)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "unpackage_import_file/result.json",
    )
    with open(filepath, encoding="utf-8") as f:
        result = json.load(f)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "unpackage_import_file/result_force_new.json",
    )
    with open(filepath, encoding="utf-8") as f:
        result_force_new = json.load(f)

    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "unpackage_import_file"
    )
    with app.test_request_context():
        with set_locale("en"):
            assert unpackage_import_file(path, "items.csv", "csv", False) == result
            assert (
                unpackage_import_file(path, "items.csv", "csv", True)
                == result_force_new
            )


# def generate_metadata_from_jpcoar(data_path: str, filenames: list, item_type_id: int, is_change_identifier=False)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_generate_metadata_from_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_generate_metadata_from_jpcoar(app, db_itemtype_jpcoar):
    item_type = db_itemtype_jpcoar['item_type_multiple']

    with app.test_request_context():
        # Case01: parse and mapping metadata success
        result = generate_metadata_from_jpcoar('tests/data/jpcoar/v2', ['test_base.xml'], item_type.id)
        for record in result:
            assert '$schema' in record
            assert 'metadata' in record
            assert record['item_type_name'] == item_type.item_type_name.name
            assert record['item_type_id'] == item_type.id
            assert record['errors'] is None
            assert record['is_change_identifier'] == False

        # Case02: schema validation error happend
        result = generate_metadata_from_jpcoar('tests/data/jpcoar/v2', ['test_base_failed.xml'], item_type.id)
        for record in result:
            assert len(record['errors']) > 0

        # Case03: item type not found
        with pytest.raises(Exception) as ex:
            result = generate_metadata_from_jpcoar('tests/data/jpcoar/v2', ['test_base.xml'], item_type.id+1)
        assert ex.value.args[0] == {
            "error_msg": "The item type ID specified in the XML file does not exist."
        }


# def check_jsonld_import_items(file, packaging, mapping_id, meta_data_api=None,shared_id=-1, validate_bagit=True, is_change_identifier=False):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_jsonld_import_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_jsonld_import_items(i18n_app, db, test_indices, item_type2, item_type_mapping2, ro_crate, mocker):
    schema = json_data("data/jsonld/item_type_schema_full.json")
    item_type2.model.schema = schema
    mapping = json_data("data/jsonld/item_type_mapping_full.json")
    item_type_mapping2.model.mapping = mapping
    db.session.commit()

    jsonld_mapping = json_data("data/jsonld/jsonld_mapping.json")
    obj = JsonldMapping.create(name="test_full", mapping=jsonld_mapping, item_type_id=item_type2.id)

    mocker.patch("weko_search_ui.utils.handle_metadata_amend_by_doi")
    mocker.patch("weko_search_ui.utils.handle_item_title")
    mocker.patch("weko_search_ui.utils.handle_check_doi_ra")
    mocker.patch("weko_search_ui.utils.handle_check_doi")
    mocker.patch("weko_search_ui.utils.handle_check_authors_prefix")
    mocker.patch("weko_search_ui.utils.handle_check_authors_affiliation")

    result = check_jsonld_import_items(ro_crate, "SimpleZip", obj.id, shared_id=-1)
    assert result["data_path"].startswith('/var/tmp/weko_import_')
    assert result["item_type_id"] == item_type2.id
    assert result["list_record"][0]["item_type_id"] == item_type2.id
    assert result["list_record"][0]["item_type_name"] == item_type2.model.item_type_name.name
    assert result["list_record"][0]["metadata"]
    assert result["list_record"][0].get("errors") is None
    assert result.get("error") is None

    with patch("weko_search_ui.utils.zipfile.ZipFile",side_effect=zipfile.BadZipFile):
        result = check_jsonld_import_items(ro_crate, "SimpleZip", obj.id, shared_id=-1)
        assert result["error"] == "The format of the specified file {filename} dose not support import. Please specify a zip file.".format(filename=os.path.basename(ro_crate))
        assert "data_path" not in result
        assert "item_type_id" not in result
        assert "list_record" not in result
        time.sleep(0.1)


    with patch("weko_search_ui.utils.zipfile.ZipFile",side_effect=UnicodeDecodeError("uni", b'\xe3\x81\xad\xe3\x81\x93',2,4,"cp932 cant decode")):
        result = check_jsonld_import_items(ro_crate, "SimpleZip", obj.id, shared_id=-1)
        assert result["error"] == "cp932 cant decode"
        assert "data_path" not in result
        assert "item_type_id" not in result
        assert "list_record" not in result
        time.sleep(0.1)

    with patch("weko_search_ui.utils.bagit.Bag.validate",side_effect=bagit.BagValidationError("Bag validation error")):
        result = check_jsonld_import_items(ro_crate, "SimpleZip", obj.id, shared_id=-1, validate_bagit=False)
        assert result["data_path"].startswith('/var/tmp/weko_import_')
        assert result["item_type_id"] == item_type2.id
        assert result["list_record"][0]["item_type_id"] == item_type2.id
        assert result["list_record"][0]["item_type_name"] == item_type2.model.item_type_name.name
        assert result["list_record"][0]["metadata"]
        assert result["list_record"][0].get("errors") is None
        assert result.get("error") is None

        result = check_jsonld_import_items(ro_crate, "SimpleZip", obj.id, shared_id=-1)
        assert result["error"] == "Bag validation error"

    from werkzeug.datastructures import FileStorage
    with open(ro_crate, "br") as f:
        file = FileStorage(
            stream=f, filename=os.path.basename(ro_crate), content_type="application/zip"
        )
        result = check_jsonld_import_items(file, "SimpleZip", obj.id, shared_id=-1)
        assert result["data_path"].startswith('/var/tmp/weko_import_')
        assert result["item_type_id"] == item_type2.id
        assert result["list_record"][0]["item_type_id"] == item_type2.id
        assert result["list_record"][0]["item_type_name"] == item_type2.model.item_type_name.name
        assert result["list_record"][0]["metadata"]
        assert result["list_record"][0].get("errors") is None
        assert result.get("error") is None

    with patch("weko_search_ui.utils.JsonLdMapper.validate", return_value=["something wrong"]):
        result = check_jsonld_import_items(ro_crate, "SimpleZip", obj.id, shared_id=-1)
        assert result["error"] == "Mapping is invalid for item type {}.".format(item_type2.model.item_type_name.name)

    JsonldMapping.delete(obj.id)
    result = check_jsonld_import_items(ro_crate, "SimpleZip", obj.id, shared_id=-1)
    assert result["error"] == "Metadata mapping not defined for registration your item."

    # print(f"result: {json.dumps(result, indent=2, ensure_ascii=False)}")


# def handle_shared_ids(list_record, shared_id=-1):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_shared_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_shared_ids():
    with open("tests/data/list_records/list_records.json", "r") as json_file:
        list_record = json.load(json_file)

    assert "weko_shared_ids" not in list_record[0]["metadata"]

    handle_shared_ids(list_record, shared_ids=["3"])
    assert "weko_shared_ids" not in list_record[0]["metadata"]

    handle_shared_ids(list_record)
    assert list_record[0]["metadata"]["weko_shared_ids"] == []

    handle_shared_ids(list_record, shared_ids=[3])
    assert list_record[0]["metadata"]["weko_shared_ids"] == [3]


# def handle_save_bagit(list_record, file, data_path, filename):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_save_bagit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_save_bagit(i18n_app, db_itemtype_jpcoar, tmpdir):

    tmp_dir = tmpdir.mkdir("test")
    # create file
    file_path = os.path.join(tmp_dir, "payload.zip")
    with open(file_path, "w") as f:
        f.write("This is a placeholder for payload.zip")
    data_path = tmpdir.mkdir("test／data")

    with open("tests/data/list_records/list_records.json", "r") as json_file:
        list_record = json.load(json_file)
    handle_save_bagit(list_record, file_path, data_path, "payload.zip")
    assert list_record[0]["metadata"]["item_1617605131499"][0]["filename"] == "1KB.pdf"

    list_record[0]["save_as_is"] = True
    list_record[0]["metadata"]["files_info"] = [{"key": "item_1617605131499"}]
    list_record2 = [list_record[0], list_record[0].copy()]
    handle_save_bagit(list_record2, file_path, data_path, "payload.zip")
    assert list_record2[0]["metadata"]["item_1617605131499"][0]["filename"] == "1KB.pdf"

    handle_save_bagit(list_record, file_path, data_path, "payload.zip")
    assert list_record[0]["metadata"]["item_1617605131499"][0]["filename"] == "payload.zip"
    assert os.path.exists(os.path.join(data_path, "payload.zip"))

    file_path = os.path.join(tmp_dir, "instance.zip")
    with open("tests/data/list_records/list_records.json", "r") as json_file:
        list_record = json.load(json_file)
    list_record[0]["save_as_is"] = True
    list_record[0]["metadata"]["files_info"] = [{"key": "item_1617605131499"}]

    from werkzeug.datastructures import FileStorage
    with open(file_path, "w") as f:
        f.write("This is a placeholder for instance.zip")
    with open(file_path, "br") as f:
        file = FileStorage(
            stream=f, filename="instance.zip", content_type="application/zip"
        )
        handle_save_bagit(list_record, file, data_path, "instance.zip")
    assert list_record[0]["metadata"]["item_1617605131499"][0]["filename"] == "instance.zip"


# def make_file_info(dir_path, filename, label=None, object_type=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_make_file_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_make_file_info(tmpdir):
    tmp_dir = tmpdir.mkdir("test")
    # create file
    file_path = os.path.join(tmp_dir, "payload.zip")
    with open(file_path, "w") as f:
        f.write("This is a placeholder for payload.zip")

    result = make_file_info(tmp_dir, "payload.zip")
    assert result["filename"] == "payload.zip"
    assert result["format"] == "application/zip"


# def getEncode(filepath):
def test_getEncode():
    csv_files = [
        {"file": "eucjp_lf_items.csv", "enc": "euc-jp"},
        {"file": "iso2022jp_lf_items.csv", "enc": "iso-2022-jp"},
        {"file": "sjis_lf_items.csv", "enc": "shift_jis"},
        {"file": "utf8_cr_items.csv", "enc": "utf-8"},
        {"file": "utf8_crlf_items.csv", "enc": "utf-8"},
        {"file": "utf8_lf_items.csv", "enc": "utf-8"},
        {"file": "utf8bom_lf_items.csv", "enc": "utf-8-sig"},
        {"file": "utf16be_bom_lf_items.csv", "enc": "utf-16"},
        {"file": "utf16le_bom_lf_items.csv", "enc": "utf-16"},
        # {"file":"utf32be_bom_lf_items.csv","enc":"utf-32"},
        # {"file":"utf32le_bom_lf_items.csv","enc":"utf-32"},
        {"file": "big5.txt", "enc": "tis-620"},
    ]

    for f in csv_files:
        filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "data", "csv", f["file"]
        )
        assert getEncode(filepath).lower() == f["enc"]


# def read_stats_file(file_path: str, file_name: str, file_format: str) -> dict:
def test_read_stats_file(i18n_app, db_itemtype, users):
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_name_tsv = "sample_tsv.tsv"
    file_path_tsv = os.path.join(current_path, "data", "sample_file", file_name_tsv)

    file_name_csv = "sample_csv.csv"
    file_path_csv = os.path.join(current_path, "data", "sample_file", file_name_csv)

    file_name_tsv_2 = "sample_tsv_2.tsv"
    file_path_tsv_2 = os.path.join(current_path, "data", "sample_file", file_name_tsv_2)

    check_item_type = {
        "schema": "test",
        "is_lastest": "test",
        "name": "test",
        "item_type_id": "test",
    }

    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        with patch("weko_search_ui.utils.get_item_type", return_value=check_item_type):
            assert read_stats_file(file_path_tsv, file_name_tsv, "tsv")
            assert read_stats_file(file_path_csv, file_name_csv, "csv")
            assert read_stats_file(file_path_tsv_2, file_name_tsv_2, "tsv")


# def read_jpcoar_xml_file(file_path, item_type_info) -> dict:
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_read_jpcoar_xml_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_read_jpcoar_xml_file(i18n_app, db_itemtype, users):
    xml_file_name = "test_base.xml"
    xml_file_path = os.path.join("tests", "data", "jpcoar", "v2", xml_file_name)

    item_type_info = {
        "schema": "/items/jsonschema/test",
        "is_lastest": "test",
        "name": "テストアイテムタイプ",
        "item_type_id": "test",
    }

    # Case01: read JPCOAR xml correctly
    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        result = read_jpcoar_xml_file(xml_file_path, item_type_info)
        assert 'metadata' in result['data_list'][0]
        metadata = result['data_list'][0].pop('metadata')
        assert result == {
            'error': False,
            'error_code': 0,
            'data_list': [
                {
                    "$schema": item_type_info['schema'],
                    "item_type_name": item_type_info['name'],
                    "item_type_id": item_type_info['item_type_id'],
                    "file_path": [],
                }
            ],
            'item_type_schema': item_type_info['schema']
        }

    # Case02: UnicodeDecodeError occured
    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        with patch("weko_search_ui.mapper.JPCOARV2Mapper.map", side_effect=lambda x: "foo".encode('utf-16').decode('utf-8')):
            try:
                result = read_jpcoar_xml_file(xml_file_path, item_type_info)
                pytest.fail()
            except UnicodeDecodeError as ex:
                assert ex.reason == "The XML file could not be read. Make sure the file format is XML and that the file is UTF-8 encoded."

    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        with patch("weko_search_ui.mapper.JPCOARV2Mapper.map", side_effect=Exception()):
            with pytest.raises(Exception) as ex:
                result = read_jpcoar_xml_file(xml_file_path, item_type_info)


# def handle_convert_validate_msg_to_jp(message: str):
def test_handle_convert_validate_msg_to_jp(i18n_app):
    message = ["%r is too long", "%r is not one of %r", "%r is a required property"]

    for msg in message:
        assert handle_convert_validate_msg_to_jp(msg)

    assert handle_convert_validate_msg_to_jp("msg")


# def handle_validate_item_import(list_record, schema) -> list:
def test_handle_validate_item_import(app, mocker_itemtype):
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "csv", "data.json"
    )
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "list_records.json",
    )
    with open(filepath, encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "list_records_result.json",
    )
    with open(filepath, encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        with set_locale("en"):
            assert (
                handle_validate_item_import(
                    list_record, data.get("item_type_schema", {})
                )
                == result
            )


# def represents_int(s):
def test_represents_int():
    assert represents_int("a") == False
    assert represents_int("30") == True
    assert represents_int("31.1") == False


# def get_item_type(item_type_id=0) -> dict:
def test_get_item_type(mocker_itemtype):
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "item_type/15_get_item_type_result.json",
    )
    with open(filepath, encoding="utf-8") as f:
        except_result = json.load(f)
    result = get_item_type(15)
    assert result["is_lastest"] == except_result["is_lastest"]
    assert result["name"] == except_result["name"]
    assert result["item_type_id"] == except_result["item_type_id"]
    assert result["schema"] == except_result["schema"]
    assert result == except_result

    assert get_item_type(0) == {}

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_duplicate_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
# def handle_check_duplicate_record(list_record):
def test_handle_check_duplicate_record(app):
    record = {"metadata": {"title": "Title 1"}}
    expect = {"metadata": {"title": "Title 1"}}
    with patch("weko_items_ui.utils.is_duplicate_item") as mock_is_duplicate:
        mock_is_duplicate.return_value = False, [], []
        handle_check_duplicate_record([record])
    assert mock_is_duplicate.call_count == 1
    assert record == expect

    record = {"id": "1", "metadata": {"title": "Title 1"}}
    expect = {"id": "1", "metadata": {"title": "Title 1"}}
    with patch("weko_items_ui.utils.is_duplicate_item") as mock_is_duplicate:
        mock_is_duplicate.return_value = False, [], []
        handle_check_duplicate_record([record])
    assert mock_is_duplicate.call_count == 1
    assert record == expect

    record = {"id": "invalid", "metadata": {"title": "Title 1"}}
    expect = {"id": "invalid", "metadata": {"title": "Title 1"}}
    with patch("weko_items_ui.utils.is_duplicate_item") as mock_is_duplicate:
        mock_is_duplicate.return_value = False, [], []
        handle_check_duplicate_record([record])
    assert mock_is_duplicate.call_count == 1
    assert record == expect

    link = "https://example.com/duplicate/1"
    record = {"metadata": {"title": "Title 1"}}
    expect = {"metadata": {"title": "Title 1"}, "warning": f'The same item may have been registered.<br><a href="{link}" target="_blank">{link}</a><br>'}
    with patch("weko_items_ui.utils.is_duplicate_item") as mock_is_duplicate:
        mock_is_duplicate.return_value = True, ["1"], [link]
        handle_check_duplicate_record([record])


# def handle_check_exist_record(list_record) -> list:
def test_handle_check_exist_record(app):
    case = unittest.TestCase()
    # case 1 import new items
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_exist_record.json",
    )
    with open(filepath, encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_exist_record_result.json",
    )
    with open(filepath, encoding="utf-8") as f:
        result = json.load(f)

    case.assertCountEqual(handle_check_exist_record(list_record), result)

    # case 2 import items with id
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_exist_record1.json",
    )
    with open(filepath, encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_exist_record_result1.json",
    )
    with open(filepath, encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        with set_locale("en"):
            case.assertCountEqual(handle_check_exist_record(list_record), result)

    # case 3 import items with id and uri
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_exist_record2.json",
    )
    with open(filepath, encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_exist_record_result2.json",
    )
    with open(filepath, encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        with set_locale("en"):
            with patch("weko_deposit.api.WekoRecord.get_record_by_pid") as m:
                m.return_value.pid.is_deleted.return_value = False
                m.return_value.get.side_effect = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                case.assertCountEqual(handle_check_exist_record(list_record), result)

    # case 4 import new items with doi_ra
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_exist_record3.json",
    )
    with open(filepath, encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_exist_record3_result.json",
    )
    with open(filepath, encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        with set_locale("en"):
            case.assertCountEqual(handle_check_exist_record(list_record), result)


# def make_file_by_line(lines):
def test_make_file_by_line(i18n_app):
    assert make_file_by_line("lines")


# def make_stats_file(raw_stats, list_name):
def test_make_stats_file(i18n_app):
    raw_stats = [
        {"a": 1},
        {"b": 2},
        {"c": 3},
    ]

    list_name = ["a", "b", "c"]

    assert make_stats_file(raw_stats, list_name)


# def create_deposit(item_id):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_create_deposit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_create_deposit(i18n_app, location, indices):
    assert create_deposit(None)['recid']=='1'
    assert create_deposit(33)['recid']=='33'


# def clean_thumbnail_file(deposit, root_path, thumbnail_path):
def test_clean_thumbnail_file(i18n_app, deposit):
    deposit = deposit
    root_path = "/"
    thumbnail_path = "/"

    # Doesn't return a value
    assert not clean_thumbnail_file(deposit, root_path, thumbnail_path)


# def up_load_file(record, root_path, deposit, allow_upload_file_content, old_files):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_up_load_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_up_load_file(i18n_app, deposit, db_activity):
    record = db_activity["record"]
    root_path = "/"
    deposit = deposit
    allow_upload_file_content = True
    old_files = {}

    # Doesn't return a value
    assert not up_load_file(
        record, root_path, deposit, old_files, allow_upload_file_content
    )


# def get_file_name(file_path):
def test_get_file_name(i18n_app):
    assert get_file_name("test/test/test")


# def register_item_metadata(item, root_path, is_gakuninrdm=False): ERROR ~ sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such function: concat
"""
Error file: invenio_files_rest/utils.py
Error function:
def find_and_update_location_size():
    ret = db.session.query(
        Location.id,
        sa.func.sum(FileInstance.size),
        Location.size
    ).filter(
        FileInstance.uri.like(sa.func.concat(Location.uri, '%'))
    ).group_by(Location.id)

    for row in ret:
        if row[1] != row[2]:
            with db.session.begin_nested():
                loc = db.session.query(Location).filter(
                    Location.id == row[0]).one()
                loc.size = row[1]
"""
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_register_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_register_item_metadata(i18n_app, es_item_file_pipeline, deposit, es_records, mocker):
    item = es_records["results"][0]["item"]
    root_path = os.path.dirname(os.path.abspath(__file__))

    mock_commit = mocker.patch('weko_deposit.api.WekoDeposit.commit', return_value=None)
    with patch("invenio_files_rest.utils.find_and_update_location_size"):
        assert register_item_metadata(item, root_path, -1, is_gakuninrdm=False)


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_register_item_metadata2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_register_item_metadata2(i18n_app, es_item_file_pipeline, deposit, es_records, db_index, es, db, mocker):
    item = es_records["results"][0]["item"]
    item["item_type_id"] = 1000
    item["$schema"] = "/items/jsonschema/1000"
    item["metadata"]["item_1617605131499"] = item["metadata"]["item_1617605131499"]["attribute_value_mlt"]
    root_path = os.path.dirname(os.path.abspath(__file__))

    with patch("weko_search_ui.utils.find_and_update_location_size"):
        with patch("weko_search_ui.utils.WekoDeposit.commit", return_value=None):
            with patch("weko_search_ui.utils.WekoDeposit.publish_without_commit", return_value=None):
                with patch("weko_search_ui.utils.RequestMailList.delete_without_commit") as delete_request_mail:
                        register_item_metadata(item, root_path, -1, is_gakuninrdm=False)
                        delete_request_mail.assert_called()

                item["metadata"]["request_mail_list"]=[{"email": "contributor@test.org", "author_id": ""}]
                item["metadata"]["feedback_mail_list"]=[{"email": "contributor@test.org", "author_id": ""}]
                with patch("weko_search_ui.utils.WekoDeposit.merge_data_to_record_without_version"):
                    with patch("weko_search_ui.utils.RequestMailList.update") as update_request_mail:
                        register_item_metadata(item, root_path, -1, is_gakuninrdm=False)
                        update_request_mail.assert_called()

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_register_item_metadata3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
# @pytest.mark.parametrize('order_if', [1,2])
@pytest.mark.parametrize('order_if', [1,2,3,4])
def test_register_item_metadata3(i18n_app, es_item_file_pipeline, deposit, es_records2, db_index, es, db, mocker, order_if):
    item = es_records2["results"][0]["item"]
    root_path = os.path.dirname(os.path.abspath(__file__))
    if order_if == 1:
        with patch("weko_search_ui.utils.find_and_update_location_size", return_value=None):
            with patch("weko_deposit.api.Indexes.get_path_list", return_value={"","",""}):
                with patch("weko_search_ui.utils.WekoDeposit.commit", return_value=None):
                    with patch("weko_search_ui.utils.WekoDeposit.publish_without_commit", return_value=None):
                        remove_request = mocker.patch("weko_search_ui.utils.WekoDeposit.remove_request_mail")
                        delete_item_application = mocker.patch("weko_search_ui.utils.ItemApplication.delete_without_commit")
                        register_item_metadata(item, root_path, item['owner'], is_gakuninrdm=False)
                        remove_request.assert_called()
                        delete_item_application.assert_called()

    item["metadata"]["request_mail_list"]={"email": "contributor@test.org", "author_id": ""}
    item["metadata"]["feedback_mail_list"]={"email": "contributor@test.org", "author_id": ""}
    item["item_application"]={"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"}
    item["status"]="keep"

    item["identifier_key"]="item_1617186331708"
    with patch("weko_search_ui.utils.find_and_update_location_size", return_value=None):
        with patch("weko_deposit.api.Indexes.get_path_list", return_value={"","",""}):
            with patch("weko_search_ui.utils.WekoDeposit.commit", return_value=None):
                with patch("weko_search_ui.utils.WekoDeposit.publish_without_commit", return_value=None):
                    mock_feedback_mail = mocker.patch('weko_search_ui.utils.FeedbackMailList.update')
                    if order_if == 2:
                        mocker.patch("weko_search_ui.utils.WekoDeposit.get_file_data", return_value=[{"version_id":"1.2"}])
                        item["pid"]=None
                        register_item_metadata(item, root_path, item['owner'], is_gakuninrdm=False)
                        mock_feedback_mail.assert_called()
                    if order_if == 3:
                        mocker.patch("weko_search_ui.utils.WekoDeposit.get_file_data", return_value=[{"version_id":None}])
                        register_item_metadata(item, root_path, item['owner'], is_gakuninrdm=False)
                        mock_feedback_mail.assert_called()
                    if order_if == 4:
                        mocker.patch("weko_search_ui.utils.WekoDeposit.update_feedback_mail")
                        update_request = mocker.patch("weko_search_ui.utils.WekoDeposit.update_request_mail")
                        update_item_application = mocker.patch("weko_search_ui.utils.ItemApplication.update")
                        mocker.patch("weko_search_ui.utils.WekoDeposit.newversion", return_value = WekoDeposit(0))
                        item["pid"]=None
                        item["status"]="new"
                        register_item_metadata(item, root_path, item['owner'], is_gakuninrdm=False)
                        update_request.assert_called()
                        update_item_application = mocker.patch("weko_search_ui.utils.ItemApplication.update")
                        mock_feedback_mail.assert_called()


# def update_publish_status(item_id, status):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_update_publish_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_update_publish_status(i18n_app, es_item_file_pipeline, es_records):
    item_id = 1
    status = None

    # Doesn't return a value
    assert not update_publish_status(item_id, status)


# def handle_workflow(item: dict):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_workflow(i18n_app, es_item_file_pipeline, es_records, db):
    item = es_records["results"][0]["item"]

    with patch(
        "weko_workflow.api.WorkActivity.get_workflow_activity_by_item_id",
        return_value=True,
    ):
        # Doesn't return any value
        assert not handle_workflow(item)

        item = {"id": "test", "item_type_id": 1}
        # Doesn't return any value
        assert not handle_workflow(item)

        item = {"id": "test", "item_type_id": 2}
        # Doesn't return any value
        assert not handle_workflow(item)


# def handle_metadata_by_doi(item: dict):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_metadata_by_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_metadata_by_doi():
    item = {"metadata": {"test": "test"}, "item_type_id": 1}
    doi = "test"
    meta_data_api = ["CrossRef", "DataCite", "Original"]
    fetched_metadata = {**item["metadata"], "fetched_metadata": "test"}
    with patch("weko_items_autofill.utils.fetch_metadata_by_doi", return_value=fetched_metadata):
        metadata = handle_metadata_by_doi(item, doi, meta_data_api)
        assert metadata == fetched_metadata

# def handle_metadata_amend_by_doi(list_record, meta_data_api):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_metadata_amend_by_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_metadata_amend_by_doi():
    metadata = {"test": "test"}
    item = {"metadata": {"test": "test"}, "item_type_id": 1, "amend_doi": "123.4567/test"}
    meta_data_api = ["CrossRef", "DataCite", "Original"]
    fetched_metadata = {**metadata, "fetched_metadata": "test"}
    with patch("weko_items_autofill.utils.fetch_metadata_by_doi", return_value=fetched_metadata):
        handle_metadata_amend_by_doi([item], meta_data_api)
        assert item["metadata"] == fetched_metadata

    item = {"metadata": {"test": "test"}, "item_type_id": 1, "amend_doi": ""}
    with patch("weko_items_autofill.utils.fetch_metadata_by_doi", return_value=fetched_metadata):
        handle_metadata_amend_by_doi([item], meta_data_api)
        assert item["metadata"] == metadata

# def create_work_flow(item_type_id):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_update_publish_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_create_work_flow(i18n_app, db_itemtype, db_workflow):
    # Doesn't return any value
    assert not create_work_flow(db_itemtype["item_type"].id)


# def create_flow_define():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_update_publish_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_create_flow_define(i18n_app, db_workflow):
    # Doesn't return anything
    assert not create_flow_define()


# def send_item_created_event_to_es(item, request_info): *** ERR
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_send_item_created_event_to_es -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_send_item_created_event_to_es(
    i18n_app, es_item_file_pipeline, es_records, client_request_args, users, es
):
    # with patch("weko_search_ui.utils.send_item_created_event_to_es._push_item_to_elasticsearch", return_value=""):
    # with patch("weko_search_ui.utils._push_item_to_elasticsearch", return_value=""):
    item = es_records["results"][0]["item"]
    request_info = {
        "remote_addr": request.remote_addr,
        "referrer": request.referrer,
        "hostname": request.host,
        "user_id": 1,
    }

    send_item_created_event_to_es(item, request_info)


# def import_items_to_system(item: dict, request_info=None, is_gakuninrdm=False): ERROR = TypeError: handle_remove_es_metadata() missing 2 required positional arguments: 'bef_metadata' and 'bef_las...
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_import_items_to_system -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_import_items_to_system(i18n_app, db, es_item_file_pipeline, es_records, app, mocker):
    item = es_records["results"][0]["item"]
    db.session.commit()
    with patch("weko_search_ui.utils.register_item_metadata", return_value={}):
        with patch("weko_search_ui.utils.register_item_doi", return_value={}):
            with patch(
                "weko_search_ui.utils.register_item_update_publish_status",
                return_value={},
            ):
                with patch(
                    "weko_search_ui.utils.create_deposit", return_value=item["id"]
                ):
                    with patch(
                        "weko_search_ui.utils.send_item_created_event_to_es",
                        return_value=item["id"],
                    ):
                        with patch(
                            "weko_workflow.utils.get_cache_data", return_value=["sample"]
                        ):
                            # with i18n_app.test_request_context():
                            with patch("weko_search_ui.utils.current_app") as c:

                                c.logger.error = MagicMock(return_value = None)

                                # SQLAlchemyError
                                with patch("weko_search_ui.utils.handle_check_item_is_locked", side_effect = SQLAlchemyError("SQLAlchemyError")):
                                    assert import_items_to_system(item).get("success") == False
                                with patch("weko_search_ui.utils.handle_check_item_is_locked", side_effect = SQLAlchemyError()):
                                    assert import_items_to_system(item).get("success") == False

                                # ElasticsearchException
                                with patch("weko_search_ui.utils.handle_check_item_is_locked", side_effect = ElasticsearchException({"error_id": "sample"})):
                                    assert import_items_to_system(item).get("success") == False
                                with patch("weko_search_ui.utils.handle_check_item_is_locked", side_effect = ElasticsearchException()):
                                    assert import_items_to_system(item).get("success") == False

                                # redis.RedisError
                                with patch("weko_search_ui.utils.handle_check_item_is_locked", side_effect = redis.RedisError({"error_id": "sample"})):
                                    assert import_items_to_system(item).get("success") == False
                                with patch("weko_search_ui.utils.handle_check_item_is_locked", side_effect = redis.RedisError()):
                                    assert import_items_to_system(item).get("success") == False

                                # BaseException
                                with patch("weko_search_ui.utils.handle_check_item_is_locked", side_effect = BaseException({"error_id": "sample"})):
                                    assert import_items_to_system(item).get("success") == False
                                with patch("weko_search_ui.utils.handle_check_item_is_locked", side_effect = BaseException()):
                                    assert import_items_to_system(item).get("success") == False

    with patch("weko_search_ui.utils.register_item_metadata", return_value={}):
        with patch("weko_search_ui.utils.register_item_doi", return_value={}):
            with patch(
                "weko_search_ui.utils.register_item_update_publish_status",
                return_value={},
            ):
                with patch(
                    "weko_search_ui.utils.create_deposit", return_value=item["id"]
                ):
                    with patch(
                        "weko_search_ui.utils.send_item_created_event_to_es",
                        return_value=item["id"],
                    ):
                         with patch(
                            "weko_search_ui.utils.get_cache_data", return_value=["sample"]
                        ):
                            request_info = {
                                "remote_addr": None,
                                "referrer": None,
                                "hostname": "TEST_SERVER",
                                "user_id": 1
                            }
                            assert not import_items_to_system(None, request_info = request_info)
                            with patch("invenio_files_rest.storage.pyfs.PyFSFileStorage._get_fs") as g:
                                g.return_value = (g, "sample")
                                g.exists = MagicMock(return_value = True)
                                g.delete = MagicMock(return_value = None)
                                assert import_items_to_system(item)
                            item["status"] = "new"

                            assert import_items_to_system(item).get("success") == False

                    assert import_items_to_system(
                        item
                    )

    item = es_records["results"][0]
    item['item']['researchmap_linkage'] = "researchmap"

    with patch("weko_search_ui.utils.register_item_metadata", return_value={}):
        with patch("weko_search_ui.utils.register_item_doi", return_value={}):
            with patch(
                "weko_search_ui.utils.register_item_update_publish_status",
                return_value={},
            ):
                with patch(
                    "weko_search_ui.utils.create_deposit", return_value=item["deposit"]
                ):
                    with patch(
                        "weko_search_ui.utils.send_item_created_event_to_es",
                        return_value=item["item"]["id"],
                    ):
                        with patch(
                            "weko_workflow.utils.get_cache_data", return_value=True
                        ):
                            with patch("weko_search_ui.utils.call_external_system") as mock_external:
                                item["item"]["status"] = "edited"
                                assert import_items_to_system(item["item"])
                                mock_external.assert_called()
                                assert mock_external.call_args[1]["old_record"] is not None
                                assert mock_external.call_args[1]["new_record"] is not None
                            with patch("weko_search_ui.utils.call_external_system") as mock_external:
                                item["item"]["status"] = "new"
                                assert import_items_to_system(item["item"],request_info=None, is_gakuninrdm=True)
                                assert mock_external.call_args[1]["old_record"] is None
                                assert mock_external.call_args[1]["new_record"] is not None
                                mock_external.assert_called()
                            with patch("weko_search_ui.utils.call_external_system") as mock_external:
                                app.config.update(WEKO_HANDLE_ALLOW_REGISTER_CNRI=None)
                                assert import_items_to_system(item["item"],request_info=None, is_gakuninrdm=True)
                                assert mock_external.call_args[1]["old_record"] is None
                                assert mock_external.call_args[1]["new_record"] is not None
                                mock_external.assert_called()

                    assert import_items_to_system(
                        item["item"]
                    )  # Will result in error but will cover exception part


# def import_items_to_activity(item, request_info):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_import_items_to_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_import_items_to_activity(i18n_app, es_item_file_pipeline, es_records, db_workflow, mocker):
    mock_auto = mocker.patch("weko_workflow.headless.HeadlessActivity.auto", return_value=("test/A-TEST-1", "end_action", "2000001"))

    item = es_records["results"][0]["item"]
    item["id"] = "2000001"
    item["root_path"] = tempfile.gettempdir()
    item["file_path"] = ["hello.txt"]
    item["comment"] = "test comment"
    item["non_extract"] = ["hello.txt"]

    request_info = {
        "workflow_id": 1,
        "user_id": 1,
    }
    url, recid, action, error = import_items_to_activity(item, request_info)
    mock_auto.assert_called_once_with(
        user_id=request_info["user_id"],
        workflow_id=request_info["workflow_id"],
        item_id=item["id"],
        index=item["metadata"]["path"],
        metadata=item["metadata"],
        files=[tempfile.gettempdir()+"/hello.txt"],
        comment="test comment",
        link_data=None, grant_data=None,
        non_extract=["hello.txt"]
    )
    assert url == "test/A-TEST-1"
    assert recid == "2000001"
    assert action == "end_action"
    assert error == None

    mock_auto.reset_mock()
    mock_auto.side_effect = WekoWorkflowException("test error")

    mock_activity = MagicMock(spec=Activity)
    mock_activity.activity_id = "A-TEST-2"
    mock_activity.activity_community_id = "com"
    mock_headless = MagicMock(spec=HeadlessActivity)
    mock_headless._model = mock_activity
    mock_headless.current_action = "item_login"
    mock_headless.recid = "2000001"
    mock_headless.auto = mock_auto
    mocker.patch("weko_workflow.headless.HeadlessActivity.__new__", return_value=mock_headless)
    mocker.patch("weko_workflow.headless.HeadlessActivity", return_value=mock_headless)

    with i18n_app.test_request_context():
        url, recid, action, error = import_items_to_activity(item, request_info)
    assert url.endswith("A-TEST-2")
    assert recid == "2000001"
    assert action == "item_login"
    assert error == "test error"


# def delete_items_with_activity(item_id, request_info):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_delete_items_with_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_delete_items_with_activity(i18n_app, es_item_file_pipeline, es_records, db_workflow, mocker):
    request_info = {
        "user_id": 1,
        "shared_id": -1,
        "community": "test_community",
    }

    with patch("weko_workflow.headless.HeadlessActivity.init_activity") as mock_init_activity:
        mock_init_activity.side_effect = WekoWorkflowException("test error")

        with pytest.raises(WekoWorkflowException) as exc_info:
            delete_items_with_activity("2000001", request_info)
        assert str(exc_info.value) == "test error"

    with patch("weko_workflow.headless.HeadlessActivity.init_activity") as mock_init_activity:
        mock_init_activity.return_value = "https://TEST_SEVER/activity/A-TEST-1"

        mock_activity = MagicMock()
        mock_activity.activity_id = "A-TEST-1"
        mock_activity.activity_community_id = "com"
        mock_headless = MagicMock()
        mock_headless._model = mock_activity
        mock_headless.current_action = "end_action"
        mock_headless.recid = "2000001"
        mock_headless.init_activity = mock_init_activity
        mocker.patch("weko_workflow.headless.HeadlessActivity.__new__", return_value=mock_headless)
        mocker.patch("weko_workflow.headless.HeadlessActivity.__init__")

        url, action = delete_items_with_activity("2000001", request_info)
        assert url == mock_init_activity.return_value
        assert action == "end_action"
        mock_init_activity.assert_called_once_with(
            user_id=request_info["user_id"], community=request_info["community"], item_id="2000001",
            shared_id=request_info["shared_id"], for_delete=True
        )


# def handle_item_title(list_record):
def test_handle_item_title(i18n_app, es_item_file_pipeline, es_records):
    list_record = [es_records["results"][0]["item"]]

    # Doesn't return any value
    assert not handle_item_title(list_record)


# def handle_check_and_prepare_publish_status(list_record):
def test_handle_check_and_prepare_publish_status(i18n_app):
    record = {"publish_status": False}

    # Doesn't return any value
    assert not handle_check_and_prepare_publish_status([record])

    record["publish_status"] = "test"

    # Doesn't return any value
    assert not handle_check_and_prepare_publish_status([record])


# def handle_check_and_prepare_index_tree(list_record, all_index_permission, can_edit_indexes): *** not yet done
def test_handle_check_and_prepare_index_tree(i18n_app, record_with_metadata, indices):
    list_record = [record_with_metadata[0]]
    can_edit_indexes = [indices["index_dict"]]
    item_2 = record_with_metadata[0]

    all_index_permission = False
    assert not handle_check_and_prepare_index_tree(
        list_record, all_index_permission, can_edit_indexes
    )

    index = MagicMock()
    index.index_name = "test"
    index.index_name_english = "eng_test"
    with patch("weko_index_tree.api.Indexes.get_index", return_value=index):
        assert not handle_check_and_prepare_index_tree(
            [item_2], all_index_permission, can_edit_indexes
        )

    del item_2["metadata"]
    del item_2["pos_index"]
    assert not handle_check_and_prepare_index_tree(
        [item_2], all_index_permission, can_edit_indexes
    )

    all_index_permission = True
    assert not handle_check_and_prepare_index_tree(
        list_record, all_index_permission, can_edit_indexes
    )


# def handle_check_and_prepare_index_tree(list_record, all_index_permission, can_edit_indexes):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_and_prepare_index_tree2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_and_prepare_index_tree2(i18n_app, record_with_metadata, indices2):
    i18n_app.config["WEKO_ITEMS_UI_INDEX_PATH_SPLIT"] = "///"
    list_record = [record_with_metadata[0]]

    list_record[0]["metadata"]["path"] = []
    list_record[0]["pos_index"] = ["A///C"]
    all_index_permission = False
    handle_check_and_prepare_index_tree(
        list_record, all_index_permission, None
    )
    assert list_record[0]["metadata"]["path"] == []

    list_record[0]["metadata"]["path"] = []
    handle_check_and_prepare_index_tree(
        list_record, all_index_permission, [4]
    )
    assert list_record[0]["metadata"]["path"] == []

    list_record[0]["metadata"]["path"] = []
    handle_check_and_prepare_index_tree(
        list_record, all_index_permission, [2]
    )
    assert list_record[0]["metadata"]["path"] == [2]


# def handle_check_and_prepare_feedback_mail(list_record):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_and_prepare_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_and_prepare_feedback_mail(i18n_app, record_with_metadata, es_authors_index):
    i18n_app.config["WEKO_AUTHORS_ES_INDEX_NAME"] = "test-authors"
    list_record = [record_with_metadata[0]]

    # Doesn't return any value
    assert not handle_check_and_prepare_feedback_mail(list_record)

    record = {
        "feedback_mail": ["wekosoftware@test.com"],
        "metadata": {"feedback_mail_list": ""},
    }

    # Doesn't return any value
    assert not handle_check_and_prepare_feedback_mail([record])

    record["feedback_mail"] = ["test"]

    # Doesn't return any value
    assert not handle_check_and_prepare_feedback_mail([record])

# def handle_check_and_prepare_request_mail(list_record):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_and_prepare_request_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_and_prepare_request_mail(i18n_app, record_with_metadata, es_authors_index):
    i18n_app.config["WEKO_AUTHORS_ES_INDEX_NAME"] = "test-authors"
    list_record = [record_with_metadata[0]]

    # Doesn't return any value
    assert not handle_check_and_prepare_request_mail(list_record)

    record = {
        "request_mail": ["wekosoftware@test.com"],
        "metadata": {"request_mail_list": ""},
    }

    # Doesn't return any value
    assert not handle_check_and_prepare_request_mail([record])
    assert record["metadata"]["request_mail_list"] == [{'email': 'wekosoftware@test.com', 'author_id': ''}]

    record["request_mail"] = ["test"]

    # Doesn't return any value
    assert not handle_check_and_prepare_request_mail([record])
    assert record["errors"] == ['指定されたtestは不正です。']

# def handle_check_and_prepare_item_application(list_record):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_and_prepare_item_application -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_and_prepare_item_application(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[0]]

    # Doesn't return any value
    assert not handle_check_and_prepare_item_application(list_record)

    # 正常系
    workflow = WorkFlow(id=1)
    with patch("weko_search_ui.utils.WorkFlowApi.get_workflow_list", return_value=[workflow]):
        record = {"metadata":{}, "item_application":{"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"}}
        handle_check_and_prepare_item_application([record])
        assert record["metadata"]["item_application"] == {"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"}

    # 正常系 item_applicationのworkflowが存在しない
    workflow = WorkFlow(id=1)
    with patch("weko_search_ui.utils.WorkFlowApi.get_workflow_list", return_value=[workflow]):
        record = {"metadata":{}, "item_application":{"terms":"term_free", "termsDescription":"利用規約自由入力"}}
        handle_check_and_prepare_item_application([record])
        assert not record["metadata"].get("item_application", "")

    # 正常系 item_applicationのtermsが存在しない。
    workflow = WorkFlow(id=1)
    with patch("weko_search_ui.utils.WorkFlowApi.get_workflow_list", return_value=[workflow]):
        record = {"metadata":{}, "item_application":{"workflow":"1", "termsDescription":"利用規約自由入力"}}
        handle_check_and_prepare_item_application([record])
        assert not record["metadata"].get("item_application", "")

    # 異常系 ファイル情報を持っている。
    record = {"metadata":{}, "file_path":"/recid15/test.txt", "item_application":{"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"}}
    handle_check_and_prepare_item_application([record])
    assert record["errors"][0] == "If there is a info of content file, terms of use cannot be set."

    # 異常系 workflowが文字列である。
    workflow = WorkFlow(id=1)
    with patch("weko_search_ui.utils.WorkFlowApi.get_workflow_list", return_value=[workflow]):
        record = {"metadata":{}, "item_application":{"workflow":"not_exist", "terms":"term_free", "termsDescription":"利用規約自由入力"}}
        handle_check_and_prepare_item_application([record])
        assert record["errors"][0] == "指定する提供方法はシステムに存在しません。"

    # 異常系 workflowがシステムに存在しないworkflowである。
    workflow = WorkFlow(id=1)
    with patch("weko_search_ui.utils.WorkFlowApi.get_workflow_list", return_value=[workflow]):
        record = {"metadata":{}, "item_application":{"workflow":"999999999999", "terms":"term_free", "termsDescription":"利用規約自由入力"}}
        handle_check_and_prepare_item_application([record])
        assert record["errors"][0] == "指定する提供方法はシステムに存在しません。"

    # 異常系 termsが存在しないtermsである。
    with patch("weko_search_ui.utils.WorkFlowApi.get_workflow_list", return_value=[workflow]):
        record = {"metadata":{}, "item_application":{"workflow":"1", "terms":"not_exist", "termsDescription":"利用規約自由入力"}}
        handle_check_and_prepare_item_application([record])
        assert record["errors"][0] == "指定する利用規約はシステムに存在しません。"


# def check_exists_file_name(item):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_exists_file_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_exists_file_name(i18n_app, record_with_metadata):
    item = record_with_metadata[0]
    # *.filenameに値が存在する。
    assert check_exists_file_name(item)

    # *.filenameに値が存在しない。
    item = {"metadata":{"filename_test":[{"filename":""}]}}
    assert not check_exists_file_name(item)

# def check_terms_in_system_for_item_application(terms):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_terms_in_system_for_item_application -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_terms_in_system_for_item_application():
    terms_list = [{"key":"1234567890", "content":{"en":{},"ja":{}}}]
    with patch("weko_search_ui.utils.get_restricted_access", return_value=terms_list):
        # temrsが空文字
        assert check_terms_in_system_for_item_application("")

        # termsが自由入力
        assert check_terms_in_system_for_item_application("term_free")

        # termsが存在するkey
        assert check_terms_in_system_for_item_application("1234567890")

        # termsが存在しないkey
        assert not check_terms_in_system_for_item_application("not_exists")

    # get_restricted_accessがNoneを返す場合
    with patch("weko_search_ui.utils.get_restricted_access", return_value=None):
        assert not check_terms_in_system_for_item_application("1234567890")

# def handle_set_change_identifier_flag(list_record, is_change_identifier):
def test_handle_set_change_identifier_flag(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[0]]
    is_change_identifier = True

    # Doesn't return any value
    assert not handle_set_change_identifier_flag(list_record, is_change_identifier)


# def handle_check_cnri(list_record):
def test_handle_check_cnri(i18n_app):
    item = MagicMock()
    # item = {
    #     "id": 1,
    #     "cnri": None,
    #     "is_change_identifier": True
    # }
    # Doesn't return any value
    assert not handle_check_cnri([item])


def test_handle_check_cnri_2(i18n_app):
    # item["cnri"] =
    # item["is_change_identifier"] = False
    item2 = {"id": 1, "cnri": f"{'x'*200}/{'y'*100}", "is_change_identifier": False}
    # Doesn't return any value
    assert not handle_check_cnri([item2])


# def handle_check_doi_indexes(list_record):
def test_handle_check_doi_indexes(i18n_app, es_item_file_pipeline, es_records):
    list_record = [es_records["results"][0]["item"]]

    # Doesn't return any value
    assert not handle_check_doi_indexes(list_record)


# def handle_check_doi_ra(list_record):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_doi_ra -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_doi_ra(i18n_app, db,es_item_file_pipeline, es_records,identifier):
    # list_record = [es_records['results'][0]['item']]
    item = MagicMock()

    # Doesn't return any value
    assert not handle_check_doi_ra([item])

    item = {"doi_ra": "JaLC", "is_change_identifier": False, "status": "keep"}

    with patch("weko_search_ui.utils.handle_doi_required_check", return_value="1"):
        with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value="1"):
            # Doesn't return any value
            assert not handle_check_doi_ra([item])

    def create_record_with_doi(recid, doi_type, doi_value=""):
        """create item with doi"""
        from tests.helpers import create_record
        doi_prefix = identifier["Root Index"].get(doi_type,"")
        if not doi_value:
            doi_value = "{prefix}/{suffix}".format(
                prefix=doi_prefix,
                suffix="{:010}".format(recid)
            )
        record_tmp = {"_oai": {"id": "oai:weko3.example.org:{:08}".format(recid), "sets": ["1"]}, "path": ["1"], "owner": "1", "recid": str(recid), "title": [f"record_with_doi: {recid}"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-20"}, "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"}, "_deposit": {"id": str(recid), "pid": {"type": "depid", "value": str(recid), "revision_id": 0}, "owner": "1", "owners": [1], "status": "draft", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}}, "item_title": f"record_with_doi: {recid}", "author_link": [], "item_type_id": "1", "publish_date": "2022-08-20", "publish_status": "0", "weko_shared_id": -1, "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": f"record_with_doi: {recid}", "subitem_1551255648112": "ja"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}]}, "item_1617186819068":{"attribute_name":"","attribute_value_mlt":[{"subitem_identifier_reg_text":doi_value,"subitem_identifier_reg_type":doi_type}]},"relation_version_is_last": True}
        item_tmp = {"id": str(recid), "pid": {"type": "depid", "value": str(recid), "revision_id": 0}, "lang": "ja", "owner": "1", "title": f"record_with_doi: {recid}", "owners": [1], "status": "published", "$schema": "/items/jsonschema/1", "pubdate": "2022-08-20", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}, "shared_user_id": -1, "item_1617186331708": [{"subitem_1551255647225": f"record_with_doi: {recid}", "subitem_1551255648112": "ja"}], "item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"},"item_1617186819068":[{"subitem_identifier_reg_text":doi_value,"subitem_identifier_reg_type":doi_type}]}
        _,pid_recid,_,_,_,_ = create_record(record_tmp, item_tmp)
        doi = PersistentIdentifier.query.filter_by(pid_type="doi",pid_value="https://doi.org/10.xyz/{:010}".format(recid)).one_or_none()
        doi_url = f"https://doi.org/{doi_value}"
        if doi:
            doi.pid_value = doi_url
            db.session.merge(doi)
        else:
            doi = PersistentIdentifier.create("doi",doi_url,object_type="rec",object_uuid=pid_recid.object_uuid,status=PIDStatus.REGISTERED)
            db.session.add(doi)
        db.session.commit()

    create_record_with_doi(10, "JaLC") # JaLC DOI
    create_record_with_doi(11, "Crossref") # Crossref
    create_record_with_doi(12, "DataCite") # DataCite
    create_record_with_doi(13, "NDL JaLC") # NDL JaLC
    create_record_with_doi(14, "JaLC","xyz.jalc/0000000014") # JaLC, NDL JaLC prefix

    item = [
        {"errors":[],"doi":"xyz.jalc/0000000010"}, # exist doi, not exist doi_ra
        {"errors":[],"doi":"xyz.jalc/0000000010", "doi_ra":"wrong doi"},# wrong doi_ra
        {"errors":[],"id":"10","doi":"xyz.jalc/000000010", "doi_ra":"JaLC","is_change_identifier":False,"status":"keep"}, # exist doi, exist doi_ra
        {"errors":[],"id":"10","doi":"xyz.crossref/000000010", "doi_ra":"Crossref","is_change_identifier":False,"status":"keep"}, # exist doi, exist doi_ra
        {"errors":[],"id":"14","doi":"xyz.ndl/0000000014", "doi_ra":"NDL LaLC","is_change_identifier":False,"status":"keep"}, # exist doi, exist doi_ra
    ]

    test = [
        {"errors":["Please specify DOI_RA."],"doi":"xyz.jalc/0000000010"}, # exist doi, not exist doi_ra
        {"errors":["DOI_RA should be set by on of JaLC, Crossref, DataCite, NDL JaLC"],"doi":"xyz.jalc/0000000010", "doi_ra":"wrong doi"},# wrong doi_ra
        {"errors":["Specified DOI_RA is different from existing DOI_RA"],"id":"10","doi":"xyz.jalc/000000010", "doi_ra":"JaLC","is_change_identifier":False,"status":"keep"}, # exist doi, exist doi_ra
        {"errors":[],"id":"10","doi":"xyz.crossref/000000010", "doi_ra":"Crossref","is_change_identifier":False,"status":"keep"}, # exist doi, exist doi_ra
        {"errors":[],"id":"14","doi":"xyz.ndl/0000000014", "doi_ra":"NDL LaLC","is_change_identifier":False,"status":"keep"}, # exist doi, exist doi_ra
    ]
    with patch("weko_search_ui.utils.handle_doi_required_check",return_value=False):
        handle_check_doi_ra(item)
        assert item == test


# def handle_check_doi(list_record):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_doi(app,identifier):
    list_record = json_data("data/list_records/list_records.json")
    assert handle_check_doi(list_record) == None

    # case new items with doi_ra
    list_record = json_data("data/list_records/b4_handle_check_doi.json")
    assert handle_check_doi(list_record) == None

    # item status is not new
    # change identifier mode on, but not specified DOI
    item = {"id": "1", "status": "Keep", "doi": "", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item , "errors":["Please specify DOI."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode on, but specified DOI exceeds the maximum length
    item = {"id": "2", "status": "Keep", "doi": "a"*300, "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item , "errors":["The specified DOI exceeds the maximum length."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode on, but specified DOI prefix is incorrect
    item = {"id": "3", "status": "Keep", "doi": "wrong_prefix/", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item , "errors":["Specified Prefix of DOI is incorrect."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode on, but specified DOI suffix is not specified
    item = {"id": "4", "status": "Keep", "doi": "xyz.jalc/", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item , "errors":["Please specify DOI suffix."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode on, but suffix of DOI is empty
    item = {"id": "4", "status": "Keep", "doi": "xyz.jalc", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item , "errors":["Please specify DOI suffix."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode on, specified DOI is correct
    item = {"id": "5", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_doi = MagicMock()
    mock_doi.status = PIDStatus.REGISTERED
    mock_doi.object_uuid = mock_record.pid_recid.object_uuid
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.check_pidstore_exist", return_value=mock_doi):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode on, but specified DOI is used already
    item = {"id": "6", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item, "errors": ["Specified DOI has been used already for another item. Please specify another DOI."]}
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_doi = MagicMock()
    mock_doi.status = PIDStatus.REGISTERED
    mock_doi.object_uuid = uuid.uuid4()
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.check_pidstore_exist", return_value=mock_doi):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode on, but specified DOI already withdrawn
    item = {"id": "7", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item, "errors": ["Specified DOI was withdrawn. Please specify another DOI."]}
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_doi = MagicMock()
    mock_doi.status = PIDStatus.DELETED
    mock_doi.object_uuid = mock_record.pid_recid.object_uuid
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.check_pidstore_exist", return_value=mock_doi):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode on, but specified DOI is used already and SQLAlchemyError
    item = {"id": "x", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item, "errors": ["Specified DOI has been used already for another item. Please specify another DOI."] }
    mock_doi = MagicMock()
    mock_doi.status = PIDStatus.REGISTERED
    mock_doi.object_uuid = mock_record.pid_recid.object_uuid
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", side_effect=SQLAlchemyError()), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.check_pidstore_exist", return_value=mock_doi):
        handle_check_doi([item])
    assert item == expect

    # item status is new
    item = {"status":"new", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True}
    expect = { **item, "errors": ["Specified DOI has been used already for another item. Please specify another DOI."]}
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_doi = MagicMock()
    mock_doi.status = PIDStatus.REGISTERED
    mock_doi.object_uuid = uuid.uuid4()
    with patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.check_pidstore_exist", return_value=mock_doi):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode off, but specified doi
    item = {"status": "new", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item, "errors": ["DOI cannot be set."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode off, but specified DOI prefix is incorrect
    item = {"status": "new", "doi": "wrong_prefix/", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item, "doi_suffix_not_existed": True, "errors": ["Specified Prefix of DOI is incorrect."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode off, but specified DOI prefix is incorrect and ignore_check_doi_prefix is True
    item = {"status": "new", "doi": "wrong_prefix/", "doi_ra": "JaLC", "is_change_identifier": False, "ignore_check_doi_prefix": True}
    expect = { **item, "doi_suffix_not_existed": True}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode off, but specified DOI suffix is empty
    item = {"status": "new", "doi": "xyz.jalc/", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item, "doi_suffix_not_existed": True, }
    handle_check_doi([item])
    assert item == expect

    # change identifier mode off, only RA is specified
    item = {"status": "new", "doi": "", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item }
    handle_check_doi([item])
    assert item == expect

    # change identifier mode off, but specified DOI suffix is empty, RA is NDL JaLC
    item = {"status": "new", "doi": "xyz.ndl", "doi_ra": "NDL JaLC", "is_change_identifier": False}
    expect = { **item, "errors": ["DOI cannot be set."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode off, but specified DOI prefix is incorrect
    item = {"status": "new", "doi": "wrong_prefix/12345", "doi_ra": "NDL JaLC", "is_change_identifier": False}
    expect = { **item, "errors": ["Specified Prefix of DOI is incorrect."]}
    handle_check_doi([item])
    assert item == expect

    # change identifier mode off
    # any valid DOI specified by the user can be registered if NDL JaLC is selected
    item = {"status": "new", "doi": "xyz.ndl/12345", "doi_ra": "NDL JaLC", "is_change_identifier": False}
    expect = { **item }
    handle_check_doi([item])
    assert item == expect

    # change identifier mode off, item status is not new, no DOI registered, only specified RA
    item = {"id": "8", "status": "Keep", "doi": "", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_record.pid_doi = None
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.get_idt_registration_data", return_value=(None, None)):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode off, item status is not new, no DOI registered but specified doi
    item = {"id": "8", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item, "errors": ["DOI cannot be set."] }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_record.pid_doi = None
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.get_idt_registration_data", return_value=(None, None)):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode off, item status is not new, no DOI registered but specified doi, SQLAlchemyError
    item = {"id": "8", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item, "errors": ["DOI cannot be set."] }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_record.pid_doi = None
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", side_effect=SQLAlchemyError()):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode off, item status is not new, DOI registered in record metadata, specified DOI and match doi
    item = {"id": "9", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_record.pid_doi.pid_value = "https://doi.org/xyz.jalc/12345"
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.get_idt_registration_data", return_value=(mock_record.pid_doi.pid_value, "JaLC")):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode off, item status is not new, DOI registered in record metadata, specified DOI and not match doi
    item = {"id": "10", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item, "errors": ["Specified DOI is different from existing DOI."] }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_record.pid_doi.pid_value = "https://doi.org/mis.jalc/12345"
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.get_idt_registration_data", return_value=(mock_record.pid_doi.pid_value, "JaLC")):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode off, item status is not new, DOI registered in record metadata, specified RA but DOI empty
    item = {"id": "11", "status": "Keep", "doi": "", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item, "errors": ["Please specify DOI."] }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_record.pid_doi.pid_value = "https://doi.org/mis.jalc/12345"
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.get_idt_registration_data", return_value=(mock_record.pid_doi.pid_value, "JaLC")):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode off, item status is not new, DOI not registered, but DOI exists in record metadata and specified DOI
    item = {"id": "12", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item, "errors": ["DOI cannot be set."] }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_record.pid_doi = None
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.get_idt_registration_data", return_value=("some_doi", "JaLC")):
        handle_check_doi([item])
    assert item == expect

    # change identifier mode off, item status is not new, DOI not registered, but DOI exists in record metadata and specified RA, not specified DOI
    item = {"id": "13", "status": "Keep", "doi": "", "doi_ra": "JaLC", "is_change_identifier": False}
    expect = { **item }
    mock_record = MagicMock()
    mock_record.pid_recid.object_uuid = uuid.uuid4()
    mock_record.pid_doi = None
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", return_value=mock_record), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.get_idt_registration_data", return_value=("some_doi", "JaLC")):
        handle_check_doi([item])
    assert item == expect

    # not specified RA
    item = {"id": "13", "status": "Keep", "doi": "", "doi_ra": "", "is_change_identifier": False}
    expect = { **item }
    handle_check_doi([item])
    assert item == expect


    # duplicate check inside import file
    list_record = [
        {"status": "new", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True}, # duplicate with existing item: id 17
        {"status": "new", "doi": "xyz.jalc/12344", "doi_ra": "JaLC", "is_change_identifier": True}, # duplicate in import items: index 2
        {"status": "new", "doi": "xyz.jalc/12344", "doi_ra": "JaLC", "is_change_identifier": True}, # duplicate in import items: index 1
        {"status": "new", "doi": "xyz.jalc/12348", "doi_ra": "JaLC", "is_change_identifier": True}, # duplicate in import items: id 18
        {"id": "15", "status": "Keep", "doi": "xyz.jalc/12346", "doi_ra": "JaLC", "is_change_identifier": True}, # existing item
        {"id": "16", "status": "Keep", "doi": "xyz.jalc/12347", "doi_ra": "JaLC", "is_change_identifier": True}, # existing item
        {"id": "17", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True}, # duplicate with new import item: index 0
        {"id": "18", "status": "Keep", "doi": "xyz.jalc/12348", "doi_ra": "JaLC", "is_change_identifier": True}, # change doi, but duplicate in import items: index 3
    ]
    expect = [
        {"status": "new", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True, "errors": ["Specified DOI has been used already for another item. Please specify another DOI."]},
        {"status": "new", "doi": "xyz.jalc/12344", "doi_ra": "JaLC", "is_change_identifier": True, "errors": ["Specified DOI is duplicated with another import item. Please specify another DOI."]},
        {"status": "new", "doi": "xyz.jalc/12344", "doi_ra": "JaLC", "is_change_identifier": True, "errors": ["Specified DOI is duplicated with another import item. Please specify another DOI."]},
        {"status": "new", "doi": "xyz.jalc/12348", "doi_ra": "JaLC", "is_change_identifier": True, "errors": ["Specified DOI is duplicated with another import item. Please specify another DOI."]},
        {"id": "15", "status": "Keep", "doi": "xyz.jalc/12346", "doi_ra": "JaLC", "is_change_identifier": True},
        {"id": "16", "status": "Keep", "doi": "xyz.jalc/12347", "doi_ra": "JaLC", "is_change_identifier": True},
        {"id": "17", "status": "Keep", "doi": "xyz.jalc/12345", "doi_ra": "JaLC", "is_change_identifier": True},
        {"id": "18", "status": "Keep", "doi": "xyz.jalc/12348", "doi_ra": "JaLC", "is_change_identifier": True, "errors": ["Specified DOI is duplicated with another import item. Please specify another DOI."]},
    ]

    def mock_get_record_by_pid(recid):
        record = MagicMock()
        record.pid_recid.object_uuid = "uuid-{}".format(recid)
        if recid == "15":
            record.pid_doi.pid_value = "https://doi.org/xyz.jalc/12346"
        elif recid == "16":
            record.pid_doi.pid_value = "https://doi.org/xyz.jalc/12347"
        elif recid == "17":
            record.pid_doi.pid_value = "https://doi.org/xyz.jalc/12345"
        elif recid == "18":
            record.pid_doi.pid_value = "https://doi.org/xyz.jalc/12399"
        return record

    def mock_doi_check_pidstore_exist(type, doi_link):
        doi = MagicMock()
        if doi_link == "https://doi.org/xyz.jalc/12345":
            doi.status = PIDStatus.REGISTERED
            doi.object_uuid = "uuid-17"
            return doi
        elif doi_link == "https://doi.org/xyz.jalc/12344":
            return None
        elif doi_link == "https://doi.org/xyz.jalc/12346":
            doi.status = PIDStatus.REGISTERED
            doi.object_uuid = "uuid-15"
            return doi
        elif doi_link == "https://doi.org/xyz.jalc/12347":
            doi.status = PIDStatus.REGISTERED
            doi.object_uuid = "uuid-16"
        elif doi_link == "https://doi.org/xyz.jalc/12399":
            doi.status = PIDStatus.REGISTERED
            doi.object_uuid = "uuid-18"
            return doi

    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid", side_effect=mock_get_record_by_pid), \
            patch("weko_search_ui.utils.IdentifierHandle.__init__", return_value=None), \
            patch("weko_search_ui.utils.IdentifierHandle.check_pidstore_exist", side_effect=mock_doi_check_pidstore_exist):
        handle_check_doi(list_record)
    for record, expected in zip(list_record, expect):
        assert record == expected


# def handle_check_item_link(list_record):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_item_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_item_link(app, mocker):
    list_record = [{
        "_id": "item1",
        "link_data": [
            {"item_id": "http://TEST_SERVER/records/1", "sele_id": "isSupplementTo"}
        ]
    }]

    mock_item = MagicMock()
    mock_item.pid.is_deleted.return_value = False
    mock_record = mocker.patch("weko_search_ui.utils.WekoRecord.get_record_by_pid")
    mock_record.return_value = mock_item

    with app.test_request_context():
        handle_check_item_link(list_record)

    assert list_record[0].get("errors") is None
    assert list_record[0].get("link_data")[0].get("item_id") == "1"

    list_record = [{
        "_id": "item1",
        "link_data": [
            {"item_id": "http://TEST_SERVER/records/1", "sele_id": "isSupplementTo"}
        ]
    }]
    mock_item.pid.is_deleted.return_value = True
    with app.test_request_context():
        handle_check_item_link(list_record)

    assert list_record[0]["errors"][0] == "Linking item already deleted in the system."

    list_record = [{
        "_id": "item1",
        "link_data": [
            {"item_id": "http://TEST_SERVER/records/1", "sele_id": "isSupplementTo"}
        ]
    }]
    mock_record.reset_mock()
    mock_record.side_effect = PIDDoesNotExistError("depid", 1)
    with app.test_request_context():
        handle_check_item_link(list_record)
    assert list_record[0]["errors"][0] == "Linking item does not exist in the system."

    mock_record.reset_mock()
    mock_item.pid.is_deleted.return_value = False
    mock_record.return_value = mock_item
    list_record = [{
        "_id": "item2",
        "link_data": [
            {"item_id": "http://INVALID_SERVER/records/1", "sele_id": "invalidSeleId"}
        ]
    }]

    with app.test_request_context():
        handle_check_item_link(list_record)

    assert list_record[0]["errors"][0] == "Item Link type: '{}' is not one of {}.".format("invalidSeleId", WEKO_SCHEMA_RELATION_TYPE)
    assert list_record[0]["errors"][1] == "Specified Item Link URI and system URI do not match."

    list_record = [
        {
            "_id": "item3",
            "link_data": [
                {"item_id": 1, "sele_id": "isSupplementTo"}
            ]
        },
        {
            "_id": "item4",
            "link_data": [
                {"item_id": "item3", "sele_id": "isSupplementedBy"}
            ]
        },
        {
            "_id": "item5",
            "link_data": ["http://TEST_SERVER/records/1"]
        },
        {
            "_id": "item6",
            "link_data": "http://TEST_SERVER/records/1"
        }
    ]
    with app.test_request_context():
        handle_check_item_link(list_record)
    assert list_record[0]["errors"][0] == "Please specify Item URL for item link."
    assert list_record[0]["link_data"][0]["item_id"] == 1
    assert list_record[1].get("errors") is None
    assert list_record[1]["link_data"][0]["item_id"] == "item3"

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_duplicate_item_link -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_duplicate_item_link(app):

    # pattern of link dst is existing ID
    # expect reduction of duplicate link
    item_1 = {
        "_id": "journal1",
        "link_data": [
            {"item_id": "100", "sele_id": "ccc"},
            {"item_id": "100", "sele_id": "ccc"}
        ]
    }
    item_2 = {
        "_id": "journal2",
        "link_data": [
            {"item_id": "100", "sele_id": "isSupplementTo"},
            {"item_id": "100", "sele_id": "isSupplementTo"}
        ]
    }
    list_record = [item_1, item_2]
    list_record.sort(key=lambda x: get_priority(x["link_data"]))
    handle_check_duplicate_item_link(list_record)
    assert not list_record[0].get("errors")
    assert not list_record[1].get("errors")
    assert len(list_record[0]["link_data"]) == 1
    assert len(list_record[1]["link_data"]) == 1

    # duplicate link error
    item_1 = {
        "_id": "journal1",
        "link_data": [
            {"item_id": "100", "sele_id": "ccc"},
            {"item_id": "100", "sele_id": "ddd"}
        ]
    }
    item_2 = {
        "_id": "journal2",
        "link_data": [
            {"item_id": "100", "sele_id": "ccc"},
            {"item_id": "100", "sele_id": "isSupplementTo"}
        ]
    }
    item_3 = {
        "_id": "journal3",
        "link_data": [
            {"item_id": "100", "sele_id": "isSupplementTo"},
            {"item_id": "100", "sele_id": "isSupplementedBy"}
        ]
    }
    list_record = [item_1, item_2, item_3]
    list_record.sort(key=lambda x: get_priority(x["link_data"]))
    handle_check_duplicate_item_link(list_record)
    assert "Duplicate Item Link." in list_record[0]["errors"][0]
    assert "Duplicate Item Link." in list_record[1]["errors"][0]
    assert "Duplicate Item Link." in list_record[2]["errors"][0]

    # pattern of link dst is split item
    item_1 = {
        "_id": "journal",
        "link_data": [
            {"item_id": "evidence", "sele_id": "ccc"}
        ]
    }
    list_record = [item_1]
    list_record.sort(key=lambda x: get_priority(x["link_data"]))
    handle_check_duplicate_item_link(list_record)
    assert "It is not allowed to create links other than" \
        in list_record[0]["errors"][0]

    # expect reduction of duplicate inverse link
    item_1 = {
        "_id": "journal",
        "link_data": [
            {"item_id": "evidence", "sele_id": "isSupplementedBy"}
        ]
    }
    item_2 = {
        "_id": "evidence",
        "link_data": [
            {"item_id": "journal", "sele_id": "isSupplementTo"}
        ]
    }
    list_record = [item_1, item_2]
    list_record.sort(key=lambda x: get_priority(x["link_data"]))
    assert list_record[0]["_id"] == "evidence"
    assert list_record[1]["_id"] == "journal"
    handle_check_duplicate_item_link(list_record)
    assert len(list_record[0]["link_data"]) == 0
    assert len(list_record[1]["link_data"]) == 1

    # duplicate link error
    item_1 = {
        "_id": "evidence",
        "link_data": [
            {"item_id": "journal", "sele_id": "isSupplementedBy"}
        ]
    }
    item_2 = {
        "_id": "journal",
        "link_data": [
            {"item_id": "evidence", "sele_id": "isSupplementedBy"}
        ]
    }
    list_record = [item_1, item_2]
    list_record.sort(key=lambda x: get_priority(x["link_data"]))
    assert list_record[0]["_id"] == "evidence"
    assert list_record[1]["_id"] == "journal"
    handle_check_duplicate_item_link(list_record)
    assert "Duplicate Item Link." in list_record[0]["errors"][0]
    assert "Duplicate Item Link." in list_record[1]["errors"][0]

    # error link to item itself
    item_1 = {
        "_id": "evidence",
        "id": "100",
        "link_data": [
            {"item_id": "100", "sele_id": "hasPart"}
        ]
    }
    item_2 = {
        "_id": "journal",
        "link_data": [
            {"item_id": "journal", "sele_id": "isSupplementedBy"},
        ]
    }
    list_record = [item_1, item_2]
    list_record.sort(key=lambda x: get_priority(x["link_data"]))
    assert list_record[0]["_id"] == "journal"
    assert list_record[1]["_id"] == "evidence"
    handle_check_duplicate_item_link(list_record)
    assert "It is not allowed to create links to the item itself." \
        in list_record[0]["errors"][0]
    assert "It is not allowed to create links to the item itself." \
        in list_record[1]["errors"][0]

    # replace links with inverse links (isSupplementTo)
    item_1 = {
        "_id": "journal",
        "link_data": [
            {"item_id": "100", "sele_id": "hasPart"}
        ]
    }
    item_2 = {
        "_id": "evidence",
        "link_data": [
            {"item_id": "journal", "sele_id": "isSupplementTo"},
        ]
    }
    list_record = [item_1, item_2]
    list_record.sort(key=lambda x: get_priority(x["link_data"]))
    assert list_record[0]["_id"] == "evidence"
    assert list_record[1]["_id"] == "journal"
    handle_check_duplicate_item_link(list_record)
    assert not list_record[0].get("errors")
    assert not list_record[1].get("errors")
    assert len(list_record[0]["link_data"]) == 0
    assert len(list_record[1]["link_data"]) == 2

    # replace links with inverse links (isSupplementedBy)
    item_1 = {
        "_id": "evidence",
        "link_data": [
            {"item_id": "100", "sele_id": "hasPart"}
        ]
    }
    item_2 = {
        "_id": "journal",
        "link_data": [
            {"item_id": "evidence", "sele_id": "isSupplementedBy"},
        ]
    }
    list_record = [item_1, item_2]
    list_record.sort(key=lambda x: get_priority(x["link_data"]))
    assert list_record[0]["_id"] == "journal"
    assert list_record[1]["_id"] == "evidence"
    handle_check_duplicate_item_link(list_record)
    assert not list_record[0].get("errors")
    assert not list_record[1].get("errors")
    assert len(list_record[0]["link_data"]) == 0
    assert len(list_record[1]["link_data"]) == 2

    # invaild input data
    list_record = []
    handle_check_duplicate_item_link(list_record)
    item_1 = {
        "_id": "evidence",
        "link_data": None
    }
    item_2 = {
    }
    item_3 = None
    list_record = [item_1, item_2, item_3]
    handle_check_duplicate_item_link(list_record)
    assert not list_record[0].get("errors")

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_operation_flags -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_operation_flags(tmpdir):
    tmp_dir = tmpdir.mkdir("test")
    with open(os.path.join(tmp_dir, "test_1.txt"), "w") as f11, \
            open(os.path.join(tmp_dir, "test_1.csv"), "w") as f12:
        f11.write("This is a test file.")
        f12.write("This is a test file.")
    with open(os.path.join(tmp_dir, "test_2.txt"), "w") as f21, \
            open(os.path.join(tmp_dir, "test_2.csv"), "w") as f22:
        f21.write("This is a test file.")
        f22.write("This is a test file.")
    with open(os.path.join(tmp_dir, "test_3.txt"), "w") as f31, \
            open(os.path.join(tmp_dir, "test_3.csv"), "w") as f32:
        f31.write("This is a test file.")
        f32.write("This is a test file.")
    with open(os.path.join(tmp_dir, "test_4.txt"), "w") as f41, \
            open(os.path.join(tmp_dir, "test_4.csv"), "w") as f42:
        f41.write("This is a test file.")
        f42.write("This is a test file.")

    assert len(os.listdir(tmp_dir)) == 8

    list_record = [
        {"status": "new", "metadata_replace": True, "file_path":["test_1.txt", "test_1.csv", "https://..."]},
        {"status": "Keep", "metadata_replace": True, "file_path":["test_2.txt", "test_2.csv", "https://..."]},
        {"status": "Keep", "metadata_replace": False, "file_path":["test_3.txt", "test_3.csv", "https://..."]},
        {"status": "Upgrede", "file_path":["test_4.txt", "test_4.csv"]},
    ]

    test = [
        {"status": "new", "metadata_replace": True, "file_path":["test_1.txt", "test_1.csv", "https://..."], "errors": ["The 'wk:metadataReplace' flag cannot be used when registering an item."]},
        {"status": "Keep", "metadata_replace": True, "file_path":["test_2.txt", "test_2.csv", "https://..."]},
        {"status": "Keep", "metadata_replace": False, "file_path":["test_3.txt", "test_3.csv", "https://..."]},
        {"status": "Upgrede", "file_path":["test_4.txt", "test_4.csv"]},
    ]

    handle_check_operation_flags(list_record, tmp_dir)
    assert list_record == test
    assert not os.path.isfile(os.path.join(tmp_dir, "test_2.txt"))
    assert not os.path.isfile(os.path.join(tmp_dir, "test_2.csv"))
    assert len(os.listdir(tmp_dir)) == 6

# def register_item_handle(item):
def test_register_item_handle(i18n_app, es_item_file_pipeline, es_records):
    item = es_records["results"][0]["item"]

    assert not register_item_handle(item)

    with patch("weko_workflow.utils.register_hdl_by_handle", return_value=""):
        item["status"] = "new"
        # Doesn't return any value
        assert not register_item_handle(item)

    item["is_change_identifier"] = False
    assert not register_item_handle(item)

    with patch("weko_workflow.utils.register_hdl_by_handle", return_value=""):
        item["status"] = "new"
        # Doesn't return any value
        assert not register_item_handle(item)


# def prepare_doi_setting():
def test_prepare_doi_setting(i18n_app, communities2, db):
    from weko_admin.models import Identifier
    from weko_workflow.utils import get_identifier_setting

    test_identifier = Identifier(
        id=1,
        repository="Root Index",
        created_userId="user1",
        created_date=datetime.now(),
        updated_userId="user1",
    )
    db.session.add(test_identifier)
    db.session.commit()

    assert prepare_doi_setting()


# def get_doi_prefix(doi_ra):
WEKO_IMPORT_DOI_TYPE = ["JaLC", "Crossref", "DataCite", "NDL JaLC"]


@pytest.mark.parametrize("doi_ra", WEKO_IMPORT_DOI_TYPE)
def test_get_doi_prefix(i18n_app, communities2, doi_ra, db):
    from weko_admin.models import Identifier
    from weko_workflow.utils import get_identifier_setting

    test_identifier = Identifier(
        id=1,
        repository="Root Index",
        created_userId="user1",
        created_date=datetime.now(),
        updated_userId="user1",
    )
    db.session.add(test_identifier)
    db.session.commit()

    assert get_doi_prefix(doi_ra)


# def get_doi_link(doi_ra, data):
def test_get_doi_link(i18n_app):
    doi_ra = ["JaLC", "Crossref", "DataCite", "NDL JaLC"]
    data = {
        "identifier_grant_jalc_doi_link": doi_ra[0],
        "identifier_grant_jalc_cr_doi_link": doi_ra[1],
        "identifier_grant_jalc_dc_doi_link": doi_ra[2],
        "identifier_grant_ndl_jalc_doi_link": doi_ra[3],
    }

    assert get_doi_link(doi_ra[0], data)
    assert get_doi_link(doi_ra[1], data)
    assert get_doi_link(doi_ra[2], data)
    assert get_doi_link(doi_ra[3], data)


# def prepare_doi_link(item_id):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_prepare_doi_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_prepare_doi_link(i18n_app, communities2, db):
    from weko_admin.models import Identifier

    test_identifier = Identifier(
        id=1,
        repository="Root Index",
        created_userId="user1",
        created_date=datetime.now(),
        updated_userId="user1",
    )
    db.session.add(test_identifier)
    db.session.commit()
    item_id = 90

    result = prepare_doi_link(item_id)
    test = {
        "identifier_grant_jalc_doi_link":"https://doi.org/<Empty>/0000000090",
        "identifier_grant_jalc_cr_doi_link":"https://doi.org/<Empty>/0000000090",
        "identifier_grant_jalc_dc_doi_link":"https://doi.org/<Empty>/0000000090",
        "identifier_grant_ndl_jalc_doi_link":"https://doi.org/<Empty>/",
    }
    assert result == test

    item_id = MagicMock()
    result = prepare_doi_link(item_id)
    test = {
        "identifier_grant_jalc_doi_link":"https://doi.org/<Empty>/0000000001",
        "identifier_grant_jalc_cr_doi_link":"https://doi.org/<Empty>/0000000001",
        "identifier_grant_jalc_dc_doi_link":"https://doi.org/<Empty>/0000000001",
        "identifier_grant_ndl_jalc_doi_link":"https://doi.org/<Empty>/",
    }
    assert result == test


# def register_item_doi(item):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_register_item_doi -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_register_item_doi(i18n_app, db_activity, identifier, mocker):

    mocker.patch("weko_search_ui.utils.WekoDeposit.get_record",return_value=MagicMock())

    mock_without_version = MagicMock()
    mock_recid=MagicMock()
    mock_without_version.pid_recid=mock_recid
    mock_pid_doi = MagicMock()
    mock_pid_doi.pid_value = "https://doi.org/xyz.jalc/0000022222" # path delete
    mock_without_version.pid_doi = mock_pid_doi

    mock_lasted=MagicMock()
    mock_lasted_pid=MagicMock()
    mock_lasted.pid_recid=mock_lasted_pid

    # is_change_identifier is True, not doi_ra and doi
    item = {
        "id":"1",
        "is_change_identifier":True
    }
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
            register_item_doi(item)
            mock_save.assert_not_called()

    # is_change_identifier is True, pid_value.endswith is False, doi_duplicated is True
    item = {
        "id":"2",
        "is_change_identifier":True,
        "doi_ra":"JaLC",
        "doi":"xyz.jalc/0000011111"
    }
    return_check = {"isWithdrawnDoi":True,"isExistDOI":False}

    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.check_existed_doi",return_value=return_check):
            with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
                with pytest.raises(Exception) as e:
                    register_item_doi(item)
                assert e.value.args[0] == {"error_id":"is_withdraw_doi"}

    # is_change_identifier is True, pid_value.endswith is False, called saving_doi_pidstore
    item = {
        "id":"3",
        "is_change_identifier":True,
        "doi_ra":"JaLC",
        "doi":"xyz.jalc/0000011111"
    }
    return_check = {"isWithdrawnDoi":False,"isExistDOI":False}
    test_data = {
        "identifier_grant_jalc_doi_link":"https://doi.org/xyz.jalc/0000011111",
        "identifier_grant_jalc_cr_doi_link":"https://doi.org/xyz.jalc/0000011111",
        "identifier_grant_jalc_dc_doi_link":"https://doi.org/xyz.jalc/0000011111",
        "identifier_grant_ndl_jalc_doi_link":"https://doi.org/xyz.jalc/0000011111"
    }
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.check_existed_doi",return_value=return_check):
            with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
                register_item_doi(item)
                args, kwargs = mock_save.call_args
                assert args[2] == test_data

    # is_change_identifier is True, pid_value.endswith is True
    item = {
        "id":"4",
        "is_change_identifier":True,
        "doi_ra":"JaLC",
        "doi":"xyz.jalc/0000022222"
    }
    return_check = {"isWithdrawnDoi":False,"isExistDOI":False}
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.check_existed_doi",return_value=return_check):
            with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
                register_item_doi(item)
                mock_save.assert_not_called()

    # is_change_identifier is False, doi_ra not NDL, doi_duplicated is True
    item = {
        "id":"5",
        "is_change_identifier":False,
        "doi_ra":"JaLC",
    }
    return_check = {"isWithdrawnDoi":False,"isExistDOI":True}
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.check_existed_doi",return_value=return_check):
            with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
                with pytest.raises(Exception) as e:
                    register_item_doi(item)
                assert e.value.args[0] == {"error_id":"is_duplicated_doi"}

    # is_change_identifier is False, doi_ra not NDL, called saving_doi_pidstore
    item = {
        "id":"6",
        "is_change_identifier":False,
        "doi_ra":"JaLC",
    }
    return_check = {"isWithdrawnDoi":False,"isExistDOI":False}
    test_data = {
        "identifier_grant_jalc_doi_link":"https://doi.org/xyz.jalc/0000000006",
        "identifier_grant_jalc_cr_doi_link":"https://doi.org/xyz.crossref/0000000006",
        "identifier_grant_jalc_dc_doi_link":"https://doi.org/xyz.datacite/0000000006",
        "identifier_grant_ndl_jalc_doi_link":"https://doi.org/xyz.ndl/"
    }
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.check_existed_doi",return_value=return_check):
            with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
                register_item_doi(item)
                args, kwargs = mock_save.call_args
                assert args[2] == test_data

    # is_change_identifier is False, doi_ra is NDL, doi_duplicated is True
    mock_without_version.pid_doi = None
    item = {
        "id":"7",
        "is_change_identifier":False,
        "doi_ra":"NDL JaLC",
        "doi":"xyz.ndl/0000012345"
    }
    return_check = {"isWithdrawnDoi":True,"isExistDOI":False}
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.check_existed_doi",return_value=return_check):
            with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
                with pytest.raises(Exception) as e:
                    register_item_doi(item)
                assert e.value.args[0] == {"error_id": "is_withdraw_doi"}

    # is_change_identifier is False, doi_ra is NDL, called saving_doi_pidstore
    item = {
        "id":"8",
        "is_change_identifier":False,
        "doi_ra":"NDL JaLC",
        "doi":"xyz.ndl/0000012345"
    }
    return_check = {"isWithdrawnDoi":False,"isExistDOI":False}
    test_data = {
        "identifier_grant_jalc_doi_link":"https://doi.org/xyz.ndl/0000012345",
        "identifier_grant_jalc_cr_doi_link":"https://doi.org/xyz.ndl/0000012345",
        "identifier_grant_jalc_dc_doi_link":"https://doi.org/xyz.ndl/0000012345",
        "identifier_grant_ndl_jalc_doi_link":"https://doi.org/xyz.ndl/0000012345"
    }
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.check_existed_doi",return_value=return_check):
            with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
                register_item_doi(item)
                args, kwargs = mock_save.call_args
                assert args[2] == test_data

    # data is None
    item = {
        "id":"9",
        "is_change_identifier":False,
    }
    with patch("weko_search_ui.utils.WekoRecord.get_record_by_pid",side_effect=[mock_without_version,mock_lasted]):
        with patch("weko_search_ui.utils.check_existed_doi",return_value=return_check):
            with patch("weko_search_ui.utils.saving_doi_pidstore") as mock_save:
                register_item_doi(item)

# def register_item_update_publish_status(item, status):
def test_register_item_update_publish_status(
    i18n_app, es_item_file_pipeline, es_records
):
    item = es_records["results"][0]["item"]
    # item = db_activity['item']
    status = 0

    with patch("weko_search_ui.utils.update_publish_status", return_value={}):
        # Doesn't return any value
        assert not register_item_update_publish_status(item, status)


# def handle_doi_required_check(record):
def test_handle_doi_required_check(
    i18n_app,
    es_item_file_pipeline,
    es_records,
    record_with_metadata,
    db_itemtype,
    item_type,
):
    record = record_with_metadata[1]

    record2 = {
        "id": 1,
        "item_type_id": 1,
        "metadata": {"a": 1},
        "doi_ra": "JaLC",
        "file_path": "a b c d",
        "status": "keep",
    }

    error_list_dict = {
        "mapping": "mapping",
        "other": "other",
        "required_key": "required_key",
        "either_key": "either_key",
    }
    with patch(
        "weko_workflow.utils.item_metadata_validation", return_value=error_list_dict
    ):
        # Should have no return value
        assert not handle_doi_required_check(record)

    with patch(
        "weko_workflow.utils.item_metadata_validation", return_value=error_list_dict
    ):
        assert handle_doi_required_check(record2)


# def handle_check_date(list_record):
def test_handle_check_date(app, test_list_records, mocker_itemtype):
    for t in test_list_records:
        input_data = t.get("input")
        output_data = t.get("output")
        with app.app_context():
            ret = handle_check_date(input_data)
            assert ret == output_data
    # with patch("weko_search_ui.utils.validation_date_property", return_value=""):
    #     assert handle_check_date(test_list_records)


# def handle_check_id(list_record):
def test_handle_check_id(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[1]]

    # Doesn't return any value
    assert not handle_check_id(list_record)


# def get_data_in_deep_dict(search_key, _dict={}):
def test_get_data_in_deep_dict(i18n_app):
    search_key = "test"
    _dict = {"test": 1, "sample": {"a": 1}}
    _dict2 = {"test": {"a": 1, "b": 2}, "sample": {"a": 1}}

    assert get_data_in_deep_dict(search_key, _dict)

    with patch(
        "weko_search_ui.utils.get_data_in_deep_dict", return_value=[{"tree_key": 1}]
    ):
        assert get_data_in_deep_dict("tests", _dict2)

        _dict["test"] = [{"a": 1}, 2]
        assert get_data_in_deep_dict("tests", _dict)


# def validation_file_open_date(record):
def test_validation_file_open_date(app, test_records):
    for t in test_records:
        filepath = t.get("input")
        result = t.get("output")
        with open(filepath, encoding="utf-8") as f:
            ret = json.load(f)
        with app.app_context():
            assert validation_file_open_date(ret) == result


# def validation_date_property(date_str):
def test_validation_date_property():
    # with pytest.raises(Exception):
    assert validation_date_property("2022") == True
    assert validation_date_property("2022-03") == True
    assert validation_date_property("2022-1") == False
    assert validation_date_property("2022-1-1") == False
    assert validation_date_property("2022-2-31") == False
    assert validation_date_property("2022-12-01") == True
    assert validation_date_property("2022-02-31") == False
    assert validation_date_property("2022-12-0110") == False
    assert validation_date_property("hogehoge") == False


# def get_list_key_of_iso_date(schemaform):
def test_get_list_key_of_iso_date():
    form = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type", "form00.json"
    )
    result = [
        "item_1617186660861.subitem_1522300722591",
        "item_1617187056579.bibliographicIssueDates.bibliographicIssueDate",
        "item_1617187136212.subitem_1551256096004",
        "item_1617605131499.fileDate.fileDateValue",
        "item_1617605131499.date[0].dateValue"
    ]
    with open(form, encoding="utf-8") as f:
        df = json.load(f)
    assert get_list_key_of_iso_date(df) == result


# def get_current_language():
def test_get_current_language(i18n_app):
    assert get_current_language()


# def get_change_identifier_mode_content():
def test_get_change_identifier_mode_content(i18n_app):
    assert get_change_identifier_mode_content()


# def get_root_item_option(item_id, item, sub_form={"title_i18n": {}}):
def test_get_root_item_option(i18n_app):
    item_id = 1
    item = {
        "title": "title",
        "option": {
            "required": "required",
            "hidden": "hidden",
            "multiple": "multiple",
        },
    }

    assert get_root_item_option(item_id, item)


# def get_sub_item_option(key, schemaform):
def test_get_sub_item_option(i18n_app):
    key = "key"
    schemaform = [
        {"key": "key", "required": "required", "isHide": "isHide", "readonly": True},
    ]
    schemaform2 = [
        {
            "items": {
                "key": "key",
                "required": "required",
                "isHide": "isHide",
                "readonly": True,
            }
        },
    ]

    assert get_sub_item_option(key, schemaform)

    with patch("weko_search_ui.utils.get_sub_item_option", return_value=True):
        assert get_sub_item_option(key, schemaform2)


# def check_sub_item_is_system(key, schemaform):
def test_check_sub_item_is_system(i18n_app):
    key = "key"
    schemaform = [
        {"key": "key", "required": "required", "isHide": "isHide", "readonly": True},
    ]
    schemaform2 = [
        {
            "items": {
                "key": "key",
                "required": "required",
                "isHide": "isHide",
                "readonly": True,
            }
        },
    ]

    assert check_sub_item_is_system(key, schemaform)

    with patch("weko_search_ui.utils.check_sub_item_is_system", return_value=True):
        assert check_sub_item_is_system(key, schemaform2)


# def get_lifetime():
def test_get_lifetime(i18n_app, db_register2):
    assert get_lifetime()
    with patch("weko_admin.models.SessionLifetime.get_validtime", return_value=None):
        assert get_lifetime()
    with patch("weko_admin.models.SessionLifetime.get_validtime", return_value=""):
        assert not get_lifetime()


# def get_system_data_uri(key_type, key):
def test_get_system_data_uri():
    data = [
        {"resource_type": RESOURCE_TYPE_URI},
        {"version_type": VERSION_TYPE_URI},
        {"access_right": ACCESS_RIGHT_TYPE_URI},
    ]
    for t in data:
        for key_type in t.keys():
            val = t.get(key_type)
            for key in val.keys():
                url = val.get(key)
                assert get_system_data_uri(key_type, key) == url


# def handle_fill_system_item(list_record):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_fill_system_item -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp

def test_handle_fill_system_item(app, test_list_records,identifier, mocker):

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "item_map.json"
    )
    with open(filepath, encoding="utf-8") as f:
        item_map = json.load(f)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "item_type_mapping.json"
    )
    with open(filepath, encoding="utf-8") as f:
        item_type_mapping = json.load(f)
    #mocker.patch("weko_records.serializers.utils.get_mapping", return_value=item_map)
    mocker.patch("weko_search_ui.utils.get_mapping", return_value=item_map)
    #mocker.patch("weko_records.api.Mapping.get_record", return_value=item_type_mapping)
    #mocker.patch("weko_search_ui.utils.get_record", return_value=item_type_mapping)

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records/list_records_fill_system.json",
    )
    with open(filepath, encoding="utf-8") as f:
        list_record = json.load(f)

    items = []
    items_result = []

    for a in VERSION_TYPE_URI:
        item = copy.deepcopy(list_record[0])
        item["metadata"]["item_1617265215918"]["subitem_1522305645492"] = a
        item["metadata"]["item_1617265215918"][
            "subitem_1600292170262"
        ] = VERSION_TYPE_URI[a]
        item["metadata"]["item_1617186476635"]["subitem_1522299639480"] = "open access"
        item["metadata"]["item_1617186476635"][
            "subitem_1600958577026"
        ] = ACCESS_RIGHT_TYPE_URI["open access"]
        item["metadata"]["item_1617258105262"]["resourcetype"] = "conference paper"
        item["metadata"]["item_1617258105262"]["resourceuri"] = RESOURCE_TYPE_URI[
            "conference paper"
        ]
        item["warnings"] = []
        item["errors"] = []
        items_result.append(item)
        item2 = copy.deepcopy(item)
        item2["metadata"]["item_1617265215918"]["subitem_1522305645492"] = a
        item2["metadata"]["item_1617265215918"]["subitem_1600292170262"] = ""
        items.append(item2)

    for a in ACCESS_RIGHT_TYPE_URI:
        item = copy.deepcopy(list_record[0])
        item["metadata"]["item_1617265215918"]["subitem_1522305645492"] = "VoR"
        item["metadata"]["item_1617265215918"][
            "subitem_1600292170262"
        ] = VERSION_TYPE_URI["VoR"]
        item["metadata"]["item_1617186476635"]["subitem_1522299639480"] = a
        item["metadata"]["item_1617186476635"][
            "subitem_1600958577026"
        ] = ACCESS_RIGHT_TYPE_URI[a]
        item["metadata"]["item_1617258105262"]["resourcetype"] = "conference paper"
        item["metadata"]["item_1617258105262"]["resourceuri"] = RESOURCE_TYPE_URI[
            "conference paper"
        ]
        item["warnings"] = []
        item["errors"] = []
        items_result.append(item)
        item2 = copy.deepcopy(item)
        item2["metadata"]["item_1617186476635"]["subitem_1522299639480"] = a
        item2["metadata"]["item_1617186476635"]["subitem_1600958577026"] = ""
        items.append(item2)

    for a in RESOURCE_TYPE_URI:
        item = copy.deepcopy(list_record[0])
        item["metadata"]["item_1617265215918"]["subitem_1522305645492"] = "VoR"
        item["metadata"]["item_1617265215918"][
            "subitem_1600292170262"
        ] = VERSION_TYPE_URI["VoR"]
        item["metadata"]["item_1617186476635"]["subitem_1522299639480"] = "open access"
        item["metadata"]["item_1617186476635"][
            "subitem_1600958577026"
        ] = ACCESS_RIGHT_TYPE_URI["open access"]
        item["metadata"]["item_1617258105262"]["resourcetype"] = a
        item["metadata"]["item_1617258105262"]["resourceuri"] = RESOURCE_TYPE_URI[a]
        item["warnings"] = []
        item["errors"] = []
        items_result.append(item)
        item2 = copy.deepcopy(item)
        item2["metadata"]["item_1617258105262"]["resourcetype"] = a
        item2["metadata"]["item_1617258105262"]["resourceuri"] = ""
        items.append(item2)
    # identifier_type is NDL JaLC, not prefix/suffix
    item = copy.deepcopy(list_record[0])
    item["metadata"]["item_1617186819068"]={'subitem_identifier_reg_type':"NDL JaLC", 'subitem_identifier_reg_text': "xyz.ndl/123456"}
    item["metadata"]["item_1617186476635"]["subitem_1522299639480"] = "open access"
    item["metadata"]["item_1617186476635"][
        "subitem_1600958577026"
    ] = ACCESS_RIGHT_TYPE_URI["open access"]
    item["metadata"]["item_1617265215918"]["subitem_1522305645492"] = "VoR"
    item["metadata"]["item_1617265215918"][
        "subitem_1600292170262"
    ] = VERSION_TYPE_URI["VoR"]
    item["metadata"]["item_1617258105262"]["resourcetype"] = "conference paper"
    item["metadata"]["item_1617258105262"]["resourceuri"] = RESOURCE_TYPE_URI[
        "conference paper"
    ]
    item["doi"] = "xyz.ndl/123456"
    item["doi_ra"] = "NDL JaLC"
    item["is_change_identifier"]=False
    item["warnings"]=[]
    item["errors"]=[]
    items_result.append(item)
    item2 = copy.deepcopy(item)
    del item2["metadata"]["item_1617186819068"]
    item2["metadata"]["item_1617186476635"]["subitem_1600958577026"] = ""
    item2["metadata"]["item_1617258105262"]["resourceuri"] = ""
    items.append(item2)

    # identifier_type is NDL JaLC, not suffix
    item = copy.deepcopy(list_record[0])
    item["metadata"]["item_1617186819068"]={'subitem_identifier_reg_type':"NDL JaLC", 'subitem_identifier_reg_text': ""}
    item["metadata"]["item_1617186476635"]["subitem_1522299639480"] = "open access"
    item["metadata"]["item_1617186476635"][
        "subitem_1600958577026"
    ] = ACCESS_RIGHT_TYPE_URI["open access"]
    item["metadata"]["item_1617265215918"]["subitem_1522305645492"] = "VoR"
    item["metadata"]["item_1617265215918"][
        "subitem_1600292170262"
    ] = VERSION_TYPE_URI["VoR"]
    item["metadata"]["item_1617258105262"]["resourcetype"] = "conference paper"
    item["metadata"]["item_1617258105262"]["resourceuri"] = RESOURCE_TYPE_URI[
        "conference paper"
    ]
    item["doi"] = ""
    item["doi_ra"] = "NDL JaLC"
    item["is_change_identifier"]=False
    item["warnings"]=[]
    item["errors"]=["Please specify DOI prefix/suffix."]
    items_result.append(item)
    item2 = copy.deepcopy(item)
    item2["errors"] = []
    del item2["metadata"]["item_1617186819068"]
    item2["metadata"]["item_1617186476635"]["subitem_1600958577026"] = ""
    item2["metadata"]["item_1617258105262"]["resourceuri"] = ""
    items.append(item2)

    # identifier_type is NDL JaLC, not suffix
    item = copy.deepcopy(list_record[0])
    item["metadata"]["item_1617186819068"]={'subitem_identifier_reg_type':"NDL JaLC", 'subitem_identifier_reg_text': "xyz.ndl/"}
    item["metadata"]["item_1617186476635"]["subitem_1522299639480"] = "open access"
    item["metadata"]["item_1617186476635"][
        "subitem_1600958577026"
    ] = ACCESS_RIGHT_TYPE_URI["open access"]
    item["metadata"]["item_1617265215918"]["subitem_1522305645492"] = "VoR"
    item["metadata"]["item_1617265215918"][
        "subitem_1600292170262"
    ] = VERSION_TYPE_URI["VoR"]
    item["metadata"]["item_1617258105262"]["resourcetype"] = "conference paper"
    item["metadata"]["item_1617258105262"]["resourceuri"] = RESOURCE_TYPE_URI[
        "conference paper"
    ]
    item["doi"] = "xyz.ndl/"
    item["doi_ra"] = "NDL JaLC"
    item["is_change_identifier"]=False
    item["warnings"]=[]
    item["errors"]=["Please specify DOI suffix."]
    items_result.append(item)
    item2 = copy.deepcopy(item)
    item2["errors"] = []
    del item2["metadata"]["item_1617186819068"]
    item2["metadata"]["item_1617186476635"]["subitem_1600958577026"] = ""
    item2["metadata"]["item_1617258105262"]["resourceuri"] = ""
    items.append(item2)

    mock_record = MagicMock()
    mock_doi = MagicMock()
    mock_record.pid_doi=None
    #mock_doi.pid_value=
    # with open("items.json","w") as f:
    #     json.dump(items,f)

    # with open("items_result.json","w") as f:
    #     json.dump(items_result,f)

    # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data/handle_fill_system_item/items.json")
    # with open(filepath,encoding="utf-8") as f:
    #     items = json.load(f)

    # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data/handle_fill_system_item/items_result.json")
    # with open(filepath,encoding="utf-8") as f:
    #     items_result = json.load(f)
    mocker.patch("weko_deposit.api.WekoRecord.get_record_by_pid",return_value=mock_record)
    with app.test_request_context():
        with set_locale("en"):
            handle_fill_system_item(items)
            assert len(items) == len(items_result)
            assert items == items_result


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_fill_system_item3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
# doi2, doi_ra2 は自動補完が原則
@pytest.mark.parametrize(
    "item_id, before_doi,after_doi,warnings,errors,is_change_identifier,is_register_cnri",
    [
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},[],[],False,False),
        (1,{"doi": "","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": None,"doi_ra2":None},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "","doi_ra2":""},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},[],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "xyz.jalc/0000000001","doi_ra2":""},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},[],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},[],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "","doi_ra2":"DataCite"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "xyz.jalc/0000000001","doi_ra2":"DataCite"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "xyz.jalc/0000000002","doi_ra2":"DataCite"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "","doi_ra2":"JaLC2"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "","doi_ra2":""},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC2","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": None,"doi_ra2":None},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (1,{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "xyz.jalc/0000000002","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (1,{"doi": None,"doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.','The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (1,{"doi": None,"doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},[],[],True,False),
        (1,{"doi": "","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "","doi_ra":"","doi2": "","doi_ra2":""},[],['Please specify DOI prefix/suffix.'],True,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.jalc/0000000001","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),

        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "","doi_ra2":""},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},[],[],True,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "xyz.jalc/0000000001","doi_ra2":""},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},[],[],True,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},[],[],True,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "","doi_ra2":"DataCite"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "xyz.jalc/0000000001","doi_ra2":"DataCite"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "xyz.jalc/0000000002","doi_ra2":"DataCite"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC", "doi2": "","doi_ra2":"JaLC2"},{"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (1,{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "","doi_ra2":""},{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "xyz.jalc/0000000002","doi_ra2":"JaLC"},[],[],True,False),
        (1,{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "xyz.jalc/0000000002","doi_ra2":"JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],True,False),
        (1,{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC2","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC2","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (1,{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "xyz.jalc/0000000002","doi_ra2":"JaLC"},{"doi": "xyz.jalc/0000000002","doi_ra":"JaLC","doi2": "xyz.jalc/0000000002","doi_ra2":"JaLC"},[],[],True,False),
        (1,{"doi": None,"doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"","doi2": None,"doi_ra2":None},[],['Please specify DOI prefix/suffix.'],True,False),
        (1,{"doi": "xyz.jalc/0000000001","doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/0000000001","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (1,{"doi": None,"doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"JaLC","doi2": "","doi_ra2":"JaLC"},[],['Please specify DOI prefix/suffix.'],True,False),

        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},[],[],False,False),
        (2,{"doi": "","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": None,"doi_ra2":None},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "","doi_ra2":""},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},[],[],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "xyz.crossref/0000000002","doi_ra2":""},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},[],[],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},[],[],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "","doi_ra2":"DataCite"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "xyz.crossref/0000000002","doi_ra2":"DataCite"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "xyz.crossref/0000000003","doi_ra2":"DataCite"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "","doi_ra2":"JaLC2"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (2,{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "","doi_ra2":""},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (2,{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (2,{"doi": "xyz.crossref/0000000003","doi_ra":"JaLC2","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": None,"doi_ra2":None},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (2,{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "xyz.crossref/0000000003","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (2,{"doi": None,"doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.','The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (2,{"doi": None,"doi_ra":"Crossref","doi2": None,"doi_ra2":None},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),

        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},[],[],True,False),
        (2,{"doi": "","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "","doi_ra":"","doi2": "","doi_ra2":""},[],['Please specify DOI prefix/suffix.'],True,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.crossref/0000000002","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),

        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "","doi_ra2":""},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},[],[],True,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "xyz.crossref/0000000002","doi_ra2":""},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},[],[],True,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},[],[],True,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "","doi_ra2":"DataCite"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "xyz.crossref/0000000002","doi_ra2":"DataCite"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "xyz.crossref/0000000003","doi_ra2":"DataCite"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref", "doi2": "","doi_ra2":"JaLC2"},{"doi": "xyz.crossref/0000000002","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (2,{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "","doi_ra2":""},{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "xyz.crossref/0000000003","doi_ra2":"Crossref"},[],[],True,False),
        (2,{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "xyz.crossref/0000000003","doi_ra2":"Crossref"},['The specified DOI is wrong and fixed with the registered DOI.'],[],True,False),
        (2,{"doi": "xyz.crossref/0000000003","doi_ra":"JaLC2","doi2": "xyz.crossref/0000000002","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000003","doi_ra":"JaLC2","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (2,{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "xyz.crossref/0000000003","doi_ra2":"Crossref"},{"doi": "xyz.crossref/0000000003","doi_ra":"Crossref","doi2": "xyz.crossref/0000000003","doi_ra2":"Crossref"},[],[],True,False),
        (2,{"doi": None,"doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"","doi2": None,"doi_ra2":None},[],['Please specify DOI prefix/suffix.'],True,False),
        (2,{"doi": "xyz.crossref/0000000002","doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.crossref/0000000002","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (2,{"doi": None,"doi_ra":"Crossref","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"Crossref","doi2": "","doi_ra2":"Crossref"},[],['Please specify DOI prefix/suffix.'],True,False),

        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},[],[],False,False),
        (3,{"doi": "","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": None,"doi_ra2":None},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "","doi_ra2":""},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},[],[],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "xyz.datacite/0000000003","doi_ra2":""},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},[],[],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},[],[],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "","doi_ra2":"JaLC"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "xyz.datacite/0000000003","doi_ra2":"JaLC"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "xyz.datacite/0000000004","doi_ra2":"JaLC"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "","doi_ra2":"JaLC2"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (3,{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "","doi_ra2":""},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (3,{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (3,{"doi": "xyz.datacite/0000000004","doi_ra":"JaLC2","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": None,"doi_ra2":None},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (3,{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "xyz.datacite/0000000004","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (3,{"doi": None,"doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.','The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (3,{"doi": None,"doi_ra":"DataCite","doi2": None,"doi_ra2":None},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),

        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},[],[],True,False),
        (3,{"doi": "","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "","doi_ra":"","doi2": "","doi_ra2":""},[],['Please specify DOI prefix/suffix.'],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.datacite/0000000003","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "","doi_ra2":""},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},[],[],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "xyz.datacite/0000000003","doi_ra2":""},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},[],[],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},[],[],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "","doi_ra2":"JaLC"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "xyz.datacite/0000000003","doi_ra2":"JaLC"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "xyz.datacite/0000000004","doi_ra2":"JaLC"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite", "doi2": "","doi_ra2":"JaLC2"},{"doi": "xyz.datacite/0000000003","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (3,{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "","doi_ra2":""},{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "xyz.datacite/0000000004","doi_ra2":"DataCite"},[],[],True,False),
        (3,{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "xyz.datacite/0000000004","doi_ra2":"DataCite"},['The specified DOI is wrong and fixed with the registered DOI.'],[],True,False),
        (3,{"doi": "xyz.datacite/0000000004","doi_ra":"JaLC2","doi2": "xyz.datacite/0000000003","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000004","doi_ra":"JaLC2","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (3,{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "xyz.datacite/0000000004","doi_ra2":"DataCite"},{"doi": "xyz.datacite/0000000004","doi_ra":"DataCite","doi2": "xyz.datacite/0000000004","doi_ra2":"DataCite"},[],[],True,False),
        (3,{"doi": None,"doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"","doi2": None,"doi_ra2":None},[],['Please specify DOI prefix/suffix.'],True,False),
        (3,{"doi": "xyz.datacite/0000000003","doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.datacite/0000000003","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (3,{"doi": None,"doi_ra":"DataCite","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"DataCite","doi2": "","doi_ra2":"DataCite"},[],['Please specify DOI prefix/suffix.'],True,False),


        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},[],[],False,False),
        (4,{"doi": "","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": None,"doi_ra2":None},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "","doi_ra2":""},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},[],[],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "xyz.ndl/0000000004","doi_ra2":""},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},[],[],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},[],[],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "","doi_ra2":"DataCite"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "xyz.ndl/0000000004","doi_ra2":"DataCite"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "xyz.ndl/0000000005","doi_ra2":"DataCite"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "","doi_ra2":"JaLC2"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (4,{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "","doi_ra2":""},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (4,{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (4,{"doi": "xyz.ndl/0000000005","doi_ra":"JaLC2","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": None,"doi_ra2":None},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (4,{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000005","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),
        (4,{"doi": None,"doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.','The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],False,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (4,{"doi": None,"doi_ra":"NDL JaLC","doi2": None,"doi_ra2":None},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],False,False),

        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},[],[],True,False),
        (4,{"doi": "","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "","doi_ra":"","doi2": "","doi_ra2":""},[],['Please specify DOI prefix/suffix.'],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"", "doi2": "","doi_ra2":""},{"doi": "xyz.ndl/0000000004","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "","doi_ra2":""},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},[],[],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "xyz.ndl/0000000004","doi_ra2":""},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},[],[],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},[],[],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "","doi_ra2":"DataCite"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "xyz.ndl/0000000004","doi_ra2":"DataCite"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "xyz.ndl/0000000005","doi_ra2":"DataCite"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.', 'The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC", "doi2": "","doi_ra2":"JaLC2"},{"doi": "xyz.ndl/0000000004","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},['The specified DOI RA is wrong and fixed with the correct DOI RA of the registered DOI.'],[],True,False),
        (4,{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "","doi_ra2":""},{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000005","doi_ra2":"NDL JaLC"},[],[],True,False),
        (4,{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000005","doi_ra2":"NDL JaLC"},['The specified DOI is wrong and fixed with the registered DOI.'],[],True,False),
        (4,{"doi": "xyz.ndl/0000000005","doi_ra":"JaLC2","doi2": "xyz.ndl/0000000004","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000005","doi_ra":"JaLC2","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (4,{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000005","doi_ra2":"NDL JaLC"},{"doi": "xyz.ndl/0000000005","doi_ra":"NDL JaLC","doi2": "xyz.ndl/0000000005","doi_ra2":"NDL JaLC"},[],[],True,False),
        (4,{"doi": None,"doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"","doi2": None,"doi_ra2":None},[],['Please specify DOI prefix/suffix.'],True,False),
        (4,{"doi": "xyz.ndl/0000000004","doi_ra":None,"doi2": None,"doi_ra2":None},{"doi": "xyz.ndl/0000000004","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (4,{"doi": None,"doi_ra":"NDL JaLC","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"NDL JaLC","doi2": "","doi_ra2":"NDL JaLC"},[],['Please specify DOI prefix/suffix.'],True,False),

        (5,{"doi":"","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"JaLC","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.jalc","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc","doi_ra":"JaLC","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.jalc/","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc/","doi_ra":"JaLC","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.jalc","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (5,{"doi":"xyz.jalc/","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc/","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (5,{"doi":"","doi_ra":"Crossref","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"Crossref","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.crossref","doi_ra":"Crossref","doi2":None,"doi_ra2":None},{"doi":"xyz.crossref","doi_ra":"Crossref","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.crossref/","doi_ra":"Crossref","doi2":None,"doi_ra2":None},{"doi":"xyz.crossref/","doi_ra":"Crossref","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.crossref","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.crossref","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (5,{"doi":"xyz.crossref/","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.crossref/","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (5,{"doi":"","doi_ra":"DataCite","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"DataCite","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.datacite","doi_ra":"DataCite","doi2":None,"doi_ra2":None},{"doi":"xyz.datacite","doi_ra":"DataCite","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.datacite/","doi_ra":"DataCite","doi2":None,"doi_ra2":None},{"doi":"xyz.datacite/","doi_ra":"DataCite","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.datacite","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.datacite","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (5,{"doi":"xyz.datacite/","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.datacite/","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (5,{"doi":"","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.ndl","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.ndl/","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl/","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},[],[],False,False),
        (5,{"doi":"xyz.ndl","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (5,{"doi":"xyz.ndl/","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl/","doi_ra":"","doi2":None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (5,{"doi":"xyz.ndl","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl","doi_ra":"JaLC","doi2":None,"doi_ra2":None},[],['Specified Prefix of DOI is incorrect.'],False,False),
        (5,{"doi":"xyz.ndl/","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl/","doi_ra":"JaLC","doi2":None,"doi_ra2":None},[],['Specified Prefix of DOI is incorrect.'],False,False),
        # 更新によるDOI付与
        (5,{"doi":"","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI prefix/suffix.'],True,False),
        (5,{"doi":"","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"JaLC","doi2":"","doi_ra2":"JaLC"},[],['Please specify DOI prefix/suffix.'],True,False),
        (5,{"doi":"xyz.jalc","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc","doi_ra":"JaLC","doi2":"xyz.jalc","doi_ra2":"JaLC"},[],['Please specify DOI suffix.'],True,False),
        (5,{"doi":"xyz.jalc/","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc/","doi_ra":"JaLC","doi2":"xyz.jalc/","doi_ra2":"JaLC"},[],['Please specify DOI suffix.'],True,False),
        (5,{"doi":"xyz.jalc/xyz","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc/xyz","doi_ra":"JaLC","doi2":"xyz.jalc/xyz","doi_ra2":"JaLC"},[],[],True,False),
        (5,{"doi":"xyz.jalc","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (5,{"doi":"xyz.jalc/","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.jalc/","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (5,{"doi":"","doi_ra":"Crossref","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"Crossref","doi2":"","doi_ra2":"Crossref"},[],['Please specify DOI prefix/suffix.'],True,False),
        (5,{"doi":"xyz.crossref","doi_ra":"Crossref","doi2":None,"doi_ra2":None},{"doi":"xyz.crossref","doi_ra":"Crossref","doi2":"xyz.crossref","doi_ra2":"Crossref"},[],['Please specify DOI suffix.'],True,False),
        (5,{"doi":"xyz.crossref/","doi_ra":"Crossref","doi2":None,"doi_ra2":None},{"doi":"xyz.crossref/","doi_ra":"Crossref","doi2":"xyz.crossref/","doi_ra2":"Crossref"},[],['Please specify DOI suffix.'],True,False),
        (5,{"doi":"xyz.crossref","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.crossref","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (5,{"doi":"xyz.crossref/","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.crossref/","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (5,{"doi":"","doi_ra":"DataCite","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"DataCite","doi2":"","doi_ra2":"DataCite"},[],['Please specify DOI prefix/suffix.'],True,False),
        (5,{"doi":"xyz.datacite","doi_ra":"DataCite","doi2":None,"doi_ra2":None},{"doi":"xyz.datacite","doi_ra":"DataCite","doi2":"xyz.datacite","doi_ra2":"DataCite"},[],['Please specify DOI suffix.'],True,False),
        (5,{"doi":"xyz.datacite/","doi_ra":"DataCite","doi2":None,"doi_ra2":None},{"doi":"xyz.datacite/","doi_ra":"DataCite","doi2":"xyz.datacite/","doi_ra2":"DataCite"},[],['Please specify DOI suffix.'],True,False),
        (5,{"doi":"xyz.datacite","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.datacite","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (5,{"doi":"xyz.datacite/","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.datacite/","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (5,{"doi":"","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},{"doi":"","doi_ra":"NDL JaLC","doi2":"","doi_ra2":"NDL JaLC"},[],['Please specify DOI prefix/suffix.'],True,False),
        (5,{"doi":"xyz.ndl","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl","doi_ra":"NDL JaLC","doi2":"xyz.ndl","doi_ra2":"NDL JaLC"},[],['Please specify DOI suffix.'],True,False),
        (5,{"doi":"xyz.ndl/","doi_ra":"NDL JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl/","doi_ra":"NDL JaLC","doi2":"xyz.ndl/","doi_ra2":"NDL JaLC"},[],['Please specify DOI suffix.'],True,False),
        (5,{"doi":"xyz.ndl","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (5,{"doi":"xyz.ndl/","doi_ra":"","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl/","doi_ra":"","doi2":None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (5,{"doi":"xyz.ndl","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl","doi_ra":"JaLC","doi2":"xyz.ndl","doi_ra2":"JaLC"},[],['Please specify DOI suffix.', 'Specified Prefix of DOI is incorrect.'],True,False),
        (5,{"doi":"xyz.ndl/","doi_ra":"JaLC","doi2":None,"doi_ra2":None},{"doi":"xyz.ndl/","doi_ra":"JaLC","doi2":"xyz.ndl/","doi_ra2":"JaLC"},[],['Please specify DOI suffix.', 'Specified Prefix of DOI is incorrect.'],True,False),
        # 新規登録時DOI付与
        (None,{"doi": "","doi_ra":"","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"","doi2": None,"doi_ra2":None},[],[],False,False),
        (None,{"doi": "","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"JaLC","doi2": None,"doi_ra2":None},[],[],False,False),
        (None,{"doi": "xyz.jalc","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc","doi_ra":"JaLC","doi2": None,"doi_ra2":None},[],[],False,False),
        (None,{"doi": "xyz.jalc/","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/","doi_ra":"JaLC","doi2": None,"doi_ra2":None},[],[],False,False),
        (None,{"doi": "xyz.jalc","doi_ra":"","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (None,{"doi": "xyz.jalc/","doi_ra":"","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/","doi_ra":"","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (None,{"doi": "","doi_ra":"JaLC2","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"JaLC2","doi2": None,"doi_ra2":None},[],['DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],False,False),
        (None,{"doi": "xyz.jalc/abc","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/abc","doi_ra":"JaLC","doi2": None,"doi_ra2":None},[],['Do not specify DOI suffix.'],False,False),
        # 新規登録時DOI付与
        (None,{"doi": "","doi_ra":"","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"","doi2": None,"doi_ra2":None},[],['Please specify DOI prefix/suffix.'],True,False),
        (None,{"doi": "","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"JaLC","doi2": "","doi_ra2":"JaLC"},[],['Please specify DOI prefix/suffix.'],True,False),
        (None,{"doi": "xyz.jalc","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc","doi_ra":"JaLC","doi2": "xyz.jalc","doi_ra2":"JaLC"},[],['Please specify DOI suffix.'],True,False),
        (None,{"doi": "xyz.jalc/","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/","doi_ra":"JaLC","doi2": "xyz.jalc/","doi_ra2":"JaLC"},[],['Please specify DOI suffix.'],True,False),
        (None,{"doi": "xyz.jalc","doi_ra":"","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc","doi_ra":"","doi2": None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (None,{"doi": "xyz.jalc/","doi_ra":"","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/","doi_ra":"","doi2": None,"doi_ra2":None},[],['Please specify DOI suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (None,{"doi": "","doi_ra":"JaLC2","doi2": None,"doi_ra2":None},{"doi": "","doi_ra":"JaLC2","doi2": None,"doi_ra2":None},[],['Please specify DOI prefix/suffix.', 'DOI_RA should be set by one of JaLC, Crossref, DataCite, NDL JaLC.'],True,False),
        (None,{"doi": "xyz.jalc/abc","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"doi": "xyz.jalc/abc","doi_ra":"JaLC","doi2": "xyz.jalc/abc","doi_ra2":"JaLC"},[],[],True,False),
        # cnri登録可能
        (None,{"cnri":"","doi": "xyz.jalc/abc","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"cnri":"", "doi": "xyz.jalc/abc","doi_ra":"JaLC","doi2": "xyz.jalc/abc","doi_ra2":"JaLC"},[],[],True,True),
        (None,{"cnri":"","doi": "","doi_ra":"","doi2": None,"doi_ra2":None},{"cnri":"","doi": "","doi_ra":"","doi2": None,"doi_ra2":None},[],['Please specify DOI prefix/suffix.'],True,True),
        (None,{"cnri":"test_cnri","doi": "xyz.jalc/abc","doi_ra":"JaLC","doi2": None,"doi_ra2":None},{"cnri":"test_cnri","doi": "xyz.jalc/abc","doi_ra":"JaLC","doi2": "xyz.jalc/abc","doi_ra2":"JaLC"},[],[],True,True),
        (None,{"cnri":"test_cnri","doi": "","doi_ra":"","doi2": None,"doi_ra2":None},{"cnri":"test_cnri","doi": "","doi_ra":"","doi2": None,"doi_ra2":None},[],[],True,True),
    ])
@pytest.mark.skip("Run time is too long and all tests failed.")
def test_handle_fill_system_item3(app,doi_records,item_id,before_doi,after_doi,warnings,errors,is_change_identifier,is_register_cnri):
    app.config.update(
        WEKO_HANDLE_ALLOW_REGISTER_CRNI=is_register_cnri
    )
    before = {
            "metadata": {
                "path": ["1667004052852"],
                "pubdate": "2022-10-29",
                "item_1617186331708": [
                    {"subitem_1551255647225": "title", "subitem_1551255648112": "en"}
                ],
                "item_1617258105262": {
                    "resourcetype": "conference paper",
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                },
                "item_1617605131499": [
                    {
                        "accessrole": "open_access",
                        "date": [{"dateType": "Available", "dateValue": "2022-10-29"}],
                        "filename": "a.zip",
                        "filesize": [{"value": "82 KB"}],
                        "format": "application/zip",
                    }
                ],
            },
            "pos_index": ["IndexA"],
            "publish_status": "public",
            "edit_mode": "Keep",
            "file_path": [""],
            "item_type_name": "デフォルトアイテムタイプ（フル）",
            "item_type_id": 1,
            "$schema": "https://localhost:8443/items/jsonschema/1",
        }

    if item_id:
        before["id"] = "{}".format(item_id)
        before["uri"] = "https://localhost:8443/records/{}".format(item_id)
        before["metadata"]["item_1617605131499"][0]["url"] = {"url": "https://weko3.example.org/record/{}/files/a.zip".format(item_id)}

    if before_doi["doi_ra2"] is not None:
        before["metadata"]["item_1617186819068"]=before["metadata"].get("item_1617186819068",{})
        before["metadata"]["item_1617186819068"]["subitem_identifier_reg_type"]= "{}".format(before_doi['doi_ra2'])

    if before_doi["doi2"] is not None:
        before["metadata"]["item_1617186819068"]=before["metadata"].get("item_1617186819068",{})
        before["metadata"]["item_1617186819068"]["subitem_identifier_reg_text"]= "{}".format(before_doi['doi2'])

    if before_doi['doi_ra'] is not None:
        before["doi_ra"]="{}".format(before_doi['doi_ra'])

    if before_doi['doi'] is not None:
        before["doi"]="{}".format(before_doi['doi'])

    if "cnri" in before_doi and before_doi["cnri"] is not None:
        before["cnri"] = "{}".format(before_doi["cnri"])

    before_list = [before]
    after = {
            "metadata": {
                "path": ["1667004052852"],
                "pubdate": "2022-10-29",
                "item_1617186331708": [
                    {"subitem_1551255647225": "title", "subitem_1551255648112": "en"}
                ],
                "item_1617258105262": {
                    "resourcetype": "conference paper",
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                },
                "item_1617605131499": [
                    {
                        "accessrole": "open_access",
                        "date": [{"dateType": "Available", "dateValue": "2022-10-29"}],
                        "filename": "a.zip",
                        "filesize": [{"value": "82 KB"}],
                        "format": "application/zip",
                    }
                ],
            },
            "pos_index": ["IndexA"],
            "publish_status": "public",
            "edit_mode": "Keep",
            "file_path": [""],
            "item_type_name": "デフォルトアイテムタイプ（フル）",
            "item_type_id": 1,
            "$schema": "https://localhost:8443/items/jsonschema/1",
            "identifier_key": "item_1617186819068",
            "errors": errors,
            "warnings": warnings,
        }

    if item_id:
        after["id"] = "{}".format(item_id)
        after["uri"] = "https://localhost:8443/records/{}".format(item_id)
        after["metadata"]["item_1617605131499"][0]["url"] = {"url": "https://weko3.example.org/record/{}/files/a.zip".format(item_id)}

    if after_doi["doi_ra"] is not None:
        after["doi_ra"]="{}".format(after_doi['doi_ra'])

    if after_doi["doi"] is not None:
        after["doi"]="{}".format(after_doi["doi"])

    if after_doi["doi_ra2"] is not None:
        after["metadata"]["item_1617186819068"]=after["metadata"].get("item_1617186819068",{})
        after["metadata"]["item_1617186819068"]["subitem_identifier_reg_type"]= "{}".format(after_doi['doi_ra2'])

    if after_doi["doi2"] is not None:
        after["metadata"]["item_1617186819068"]= after["metadata"].get("item_1617186819068",{})
        after["metadata"]["item_1617186819068"]["subitem_identifier_reg_text"]= "{}".format(after_doi['doi2'])

    if "cnri" in after_doi and after_doi["cnri"] is not None:
        after["cnri"] = after_doi["cnri"]

    after_list = [after]

    if is_change_identifier:
        before_list[0]['is_change_identifier']=True
        after_list[0]['is_change_identifier']=True

    with app.test_request_context():
        assert before_list != after_list
        handle_fill_system_item(before_list)
        assert after_list == before_list


# def get_thumbnail_key(item_type_id=0):
def test_get_thumbnail_key(i18n_app, db_itemtype, db_workflow):
    assert get_thumbnail_key(item_type_id=1)


# def handle_check_thumbnail_file_type(thumbnail_paths):
def test_handle_check_thumbnail_file_type(i18n_app):
    assert handle_check_thumbnail_file_type(["/"])


# def handle_check_metadata_not_existed(str_keys, item_type_id=0): *** not yet done
def test_handle_check_metadata_not_existed(i18n_app, db_itemtype):
    # Test 1
    assert not handle_check_metadata_not_existed(
        ".metadata", db_itemtype["item_type"].id
    )


# def handle_get_all_sub_id_and_name(items, root_id=None, root_name=None, form=[]):
@pytest.mark.parametrize(
    "items,root_id,root_name,form,ids,names",
    [
        pytest.param(
            {"interim": {"type": "string"}},
            ".metadata.item_1657196790737[0]",
            "text[0]",
            [{"key": "item_1657196790737[].interim", "type": "text", "notitle": True}],
            [".metadata.item_1657196790737[0].interim"],
            ["text[0].None"],
        ),
        pytest.param(
            {
                "interim": {
                    "enum": [None, "op1", "op2", "op3", "op4"],
                    "type": ["null", "string"],
                    "title": "list",
                    "title_i18n": {"en": "", "ja": ""},
                }
            },
            ".metadata.item_1657204077414[0]",
            "list[0]",
            [
                {
                    "key": "item_1657204077414[].interim",
                    "type": "select",
                    "title": "list",
                    "notitle": True,
                    "titleMap": [
                        {"name": "op1", "value": "op1"},
                        {"name": "op2", "value": "op2"},
                        {"name": "op3", "value": "op3"},
                        {"name": "op4", "value": "op4"},
                    ],
                    "title_i18n": {"en": "", "ja": ""},
                }
            ],
            [".metadata.item_1657204026946.interim[0]"],
            ["check.check[0]"],
        ),
        pytest.param(
            {
                "interim": {
                    "enum": [None, "op1", "op2", "op3", "op4"],
                    "type": ["null", "string"],
                    "title": "list",
                    "format": "select",
                }
            },
            ".metadata.item_1657204070640",
            "list",
            [
                {
                    "key": "item_1657204070640.interim",
                    "type": "select",
                    "title": "list",
                    "titleMap": [
                        {"name": "op1", "value": "op1"},
                        {"name": "op2", "value": "op2"},
                        {"name": "op3", "value": "op3"},
                        {"name": "op4", "value": "op4"},
                    ],
                    "title_i18n": {"en": "", "ja": ""},
                }
            ],
            [".metadata.item_1657204036771[0].interim[0]"],
            ["checjk[0].checjk[0]"],
        ),
        pytest.param(
            {
                "interim": {
                    "type": "array",
                    "items": {"enum": ["op1", "op2", "op3", "op4"], "type": "string"},
                    "title": "check",
                    "format": "checkboxes",
                    "title_i18n": {"en": "", "ja": ""},
                }
            },
            ".metadata.item_1657204026946",
            "check",
            [
                {
                    "key": "item_1657204026946.interim",
                    "type": "template",
                    "title": "check",
                    "titleMap": [
                        {"name": "op1", "value": "op1"},
                        {"name": "op2", "value": "op2"},
                        {"name": "op3", "value": "op3"},
                        {"name": "op4", "value": "op4"},
                    ],
                    "title_i18n": {"en": "", "ja": ""},
                    "templateUrl": "/static/templates/weko_deposit/checkboxes.html",
                }
            ],
            [".metadata.item_1657204043063.interim"],
            ["rad.rad"],
        ),
        pytest.param(
            {
                "interim": {
                    "type": "array",
                    "items": {"enum": ["op1", "op2", "op3", "op4"], "type": "string"},
                    "title": "checjk",
                    "format": "checkboxes",
                    "title_i18n": {"en": "", "ja": ""},
                }
            },
            ".metadata.item_1657204036771[0]",
            "check[0]",
            [
                {
                    "key": "item_1657204036771[].interim",
                    "type": "template",
                    "title": "checjk",
                    "notitle": True,
                    "titleMap": [
                        {"name": "op1", "value": "op1"},
                        {"name": "op2", "value": "op2"},
                        {"name": "op3", "value": "op3"},
                        {"name": "op4", "value": "op4"},
                    ],
                    "title_i18n": {"en": "", "ja": ""},
                    "templateUrl": "/static/templates/weko_deposit/checkboxes.html",
                }
            ],
            [".metadata.item_1657204049138[0].interim"],
            ["rd[0].rd"],
        ),
        pytest.param(
            {
                "interim": {
                    "enum": ["op1", "op2", "op3", "op4"],
                    "type": ["null", "string"],
                    "title": "rad",
                    "format": "radios",
                }
            },
            ".metadata.item_1657204043063",
            "rad",
            [
                {
                    "key": "item_1657204043063.interim",
                    "type": "radios",
                    "title": "rad",
                    "titleMap": [
                        {"name": "op1", "value": "op1"},
                        {"name": "op2", "value": "op2"},
                        {"name": "op3", "value": "op3"},
                        {"name": "op4", "value": "op4"},
                    ],
                    "title_i18n": {"en": "", "ja": ""},
                }
            ],
            [".metadata.item_1657204070640.interim"],
            ["list.list"],
        ),
        pytest.param(
            {
                "interim": {
                    "enum": ["op1", "op2", "op3", "op4"],
                    "type": ["null", "string"],
                    "title": "rd",
                    "title_i18n": {"en": "", "ja": ""},
                }
            },
            ".metadata.item_1657204049138[0]",
            "rd[0]",
            [
                {
                    "key": "item_1657204049138[].interim",
                    "type": "radios",
                    "title": "rd",
                    "notitle": True,
                    "titleMap": [
                        {"name": "op1", "value": "op1"},
                        {"name": "op2", "value": "op2"},
                        {"name": "op3", "value": "op3"},
                        {"name": "op4", "value": "op4"},
                    ],
                    "title_i18n": {"en": "", "ja": ""},
                }
            ],
            [".metadata.item_1657204077414[0].interim"],
            ["list[0].list"],
        ),
    ],
)
def test_handle_get_all_sub_id_and_name(
    app, items, root_id, root_name, form, ids, names
):
    with app.app_context():
        assert ids, names == handle_get_all_sub_id_and_name(
            items, root_id, root_name, form
        )


# def handle_get_all_id_in_item_type(item_type_id):
def test_handle_get_all_id_in_item_type(i18n_app, db_itemtype):
    assert handle_get_all_id_in_item_type(db_itemtype["item_type"].id)


# def handle_check_consistence_with_mapping(mapping_ids, keys): *** not yet done
def test_handle_check_consistence_with_mapping(i18n_app):
    mapping_ids = ["abc"]
    keys = ["abc"]

    # Test 1
    assert not handle_check_consistence_with_mapping(mapping_ids, keys)


# def handle_check_duplication_item_id(ids: list): *** not yet done
def test_handle_check_duplication_item_id(i18n_app):
    ids = [[1, 2, 3, 4], 2, 3, 4]

    # Test 1
    assert not handle_check_duplication_item_id(ids)


# def export_all(root_url, user_id, data): *** not yet done
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_export_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_export_all(db_activity, i18n_app, users, item_type, db_records2, redis_connect, db, create_export_all_data, mocker):
    i18n_app.config["WEKO_ADMIN_CACHE_PREFIX"] = "test_admin_cache_{name}_{user_id}"
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_search_ui.utils.os.getenv", return_value="/tmp/bulk_export"):
            with patch("weko_search_ui.utils.os.makedirs") as mock_makedirs:
                mock_makedirs.return_value = None  # モックの戻り値を設定
                root_url = "/"
                user_id = users[3]["obj"].id
                data = {"item_type_id": "1", "item_id_range": "1"}
                data2 = {"item_type_id": "-1", "item_id_range": "1-9"}
                start_time_str = '2024/05/21 23:44:12'
                msg_key = i18n_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
                    name="MSG_EXPORT_ALL", user_id=current_user.get_id()
                )
                uri_key = i18n_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
                    name="URI_EXPORT_ALL", user_id=current_user.get_id()
                )
                file_key = i18n_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
                    name="RUN_MSG_EXPORT_ALL_FILE_CREATE", user_id=current_user.get_id()
                )
                datastore = redis_connect

                task = MagicMock()
                task.task_id = 1
                mocker.patch("weko_search_ui.tasks.write_files_task", return_value=task)
                mocker.patch('builtins.open', side_effect=unittest.mock.mock_open())
                mocker.patch("weko_search_ui.utils.pickle.dump")

                # datastore.put(uri_key, "testuri".encode('utf-8'))
                datastore.delete(uri_key)
                export_all(root_url, user_id, data, start_time_str)
                msg = datastore.get(msg_key)
                assert msg.decode() == ""

                with patch("weko_search_ui.utils.delete_exported_file", return_value=None) as mock_delete_file:
                    datastore.put(uri_key, 'test_uri'.encode('utf-8'))
                    export_all(root_url, user_id, data2, start_time_str)
                    msg = datastore.get(msg_key)
                    mock_delete_file.assert_called_with("test_uri",uri_key)
                    assert msg.decode() == ""

                datastore.delete(uri_key)

                data_no_range = {"item_type_id": "1", "item_id_range": ""}
                export_all(root_url, user_id, data_no_range, start_time_str)

                recid_data_1 = [
                    MagicMock(pid_value=str(1), object_uuid="uuid1", json= {"publish_status": "public"}),  # json属性が存在しない
                    MagicMock(pid_value=str(2), object_uuid="uuid2", json={"publish_status": "private"}),  # publish_statusがPUBLICまたはPRIVATEでない
                ]

                with patch("weko_search_ui.utils.get_all_record_id", return_value=recid_data_1):
                    export_all(root_url, user_id, data, start_time_str)

                    data_err = {"item_type_id": "1", "item_id_range": "10-1"}
                    export_all(root_url, user_id, data_err, start_time_str)
                    msg = datastore.get(msg_key)
                    assert msg.decode() == "Export failed. Please check item id range."

                    with patch("weko_search_ui.utils.get_record_ids", return_value={}):
                        export_all(root_url, user_id, data, start_time_str)

                    with patch("builtins.open", side_effect=SQLAlchemyError("Test SQLAlchemyError")):
                        export_all(root_url, user_id, data, start_time_str)

                    with patch("weko_search_ui.tasks.write_files_task.apply_async", return_value=None):
                        with patch("weko_search_ui.utils.WekoRecord.get_record_by_uuid", side_effect=SQLAlchemyError("test_error")):
                            export_all(root_url, user_id, data, start_time_str)

                    # recidsをモックして、record_idsが空になるように設定
                    recids = [
                        MagicMock(pid_value=str(uuid.uuid4()), object_uuid="uuid1", json=None),  # json属性が存在しない
                        MagicMock(pid_value=str(uuid.uuid4()), object_uuid="uuid2", json={"publish_status": "draft"}),  # publish_statusがPUBLICまたはPRIVATEでない
                        MagicMock(pid_value=str(uuid.uuid4()), object_uuid="uuid3", json={})  # json属性にpublish_statusが含まれていない
                    ]

                    with patch("weko_search_ui.utils.db.session.query", return_value=recids):
                        export_all(root_url, user_id, data, start_time_str)

                    with patch("weko_search_ui.utils.math.ceil", side_effect=Exception("test_error")):
                        export_all(root_url, user_id, data, start_time_str)

                    # raise Exception in _get_item_type_list
                    with patch("weko_search_ui.utils.ItemTypes.get_by_id", side_effect=Exception("test_error")):
                        export_all(root_url, user_id, data, start_time_str)

                    # # raise Exception in _get_export_data
                    with patch("weko_search_ui.tasks.write_files_task", side_effect=Exception("test_error")):
                        export_all(root_url, user_id, data_no_range, start_time_str)
                with patch("weko_search_ui.utils.get_all_record_id", return_value=[]):
                    export_all(root_url, user_id, data, start_time_str)

                with patch("weko_search_ui.utils.get_all_record_id", side_effect=SQLAlchemyError("test_error")) as mock_get:
                    export_all(root_url, user_id, data, start_time_str)
                    assert mock_get.call_count==6
                    assert json.loads(datastore.get(file_key).decode()).get("cancel_flg")==True
                    assert datastore.get(msg_key).decode() == "Export failed."

def test_get_retry_info():
    # Test case 1: When item_type_id is included in retry_info
    item_type_id = "1"
    retry_info = {
        "1": {
            "counter": 5,
            "part": 2,
            "max": "10"
        }
    }
    fromid = "1"

    counter, file_part, from_pid = get_retry_info(item_type_id, retry_info, fromid)

    assert counter == 5
    assert file_part == 2
    assert from_pid == "10"

    # Test case 2: When item_type_id is not included in retry_info
    item_type_id = "2"
    retry_info = {}
    fromid = "1"

    counter, file_part, from_pid = get_retry_info(item_type_id, retry_info, fromid)

    assert counter == 0
    assert file_part == 1
    assert from_pid == "1"

    # Test case 3: When fromid is empty
    item_type_id = "2"
    retry_info = {}
    fromid = ""

    counter, file_part, from_pid = get_retry_info(item_type_id, retry_info, fromid)

    assert counter == 0
    assert file_part == 1
    assert from_pid == "1"

# def delete_exported_file(uri, cache_key):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_delete_exported_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_delete_exported_file(db,redis_connect,location):

    location.size = 100
    db.session.merge(location)
    db.session.commit()

    loc_uri = location.uri
    loc_id=location.id
    id = uuid.uuid4()
    uri = f"{loc_uri}/test/tmp/dir"
    cache_key="test_cache_key"

    # not exist cache_key in redis
    fi = FileInstance(
        id=id,
        uri=uri,
        size=5,
        updated=None
    )
    db.session.add(fi)
    db.session.commit()
    delete_exported_file(uri, cache_key)
    db.session.commit()
    assert Location.query.filter_by(id=loc_id).one().size == 95
    assert FileInstance.query.filter_by(id=id).one_or_none() == None

    # exist cache_key in redis
    fi = FileInstance(
        id=id,
        uri=uri,
        size=5,
        updated=None
    )
    db.session.add(fi)
    db.session.commit()
    redis_connect.put(cache_key,"test_cache_value".encode("utf-8"),ttl_secs=30)
    delete_exported_file(uri, cache_key)
    db.session.commit()
    assert redis_connect.redis.exists(cache_key) == False
    assert Location.query.filter_by(id=loc_id).one().size == 90
    assert FileInstance.query.filter_by(id=id).one_or_none() == None


# def delete_exported(uri, cache_key):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_delete_exported -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_delete_exported(i18n_app, file_instance_mock,redis_connect,mocker):
    import tempfile, shutil
    mock_delete = mocker.patch("weko_search_ui.utils.delete_exported_file")

    cache_prefix="test_admin_cache_{name}_1"
    uri = "/test/export/tmp_dir"
    export_info = {
        "uri":uri,
        "cache_key":cache_prefix.format(name=WEKO_SEARCH_UI_BULK_EXPORT_URI),
        "task_key":cache_prefix.format(name=WEKO_SEARCH_UI_BULK_EXPORT_TASK),
    }
    task_id = str(uuid.uuid4())
    redis_connect.put(export_info["task_key"],task_id.encode("utf-8"),ttl_secs=30)
    try:
        # not exist cache_key in redis
        export_path = tempfile.mkdtemp()
        result = delete_exported(export_path, export_info)
        assert result == True
        assert os.path.isdir(export_path) is False
        assert redis_connect.redis.exists(export_info["task_key"]) == True
        mock_delete.assert_called_with(uri, export_info["cache_key"])
        mock_delete.reset_mock()

        # exist cache_key in redis
        redis_connect.put(export_info["cache_key"],"/test/download/uri".encode("utf-8"),ttl_secs=30)
        export_path = tempfile.mkdtemp()
        result = delete_exported(export_path, export_info)
        assert result == True
        assert os.path.isdir(export_path) is False
        assert redis_connect.redis.exists(export_info["task_key"]) == False
        mock_delete.assert_called_with(uri, export_info["cache_key"])
        mock_delete.reset_mock()

        # raise exception
        with patch("weko_search_ui.utils.delete_exported_file",side_effect=Exception("test_error")):
            export_path = tempfile.mkdtemp()
            result = delete_exported(export_path, export_info)
            assert result == False
            assert os.path.isdir(export_path) is True
            assert redis_connect.redis.exists(export_info["task_key"]) == False
            shutil.rmtree(export_path)
    finally:
        if redis_connect.redis.exists(export_info["task_key"]):
            redis_connect.delete(export_info["task_key"])
        if redis_connect.redis.exists(export_info["cache_key"]):
            redis_connect.delete(export_info["cache_key"])


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_get_record_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_record_ids():

    # publish_status in status_ok
    mock_recid1 = MagicMock()
    mock_recid1.pid_value = "1"
    mock_recid1.object_uuid = "uuid1"
    mock_recid1.json = {"publish_status": "0", "path": ["100"]}

    # publish_status not in status_ok
    mock_recid2 = MagicMock()
    mock_recid2.pid_value = "2"
    mock_recid2.object_uuid = "uuid2"
    mock_recid2.json = {"publish_status": "-1", "path": ["100"]}

    res = get_record_ids([mock_recid1, mock_recid2])
    assert res == [("1", "uuid1")]


    # path in index_id_list
    mock_recid3 = MagicMock()
    mock_recid3.pid_value = "3"
    mock_recid3.object_uuid = "uuid3"
    mock_recid3.json = {"publish_status": "0", "path": ["100","200"]}

    # path not in index_id_list
    mock_recid4 = MagicMock()
    mock_recid4.pid_value = "4"
    mock_recid4.object_uuid = "uuid4"
    mock_recid4.json = {"publish_status": "0", "path": ["300"]}

    res = get_record_ids([mock_recid3, mock_recid4],["100","200","500"])
    assert res == [("3", "uuid3")]


# def write_files(item_datas, export_path, user_id, retrys):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_write_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_write_files(db_activity, i18n_app, users, redis_connect, mocker, item_type, db_records2):
    import pytz
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        # result is True
        record = d_wekorecord.get_record_by_pid(1)
        item_datas = {
            "item_type_id": "1",
            "name": "test_item_type",
            "recids": ["1"],
            "root_url":"https://localhost/",
            "jsonschema":'items/jsonschema/1',
            "data": {
                "1": record
            }
        }

        mocker.patch("weko_search_ui.utils.os.makedirs")
        mocker.patch('builtins.open', side_effect=unittest.mock.mock_open())
        now = datetime.now()
        mocker_datetime = mocker.patch('weko_search_ui.utils.datetime')
        mocker_datetime.now.return_value = now
        with patch('weko_search_ui.utils.pytz.timezone', return_value=pytz.UTC):
            assert write_files(item_datas, "tests/data/write_files", current_user.get_id(), 0)

        # result is False
        with patch("weko_items_ui.utils.make_stats_file_with_permission", side_effect=SQLAlchemyError("test_error")):
            assert not write_files(item_datas, "tests/data/write_files", current_user.get_id(), 0)


# def cancel_export_all():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_cancel_export_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_cancel_export_all(i18n_app, users, redis_connect, mocker):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        cache_key = i18n_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name="KEY_EXPORT_ALL", user_id=current_user.get_id()
        )
        file_cache_key = i18n_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name="RUN_MSG_EXPORT_ALL_FILE_CREATE", user_id=current_user.get_id()
        )
        file_json = {
            'start_time': '2024/05/21 14:23:46',
            'finish_time': '',
            'export_path': '',
            'cancel_flg': False,
            'write_file_status': {
                '1': 'started'
            }
        }
        file_result_json = {
            'start_time': '2024/05/21 14:23:46',
            'finish_time': '',
            'export_path': '',
            'cancel_flg': True,
            'write_file_status': {
                '1': 'started'
            }
        }
        datastore = redis_connect
        datastore.put(cache_key, "test_task_key".encode("utf-8"), ttl_secs=30)

        # export_status is True
        with patch("weko_search_ui.utils.get_export_status", return_value=(True,None,None,None,None,None,None)):
            datastore.put(file_cache_key, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
            mock_revoke = mocker.patch("weko_search_ui.utils.revoke")
            mock_delete_id = mocker.patch("weko_search_ui.utils.delete_task_id_cache.apply_async")
            result = cancel_export_all()
            assert result == True
            ds_file_json = datastore.get(file_cache_key).decode('utf-8')
            assert json.loads(ds_file_json) == file_result_json
            mock_revoke.assert_called_with("test_task_key",terminate=True)
            mock_delete_id.assert_called_with(args=("test_task_key","admin_cache_KEY_EXPORT_ALL_5"),countdown=60)

        # export_status is False
        with patch("weko_search_ui.utils.get_export_status", return_value=(False,None,None,None,None,None,None)):
            datastore.put(file_cache_key, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
            mock_revoke = mocker.patch("weko_search_ui.utils.revoke")
            mock_delete_id = mocker.patch("weko_search_ui.utils.delete_task_id_cache.apply_async")
            result = cancel_export_all()
            assert result == True
            ds_file_json = datastore.get(file_cache_key).decode('utf-8')
            assert json.loads(ds_file_json) == file_json
            mock_revoke.assert_not_called()
            mock_delete_id.assert_not_called()

        # raise Exception
        with patch("weko_search_ui.utils.get_export_status",side_effect=Exception("test_error")):
            result = cancel_export_all()
            assert result == False

# def delete_task_id_cache_on_missing_meta(task_id, cache_key):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_delete_task_id_cache_on_missing_meta -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_delete_task_id_cache_on_missing_meta(redis_connect):
    cache_key = "test_cache_key"
    redis_connect.put(cache_key, "test_value".encode("utf-8"), ttl_secs=30)
    task_id=str(uuid.uuid4())
    redis_celery = RedisConnection().connection(db=current_app.config['CELERY_RESULT_BACKEND_DB_NO'], kv = True)
    celery_task_key = f"celery-task-meta-{task_id}"

    # exist celery-status in redis
    redis_celery.put(celery_task_key, "test_value".encode("utf-8"), ttl_secs=30)
    result = delete_task_id_cache_on_missing_meta(task_id, cache_key)
    assert result == False
    assert redis_connect.redis.exists(cache_key) == True

    # not exist celery-status in redis
    redis_celery.delete(celery_task_key)
    result = delete_task_id_cache_on_missing_meta(task_id, cache_key)
    assert result == True
    assert redis_connect.redis.exists(cache_key) == False

# def get_export_status():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_get_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_export_status(i18n_app, users, redis_connect,mocker, location):
    import pytz,tempfile
    class MockAsyncResult:
        def __init__(self,task_id):
            self.task_id=task_id
        @property
        def state(self):
            return self.task_id.replace("_task","")
        def successful(self):
            return self.state == "SUCCESS"
        def failed(self):
            return self.state == "FAILED"

    start_time_str = '2024/05/21 14:23:46'
    def create_file_json(status):
        return {
            'start_time': start_time_str,
            'finish_time': '',
            'export_path': '',
            'cancel_flg': False,
            'write_file_status': {
                '1': status
            }
        }

    def create_file_cancel_json(status):
        return {
            'start_time': start_time_str,
            'finish_time': '',
            'export_path': '',
            'cancel_flg': True,
            'write_file_status': {
                '1': status
            }
        }

    def create_not_status_file_json():
        return {
            'start_time': start_time_str,
            'finish_time': '',
            'export_path': '',
            'cancel_flg': False,
            'write_file_status': {}
        }

    def create_not_param_file_json():
        return {
            'start_time': start_time_str,
            'finish_time': '',
            'export_path': '',
            'cancel_flg': False
        }

    mocker.patch("weko_search_ui.utils.AsyncResult",side_effect=MockAsyncResult)
    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        current_app.config["WEKO_ADMIN_CACHE_PREFIX"] = "test_admin_cache_{name}_{user_id}"
        tmp_cache_key = "cache::test_temp_dir_info"
        current_app.config["WEKO_ADMIN_CACHE_TEMP_DIR_INFO_KEY_DEFAULT"] = tmp_cache_key
        cache_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name="KEY_EXPORT_ALL", user_id=current_user.get_id()
        )
        cache_uri = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name="URI_EXPORT_ALL", user_id=current_user.get_id()
        )
        cache_msg = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name="MSG_EXPORT_ALL", user_id=current_user.get_id()
        )
        run_msg = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name="RUN_MSG_EXPORT_ALL", user_id=current_user.get_id()
        )
        file_msg = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name='RUN_MSG_EXPORT_ALL_FILE_CREATE', user_id=current_user.get_id()
        )
        datastore = redis_connect

        datastore.put(cache_uri, "test_uri".encode("utf-8"), ttl_secs=30)
        datastore.put(cache_msg, "test_msg".encode("utf-8"), ttl_secs=30)
        datastore.put(run_msg, "test_run_msg".encode("utf-8"), ttl_secs=30)
        # not exist task_id
        datastore.delete(cache_key)
        result=get_export_status()
        assert result == (False, "test_uri", "test_msg", "test_run_msg", "", "", "")

        # exist task_id, celery_result_cache is not exist
        with patch("weko_search_ui.utils.delete_task_id_cache_on_missing_meta",
                   return_value=True):
            datastore.put(cache_key, "PENDING_task".encode("utf-8"), ttl_secs=30)
            result=get_export_status()
            assert result == (False, "test_uri", "test_msg", "test_run_msg", "", "", "")

        mocker.patch("weko_search_ui.utils.delete_task_id_cache_on_missing_meta",
                    return_value=False)

        # task is not success, failed, revoked (write_file_data is not exist)
        datastore.put(cache_key, "PENDING_task".encode("utf-8"), ttl_secs=30)
        datastore.delete(file_msg)
        datastore.put(file_msg, json.dumps({}).encode('utf-8'), ttl_secs=30)
        result=get_export_status()
        assert result == (False, "test_uri", "test_msg", "test_run_msg", "", "", "")

        # task is not success, failed, revoked (write_file_status is not exist)
        # write_file_status=BEFORE
        datastore.put(cache_key, "PENDING_task".encode("utf-8"), ttl_secs=30)
        datastore.put(file_msg, json.dumps(create_not_param_file_json()).encode('utf-8'), ttl_secs=30)
        result=get_export_status()
        assert result == (True, "test_uri", "test_msg", "test_run_msg", "", start_time_str, "")

        # task is not success, failed, revoked (write_file_status is started)
        # write_file_status=STARTED
        datastore.put(cache_key, "PENDING_task".encode("utf-8"), ttl_secs=30)
        datastore.put(file_msg, json.dumps(create_file_json('started')).encode('utf-8'), ttl_secs=30)
        result=get_export_status()
        assert result == (True, "test_uri", "test_msg", "test_run_msg", "STARTED", start_time_str, "")

        # task is not success, failed, revoked (cancel_flg is True)
        # write_file_status=REVOKED
        datastore.put(cache_key, "PENDING_task".encode("utf-8"), ttl_secs=30)
        datastore.put(file_msg, json.dumps(create_file_cancel_json('started')).encode('utf-8'), ttl_secs=30)
        result=get_export_status()
        assert result == (True, "test_uri", "test_msg", "test_run_msg", "REVOKED", start_time_str, "")

        # write_file_status is canceled
        with patch("weko_search_ui.utils.AsyncResult",return_value=MockAsyncResult("REVOKED_task")):
            export_path = tempfile.mkdtemp()
            datastore.delete(file_msg)
            file_json = create_file_json('canceled')
            file_json['export_path'] = export_path
            datastore.put(file_msg, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
            result = get_export_status()
            assert result == (False, "test_uri", "test_msg", "test_run_msg", "REVOKED", start_time_str, "")
            assert os.path.isdir(export_path) is False

        # write_file_status is errorwith patch("weko_search_ui.utils.AsyncResult",return_value=MockAsyncResult("FAILED_task")):
        with patch("weko_search_ui.utils.AsyncResult",return_value=MockAsyncResult("FAILED_task")):
            datastore.delete(file_msg)
            file_json = create_file_json('error')
            file_json['export_path'] = export_path
            datastore.put(file_msg, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
            result = get_export_status()
            assert result == (False, "test_uri", "test_msg", "test_run_msg", "ERROR", start_time_str, "")
            assert os.path.isdir(export_path) is False

        # task is success, failed, revoked (write_file_status is finished)
        mocker.patch("os.path.isdir", return_value=False)
        datastore.delete(cache_key)
        datastore.put(cache_key, "SUCCESS_task".encode("utf-8"), ttl_secs=30)
        datastore.delete(file_msg)
        file_json = create_file_json('finished')
        export_path = 'tests/data/import'
        file_json['export_path'] = export_path
        datastore.put(file_msg, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
        now = datetime.now()
        expire = now+timedelta(days=current_app.config["WEKO_SEARCH_UI_EXPORT_FILE_RETENTION_DAYS"])
        mocker_datetime = mocker.patch('weko_search_ui.utils.datetime')
        mocker_datetime.now.return_value = now
        mocker.patch('weko_search_ui.utils.bagit.make_bag')
        mocker.patch('weko_search_ui.utils.shutil.make_archive')
        mocker.patch("builtins.open", mock_open(read_data=b"data"))
        mocker.patch("weko_search_ui.utils.FileInstance.create", return_value=MagicMock(uri="test_uri"))
        mocker.patch("weko_search_ui.utils.Location.get_default", return_value=MagicMock(uri="test_location"))
        task = MagicMock()
        task.task_id = 1
        with patch('weko_search_ui.utils.pytz.timezone', return_value=pytz.UTC):
            result = get_export_status()
            uri = datastore.get(cache_uri)
            temp_cache_test = {
                "is_export":True,
                "uri":uri.decode(),
                "cache_key":cache_uri,
                "task_key":cache_key,
                "expire": expire.strftime("%Y-%m-%d %H:%M:%S")
            }
            assert result == (False, uri.decode(), "test_msg", "test_run_msg", "SUCCESS", start_time_str, now.strftime('%Y/%m/%d %H:%M:%S'))
            assert TempDirInfo().get(export_path) == temp_cache_test
            TempDirInfo().delete(export_path)
        # os.path.isdir is True
        with patch("weko_search_ui.utils.os.path.isdir", return_value=True):
            datastore.delete(file_msg)
            file_json = create_file_json('finished')
            file_json['export_path'] = 'tests/data/import'
            mocker.patch('weko_search_ui.utils.bagit.make_bag')
            mocker.patch('weko_search_ui.utils.shutil.make_archive')
            mocker.patch("builtins.open", mock_open(read_data=b"data"))
            mocker.patch("weko_search_ui.utils.FileInstance.create", return_value=MagicMock(uri="test_uri"))
            mocker.patch("weko_search_ui.utils.Location.get_default", return_value=MagicMock(uri="test_location"))
            datastore.put(file_msg, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
            datastore.delete(run_msg)
            datastore.put(run_msg, "test_run_msg".encode("utf-8"), ttl_secs=30)
            result=get_export_status()
            assert result == (False, uri.decode(), "test_msg", "test_run_msg", "SUCCESS", start_time_str, "")

        # task is success, failed, revoked (write_file_status is not value)
        datastore.put(cache_key, "PENDING_task".encode("utf-8"), ttl_secs=30)
        file_json = create_not_status_file_json()
        file_json['export_path'] = 'tests/data/import'
        datastore.put(file_msg, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
        now = datetime.now()
        mocker_datetime = mocker.patch('weko_search_ui.utils.datetime')
        mocker_datetime.now.return_value = now
        mocker.patch('weko_search_ui.utils.bagit.make_bag')
        mocker.patch('weko_search_ui.utils.shutil.make_archive')
        task = MagicMock()
        task.task_id = 1
        result=get_export_status()
        uri = datastore.get(cache_uri)
        assert result == (True, uri.decode(), "test_msg", "test_run_msg", "SUCCESS", start_time_str, "")

        # raise Exception
        with patch("weko_search_ui.utils.AsyncResult",side_effect=Exception("test_error")):
            datastore.delete(cache_uri)
            datastore.put(cache_uri, "test_uri".encode("utf-8"), ttl_secs=30)
            datastore.delete(cache_msg)
            datastore.put(cache_msg, "test_msg".encode("utf-8"), ttl_secs=30)
            datastore.delete(run_msg)
            datastore.put(run_msg, "test_run_msg".encode("utf-8"), ttl_secs=30)
            result=get_export_status()
            assert result == (False, "test_uri", "test_msg", "test_run_msg", "", "", "")


# def handle_check_item_is_locked(item):
def test_handle_check_item_is_locked(i18n_app, db_activity):
    # Doesn't return any value
    try:
        assert not handle_check_item_is_locked(db_activity["item"])
    except Exception as e:
        if "item_is_being_edit" in str(e) or "item_is_deleted" in str(e):
            assert True
        else:
            pass


# def handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata):
def test_handle_remove_es_metadata(i18n_app, es_item_file_pipeline, es_records):
    item = es_records["results"][0]["item"]
    bef_metadata = {}
    bef_metadata["_id"] = 9
    bef_metadata["_version"] = -1
    bef_metadata["_source"] = {"control_number": 9999}

    bef_last_ver_metadata = {}
    bef_last_ver_metadata["_id"] = 8
    bef_last_ver_metadata["_version"] = 1
    bef_last_ver_metadata["_source"] = {"control_number": 8888}

    # Doesn't return any value
    assert not handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata)

    # Doesn't return any value
    item["status"] = "new"
    assert not handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata)

    # Doesn't return any value
    item["status"] = "upgrade"
    assert not handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata)


# def check_index_access_permissions(func):
@check_index_access_permissions
def test_check_index_access_permissions(i18n_app, client_request_args, users):
    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):

        # Test is successful if there are no errors
        assert True


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_index_access_permissions_issue_50659 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search_ui/.tox/c1/tmp
def test_check_index_access_permissions_issue_50659(i18n_app, client_request_args, users):
    @check_index_access_permissions
    def test_function():
        return True

    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        with patch("flask.request.args", new_callable=lambda: {"search_type": "2", "q": "0"}):
            assert test_function() == True

        # args not have q
        with patch("flask.request.args", new_callable=lambda: {"search_type": "2"}):
            with pytest.raises(BadRequest):
                test_function()

        # q is not digit
        with patch("flask.request.args", new_callable=lambda: {"search_type": "2", "q": "test"}):
            with pytest.raises(BadRequest):
                test_function()


# def handle_check_file_metadata(list_record, data_path):
def test_handle_check_file_metadata(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[0]]
    data_path = "test/test/test"

    # Doesn't return any value
    assert not handle_check_file_metadata(list_record, data_path)

    # with patch("weko_search_ui.utils.handle_check_file_content", return_value=):

# def handle_check_restricted_access_property(list_record)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_restricted_access_property_en -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_restricted_access_property_en(app, db, users, record_restricted, terms, db_itemtype_restricted_access, db_workflow):
    # 利用規約(terms)が設定されていない。提供(provide)が設定されていない。
    list_record = [record_restricted[0]]
    handle_check_restricted_access_property(list_record)
    assert list_record[0]["errors"] == None

    # 利用規約(terms)に存在する規約が設定されている。提供(provide)が設定されていない。
    list_record = [record_restricted[1]]
    handle_check_restricted_access_property(list_record)
    assert list_record[0]["errors"] == None

    # 利用規約(terms)が設定されていない。提供(provide)に存在するロールID、ワークフローが設定されている。
    list_record = [record_restricted[2]]
    handle_check_restricted_access_property(list_record)
    assert list_record[0]["errors"] == None

    restricted_access_json ={
            "key": "168065611041",
            "content": {
                "en": {
                    "title": "Privacy Policy for WEKO3",
                    "content": "Privacy Policyobligations"
                },
                "ja": {
                    "title": "利用規約",
                    "content": "利用規約本文"
                }
            },
            "existed": True
        }

    ################################
    # 英語モード
    ################################
    with app.test_request_context():
        with set_locale("en"):
            with patch("weko_admin.utils.get_restricted_access", return_value=restricted_access_json):
                # 利用規約(terms)に存在しない利用規約が設定されている。提供(provide)が設定されていない。
                list_record = [record_restricted[3]]
                handle_check_restricted_access_property(list_record)
                assert list_record[0]["errors"] == ["The specified terms does not exist in the system"]

                # 利用規約(terms)が設定されていない。提供(provide)に存在しないワークフローが設定されている。
                list_record = [record_restricted[4]]
                handle_check_restricted_access_property(list_record)
                assert list_record[0]["errors"] == ["The specified provinding method does not exist in the system"]

                # 利用規約(terms)が設定されていない。提供(provide)に存在しないロールが設定されている。
                list_record = [record_restricted[5]]
                handle_check_restricted_access_property(list_record)
                assert list_record[0]["errors"] == ["The specified provinding method does not exist in the system"]

# def handle_check_restricted_access_property(list_record)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_restricted_access_property_ja -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_restricted_access_property_ja(app, db, users, record_restricted, terms, db_itemtype_restricted_access, db_workflow):
    restricted_access_json ={
            "key": "168065611041",
            "content": {
                "en": {
                    "title": "Privacy Policy for WEKO3",
                    "content": "Privacy Policyobligations"
                },
                "ja": {
                    "title": "利用規約",
                    "content": "利用規約本文"
                }
            },
            "existed": True
        }
    ################################
    # 日本語モード
    ################################
    with app.test_request_context():
        with set_locale("ja"):
            with patch("weko_admin.utils.get_restricted_access", return_value=restricted_access_json):
                # 利用規約(terms)に存在しない利用規約が設定されている。提供(provide)が設定されていない。
                list_record = [record_restricted[3]]
                handle_check_restricted_access_property(list_record)
                assert list_record[0]["errors"] == ["指定する利用規約はシステムに存在しません。"]
                # 利用規約(terms)が設定されていない。提供(provide)に存在しないワークフローが設定されている。
                list_record = [record_restricted[4]]
                handle_check_restricted_access_property(list_record)
                assert list_record[0]["errors"] == ["指定する提供方法はシステムに存在しません。"]

                # 利用規約(terms)が設定されていない。提供(provide)に存在しないロールが設定されている。
                list_record = [record_restricted[5]]
                handle_check_restricted_access_property(list_record)
                assert list_record[0]["errors"] == ["指定する提供方法はシステムに存在しません。"]

# def check_terms_in_system(key, item_index, item)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_terms_in_system -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_terms_in_system(terms, record_restricted):
    # 正常系
    key = "item_1685583796047"
    item = record_restricted[1]
    assert check_terms_in_system(key, item) == True

    # metadataにkeyが存在しない
    key = "item_111111111111"
    item = record_restricted[1]
    assert check_terms_in_system(key, item) == False

    # metadataにtermsが存在しない
    key = "item_1685583796047"
    item = record_restricted[8]
    assert check_terms_in_system(key, item) == True

    # metadataにtermsが自由入力の場合
    key = "item_1685583796047"
    item = record_restricted[1]
    item['metadata'][key][0]['terms'] = 'term_free'
    assert check_terms_in_system(key, item) == True

    # "terms": システムに存在しない適当な値
    key = "item_1685583796047"
    item = record_restricted[3]
    assert check_terms_in_system(key, item) == False

    # "terms": システムに存在しない適当な値
    # get_restricted_accessをスタブにし、戻り値をNoneにする。
    with patch('weko_admin.utils.get_restricted_access',return_value=None):
        key = "item_1685583796047"
        item = record_restricted[3]
        assert check_terms_in_system(key, item) == False

# def check_provide_in_system(key, item_index, item, provides)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_check_provide_in_system -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_provide_in_system(users, db_workflow, record_restricted):
    # "provide": [ {"workflow: システムに存在するワークフローID"},{"role", システムに存在するロールID} ]
    # 引数のprovides= itemに設定したprovideを設定する。
    key = "item_1685583796047"
    item = record_restricted[2]
    assert check_provide_in_system(key, item) == True

    # "provide": [ {"workflow: システムに存在しないワークフローID"},{"role", システムに存在するロールID} ]
    # 数のprovides= itemに設定したprovideを設定する。
    key = "item_1685583796047"
    item = record_restricted[4]
    assert check_provide_in_system(key, item) == False

    # "provide": [ {"workflow: システムに存在するワークフローID"},{"role", システムに存在しないロールID} ]
    # 数のprovides= itemに設定したprovideを設定する。
    key = "item_1685583796047"
    item = record_restricted[5]
    assert check_provide_in_system(key, item) == False

    # "key"存在せず
    key = "item_111111111111"
    item = record_restricted[1]
    assert check_provide_in_system(key, item) == False

    # "provide"存在せず
    key = "item_1685583796047"
    item = record_restricted[1]
    assert check_provide_in_system(key, item) == True

    # "workflow"存在せず
    key = "item_1685583796047"
    item = record_restricted[6]
    assert check_provide_in_system(key, item) == True

    # "role"存在せず
    key = "item_1685583796047"
    item = record_restricted[7]
    assert check_provide_in_system(key, item) == True

    key = "item_1685583796047"
    item = record_restricted[9]
    assert check_provide_in_system(key, item) == True


# def handle_check_file_path(paths, data_path, is_new=False, is_thumbnail=False, is_single_thumbnail=False):
def test_handle_check_file_path(i18n_app):
    paths = ["/test"]
    data_path = "/"

    assert handle_check_file_path(paths, data_path)


# def handle_check_file_content(record, data_path):
def test_handle_check_file_content(i18n_app, record_with_metadata):
    list_record = record_with_metadata[0]
    data_path = "test/test/test"

    assert handle_check_file_content(list_record, data_path)


# def handle_check_thumbnail(record, data_path):
def test_handle_check_thumbnail(i18n_app, record_with_metadata):
    record = record_with_metadata[0]
    data_path = "test/test/test"

    assert handle_check_thumbnail(record, data_path)

    record = {"thumbnail_path": "/", "status": "new"}
    with patch(
        "weko_search_ui.utils.handle_check_file_path", return_value=("error", "warning")
    ):
        assert handle_check_thumbnail(record, data_path)


# def get_key_by_property(record, item_map, item_property):
def test_get_key_by_property(i18n_app):
    record = "record"
    item_map = {"item_property": "item_property"}
    item_property = "item_property"

    assert get_key_by_property(record, item_map, item_property)
    assert not get_key_by_property("", {}, "")


# def get_data_by_property(item_metadata, item_map, mapping_key):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_get_data_by_property -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_data_by_property(i18n_app):
    item_metadata = {}
    item_map = {"mapping_key": "test.test"}
    mapping_key = "mapping_key"

    data, key_list = get_data_by_property(item_metadata, item_map, mapping_key)
    assert data == None
    assert key_list == "test.test"
    data, key_list = get_data_by_property(item_metadata, {}, mapping_key)
    assert data == None
    assert key_list == None

    with patch(
        "weko_workflow.utils.get_sub_item_value", return_value=[True, ["value"]]
    ):
        data, key_list = get_data_by_property(item_metadata, item_map, mapping_key)
        assert data == ["value"]
        assert key_list == "test.test"

        item_map = {"mapping_key": "test.test,test1.test1"}
        mapping_key = "mapping_key"
        data, key_list = get_data_by_property(item_metadata, item_map, mapping_key)
        assert data == ["value", "value"]
        assert key_list == "test.test,test1.test1"


# def get_filenames_from_metadata(metadata):
def test_get_filenames_from_metadata(i18n_app, record_with_metadata):
    metadata = record_with_metadata[0]["metadata"]
    assert get_filenames_from_metadata(metadata)

    metadata = {
        "_id": [{"filename": False}],
        "filename": "test_filename",
    }
    assert get_filenames_from_metadata(metadata)

    metadata["_id"] = [{"test": "test"}]
    assert not get_filenames_from_metadata(metadata)


# def handle_check_filename_consistence(file_paths, meta_filenames):
def test_handle_check_filename_consistence(i18n_app):
    file_paths = ["abc/abc", "abc/abc"]
    meta_filenames = [{"id": 1, "filename": "abc"}, {"id": 2, "filename": "xyz"}]

    assert handle_check_filename_consistence(file_paths, meta_filenames)


@pytest.mark.parametrize(
    "item_id, before_doi,after_doi,warnings,errors,is_change_identifier",
    [
        (
            1,
            {"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},
            {"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},
            [],
            [],
            True
        ),
    ]
)
def test_function_issue34520(app, doi_records, item_id, before_doi, after_doi, warnings, errors, is_change_identifier):
    before = {
            "metadata": {
                "path": ["1667004052852"],
                "pubdate": "2022-10-29",
                "item_1617186331708": [
                    {"subitem_1551255647225": "title", "subitem_1551255648112": "en"}
                ],
                "item_1617258105262": {
                    "resourcetype": "conference paper",
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                },
                "item_1617605131499": [
                    {
                        "accessrole": "open_access",
                        "date": [{"dateType": "Available", "dateValue": "2022-10-29"}],
                        "filename": "a.zip",
                        "filesize": [{"value": "82 KB"}],
                        "format": "application/zip",
                    }
                ],
            },
            "pos_index": ["IndexA"],
            "publish_status": "public",
            "edit_mode": "Keep",
            "file_path": [""],
            "item_type_name": "デフォルトアイテムタイプ（フル）",
            "item_type_id": 1,
            "$schema": "https://localhost/items/jsonschema/1",
        }

    if item_id:
        before["id"] = "{}".format(item_id)
        before["uri"] = "https://localhost/records/{}".format(item_id)
        before["metadata"]["item_1617605131499"][0]["url"] = {"url": "https://weko3.example.org/record/{}/files/a.zip".format(item_id)}

    if before_doi["doi_ra2"] is not None:
        before["metadata"]["item_1617186819068"]=before["metadata"].get("item_1617186819068",{})
        before["metadata"]["item_1617186819068"]["subitem_identifier_reg_type"]= "{}".format(before_doi['doi_ra2'])

    if before_doi["doi2"] is not None:
        before["metadata"]["item_1617186819068"]=before["metadata"].get("item_1617186819068",{})
        before["metadata"]["item_1617186819068"]["subitem_identifier_reg_text"]= "{}".format(before_doi['doi2'])

    if before_doi['doi_ra'] is not None:
        before["doi_ra"]="{}".format(before_doi['doi_ra'])

    if before_doi['doi'] is not None:
        before["doi"]="{}".format(before_doi['doi'])

    before_list = [before]
    after = {
            "metadata": {
                "path": ["1667004052852"],
                "pubdate": "2022-10-29",
                "item_1617186331708": [
                    {"subitem_1551255647225": "title", "subitem_1551255648112": "en"}
                ],
                "item_1617258105262": {
                    "resourcetype": "conference paper",
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                },
                "item_1617605131499": [
                    {
                        "accessrole": "open_access",
                        "date": [{"dateType": "Available", "dateValue": "2022-10-29"}],
                        "filename": "a.zip",
                        "filesize": [{"value": "82 KB"}],
                        "format": "application/zip",
                    }
                ],
            },
            "pos_index": ["IndexA"],
            "publish_status": "public",
            "edit_mode": "Keep",
            "file_path": [""],
            "item_type_name": "デフォルトアイテムタイプ（フル）",
            "item_type_id": 1,
            "$schema": "https://localhost/items/jsonschema/1",
            "identifier_key": "item_1617186819068",
            "errors": errors,
            "warnings": warnings,
        }

    if item_id:
        after["id"] = "{}".format(item_id)
        after["uri"] = "https://localhost/records/{}".format(item_id)
        after["metadata"]["item_1617605131499"][0]["url"] = {"url": "https://weko3.example.org/record/{}/files/a.zip".format(item_id)}

    if after_doi["doi_ra"] is not None:
        after["doi_ra"]="{}".format(after_doi['doi_ra'])

    if after_doi["doi"] is not None:
        after["doi"]="{}".format(after_doi["doi"])

    if after_doi["doi_ra2"] is not None:
        after["metadata"]["item_1617186819068"]=after["metadata"].get("item_1617186819068",{})
        after["metadata"]["item_1617186819068"]["subitem_identifier_reg_type"]= "{}".format(after_doi['doi_ra2'])

    if after_doi["doi2"] is not None:
        after["metadata"]["item_1617186819068"]= after["metadata"].get("item_1617186819068",{})
        after["metadata"]["item_1617186819068"]["subitem_identifier_reg_text"]= "{}".format(after_doi['doi2'])

    after_list = [after]

    if is_change_identifier:
        before_list[0]['is_change_identifier']=True
        after_list[0]['is_change_identifier']=True

    with app.test_request_context():
        assert before_list != after_list
        handle_fill_system_item(before_list)
        assert after_list == before_list

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_function_issue34535 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search_ui/.tox/c1/tmp
def test_function_issue34535(db,db_index,db_itemtype,location,db_oaischema,mocker):
    mocker.patch("weko_search_ui.utils.find_and_update_location_size")
    # register item
    indexer = WekoIndexer()
    indexer.get_es_index()
    record_data = {"_oai":{"id":"oai:weko3.example.org:00000004","sets":[]},"path":["1"],"owner":1,"recid":"4","title":["test item in br"],"pubdate":{"attribute_name":"PubDate","attribute_value":"2022-11-21"},"_buckets":{"deposit":"0796e490-6dcf-4e7d-b241-d7201c3de83a"},"_deposit":{"id":"4","pid":{"type":"depid","value":"4","revision_id":0},"owner":1,"owners":[1],"status":"published","created_by":1},"item_title":"test item in br","author_link":[],"item_type_id":"1","publish_date":"2022-11-21","publish_status":"0","weko_shared_ids":[],"item_1617186331708":{"attribute_name":"Title","attribute_value_mlt":[{"subitem_1551255647225":"test item in br","subitem_1551255648112":"ja"}]},"item_1617186626617":{"attribute_name":"Description","attribute_value_mlt":[{"subitem_description":"this is line1.\nthis is line2.","subitem_description_type":"Abstract","subitem_description_language":"en"}]},"item_1617258105262":{"attribute_name":"Resource Type","attribute_value_mlt":[{"resourceuri":"http://purl.org/coar/resource_type/c_5794","resourcetype":"conference paper"}]},"relation_version_is_last":True}
    item_data = {"id":"4","pid":{"type":"depid","value":"4","revision_id":0},"lang":"ja","path":[1],"owner":1,"title":"test item in br","owners":[1],"status":"published","$schema":"https://192.168.56.103/items/jsonschema/1","pubdate":"2022-11-21","edit_mode":"keep","created_by":1,"owners_ext":{"email":"wekosoftware@nii.ac.jp","username":"","displayname":""},"deleted_items":["item_1617605131499"],"shared_user_ids":[],"weko_shared_ids":[],"item_1617186331708":[{"subitem_1551255647225":"test item in br","subitem_1551255648112":"ja"}],"item_1617186626617":[{"subitem_description":"this is line1.\nthis is line2.","subitem_description_type":"Abstract","subitem_description_language":"en"}],"item_1617258105262":{"resourceuri":"http://purl.org/coar/resource_type/c_5794","resourcetype":"conference paper"}}
    rec_uuid = uuid.uuid4()
    recid = PersistentIdentifier.create(
        "recid",
        str(4),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    depid = PersistentIdentifier.create(
        "depid",
        str(4),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rel = PIDRelation.create(recid, depid, 3)
    db.session.add(rel)
    record = WekoRecord.create(record_data, id_=rec_uuid)
    item = ItemsMetadata.create(item_data, id_=rec_uuid)
    deposit = WekoDeposit(record, record.model)
    deposit.commit()
    indexer.upload_metadata(record_data, rec_uuid, 1, False)

    # new item
    root_path = os.path.dirname(os.path.abspath(__file__))
    new_item = {'$schema': 'https://192.168.56.103/items/jsonschema/1', 'edit_mode': 'Keep', 'errors': None, 'file_path': [''], 'filenames': [{'filename': '', 'id': '.metadata.item_1617605131499[0].filename'}], 'id': '4', 'identifier_key': 'item_1617186819068', 'is_change_identifier': False, 'item_title': 'test item in br', 'item_type_id': 1, 'item_type_name': 'デフォルトアイテムタイプ（フル）', 'metadata': {'item_1617186331708': [{'subitem_1551255647225': 'test item in br', 'subitem_1551255648112': 'ja'}], 'item_1617186626617': [{'subitem_description': 'this is line1.<br/>this is line2.', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'path': [1], 'pubdate': '2022-11-21'}, 'pos_index': ['Faculty of Humanities and Social Sciences'], 'publish_status': 'public', 'status': 'keep', 'uri': 'https://192.168.56.103/records/4', 'warnings': [], 'root_path': root_path}

    register_item_metadata(new_item,root_path,True)
    record = WekoDeposit.get_record(recid.object_uuid)
    assert record == {'_oai': {'id': 'oai:weko3.example.org:00000004', 'sets': ['1']}, 'path': ['1'], 'owner': 1, 'recid': '4', 'title': ['test item in br'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-11-21'}, '_buckets': {'deposit': '0796e490-6dcf-4e7d-b241-d7201c3de83a'}, '_deposit': {'id': '4', 'pid': {'type': 'depid', 'value': '4', 'revision_id': 0}, 'owner': 1, 'owners': [1], 'status': 'draft', 'created_by': 1}, 'item_title': 'test item in br', 'author_link': [], 'item_type_id': '1', 'publish_date': '2022-11-21', 'publish_status': '0', 'weko_shared_ids': [], 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'test item in br', 'subitem_1551255648112': 'ja'}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'this is line1.\nthis is line2.', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}, 'relation_version_is_last': True, 'control_number': '4'}

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_function_issue34958 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_function_issue34958(app, make_itemtype):
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
        itemtype_data = {
            "name":"test_import",
            "schema":"tests/item_type/34958_schema.json",
            "form":"tests/item_type/34958_form.json",
            "render":"tests/item_type/34958_render.json",
            "mapping":"tests/item_type/34958_mapping.json",
        }
        itemtype_id = "34958"
        itemtype = make_itemtype(itemtype_id, itemtype_data)
        data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "data/import_file/34958"
        )
        csv_path = "issue34958_import.csv"


        test = [{"publish_status": "public", "pos_index": ["Index A"], "metadata": {"pubdate": "2022-11-11", "item_1671508244520": {"subitem_1551255647225": "Extra items test", "subitem_1551255648112": "en"}, "item_1671508260839": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}, "item_1671508308460": [{"interim": "test_text_value0"}, {"interim": "test_text_value1"}], "item_1671606815997": "test_text", "item_1617186626617": {"subitem_description": "test_description"}}, "edit_mode": "keep", "item_type_name": "test_import", "item_type_id": 34958, "$schema": "http://TEST_SERVER/items/jsonschema/34958", "warnings": ["The following items are not registered because they do not exist in the specified item type. item_1617186626617.subitem_description"], "is_change_identifier": False, "errors": None}]
        result = unpackage_import_file(data_path,csv_path,"csv",False,False)

        assert result == test

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_function_issue34520 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "item_id, before_doi,after_doi,warnings,errors,is_change_identifier",
    [
        (
            1,
            {"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},
            {"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},
            [],
            [],
            True
        ),
        (
            1000,
            {"doi": "xyz.jalc/0000000001","doi_ra":"JaLC","doi2": "xyz.jalc/0000000001","doi_ra2":"JaLC"},
            {"doi": "xyz.jalc/0000000001","doi_ra":"JaLC"},
            [],
            [],
            True

        )
    ]
)
def test_handle_fill_system_item_issue34520(app, doi_records, item_id, before_doi, after_doi, warnings, errors, is_change_identifier):
    before = {
            "metadata": {
                "path": ["1667004052852"],
                "pubdate": "2022-10-29",
                "item_1617186331708": [
                    {"subitem_1551255647225": "title", "subitem_1551255648112": "en"}
                ],
                "item_1617258105262": {
                    "resourcetype": "conference paper",
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                },
                "item_1617605131499": [
                    {
                        "accessrole": "open_access",
                        "date": [{"dateType": "Available", "dateValue": "2022-10-29"}],
                        "filename": "a.zip",
                        "filesize": [{"value": "82 KB"}],
                        "format": "application/zip",
                    }
                ],
            },
            "pos_index": ["IndexA"],
            "publish_status": "public",
            "edit_mode": "Keep",
            "file_path": [""],
            "item_type_name": "デフォルトアイテムタイプ（フル）",
            "item_type_id": 1,
            "$schema": "https://localhost/items/jsonschema/1",
        }

    if item_id:
        before["id"] = "{}".format(item_id)
        before["uri"] = "https://localhost/records/{}".format(item_id)
        before["metadata"]["item_1617605131499"][0]["url"] = {"url": "https://weko3.example.org/record/{}/files/a.zip".format(item_id)}

    if before_doi.get("doi_ra2") is not None:
        before["metadata"]["item_1617186819068"]=before["metadata"].get("item_1617186819068",{})
        before["metadata"]["item_1617186819068"]["subitem_identifier_reg_type"]= "{}".format(before_doi['doi_ra2'])

    if before_doi.get("doi2") is not None:
        before["metadata"]["item_1617186819068"]=before["metadata"].get("item_1617186819068",{})
        before["metadata"]["item_1617186819068"]["subitem_identifier_reg_text"]= "{}".format(before_doi['doi2'])

    if before_doi.get('doi_ra') is not None:
        before["doi_ra"]="{}".format(before_doi['doi_ra'])

    if before_doi.get('doi') is not None:
        before["doi"]="{}".format(before_doi['doi'])

    before_list = [before]
    after = {
            "metadata": {
                "path": ["1667004052852"],
                "pubdate": "2022-10-29",
                "item_1617186331708": [
                    {"subitem_1551255647225": "title", "subitem_1551255648112": "en"}
                ],
                "item_1617258105262": {
                    "resourcetype": "conference paper",
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                },
                "item_1617605131499": [
                    {
                        "accessrole": "open_access",
                        "date": [{"dateType": "Available", "dateValue": "2022-10-29"}],
                        "filename": "a.zip",
                        "filesize": [{"value": "82 KB"}],
                        "format": "application/zip",
                    }
                ],
            },
            "pos_index": ["IndexA"],
            "publish_status": "public",
            "edit_mode": "Keep",
            "file_path": [""],
            "item_type_name": "デフォルトアイテムタイプ（フル）",
            "item_type_id": 1,
            "$schema": "https://localhost/items/jsonschema/1",
            "identifier_key": "item_1617186819068",
            "errors": errors,
            "warnings": warnings,
        }

    if item_id:
        after["id"] = "{}".format(item_id)
        after["uri"] = "https://localhost/records/{}".format(item_id)
        after["metadata"]["item_1617605131499"][0]["url"] = {"url": "https://weko3.example.org/record/{}/files/a.zip".format(item_id)}

    if after_doi.get("doi_ra") is not None:
        after["doi_ra"]="{}".format(after_doi['doi_ra'])

    if after_doi.get("doi") is not None:
        after["doi"]="{}".format(after_doi["doi"])

    if after_doi.get("doi_ra2") is not None:
        after["metadata"]["item_1617186819068"]=after["metadata"].get("item_1617186819068",{})
        after["metadata"]["item_1617186819068"]["subitem_identifier_reg_type"]= "{}".format(after_doi['doi_ra2'])

    if after_doi.get("doi2") is not None:
        after["metadata"]["item_1617186819068"]= after["metadata"].get("item_1617186819068",{})
        after["metadata"]["item_1617186819068"]["subitem_identifier_reg_text"]= "{}".format(after_doi['doi2'])

    after_list = [after]
    if is_change_identifier:
        before_list[0]['is_change_identifier']=True
        after_list[0]['is_change_identifier']=True

    with app.test_request_context():
        assert before_list != after_list
        handle_fill_system_item(before_list)
        assert after_list == before_list


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_exist_record_issue35315 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, uri, warnings, errors,status",
    [
        (1, "http://TEST_SERVER/records/1",[],[],"keep"),
        (1000, "http://TEST_SERVER/records/1",[],["Specified URI and system URI do not match."],None),
        (1000, "http://TEST_SERVER/records/1000",[],["Item does not exits in the system"],None),
        (None,None,[],[],"new")
    ])
def test_handle_check_exist_record_issue35315(app, doi_records, id, uri, warnings, errors, status):
    before = {
        "metadata": {
            "path": ["1667004052852"],
            "pubdate": "2022-10-29",
            "item_1617186331708": [
                { "subitem_1551255647225": "title", "subitem_1551255648112": "en" }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794"
            }
        },
        "pos_index": ["IndexA"],
        "publish_status": "public",
        "edit_mode": "Keep",
        "file_path": [""],
        "item_type_name": "デフォルトアイテムタイプ（フル）",
        "item_type_id": 1,
        "$schema": "https://localhost/items/jsonschema/1",
        "errors":[],
        "warnings":[]
    }
    if id is not None:
        before["id"] = id
    if uri is not None:
        before["uri"] = uri
    before_list = [before]

    after = {
        "metadata": {
            "path": ["1667004052852"],
            "pubdate": "2022-10-29",
            "item_1617186331708": [
                { "subitem_1551255647225": "title", "subitem_1551255648112": "en" }
            ],
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794"
            }
        },
        "pos_index": ["IndexA"],
        "publish_status": "public",
        "edit_mode": "Keep",
        "file_path": [""],
        "item_type_name": "デフォルトアイテムタイプ（フル）",
        "item_type_id": 1,
        "$schema": "https://localhost/items/jsonschema/1",
        "errors": errors,
        "warnings":warnings
    }
    after["id"] = id
    if uri is not None:
        after["uri"] = uri
    after["status"] = status

    after_list = [after]

    with app.test_request_context():
        assert before_list != after_list
        result = handle_check_exist_record(before_list)
        assert after_list == result


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_conbine_aggs -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_conbine_aggs():
    some_path = {"took": "215","time_out": False,"_shards": {"total": "1","successful": "1","skipped": "0","failed": "0"},"hits": {"total": "0","max_score": None,"hits": []},"aggregations": {"path_0": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []},"path_1": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [{"key": "1234567891011","doc_count": "1","date_range": {"doc_count": "1","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "1"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}}]},"path_2": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [{"key": "1234567891012","doc_count": "2","date_range": {"doc_count": "2","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "2"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}},{"key": "1234567891013","doc_count": "3","date_range": {"doc_count": "1","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "3"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}}]}}}
    test = {"took": "215","time_out": False,"_shards": {"total": "1","successful": "1","skipped": "0","failed": "0"},"hits": {"total": "0","max_score": None,"hits": []},"aggregations": {"path": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [{"key": "1234567891011","doc_count": "1","date_range": {"doc_count": "1","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "1"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}},{"key": "1234567891012","doc_count": "2","date_range": {"doc_count": "2","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "2"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}},{"key": "1234567891013","doc_count": "3","date_range": {"doc_count": "1","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "3"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}}]}}}
    result = combine_aggs(some_path)
    assert test == result

    one_path = {"took": "215","time_out": False,"_shards": {"total": "1","successful": "1","skipped": "0","failed": "0"},"hits": {"total": "0","max_score": None,"hits": []},"aggregations": {"path": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [{"key": "1234567891011","doc_count": "1","date_range": {"doc_count": "1","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "1"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}},{"key": "1234567891012","doc_count": "2","date_range": {"doc_count": "2","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "2"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}},{"key": "1234567891013","doc_count": "3","date_range": {"doc_count": "1","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "3"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}}]}}}
    result = combine_aggs(one_path)
    assert test == result

    not_agg = {"took": "215","time_out": False,"_shards": { "total": "1", "successful": "1", "skipped": "0", "failed": "0" },"hits": { "total": "0", "max_score": None, "hits": [] }}
    test = {'took': '215', 'time_out': False, '_shards': {'total': '1', 'successful': '1', 'skipped': '0', 'failed': '0'}, 'hits': {'total': '0', 'max_score': None, 'hits': []}}
    result = combine_aggs(not_agg)
    assert test == result

    other_agg = {"took": "215","time_out": False,"_shards": { "total": "1", "successful": "1", "skipped": "0", "failed": "0" },"hits": { "total": "0", "max_score": None, "hits": [] },"aggregations":{"path_0":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},"path_1":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets":[{"key": "1234567891011","doc_count": "1","date_range":{"doc_count": "1","available":{"buckets":[{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "1",},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0",},],},},"Data Type":{"doc_count": "0","Data Type":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Distributor":{"doc_count": "0","Distributor":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Data Language":{"doc_count": "1","Data Language":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Temporal":{"doc_count": "1","Temporal":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Access":{"doc_count": "1","Access":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"no_available": { "doc_count": "0" },"Topic":{"doc_count": "1","Topic":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Location":{"doc_count": "1","Location":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},},],},"path_2":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets":[{"key": "1234567891012","doc_count": "2","date_range":{"doc_count": "2","available":{"buckets":[{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "2",},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0",},],},},"Data Type":{"doc_count": "0","Data Type":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Distributor":{"doc_count": "0","Distributor":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Data Language":{"doc_count": "1","Data Language":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Temporal":{"doc_count": "1","Temporal":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Access":{"doc_count": "1","Access":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"no_available": { "doc_count": "0" },"Topic":{"doc_count": "1","Topic":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Location":{"doc_count": "1","Location":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},},{"key": "1234567891013","doc_count": "3","date_range":{"doc_count": "1","available":{"buckets":[{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "3",},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0",},],},},"Data Type":{"doc_count": "0","Data Type":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Distributor":{"doc_count": "0","Distributor":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Data Language":{"doc_count": "1","Data Language":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Temporal":{"doc_count": "1","Temporal":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Access":{"doc_count": "1","Access":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"no_available": { "doc_count": "0" },"Topic":{"doc_count": "1","Topic":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},"Location":{"doc_count": "1","Location":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [],},},},],},"other":{"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets":[{"key": "1234567891012","doc_count": "2","date_range":{"doc_count": "2","available":{"buckets":[{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "2",},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0",},],},},}]}},}
    test = {"took": "215","time_out": False,"_shards": {"total": "1","successful": "1","skipped": "0","failed": "0"},"hits": {"total": "0","max_score": None,"hits": []},"aggregations": {"other": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [{"key": "1234567891012","doc_count": "2","date_range": {"doc_count": "2","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "2"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}}}]},"path": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": [{"key": "1234567891011","doc_count": "1","date_range": {"doc_count": "1","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "1"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}},{"key": "1234567891012","doc_count": "2","date_range": {"doc_count": "2","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "2"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}},{"key": "1234567891013","doc_count": "3","date_range": {"doc_count": "1","available": {"buckets": [{"key": "*-2023-07-25","to": "1690243200000.0","to_as_string": "2023-07-25","doc_count": "3"},{"key": "2023-07-25-*","from": "1690243200000.0","from_as_string": "2023-07-25","doc_count": "0"}]}},"Data Type": {"doc_count": "0","Data Type": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Distributor": {"doc_count": "0","Distributor": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Data Language": {"doc_count": "1","Data Language": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Temporal": {"doc_count": "1","Temporal": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Access": {"doc_count": "1","Access": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"no_available": {"doc_count": "0"},"Topic": {"doc_count": "1","Topic": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}},"Location": {"doc_count": "1","Location": {"doc_count_error_upper_bound": "0","sum_order_doc_count": "0","buckets": []}}}]}}}
    result = combine_aggs(other_agg)
    assert test == result


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_result_download_ui -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_result_download_ui(app):
    valid_json = [{
        "id": 0,
        "name": {
            "i18n": "title",
            "en": "Title",
            "ja": "タイトル"
        },
        "roCrateKey": "title"
    }]
    with open('tests/data/rocrate/rocrate_list.json', 'r') as f:
        search_result = json.load(f)

    with app.test_request_context():
        with patch('weko_search_ui.utils.search_results_to_tsv', return_value=StringIO('test')):
            # 9 execute
            res = result_download_ui(search_result, valid_json)
            assert res.status_code == 200

            # 10 Empty search_result
            with pytest.raises(NotFound):
                res = result_download_ui(None, valid_json)


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_search_results_to_tsv -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_search_results_to_tsv(app):
    valid_json = [
        {
            "id": 0,
            "name": {
                "i18n": "title",
                "en": "Title",
                "ja": "タイトル"
            },
            "roCrateKey": "title"
        },
        {
            "id": 1,
            "name": {
                "i18n": "field",
                "en": "Field",
                "ja": "分野"
            },
            "roCrateKey": "genre"
        },
    ]
    with open('tests/data/rocrate/rocrate_list.json', 'r') as f:
        search_result = json.load(f)

    with app.test_request_context():
        # 11 Execute
        with patch('weko_search_ui.utils.create_tsv_row', return_value={"Title": "Sample Title","Field": "Sample Field"}):
            res = search_results_to_tsv(search_result, valid_json)
            assert res.getvalue() == "Title\tField\nSample Title\tSample Field\n"

        # 12 Empty json
        input_json = [{}]
        with patch('weko_search_ui.utils.create_tsv_row', return_value={}):
            try:
                search_results_to_tsv(search_result, input_json)
                assert True
            except:
                assert False


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_create_tsv_row -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_create_tsv_row(app):
    field_rocrate_dict = {'Title': 'title', 'Field': 'genre'}
    with open('tests/data/rocrate/rocrate_list.json', 'r') as f:
        search_result = json.load(f)

    data_response = [
        graph for graph in search_result[0]['metadata']['@graph']
        if graph.get('@id') == './'
    ][0]

    with app.test_request_context():
        # 13 Execute
        res = create_tsv_row(field_rocrate_dict, data_response)
        assert res == {
            'Title': 'メタボリックシンドロームモデルマウスの多臓器遺伝子発現量データ',
            'Field': '生物学'
        }


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_flatten_data_encode_filename -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_flatten_data_encode_filename(app, tmpdir):
    # Arrange
    def _create_files_from_files_info(list_record, data_path):
        for item in list_record:
            metadata = item.get("metadata")
            files_info = metadata.get("files_info")
            for file_info in files_info:
                key = file_info.get("key")
                for file in metadata.get(key, []):
                    filename = file.get("filename")
                    if not filename:
                        continue
                    # get file directory
                    file_dir = os.path.join(data_path, os.path.dirname(filename))
                    # create directory if not exists
                    os.makedirs(file_dir, exist_ok=True)
                    # create file
                    file_path = os.path.join(data_path, filename)
                    with open(file_path, "w") as f:
                        f.write(f"This is a placeholder for {filename}")

    data_path = tmpdir.mkdir("data")
    with open("tests/data/list_records/list_record_handle_flatten_data_encode_filename.json", "r") as json_file:
        list_record = json.load(json_file)
    with open("tests/data/list_records/list_record_handle_flatten_data_encode_filename_expected.json", "r") as json_file:
        expected_list_record = json.load(json_file)

    # Create files from files_info
    _create_files_from_files_info(list_record, data_path)

    # Act
    with patch("weko_search_ui.utils.current_app.logger") as mock_logger:
        handle_flatten_data_encode_filename(list_record, data_path)

    # Assert
    assert list_record == expected_list_record
    for filepath in list_record[0].get("file_path"):
        assert os.path.exists(os.path.join(data_path, filepath))


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_get_priority -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_priority():
    """
    get_priority 関数の動作をテストする。
    各ケースで期待される優先度が返されることを確認する。
    """
    # テストケース 1: すべての sele_id が 'isSupplementTo' で、すべての item_id が数字でない場合
    link_data_1 = [
        {'sele_id': 'isSupplementTo', 'item_id': 'abc'},
        {'sele_id': 'isSupplementTo', 'item_id': 'def'}
    ]
    assert get_priority(link_data_1) == 1  # 最高優先度

    # テストケース 2: すべての sele_id が 'isSupplementTo' で、一部の item_id が数字でない場合
    link_data_2 = [
        {'sele_id': 'isSupplementTo', 'item_id': '123'},
        {'sele_id': 'isSupplementTo', 'item_id': 'abc'}
    ]
    assert get_priority(link_data_2) == 2  # 第二優先度

    # テストケース 3: 一部の sele_id が 'isSupplementTo' で、対応する item_id が数字でない場合
    link_data_3 = [
        {'sele_id': 'isSupplementTo', 'item_id': 'abc'},
        {'sele_id': 'isSupplementedBy', 'item_id': '123'}
    ]
    assert get_priority(link_data_3) == 3  # 第三優先度

    # テストケース 4: すべての sele_id が 'isSupplementTo' で、すべての item_id が数字の場合
    link_data_4 = [
        {'sele_id': 'isSupplementTo', 'item_id': '123'},
        {'sele_id': 'isSupplementTo', 'item_id': '456'}
    ]
    assert get_priority(link_data_4) == 4  # 第四優先度

    # テストケース 5: すべての sele_id が 'isSupplementedBy' の場合
    link_data_5 = [
        {'sele_id': 'isSupplementedBy', 'item_id': '123'},
        {'sele_id': 'isSupplementedBy', 'item_id': '456'}
    ]
    assert get_priority(link_data_5) == 5  # 最低優先度

    # テストケース 6: その他の場合
    link_data_6 = [
        {'sele_id': 'normal', 'item_id': '123'},
        {'sele_id': 'isSupplementTo', 'item_id': '456'}
    ]
    assert get_priority(link_data_6) == 6  # その他のケース


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::TestHandleCheckAuthorsPrefix -v -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class TestHandleCheckAuthorsPrefix:

    @pytest.fixture()
    def authors_prefix_settings(self, db):
        apss = list()
        apss.append(AuthorsPrefixSettings(name="WEKO",scheme="WEKO"))
        apss.append(AuthorsPrefixSettings(name="ORCID",scheme="ORCID",url="https://orcid.org/##"))
        apss.append(AuthorsPrefixSettings(name="CiNii",scheme="CiNii",url="https://ci.nii.ac.jp/author/##"))
        apss.append(AuthorsPrefixSettings(name="KAKEN2",scheme="KAKEN2",url="https://nrid.nii.ac.jp/nrid/##"))
        apss.append(AuthorsPrefixSettings(name="ROR",scheme="ROR",url="https://ror.org/##"))
        db.session.add_all(apss)
        db.session.commit()
        return apss

    def test_handle_check_authors_prefix_no_nameidentifiers(self, db, authors_prefix_settings):
        """
        正常系
        条件：nameIdentifiersを含まないレコードの場合
        入力：nameIdentifiersがないレコードのリスト
        期待結果：errorsが追加されない
        """
        # モックデータ
        list_record = [
            {
                "metadata": {
                    "authors": [{"name": "Author 1"}, {"name": "Author 2"}]
                }
            }
        ]

        # AuthorsPrefixSettingsのモック
        with patch('weko_authors.models.AuthorsPrefixSettings') as MockSettings:
            mock_setting = MagicMock()
            mock_setting.scheme = "ORCID"
            MockSettings.query.all.return_value = [mock_setting]

            # テスト対象関数を実行
            handle_check_authors_prefix(list_record)

            # 検証
            assert "errors" not in list_record[0]


    def test_handle_check_authors_prefix_valid_scheme(self, db, authors_prefix_settings):
        """
        正常系
        条件：すべてのnameIdentifierSchemeが許可されたスキームである場合
        入力：有効なスキームを持つレコードのリスト
        期待結果：errorsが追加されない
        """
        # モックデータ
        list_record = [
            {
                "metadata": {
                    "authors": [
                        {
                            "name": "Author 1",
                            "nameIdentifiers": [
                                {"nameIdentifierScheme": "ORCID", "nameIdentifier": "0000-0001-2345-6789"}
                            ]
                        }
                    ]
                }
            }
        ]

        # AuthorsPrefixSettingsのモック
        with patch('weko_authors.models.AuthorsPrefixSettings') as MockSettings:
            mock_setting = MagicMock()
            mock_setting.scheme = "ORCID"
            MockSettings.query.all.return_value = [mock_setting]

            # テスト対象関数を実行
            handle_check_authors_prefix(list_record)

            # 検証
            assert "errors" not in list_record[0]


    def test_handle_check_authors_prefix_invalid_scheme(self, db, authors_prefix_settings):
        """
        異常系
        条件：nameIdentifierSchemeが許可されていないスキームである場合
        入力：無効なスキームを持つレコードのリスト
        期待結果：errorsに該当するエラーメッセージが追加される
        """
        # モックデータ
        list_record = [
            {
                "metadata": {
                    "authors": [
                        {
                            "name": "Author 1",
                            "nameIdentifiers": [
                                {"nameIdentifierScheme": "INVALID", "nameIdentifier": "0000-0001-2345-6789"}
                            ]
                        }
                    ]
                }
            }
        ]

        # AuthorsPrefixSettingsのモック
        with patch('weko_authors.models.AuthorsPrefixSettings') as MockSettings:
            mock_setting = MagicMock()
            mock_setting.scheme = "ORCID"
            MockSettings.query.all.return_value = [mock_setting]

            # テスト対象関数を実行
            handle_check_authors_prefix(list_record)

            # 検証
            assert "errors" in list_record[0]
            assert '"INVALID" is not one of [\'WEKO\', \'ORCID\', \'CiNii\', \'KAKEN2\', \'ROR\'] in authors' in list_record[0]["errors"]


    def test_handle_check_authors_prefix_dict_instead_of_list(self, db, authors_prefix_settings):
        """
        正常系
        条件：authorsが配列ではなくオブジェクト（辞書）である場合
        入力：authorsがオブジェクトのレコードのリスト
        期待結果：正しく処理され、無効なスキームがあればエラーが追加される
        """
        # モックデータ
        list_record = [
            {
                "metadata": {
                    "authors": {
                        "name": "Author 1",
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "INVALID", "nameIdentifier": "0000-0001-2345-6789"}
                        ]
                    }
                }
            }
        ]

        # AuthorsPrefixSettingsのモック
        with patch('weko_authors.models.AuthorsPrefixSettings') as MockSettings:
            mock_setting = MagicMock()
            mock_setting.scheme = "ORCID"
            MockSettings.query.all.return_value = [mock_setting]

            # テスト対象関数を実行
            handle_check_authors_prefix(list_record)

            # 検証
            assert "errors" in list_record[0]
            assert '"INVALID" is not one of [\'WEKO\', \'ORCID\', \'CiNii\', \'KAKEN2\', \'ROR\'] in authors' in list_record[0]["errors"]


    def test_handle_check_authors_prefix_nested_structure(self, db, authors_prefix_settings):
        """
        正常系
        条件：複雑なネスト構造を持つメタデータの場合
        入力：複雑なネスト構造を持つレコードのリスト
        期待結果：すべてのエラーが正しく検出される
        """
        # モックデータ
        list_record = [
            {
                "metadata": {
                    "contributors": [
                        {
                            "name": "Contributor 1",
                            "nameIdentifiers": [
                                {"nameIdentifierScheme": "INVALID1", "nameIdentifier": "0000-0001-2345-6789"}
                            ]
                        }
                    ],
                    "creator": {
                        "name": "Creator 1",
                        "nameIdentifiers": [
                            {"nameIdentifierScheme": "INVALID2", "nameIdentifier": "0000-0001-2345-6789"}
                        ]
                    }
                }
            }
        ]

        # AuthorsPrefixSettingsのモック
        with patch('weko_authors.models.AuthorsPrefixSettings') as MockSettings:
            mock_setting = MagicMock()
            mock_setting.scheme = "ORCID"
            MockSettings.query.all.return_value = [mock_setting]

            # テスト対象関数を実行
            handle_check_authors_prefix(list_record)

            # 検証
            assert "errors" in list_record[0]
            assert len(list_record[0]["errors"]) == 2
            assert '"INVALID1" is not one of [\'WEKO\', \'ORCID\', \'CiNii\', \'KAKEN2\', \'ROR\'] in contributors' in list_record[0]["errors"]
            assert '"INVALID2" is not one of [\'WEKO\', \'ORCID\', \'CiNii\', \'KAKEN2\', \'ROR\'] in creator' in list_record[0]["errors"]


    def test_handle_check_authors_prefix_existing_errors(self, db, authors_prefix_settings):
        """
        正常系
        条件：既にエラーがあるレコードの場合
        入力：既存のエラーを持つレコードのリスト
        期待結果：既存のエラーに新しいエラーが追加される
        """
        # モックデータ
        list_record = [
            {
                "metadata": {
                    "authors": [
                        {
                            "name": "Author 1",
                            "nameIdentifiers": [
                                {"nameIdentifierScheme": "INVALID", "nameIdentifier": "0000-0001-2345-6789"}
                            ]
                        }
                    ],
                    "test1":{"test":"test"},
                    "test2":"test2"
                },
                "errors": ["Existing error"]
            }
        ]

        # AuthorsPrefixSettingsのモック
        with patch('weko_authors.models.AuthorsPrefixSettings') as MockSettings:
            mock_setting = MagicMock()
            mock_setting.scheme = "ORCID"
            MockSettings.query.all.return_value = [mock_setting]

            # テスト対象関数を実行
            handle_check_authors_prefix(list_record)

            # 検証
            assert "errors" in list_record[0]
            assert len(list_record[0]["errors"]) == 2
            assert "Existing error" in list_record[0]["errors"]
            assert '"INVALID" is not one of [\'WEKO\', \'ORCID\', \'CiNii\', \'KAKEN2\', \'ROR\'] in authors' in list_record[0]["errors"]


    def test_handle_check_authors_prefix_none_scheme(self, db, authors_prefix_settings):
        """
        正常系
        条件：nameIdentifierSchemeがNoneの場合
        入力：nameIdentifierSchemeがNoneのレコードのリスト
        期待結果：エラーが追加されない
        """
        # モックデータ
        list_record = [
            {
                "metadata": {
                    "authors": [
                        {
                            "name": "Author 1",
                            "nameIdentifiers": [
                                {"nameIdentifierScheme": None, "nameIdentifier": "0000-0001-2345-6789"}
                            ]
                        }
                    ]
                }
            }
        ]

        # AuthorsPrefixSettingsのモック
        with patch('weko_authors.models.AuthorsPrefixSettings') as MockSettings:
            mock_setting = MagicMock()
            mock_setting.scheme = "ORCID"
            MockSettings.query.all.return_value = [mock_setting]

            # テスト対象関数を実行
            handle_check_authors_prefix(list_record)

            # 検証
            assert "errors" not in list_record[0]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::TestHandleCheckAuthorsAffiliation -v -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class TestHandleCheckAuthorsAffiliation:

    @pytest.fixture()
    def authors_affiliation_settings(self, db):
        aass = list()
        aass.append(AuthorsAffiliationSettings(name="ISNI",scheme="ISNI",url="http://www.isni.org/isni/##"))
        aass.append(AuthorsAffiliationSettings(name="ROR",scheme="ROR",url="https://ror.org/##"))
        db.session.add_all(aass)
        db.session.commit()

        return aass

    @pytest.fixture
    def mock_settings(self, app, db):
        """AuthorsAffiliationSettingsをモックする"""
        setting1 = MagicMock()
        setting1.scheme = "ROR"
        setting2 = MagicMock()
        setting2.scheme = "ISNI"

        with patch('weko_authors.models.AuthorsAffiliationSettings') as mock_settings:
            mock_settings.query.all.return_value = [setting1, setting2]
            yield mock_settings

    def test_no_affiliations(self, mock_settings, app, db):
        """
        正常系
        条件：所属機関情報がない場合
        入力：所属機関情報を含まないレコード
        期待結果：errorsフィールドが追加されない
        """
        list_record = [
            {
                "metadata": {
                    "title": "Test Title",
                    "authors": []
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" not in list_record[0]

    def test_creator_valid_scheme(self, mock_settings, app, db, authors_affiliation_settings):
        """
        正常系
        条件：creatorAffiliationsに有効なスキームがある場合
        入力：RORスキームを持つcreatorAffiliations
        期待結果：errorsフィールドが追加されない
        """
        list_record = [
            {
                "metadata": {
                    "creator": {
                        "creatorName": "Test Author",
                        "creatorAffiliations": [
                            {
                                "affiliationName": "Test University",
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "https://ror.org/12345",
                                        "affiliationNameIdentifierScheme": "ROR"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" not in list_record[0]

    def test_creator_invalid_scheme(self, mock_settings, app, db):
        """
        異常系
        条件：creatorAffiliationsに無効なスキームがある場合
        入力：無効なDOIスキームを持つcreatorAffiliations
        期待結果：errorsフィールドにエラーメッセージが追加される
        """
        list_record = [
            {
                "metadata": {
                    "creator": {
                        "creatorName": "Test Author",
                        "creatorAffiliations": [
                            {
                                "affiliationName": "Test University",
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "10.12345/67890",
                                        "affiliationNameIdentifierScheme": "DOI"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" in list_record[0]
        assert len(list_record[0]["errors"]) == 1
        assert '"DOI" is not one of' in list_record[0]["errors"][0]
        assert "creator" in list_record[0]["errors"][0]

    def test_creator_list_invalid_scheme(self, mock_settings, app, db):
        """
        異常系
        条件：リスト形式のcreatorに無効なスキームがある場合
        入力：無効なスキームを持つcreatorのリスト
        期待結果：errorsフィールドにエラーメッセージが追加される
        """
        list_record = [
            {
                "metadata": {
                    "creators": [
                        {
                            "creatorName": "Test Author 1",
                            "creatorAffiliations": [
                                {
                                    "affiliationName": "Test University",
                                    "affiliationNameIdentifiers": [
                                        {
                                            "affiliationNameIdentifier": "12345",
                                            "affiliationNameIdentifierScheme": "GRID"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" in list_record[0]
        assert len(list_record[0]["errors"]) == 1
        assert '"GRID" is not one of' in list_record[0]["errors"][0]
        assert "creators" in list_record[0]["errors"][0]

    def test_contributor_valid_scheme(self, mock_settings, app, db, authors_affiliation_settings):
        """
        正常系
        条件：contributorAffiliationsに有効なスキームがある場合
        入力：ISNIスキームを持つcontributorAffiliations
        期待結果：errorsフィールドが追加されない
        """
        list_record = [
            {
                "metadata": {
                    "contributor": {
                        "contributorName": "Test Contributor",
                        "contributorAffiliations": [
                            {
                                "affiliationName": "Test Organization",
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "0000-0001-2345-6789",
                                        "affiliationNameIdentifierScheme": "ISNI"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" not in list_record[0]

    def test_contributor_invalid_scheme(self, mock_settings, app, db):
        """
        異常系
        条件：contributorAffiliationsに無効なスキームがある場合
        入力：無効なスキームを持つcontributorAffiliations
        期待結果：errorsフィールドにエラーメッセージが追加される
        """
        list_record = [
            {
                "metadata": {
                    "contributor": {
                        "contributorName": "Test Contributor",
                        "contributorAffiliations": [
                            {
                                "affiliationName": "Test Organization",
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "12345",
                                        "affiliationNameIdentifierScheme": "ORCID"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" in list_record[0]
        assert len(list_record[0]["errors"]) == 1
        assert '"ORCID" is not one of' in list_record[0]["errors"][0]
        assert "contributor" in list_record[0]["errors"][0]

    def test_contributor_list_invalid_scheme(self, mock_settings, app, db):
        """
        異常系
        条件：リスト形式のcontributorに無効なスキームがある場合
        入力：無効なスキームを持つcontributorのリスト
        期待結果：errorsフィールドにエラーメッセージが追加される
        """
        list_record = [
            {
                "metadata": {
                    "contributors": [
                        {
                            "contributorName": "Test Contributor 1",
                            "contributorAffiliations": [
                                {
                                    "affiliationName": "Test Organization",
                                    "affiliationNameIdentifiers": [
                                        {
                                            "affiliationNameIdentifier": "12345",
                                            "affiliationNameIdentifierScheme": "Scopus"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" in list_record[0]
        assert len(list_record[0]["errors"]) == 1
        assert '"Scopus" is not one of' in list_record[0]["errors"][0]
        assert "contributors" in list_record[0]["errors"][0]

    def test_existing_errors(self, mock_settings, app, db):
        """
        正常系
        条件：既存のerrorsフィールドがある場合に新しいエラーを追加する
        入力：既存のerrorsフィールドと無効なスキーム
        期待結果：既存のerrorsに新しいエラーが追加される
        """
        list_record = [
            {
                "metadata": {
                    "creator": {
                        "creatorName": "Test Author",
                        "creatorAffiliations": [
                            {
                                "affiliationName": "Test University",
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "12345",
                                        "affiliationNameIdentifierScheme": "Wikidata"
                                    }
                                ]
                            }
                        ]
                    }
                },
                "errors": ["Existing error"]
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" in list_record[0]
        assert len(list_record[0]["errors"]) == 2
        assert "Existing error" == list_record[0]["errors"][0]
        assert '"Wikidata" is not one of' in list_record[0]["errors"][1]

    def test_multiple_invalid_schemes(self, mock_settings, app, db):
        """
        異常系
        条件：複数の無効なスキームがある場合
        入力：複数の無効なスキームを持つクリエイターとコントリビューター
        期待結果：すべてのエラーがerrorsフィールドに追加される
        """
        list_record = [
            {
                "metadata": {
                    "creator": {
                        "creatorName": "Test Author",
                        "creatorAffiliations": [
                            {
                                "affiliationName": "Test University",
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "12345",
                                        "affiliationNameIdentifierScheme": "Wikidata"
                                    }
                                ]
                            }
                        ]
                    },
                    "contributor": {
                        "contributorName": "Test Contributor",
                        "contributorAffiliations": [
                            {
                                "affiliationName": "Test Organization",
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "12345",
                                        "affiliationNameIdentifierScheme": "ORCID"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" in list_record[0]
        assert len(list_record[0]["errors"]) == 2
        assert any('"Wikidata" is not one of' in error for error in list_record[0]["errors"])
        assert any('"ORCID" is not one of' in error for error in list_record[0]["errors"])

    def test_none_scheme(self, mock_settings, app, db):
        """
        正常系
        条件：スキームがNoneの場合
        入力：affiliationNameIdentifierSchemeがNoneのレコード
        期待結果：エラーは追加されない（条件にscheme is not Noneがあるため）
        """
        list_record = [
            {
                "metadata": {
                    "creator": {
                        "creatorName": "Test Author",
                        "creatorAffiliations": [
                            {
                                "affiliationName": "Test University",
                                "affiliationNameIdentifiers": [
                                    {
                                        "affiliationNameIdentifier": "12345",
                                        "affiliationNameIdentifierScheme": None
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        ]

        handle_check_authors_affiliation(list_record)

        assert "errors" not in list_record[0]
