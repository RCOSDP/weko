# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp

import copy
import json
import os
import unittest
from datetime import datetime
import uuid

import pytest
from flask import current_app, make_response, request
from flask_babelex import Babel
from flask_login import current_user
from sqlalchemy import func as _func
from sqlalchemy.exc import SQLAlchemyError
from invenio_i18n.babel import set_locale
from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from mock import MagicMock, Mock, patch
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidrelations.models import PIDRelation
from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS
from weko_deposit.api import WekoDeposit, WekoIndexer, WekoRecord as d_wekorecord
from weko_records.api import ItemsMetadata, WekoRecord
from weko_records.models import ItemMetadata

from weko_search_ui import WekoSearchUI
from weko_search_ui.config import (
    ACCESS_RIGHT_TYPE_URI,
    RESOURCE_TYPE_URI,
    VERSION_TYPE_URI,
    WEKO_IMPORT_SYSTEM_ITEMS,
    WEKO_REPO_USER,
    WEKO_SYS_USER,
)
from weko_search_ui.utils import (
    DefaultOrderedDict,
    cancel_export_all,
    check_import_items,
    check_index_access_permissions,
    check_permission,
    check_sub_item_is_system,
    clean_thumbnail_file,
    convert_nested_item_to_list,
    create_deposit,
    create_flow_define,
    create_work_flow,
    defaultify,
    define_default_dict,
    delete_exported,
    delete_records,
    export_all,
    get_change_identifier_mode_content,
    get_content_workflow,
    get_current_language,
    get_data_by_property,
    get_data_in_deep_dict,
    get_doi_link,
    get_doi_prefix,
    get_export_status,
    get_feedback_mail_list,
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
    handle_check_and_prepare_index_tree,
    handle_check_and_prepare_publish_status,
    handle_check_cnri,
    handle_check_consistence_with_mapping,
    handle_check_date,
    handle_check_doi,
    handle_check_doi_indexes,
    handle_check_doi_ra,
    handle_check_duplication_item_id,
    handle_check_exist_record,
    handle_check_file_content,
    handle_check_file_metadata,
    handle_check_file_path,
    handle_check_filename_consistence,
    handle_check_id,
    handle_check_item_is_locked,
    handle_check_metadata_not_existed,
    handle_check_thumbnail,
    handle_check_thumbnail_file_type,
    handle_convert_validate_msg_to_jp,
    handle_doi_required_check,
    handle_fill_system_item,
    handle_generate_key_path,
    handle_get_all_id_in_item_type,
    handle_get_all_sub_id_and_name,
    handle_item_title,
    handle_remove_es_metadata,
    handle_set_change_identifier_flag,
    handle_validate_item_import,
    handle_workflow,
    import_items_to_system,
    make_file_by_line,
    make_stats_file,
    parse_to_json_form,
    prepare_doi_link,
    prepare_doi_setting,
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
)

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
# def get_tree_items(index_tree_id): ERROR ~ AttributeError: '_AppCtxGlobals' object has no attribute 'identity'
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_get_tree_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_tree_items(i18n_app, indices, users, mocker):
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
        def execute(self):
            return self.MockExecute(self.data)
    def mock_search_factory(self, search,index_id=None):
        return MockRecordsSearch(execute_result),"test_data"
    with patch(
        "weko_search_ui.utils.item_path_search_factory", side_effect=mock_search_factory
    ):
        # with patch("weko_search_ui.query.item_path_search_factory", return_value="{'abc': 123}"):
        assert get_tree_items(33)


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


# def get_feedback_mail_list(): *** not yet done
def test_get_feedback_mail_list(i18n_app, db_records2, es):
    search_instance = '{"size": 1, "query": {"bool": {"filter": [{"bool": {"must": [{"match": {"publish_status": "0"}}, {"range": {"publish_date": {"lte": "now/d"}}}, {"terms": {"path": ["1031", "1029", "1025", "952", "953", "943", "940", "1017", "1015", "1011", "881", "893", "872", "869", "758", "753", "742", "530", "533", "502", "494", "710", "702", "691", "315", "351", "288", "281", "759", "754", "744", "531", "534", "503", "495", "711", "704", "692", "316", "352", "289", "282", "773", "771", "767", "538", "539", "519", "510", "756", "745", "733", "337", "377", "308", "299", "2063", "2061", "2057", "1984", "1985", "1975", "1972", "2049", "2047", "2043", "1913", "1925", "1904", "1901", "1790", "1785", "1774", "1562", "1565", "1534", "1526", "1742", "1734", "1723", "1347", "1383", "1320", "1313", "1791", "1786", "1776", "1563", "1566", "1535", "1527", "1743", "1736", "1724", "1348", "1384", "1321", "1314", "1805", "1803", "1799", "1570", "1571", "1551", "1542", "1788", "1777", "1765", "1369", "1409", "1340", "1331", "4127", "4125", "4121", "4048", "4049", "4039", "4036", "4113", "4111", "4107", "3977", "3989", "3968", "3965", "3854", "3849", "3838", "3626", "3629", "3598", "3590", "3806", "3798", "3787", "3411", "3447", "3384", "3377", "3855", "3850", "3840", "3627", "3630", "3599", "3591", "3807", "3800", "3788", "3412", "3448", "3385", "3378", "3869", "3867", "3863", "3634", "3635", "3615", "3606", "3852", "3841", "3829", "3433", "3473", "3404", "3395", "1631495207665", "1631495247023", "1631495289664", "1631495340640", "1631510190230", "1631510251689", "1631510324260", "1631510380602", "1631510415574", "1631511387362", "1631511432362", "1631511521954", "1631511525655", "1631511606115", "1631511735866", "1631511740808", "1631511841882", "1631511874428", "1631511843164", "1631511845163", "1631512253601", "1633380618401", "1638171727119", "1638171753803", "1634120530242", "1636010714174", "1636010749240", "1638512895916", "1638512971664"]}}, {"bool": {"must": [{"match": {"publish_status": "0"}}, {"match": {"relation_version_is_last": "true"}}]}}, {"bool": {"should": [{"nested": {"query": {"multi_match": {"query": "simple", "operator": "and", "fields": ["content.attachment.content"]}}, "path": "content"}}, {"query_string": {"query": "simple", "default_operator": "and", "fields": ["search_*", "search_*.ja"]}}]}}]}}], "must": [{"match_all": {}}]}}, "aggs": {"Data Language": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Data Language": {"terms": {"field": "language", "size": 1000}}}}, "Access": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Access": {"terms": {"field": "accessRights", "size": 1000}}}}, "Location": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Location": {"terms": {"field": "geoLocation.geoLocationPlace", "size": 1000}}}}, "Temporal": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Temporal": {"terms": {"field": "temporal", "size": 1000}}}}, "Topic": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Topic": {"terms": {"field": "subject.value", "size": 1000}}}}, "Distributor": {"filter": {"bool": {"must": [{"term": {"contributor.@attributes.contributorType": "Distributor"}}, {"term": {"publish_status": "0"}}]}}, "aggs": {"Distributor": {"terms": {"field": "contributor.contributorName", "size": 1000}}}}, "Data Type": {"filter": {"bool": {"must": [{"term": {"description.descriptionType": "Other"}}, {"term": {"publish_status": "0"}}]}}, "aggs": {"Data Type": {"terms": {"field": "description.value", "size": 1000}}}}}, "sort": [{"_id": {"order": "desc", "unmapped_type": "long"}}], "_source": {"excludes": ["content"]}}'
    execute_result = {
        "aggregations": {"doc_count": 1, "key": 2},
        "feedback_mail_list": {},
        "email_list": {},
        "buckets": [],
    }
    # mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    # side_effect=mock_recordssearch
    with patch(
        "weko_search_ui.query.feedback_email_search_factory",
        return_value=search_instance,
    ):
        assert get_feedback_mail_list() == {}


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
    json_data = {'pos_index': ['IndexA'], 'publish_status': 'public', 'feedback_mail': ['wekosoftware@nii.ac.jp'], 'doi_ra': 'JaLC', 'edit_mode': 'Keep', 'metadata': {'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http: //isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617349709064': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617186783814': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}], 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}], 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617605131499': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain'}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}], 'path': [1658883231990], 'feedback_mail_list': [{'email': 'wekosoftware@nii.ac.jp', 'author_id': ''}]}, 'file_path': ['file00000001/1KB.pdf'], 'item_type_name': 'デフォルトアイテムタイプ（フル）', 'item_type_id': 1, '$schema': 'https://localhost:8443/items/jsonschema/15', 'identifier_key': 'item_1617186819068', 'status': 'new', 'id': 'oai:weko3.example.org:00000001', 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'filenames': [{'id': '.metadata.item_1617605131499[0].filename', 'filename': '1KB.pdf'}, {'id': '.metadata.item_1617605131499[1].filename', 'filename': ''}]}
    ret = parse_to_json_form(data)
    assert ret
    assert ret == json_data
    assert type(ret) == dict


# def check_import_items(file, is_change_identifier: bool, is_gakuninrdm=False,
def test_check_import_items(i18n_app):
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_name = "sample_file.zip"
    file_path = os.path.join(current_path, "data", "sample_file", file_name)

    assert check_import_items(file_path, True)


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


# def getEncode(filepath):
def test_getEncode():
    csv_files = [
        {"file": "eucjp_lf_items.csv", "enc": "euc-jp"},
        {"file": "iso2022jp_lf_items.csv", "enc": "iso-2022-jp"},
        {"file": "sjis_lf_items.csv", "enc": "shift_jis"},
        {"file": "utf8_cr_items.csv", "enc": "utf-8"},
        {"file": "utf8_crlf_items.csv", "enc": "utf-8"},
        {"file": "utf8_lf_items.csv", "enc": "utf-8"},
        {"file": "utf8bom_lf_items.csv", "enc": "utf-8"},
        {"file": "utf16be_bom_lf_items.csv", "enc": "utf-16be"},
        {"file": "utf16le_bom_lf_items.csv", "enc": "utf-16le"},
        # {"file":"utf32be_bom_lf_items.csv","enc":"utf-32"},
        # {"file":"utf32le_bom_lf_items.csv","enc":"utf-32"},
        {"file": "big5.txt", "enc": ""},
    ]

    for f in csv_files:
        filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "data", "csv", f["file"]
        )
        assert getEncode(filepath) == f["enc"]


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
def test_create_deposit(i18n_app, location, indices):
    assert create_deposit(33)


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
        record, root_path, deposit, allow_upload_file_content, old_files
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
def test_register_item_metadata(i18n_app, es_item_file_pipeline, deposit, es_records):
    item = es_records["results"][0]["item"]
    root_path = os.path.dirname(os.path.abspath(__file__))

    with patch("invenio_files_rest.utils.find_and_update_location_size"):
        assert register_item_metadata(item, root_path, is_gakuninrdm=False)


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
def test_import_items_to_system(i18n_app, es_item_file_pipeline, es_records):
    # item = dict(db_activity['item'])
    item = es_records["results"][0]["item"]

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
                            "weko_workflow.utils.get_cache_data", return_value=True
                        ):
                            assert import_items_to_system(item)
                            item["status"] = "new"
                            assert import_items_to_system(item)

                    assert import_items_to_system(
                        item
                    )  # Will result in error but will cover exception part


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


# def handle_check_and_prepare_feedback_mail(list_record):
def test_handle_check_and_prepare_feedback_mail(i18n_app, record_with_metadata):
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
def test_handle_check_doi_ra(i18n_app, es_item_file_pipeline, es_records):
    # list_record = [es_records['results'][0]['item']]
    item = MagicMock()

    # Doesn't return any value
    assert not handle_check_doi_ra([item])

    item = {"doi_ra": "JaLC", "is_change_identifier": False, "status": "keep"}

    with patch("weko_search_ui.utils.handle_doi_required_check", return_value="1"):
        with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value="1"):
            # Doesn't return any value
            assert not handle_check_doi_ra([item])


# def handle_check_doi(list_record):
def test_handle_check_doi(app):
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "list_records.json",
    )
    with open(filepath, encoding="utf-8") as f:
        list_record = json.load(f)
    assert handle_check_doi(list_record) == None

    # case new items with doi_ra
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "list_records",
        "b4_handle_check_doi.json",
    )
    with open(filepath, encoding="utf-8") as f:
        list_record = json.load(f)
    assert handle_check_doi(list_record) == None

    # item = {
    #     "doi_ra": "JaLC",
    #     "is_change_identifier": True,
    #     "status": "new"
    # }
    item = MagicMock()
    with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value="1"):
        assert not handle_check_doi([item])

    item2 = {"doi_ra": "JaLC", "is_change_identifier": False, "status": "keep"}
    mock = MagicMock()
    mock2 = MagicMock()
    mock3 = MagicMock()
    mock2.object_uuid = mock3
    mock.pid_recid = mock2

    # def myfunc():
    #     return 1,2
    # mock.get_idt_registration_data = myfunc

    with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value=mock):
        # with patch("weko_workflow.utils.IdentifierHandle", return_value=mock):
        assert not handle_check_doi([item2])


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

    assert prepare_doi_link(item_id)

    item_id = MagicMock()
    assert prepare_doi_link(item_id)


# def register_item_doi(item):
def test_register_item_doi(i18n_app, db_activity):
    # item = es_records['results'][0]['item']
    # item = db_activity['item']
    item = MagicMock()
    item.is_change_identifier = True
    item2 = MagicMock()
    item2.is_change_identifier = False

    with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value=item):
        # Doesn't return any value
        assert not register_item_doi(item)

        # Doesn't return any value
        assert not register_item_doi(item2)


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

    date_iso_keys = ['item_1617186660861.subitem_1522300722591']
    with patch("weko_search_ui.utils.get_list_key_of_iso_date", return_value=date_iso_keys):
        with patch("weko_search_ui.utils.get_sub_item_value", return_value=['2024/01/01']):
            assert handle_check_date(input_data)


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
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_fill_system_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp

def test_handle_fill_system_item(app, test_list_records, mocker):

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
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
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
        datastore = redis_connect

        task = MagicMock()
        task.task_id = 1
        mocker.patch("weko_search_ui.tasks.write_files_task", return_value=task)
        mocker.patch('builtins.open', side_effect=unittest.mock.mock_open())
        mocker.patch("weko_search_ui.utils.pickle.dump")

        recids = db.session.query(
            PersistentIdentifier.pid_value,
            PersistentIdentifier.object_uuid,
            RecordMetadata.json
        ).join(
            ItemMetadata,
            PersistentIdentifier.object_uuid == ItemMetadata.id,
        ).join(
            RecordMetadata,
            PersistentIdentifier.object_uuid == RecordMetadata.id,
        ).filter(
            PersistentIdentifier.pid_type == "recid",
            PersistentIdentifier.status == PIDStatus.REGISTERED,
            PersistentIdentifier.pid_value.notlike("%.%"),
            ItemMetadata.item_type_id == 1
        ).order_by(_func.to_number(
            PersistentIdentifier.pid_value,
            i18n_app.config["WEKO_SEARCH_UI_TO_NUMBER_FORMAT"]
        )).all()
        def get_record_by_uuid(uuid):
            if uuid == recids[105].object_uuid:
                raise SQLAlchemyError("test_error")

        # datastore.put(uri_key, "testuri".encode('utf-8'))
        datastore.delete(uri_key)
        export_all(root_url, user_id, data, start_time_str)

        datastore.put(uri_key, 'test_uri'.encode('utf-8'))
        export_all(root_url, user_id, data2, start_time_str)

        data_no_range = {"item_type_id": "1", "item_id_range": ""}
        export_all(root_url, user_id, data_no_range, start_time_str)

        # raise Exception in _get_item_type_list
        with patch("weko_search_ui.utils.ItemTypes.get_by_id", side_effect=Exception("test_error")):
            export_all(root_url, user_id, data, start_time_str)

        # raise Exception in _get_export_data
        with patch("weko_search_ui.utils.WekoRecord.get_record_by_uuid", side_effect=get_record_by_uuid):
            export_all(root_url, user_id, data_no_range, start_time_str)
            msg = datastore.get(msg_key)
            assert msg.decode() == "Export failed."

        # item_id_range error
        data_err = {"item_type_id": "1", "item_id_range": "10-1"}
        export_all(root_url, user_id, data_err, start_time_str)
        msg = datastore.get(msg_key)
        assert msg.decode() == "Export failed. Please check item id range."

        # raise Exception
        with patch("weko_search_ui.utils.os.makedirs", side_effect=Exception("test_error")):
            export_all(root_url, user_id, data, start_time_str)
            msg = datastore.get(msg_key)
            assert msg.decode() == "Export failed."


# def delete_exported(uri, cache_key):
def test_delete_exported(i18n_app, file_instance_mock):
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "sample_file",
        "sample_file.txt",
    )

    with patch("invenio_files_rest.models.FileInstance.delete", return_value=None):
        # Doesn't return any value
        assert not delete_exported(file_path, "key")


# def write_files(item_datas, export_path, user_id, retrys):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_write_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_write_files(db_activity, i18n_app, users, redis_connect, mocker, item_type, db_records2):
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


# def get_export_status():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_get_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_export_status(i18n_app, users, redis_connect,mocker, location):
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
    mocker.patch("weko_search_ui.utils.AsyncResult",side_effect=MockAsyncResult)
    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        cache_key = i18n_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
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
        result=get_export_status()
        assert result == (False, "test_uri", "test_msg", "test_run_msg", "", "", "")

        # task is not success, failed, revoked (write_file_status is started)
        datastore.put(cache_key, "PENDING_task".encode("utf-8"), ttl_secs=30)
        datastore.put(file_msg, json.dumps(create_file_json('started')).encode('utf-8'), ttl_secs=30)
        result=get_export_status()
        assert result == (True, "test_uri", "test_msg", "test_run_msg", "STARTED", start_time_str, "")

        # task is success, failed, revoked (write_file_status is finished)
        datastore.delete(cache_key)
        datastore.put(cache_key, "SUCCESS_task".encode("utf-8"), ttl_secs=30)
        datastore.delete(file_msg)
        file_json = create_file_json('finished')
        file_json['export_path'] = 'tests/data/import'
        datastore.put(file_msg, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
        now = datetime.now()
        mocker_datetime = mocker.patch('weko_search_ui.utils.datetime')
        mocker_datetime.now.return_value = now
        mocker.patch('weko_search_ui.utils.bagit.make_bag')
        mocker.patch('weko_search_ui.utils.shutil.make_archive')
        task = MagicMock()
        task.task_id = 1
        mocker.patch("weko_search_ui.tasks.delete_exported_task", return_value=task)
        result=get_export_status()
        uri = datastore.get(cache_uri)
        assert result == (False, uri.decode(), "test_msg", "test_run_msg", "SUCCESS", start_time_str, now.strftime('%Y/%m/%d %H:%M:%S'))

        # os.path.isdir is True
        with patch("weko_search_ui.utils.os.path.isdir", return_value=True):
            datastore.delete(file_msg)
            file_json = create_file_json('finished')
            file_json['export_path'] = 'tests/data/import'
            datastore.put(file_msg, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
            datastore.delete(run_msg)
            datastore.put(run_msg, "test_run_msg".encode("utf-8"), ttl_secs=30)
            result=get_export_status()
            assert result == (False, uri.decode(), "test_msg", "test_run_msg", "SUCCESS", start_time_str, "")
        
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
        
        # write_file_status is canceled
        datastore.delete(file_msg)
        datastore.put(file_msg, json.dumps(create_file_json('canceled')).encode('utf-8'), ttl_secs=30)
        result = get_export_status()
        assert result == (False, "test_uri", "test_msg", "test_run_msg", "REVOKED", start_time_str, "")

        # write_file_status is error
        datastore.delete(file_msg)
        datastore.put(file_msg, json.dumps(create_file_json('error')).encode('utf-8'), ttl_secs=30)
        result = get_export_status()
        assert result == (False, "test_uri", "test_msg", "test_run_msg", "", start_time_str, "")


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


# def handle_check_file_metadata(list_record, data_path):
def test_handle_check_file_metadata(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[0]]
    data_path = "test/test/test"

    # Doesn't return any value
    assert not handle_check_file_metadata(list_record, data_path)

    # with patch("weko_search_ui.utils.handle_check_file_content", return_value=):


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
def test_get_data_by_property(i18n_app):
    item_metadata = {}
    item_map = {"mapping_key": "test.test"}
    mapping_key = "mapping_key"

    assert get_data_by_property(item_metadata, item_map, mapping_key)
    assert get_data_by_property(item_metadata, {}, mapping_key)

    with patch(
        "weko_workflow.utils.get_sub_item_value", return_value=[True, ["value"]]
    ):
        assert get_data_by_property(item_metadata, item_map, mapping_key)


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
    record_data = {"_oai":{"id":"oai:weko3.example.org:00000004","sets":[]},"path":["1"],"owner":"1","recid":"4","title":["test item in br"],"pubdate":{"attribute_name":"PubDate","attribute_value":"2022-11-21"},"_buckets":{"deposit":"0796e490-6dcf-4e7d-b241-d7201c3de83a"},"_deposit":{"id":"4","pid":{"type":"depid","value":"4","revision_id":0},"owner":"1","owners":[1],"status":"published","created_by":1},"item_title":"test item in br","author_link":[],"item_type_id":"1","publish_date":"2022-11-21","publish_status":"0","weko_shared_id":-1,"item_1617186331708":{"attribute_name":"Title","attribute_value_mlt":[{"subitem_1551255647225":"test item in br","subitem_1551255648112":"ja"}]},"item_1617186626617":{"attribute_name":"Description","attribute_value_mlt":[{"subitem_description":"this is line1.\nthis is line2.","subitem_description_type":"Abstract","subitem_description_language":"en"}]},"item_1617258105262":{"attribute_name":"Resource Type","attribute_value_mlt":[{"resourceuri":"http://purl.org/coar/resource_type/c_5794","resourcetype":"conference paper"}]},"relation_version_is_last":True}
    item_data = {"id":"4","pid":{"type":"depid","value":"4","revision_id":0},"lang":"ja","path":[1],"owner":"1","title":"test item in br","owners":[1],"status":"published","$schema":"https://192.168.56.103/items/jsonschema/1","pubdate":"2022-11-21","edit_mode":"keep","created_by":1,"owners_ext":{"email":"wekosoftware@nii.ac.jp","username":"","displayname":""},"deleted_items":["item_1617605131499"],"shared_user_id":-1,"weko_shared_id":-1,"item_1617186331708":[{"subitem_1551255647225":"test item in br","subitem_1551255648112":"ja"}],"item_1617186626617":[{"subitem_description":"this is line1.\nthis is line2.","subitem_description_type":"Abstract","subitem_description_language":"en"}],"item_1617258105262":{"resourceuri":"http://purl.org/coar/resource_type/c_5794","resourcetype":"conference paper"}}
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
    assert record == {'_oai': {'id': 'oai:weko3.example.org:00000004', 'sets': ['1']}, 'path': ['1'], 'owner': '1', 'recid': '4', 'title': ['test item in br'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-11-21'}, '_buckets': {'deposit': '0796e490-6dcf-4e7d-b241-d7201c3de83a'}, '_deposit': {'id': '4', 'pid': {'type': 'depid', 'value': '4', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'draft', 'created_by': 1}, 'item_title': 'test item in br', 'author_link': [], 'item_type_id': '1', 'publish_date': '2022-11-21', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'test item in br', 'subitem_1551255648112': 'ja'}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'this is line1.\nthis is line2.', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}, 'relation_version_is_last': True, 'control_number': '4'}

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
