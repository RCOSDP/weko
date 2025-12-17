from unittest.mock import patch
import pytest
import json
from lxml import etree
from invenio_cache import current_cache
from flask import current_app

from weko_records.models import ItemType, ItemTypeName
from weko_workflow.models import ActionJournal

from weko_items_autofill.utils import (
    get_doi_record_data,
    fetch_metadata_by_doi,
    is_update_cache,
    cached_api_json,
    get_item_id,
    _get_title_data,
    get_title_pubdate_path,
    get_crossref_record_data,
    get_cinii_record_data,
    get_basic_cinii_data,
    pack_single_value_as_dict,
    pack_data_with_multiple_type_cinii,
    get_cinii_creator_data,
    get_cinii_contributor_data,
    get_cinii_description_data,
    get_cinii_subject_data,
    get_cinii_page_data,
    get_cinii_numpage,
    get_cinii_date_data,
    get_cinii_data_by_key,
    get_cinii_product_identifier,
    get_crossref_title_data,
    _build_name_data,
    get_crossref_creator_data,
    get_crossref_contributor_data,
    get_start_and_end_page,
    get_crossref_issue_date,
    get_crossref_source_title_data,
    get_crossref_publisher_data,
    get_crossref_relation_data,
    get_crossref_source_data,
    get_crossref_data_by_key,
    get_cinii_autofill_item,
    get_crossref_autofill_item,
    get_autofill_key_tree,
    sort_by_item_type_order,
    get_key_value,
    get_autofill_key_path,
    get_specific_key_path,
    build_record_model,
    build_model,
    build_form_model,
    merge_dict,
    deepcopy,
    fill_data,
    is_multiple,
    get_workflow_journal,
    convert_crossref_xml_data_to_dictionary,
    _get_contributor_and_author_names,
    get_wekoid_record_data,
    build_record_model_for_wekoid,
    is_multiple_item,
    get_record_model,
    set_val_for_record_model,
    set_val_for_all_child,
    remove_sub_record_model_no_value,
    get_researchmap_autofill_item,
    get_researchmapid_record_data
)
from weko_items_ui.config import WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS,WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_TYPE_MAPPINGS

from tests.helpers import json_data, login, logout


# def is_update_cache():
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_is_update_cache -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_is_update_cache(app):
    result = is_update_cache()
    assert result == True


# def cached_api_json(timeout=50, key_prefix="cached_api_json"):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_cached_api_json -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_cached_api_json(app):
    current_cache.delete("cached_api_json/test/page")
    result = cached_api_json()(lambda x, y: "url:" + x + y)("/test", "/page")
    assert result == "url:/test/page"
    assert current_cache.get("cached_api_json/test/page") == "url:/test/page"
    result = cached_api_json()(lambda x, y: "url:" + x + y)("/test", "/page")
    assert result == "url:/test/page"


# def get_item_id(item_type_id):
#     def _get_jpcoar_mapping(rtn_results, jpcoar_data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_item_id -vv -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_item_id(app, itemtypes, mocker):
    data = json_data("data/itemtypes/mapping.json")

    test = {
        "title": [
            {"title": {"model_id": "test0"}},
            {
                "title": {
                    "@value": "test1_subitem1",
                    "@attributes": {"xml:lang": "test1_subitem2"},
                    "model_id": "test_item1",
                }
            },
            {
                "title": {
                    "@value": "test2_subitem1",
                    "@attributes": {"xml:lang": "test2_subitem2"},
                    "model_id": "test_item2",
                }
            },
            {
                "title": {
                    "@value": "test3_subitem1",
                    "@attributes": {"xml:lang": "test3_subitem2"},
                    "model_id": "test_item3",
                }
            },
        ],
        "accessRights": {
            "@attributes": {"rdf:resource": "test4_subitem2"},
            "@value": "test4_subitem1",
            "model_id": "test_item5",
        },
        "contributor": {
            "contributorName": {
                "@attributes": {"xml:lang": "contributorNames.lang"},
                "@value": "contributorNames.contributorName",
            },
            "model_id": "test_item7",
        },
        "creator": {
            "creatorName": {
                "@attributes": {"xml:lang": "creatorNames.creatorNameLang"},
                "@value": "creatorNames.creatorName",
            },
            "model_id": "test_item6",
        },
        "date": {
            "@attributes": {"dateType": "test12_subitem2"},
            "@value": "test12_subitem1",
            "model_id": "test_item12",
        },
        "description": {
            "@attributes": {"xml:lang": "subitem10_lang", "descriptionType": "description_descriptionType"},
            "@value": "subitem_description",
            "model_id": "test_item10",
        },
        "identifier": {
            "@attributes": {"identifierType": "subitem_identifier_type"},
            "@value": "subitem_identifier_uri",
            "model_id": "test_item9",
        },
        "others": [
            {
                "others": {
                    "@attributes": {"xxx": "test13_subitem1"},
                    "model_id": "test_item13",
                }
            },
            {"others": {"@value": "test14_subitem1", "model_id": "test_item14"}},
        ],
        "relation": {
            "model_id": "test_item8",
            "relatedIdentifier": {
                "@attributes": {"identifierType": "test8_subitem1.test8_subitem3"},
                "@value": "test8_subitem1.test8_subitem2",
            },
        },
        "subject": {
            "@attributes": {"xml:lang":"subject_lang", "subjectScheme": "subject_subjectScheme","subjectURI":"subject_subjectURI"},
            "@value": "test11_subitem1",
            "model_id": "test_item11",
        },
        "volume": {"@value": "test15_subitem1", "model_id": "test_item15"},
    }
    result = get_item_id(1)
    assert result == test

    result = get_item_id(100)
    assert result == {"error": "'NoneType' object has no attribute 'items'"}


# def _get_title_data(jpcoar_data, key, rtn_title):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_title_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_title_data(app):
    jpcoar_data = {
        "title": {
            "@value": "test1_subitem1",
            "@attributes": {"xml:lang": "test1_subitem2"},
        }
    }
    key = "test_item1"
    rtn_title = {}
    _get_title_data(jpcoar_data, key, rtn_title)
    assert rtn_title == {
        "title_parent_key": "test_item1",
        "title_value_lst_key": ["test1_subitem1"],
        "title_lang_lst_key": ["test1_subitem2"],
    }

    jpcoar_data = {"title": {"@attributes": {}}}
    rtn_title = {}
    _get_title_data(jpcoar_data, key, rtn_title)
    assert rtn_title == {"title_parent_key": "test_item1"}

    jpcoar_data = {"title": {}}
    rtn_title = {}
    _get_title_data(jpcoar_data, key, rtn_title)
    assert rtn_title == {"title_parent_key": "test_item1"}

    # not contain 'item' in key
    jpcoar_data = {}
    key = "test"
    rtn_title = {}
    _get_title_data(jpcoar_data, key, rtn_title)
    assert rtn_title == {}

    # raise Exception
    jpcoar_data = {}
    key = "item_test"
    rtn_title = {}
    _get_title_data(jpcoar_data, key, rtn_title)
    assert rtn_title == {"title_parent_key": "item_test"}


# def get_title_pubdate_path(item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_title_pubdate_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_title_pubdate_path(app, itemtypes):
    result = get_title_pubdate_path(1)
    assert result == {
        "title": {
            "title_parent_key": "test_item1",
            "title_value_lst_key": ["test1_subitem1"],
            "title_lang_lst_key": ["test1_subitem2"],
        },
        "pubDate": "",
    }

    # not reached break
    all_false_mapping = {"test1": {}, "test2": {}, "test3":""}
    with patch(
        "weko_items_autofill.utils.Mapping.get_record", return_value=all_false_mapping
    ):
        result = get_title_pubdate_path(1)
        assert result == {"pubDate": "", "title": {}}


# def get_doi_record_data(doi, item_type_id, activity_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_doi_record_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_doi_record_data(mocker):
    doi = "10.1234/test"
    item_type_id = 1
    activity_id = 2
    fake_metadata = {"metainfo": {"foo": "bar", "empty": ""}}
    fake_metainfo_cleaned = {"foo": "bar"}
    fake_doi_result = {"title": "Test Title", "author": "Test Author"}

    # patch WorkActivity.get_activity_metadata
    mock_activity = mocker.patch("weko_items_autofill.utils.WorkActivity.get_activity_metadata", return_value=fake_metadata)
    # patch remove_empty
    mock_remove_empty = mocker.patch("weko_items_autofill.utils.remove_empty", return_value=fake_metainfo_cleaned)
    # patch fetch_metadata_by_doi
    mock_fetch_metadata = mocker.patch("weko_items_autofill.utils.fetch_metadata_by_doi", return_value=fake_doi_result)

    from weko_items_autofill.utils import get_doi_record_data

    # Act
    result = get_doi_record_data(doi, item_type_id, activity_id)

    # Assert
    mock_activity.assert_called_once_with(activity_id)
    mock_remove_empty.assert_called_once_with(fake_metadata["metainfo"])
    mock_fetch_metadata.assert_called_once_with(doi, item_type_id, fake_metainfo_cleaned)
    assert result == [{"title": "Test Title"}, {"author": "Test Author"}]


# def fetch_metadata_by_doi(doi, item_type_id, original_metadeta=None):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_fetch_metadata_by_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_fetch_metadata_by_doi(app,db,itemtypes,mocker):

    jalc_data = [{"id": "id_jalc"}, {"name_jalc": "test_name_jalc"}]
    ichushi_data = [{"id": "id_ichushi"}, {"name_ichushi": "test_name_ichushi"}]
    crossref_data = [{"id": "id_crossref"}, {"name_crossref": "test_name_crossref"}]
    datacite_data = [{"id": "id_datacite"}, {"name_datacite": "test_name_datacite"}]
    cinii_data = [{"id": "id_cinii"}, {"name_cinii": "test_name_cinii"}]

    mocker.patch("weko_items_autofill.utils.get_current_api_certification",return_value={"cert_data": "test_id"})
    mocker.patch("weko_workspace.utils.get_jalc_record_data",return_value=jalc_data)
    mocker.patch("weko_workspace.utils.get_jamas_record_data",return_value=ichushi_data)
    mocker.patch("weko_items_autofill.utils.get_crossref_record_data",return_value=crossref_data)
    mocker.patch("weko_workspace.utils.get_datacite_record_data",return_value=datacite_data)
    mocker.patch("weko_workspace.utils.get_cinii_record_data",return_value=cinii_data)

    # with all api
    app.config.update(
        WEKO_ITEMS_AUTOFILL_API_LIST = [
            "JaLC API",
            "医中誌 Web API",
            "CrossRef",
            "DataCite",
            "CiNii Research",
        ],
        WEKO_ITEMS_AUTOFILL_TO_BE_USED = [
            "JaLC API",
            "医中誌 Web API",
            "CrossRef",
            "DataCite",
            "CiNii Research",
            "Original",
        ],
    )
    original_metadata = {"id": "test_original", "name_original": "test_name_original"}
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata)
    assert result == {
        'id': 'id_jalc',
        "name_jalc": "test_name_jalc",
        "name_ichushi": "test_name_ichushi",
        "name_crossref": "test_name_crossref",
        "name_datacite": "test_name_datacite",
        "name_cinii": "test_name_cinii",
        "name_original": "test_name_original"
    }

    # with only jalc
    app.config.update(
        WEKO_ITEMS_AUTOFILL_TO_BE_USED = [
            "JaLC API",
        ],
    )
    original_metadata = {"id": "test_original", "name_original": "test_name_original"}
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata)
    assert result == {
        'id': 'id_jalc',
        "name_jalc": "test_name_jalc",
    }

    # with jalc & original
    app.config.update(
        WEKO_ITEMS_AUTOFILL_TO_BE_USED = [
            "JaLC API",
            "Original",
        ],
    )
    original_metadata = {"id": "test_original", "name_original": "test_name_original"}
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata)
    assert result == {
        'id': 'id_jalc',
        "name_jalc": "test_name_jalc",
        "name_original": "test_name_original",
    }

    # with jalc & original(empty)
    app.config.update(
        WEKO_ITEMS_AUTOFILL_TO_BE_USED = [
            "JaLC API",
            "Original",
        ],
    )
    original_metadata = {}
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata)
    assert result == {
        'id': 'id_jalc',
        "name_jalc": "test_name_jalc",
    }

    # with jalc & crossref
    app.config.update(
        WEKO_ITEMS_AUTOFILL_TO_BE_USED = [
            "JaLC API",
            "CrossRef",
        ],
    )
    original_metadata = {"id": "test_original", "name_original": "test_name_original"}
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata)
    assert result == {
        'id': 'id_jalc',
        "name_jalc": "test_name_jalc",
        "name_crossref": "test_name_crossref",
    }

    # with jalc & crossref & original(empty)
    app.config.update(
        WEKO_ITEMS_AUTOFILL_TO_BE_USED = [
            "JaLC API",
            "CrossRef",
            "Original",
        ],
    )
    original_metadata = {}
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata)
    assert result == {
        'id': 'id_jalc',
        "name_jalc": "test_name_jalc",
        "name_crossref": "test_name_crossref",
    }

    # with jalc & crossref & original
    app.config.update(
        WEKO_ITEMS_AUTOFILL_TO_BE_USED = [
            "JaLC API",
            "CrossRef",
            "Original",
        ],
    )
    original_metadata = {"id": "test_original", "name_original": "test_name_original"}
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata)
    assert result == {
        'id': 'id_jalc',
        "name_jalc": "test_name_jalc",
        "name_crossref": "test_name_crossref",
        "name_original": "test_name_original",
    }

    # sword
    app.config.update(
        WEKO_ITEMS_AUTOFILL_TO_BE_USED = [],
    )
    meta_data_api = [
        "JaLC API",
        "医中誌 Web API",
        "CrossRef",
        "DataCite",
        "CiNii Research",
        "Original"
    ]
    original_metadata = {"id": "test_original", "name_original": "test_name_original"}
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata,meta_data_api=meta_data_api)
    assert result == {
        'id': 'id_jalc',
        "name_jalc": "test_name_jalc",
        "name_ichushi": "test_name_ichushi",
        "name_crossref": "test_name_crossref",
        "name_datacite": "test_name_datacite",
        "name_cinii": "test_name_cinii",
        "name_original": "test_name_original",
    }

    result = fetch_metadata_by_doi("test_doi","test_item_type_id",original_metadata)
    assert result == {"id": "test_original", "name_original": "test_name_original"}

    mocker.patch("weko_workspace.utils.get_jalc_record_data",side_effect=Exception("test_error"))
    result = fetch_metadata_by_doi("test_doi","test_item_type_id",[],meta_data_api=meta_data_api)
    assert result == {
        "id": "id_ichushi",
        "name_ichushi": "test_name_ichushi",
        "name_crossref": "test_name_crossref",
        "name_datacite": "test_name_datacite",
        "name_cinii": "test_name_cinii",
    }



# def get_crossref_record_data(pid, doi, item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_record_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_record_data(db, itemtypes, mocker):
    mocker.patch("weko_items_autofill.utils.convert_crossref_xml_data_to_dictionary")
    mocker.patch("weko_items_autofill.utils.get_crossref_data_by_key")
    mocker.patch("weko_items_autofill.utils.sort_by_item_type_order")
    mocker.patch("weko_items_autofill.utils.get_autofill_key_tree")
    mocker.patch("weko_items_autofill.utils.get_crossref_autofill_item")
    data = [
        {'test_item1': {'test1_subitem1': 'test_article_title', 'test1_subitem2': 'en'}},
        {'test_item6': {'creatorNames': {'creatorName': 'A.Test1', 'creatorNameLang': 'en'}}},
        {'test_item7': {'contributorNames': {'contributorName': 'B.Test2', 'lang': 'en'}}},
        {'test_item8': {'test8_subitem1': {'test8_subitem2': '10.1103/PhysRev.47.777', 'test8_subitem3': 'DOI'}}},
        {'test_item16': {'test16_subitem1': '47'}}]
    mocker.patch("weko_items_autofill.utils.build_record_model",return_value=data)
    # get_data is error
    with patch("weko_items_autofill.utils.CrossRefOpenURL.get_data",return_value={"error":"test_error"}):
        result = get_crossref_record_data("test_pid","test_doi",itemtypes[0][0].id)
        assert result == []
    current_cache.delete("crossref_datatest_pidtest_doi1")

    with patch("weko_items_autofill.utils.CrossRefOpenURL.get_data",return_value={"error":None,"response":""}):
        # not exist itemtype
        result = get_crossref_record_data("test_pid","test_doi",300)
        assert result == []

        result = get_crossref_record_data("test_pid","test_doi",itemtypes[0][0].id)
        assert result == []

        # not exist itemtype.form
        itemtypes[1][0].form = None
        db.session.merge(itemtypes[1][0])
        result = get_crossref_record_data("test_pid","test_doi",itemtypes[1][0].id)
        assert result == []

    current_cache.delete("crossref_datatest_pidtest_doi1")
    current_cache.delete("crossref_datatest_pidtest_doi300")
    current_cache.delete("crossref_datatest_pidtest_doi2")

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_record_data2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_record_data2(db, itemtypes, mocker):
    mocker.patch("weko_items_autofill.utils.sort_by_item_type_order")
    mocker.patch("weko_items_autofill.utils.get_autofill_key_tree")
    mocker.patch("weko_items_autofill.utils.get_crossref_autofill_item")
    mocker.patch(
        "weko_items_autofill.utils.CrossRefOpenURL.get_data",
        return_value={'response': '<?xml version="1.0" encoding="UTF-8"?>\n<crossref_result xmlns="http://www.crossref.org/qrschema/2.0" version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.crossref.org/qrschema/2.0 https://www.crossref.org/schema/crossref_query_output2.0.xsd"><query_result><head><doi_batch_id>none</doi_batch_id></head><body><query status="resolved" fl_count="0"><doi type="journal_article">10.17352/ojps.000010</doi><issn type="electronic">26407906</issn><journal_title>Open Journal of Plant Science</journal_title><contributors><contributor sequence="first" contributor_role="author"><given_name>Peertechz</given_name><surname>Publications</surname></contributor></contributors><year media_type="online">2018</year><publication_type>full_text</publication_type><article_title>Open Journal of Plant Science</article_title></query></body></query_result></crossref_result>', 'error': ''})

    data = [
        {
            "test_item1": {
                "test1_subitem1": "test_article_title",
                "test1_subitem2": "en",
            }
        },
        {
            "test_item6": {
                "creatorNames": {"creatorName": "A.Test1", "creatorNameLang": "en"}
            }
        },
        {
            "test_item7": {
                "contributorNames": {"contributorName": "B.Test2", "lang": "en"}
            }
        },
        {
            "test_item8": {
                "test8_subitem1": {
                    "test8_subitem2": "10.1103/PhysRev.47.777",
                    "test8_subitem3": "DOI",
                }
            }
        },
        {"test_item16": {"test16_subitem1": "47"}},
    ]
    mocker.patch("weko_items_autofill.utils.build_record_model", return_value=data)
    mocker.patch("weko_items_autofill.utils.convert_crossref_xml_data_to_dictionary",return_value={'error': '','response': {'article_title': 'article title','contributor': [{'family': 'Test1', 'given': 'A.'}],'doi': 'xxx/yyy','journal_title': 'journal title'}})
    result = get_crossref_record_data("test_pid1", "test_doi1", itemtypes[0][0].id)
    assert result == [{'test_item1': {'test1_subitem1': 'test_article_title','test1_subitem2': 'en'}},{'test_item6': {'creatorNames': {'creatorName': 'A.Test1','creatorNameLang': 'en'}}},{'test_item7': {'contributorNames': {'contributorName': 'B.Test2','lang': 'en'}}},{'test_item8': {'test8_subitem1': {'test8_subitem2': '10.1103/PhysRev.47.777','test8_subitem3': 'DOI'}}},{'test_item16': {'test16_subitem1': '47'}}]

    mocker.patch("weko_items_autofill.utils.convert_crossref_xml_data_to_dictionary",return_value={'error': 'Opening and ending tag mismatch: body line 2 and query_result, line 2, column 331 (<string>, line 2)','response': {}})
    result = get_crossref_record_data("test_pid2", "test_doi2", itemtypes[0][0].id)
    assert result == []

    mocker.patch("weko_items_autofill.utils.convert_crossref_xml_data_to_dictionary",return_value={'error': '','response': {'article_title': 'article title','contributor': [{'family': 'Test1', 'given': 'A.'}],'doi': 'xxx/yyy','journal_title': 'journal title'}})
    result = get_crossref_record_data("test_pid3", "test_doi3", 300)
    assert result == []

    itemtypes[1][0].form = None
    db.session.merge(itemtypes[1][0])
    db.session.commit()
    mocker.patch("weko_items_autofill.utils.convert_crossref_xml_data_to_dictionary",return_value={'error': '','response': {'article_title': 'article title','contributor': [{'family': 'Test1', 'given': 'A.'}],'doi': 'xxx/yyy','journal_title': 'journal title'}})
    result = get_crossref_record_data("test_pid4", "test_doi4", itemtypes[1][0].id)
    assert result == []


    current_cache.delete("crossref_datatest_pid1test_doi11")
    current_cache.delete("crossref_datatest_pid2test_doi21")
    current_cache.delete("crossref_datatest_pid3test_doi31")
    current_cache.delete("crossref_datatest_pid4test_doi41")


# def get_cinii_record_data(naid, item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_record_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_record_data(db, itemtypes, mocker):
    current_cache.delete("cinii_datatest_naid1")
    current_cache.delete("cinii_datatest_naid100")
    mocker.patch("weko_items_autofill.utils.get_cinii_data_by_key")
    mocker.patch("weko_items_autofill.utils.get_autofill_key_tree")
    mocker.patch("weko_items_autofill.utils.get_cinii_autofill_item")
    data = [
        {
            "test_item1": {
                "test1_subitem1": "this is test Dissertation",
                "test1_subitem2": "ja",
            }
        },
        {
            "test_item6": {
                "creatorNames": {"creatorName": "テスト 太郎", "creatorNameLang": "ja"}
            }
        },
        {
            "test_item7": {
                "contributorNames": {"contributorName": "テスト組織", "lang": "ja"}
            }
        },
        {
            "test_item8": {
                "test8_subitem1": {
                    "test8_subitem2": "10.1016/j.test.2022.146234",
                    "test8_subitem3": "DOI",
                }
            }
        },
        {"test_item16": {"test16_subitem1": "10"}},
    ]
    mocker.patch("weko_items_autofill.utils.build_record_model", return_value=data)

    # get_data is error
    with patch(
        "weko_items_autofill.utils.CiNiiURL.get_data",
        return_value={"error": "test_error", "response": ""},
    ):
        result = get_cinii_record_data("test_naid", itemtypes[0][0].id)
        assert result == []
    current_cache.delete("cinii_datatest_naid1")

    with patch(
        "weko_items_autofill.utils.CiNiiURL.get_data",
        return_value={"error": None, "response": {}},
    ):
        # not exist itemtype
        result = get_cinii_record_data("test_naid", 100)
        assert result == []

        result = get_cinii_record_data("test_naid", itemtypes[0][0].id)
        assert result == [
            {
                "test_item1": {
                    "test1_subitem1": "this is test Dissertation",
                    "test1_subitem2": "ja",
                }
            },
            {
                "test_item6": {
                    "creatorNames": {"creatorName": "テスト 太郎", "creatorNameLang": "ja"}
                }
            },
            {
                "test_item7": {
                    "contributorNames": {"contributorName": "テスト組織", "lang": "ja"}
                }
            },
            {
                "test_item8": {
                    "test8_subitem1": {
                        "test8_subitem2": "10.1016/j.test.2022.146234",
                        "test8_subitem3": "DOI",
                    }
                }
            },
            {"test_item16": {"test16_subitem1": "10"}},
        ]

        # not exist itemtype.form
        itemtypes[1][0].form = None
        db.session.merge(itemtypes[1][0])
        db.session.commit()
        result = get_cinii_record_data("test_naid", itemtypes[1][0].id)
        assert result == []


# def get_basic_cinii_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_basic_cinii_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_basic_cinii_data():
    data = [
        {"@value": "this is test Dissertation", "@language": "en"},
        {"@value": "テスト博士論文"},
    ]
    test = [
        {"@value": "this is test Dissertation", "@language": "en"},
        {"@value": "テスト博士論文", "@language": "ja"},
    ]
    result = get_basic_cinii_data(data)
    assert result == test


# def pack_single_value_as_dict(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_title_pubdate_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_pack_single_value_as_dict():
    data = "test_data"
    result = pack_single_value_as_dict(data)
    assert result == {"@value": "test_data"}


# def pack_data_with_multiple_type_cinii(data1, type1, data2, type2):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_pack_data_with_multiple_type_cinii -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_pack_data_with_multiple_type_cinii():
    data = [
      {
        "@type": "PISSN",
        "@value": "13402625"
      },
      {
        "@type": "EISSN",
        "@value": "18845843"
      }
    ]
    type1 = "PISSN"
    type2 = "ISSN"
    result = pack_data_with_multiple_type_cinii(data, type1, type2)
    assert result == [
        {"@value": "13402625", "@type": "PISSN"},
    ]
    result = pack_data_with_multiple_type_cinii(data, "test_type1", "test_type2")
    assert result == []


# def get_cinii_creator_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_creator_data -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_creator_data():
    data = json_data("data/cinii_response_sample1.json")['response']['creator']
    result = get_cinii_creator_data(data)
    test = [
        [
            {"@value":"テスト 太郎", "@language":"ja"},
            {"@value":"TEST Taro", "@language":"en"}
        ],
        [
            {"@value":"テスト 三郎", "@language":"ja"},
            {"@value":"TEST Saburo", "@language":"en"}
        ],
    ]
    assert result == test


# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_contributor_data -vv -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_contributor_data():
    data = json_data("data/cinii_response_sample1.json")['response']["contributor"]
    test = [
        [
            {"@value": "テスト 次郎", "@language": "ja"},
            {"@value": "TEST Ziro", "@language": "en"}
        ],
        [
            {"@value": "テスト 花子", "@language": "ja"},
            {"@value": "TEST Hanako", "@language": "en"}
        ],
    ]
    result = get_cinii_contributor_data(data)
    assert result == test

# def get_cinii_description_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_description_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_description_data():
    data = json_data("data/cinii_response_sample1.json")['response']["description"]
    test = [
        {"@value": "this is test abstract.", "@language": "en", "@type": "Abstract"},
        {"@value": "これはテストの抄録です。", "@language": "ja", "@type": "Abstract"},
        {"@value": "this is other abstract.", "@language": "en", "@type": "Other"},
        {"@value": "これはその他の抄録です。", "@language": "ja", "@type": "Other"}
    ]
    result = get_cinii_description_data(data)
    assert result == test

# def get_cinii_subject_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_subject_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_subject_data():
    data = json_data("data/cinii_response_sample1.json")['response']["foaf:topic"]
    test = [
        {
            "@scheme": "Other",
            "@URI": "https://cir.nii.ac.jp/all?q=%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%83%87%E3%82%B6%E3%82%A4%E3%83%B3",
            "@value": "システムデザイン",
            "@language": "ja",
        },
        {
            "@scheme": "Other",
            "@URI": "https://cir.nii.ac.jp/all?q=%E6%A4%9C%E7%B4%A2%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%B3",
            "@value": "検索エンジン",
            "@language": "ja",
        },
    ]
    result = get_cinii_subject_data(data)
    assert result == test


# def get_cinii_page_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_page_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_page_data(app, mocker):
    mocker.patch(
        "weko_items_autofill.utils.pack_single_value_as_dict",
        side_effect=lambda x: {"@value": x},
    )
    result = get_cinii_page_data("1")
    assert result == {"@value": "1"}

    result = get_cinii_page_data("a")
    assert result == {"@value": None}


# def get_cinii_numpage(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_numpage -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_numpage(app, mocker):
    mocker.patch(
        "weko_items_autofill.utils.pack_single_value_as_dict",
        side_effect=lambda x: {"@value": int(x)} if x != None else {"@value":None},
    )
    mocker.patch(
        "weko_items_autofill.utils.get_cinii_page_data",
        side_effect=lambda x: {"@value": int(x)} if x != None else {"@value":None},
    )

    # exist numPages
    data = {
        "jpcoar:numPages": "6",
        "prism:startingPage": "10",
        "prism:endingPage": "15",
    }
    result = get_cinii_numpage(data)
    assert result == {"@value": 6}

    # not exist numPage, exist startingPage, endingPage
    data = {"prism:startingPage": "10", "prism:endingPage": "15"}
    result = get_cinii_numpage(data)
    assert result == {"@value": 6}

    # not exist numPage, startingPage, endingPage
    data = {}
    result = get_cinii_numpage(data)
    assert result == {"@value": None}

    # raise exception
    data = {"prism:startingPage": "a", "prism:endingPage": "b"}
    result = get_cinii_numpage(data)
    assert result == {"@value": None}



# def get_cinii_date_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_date_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_date_data():
    data = "2022-10-01"
    result = get_cinii_date_data(data)
    assert result == {"@value": "2022-10-01", "@type": "Issued"}

    data = "10-01"
    result = get_cinii_date_data(data)
    assert result == {"@value": None, "@type": None}

# def get_cinii_product_identifier(data, type1, type2):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_product_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_product_identifier():
    data = json_data("data/cinii_response_sample1.json")['response']["productIdentifier"]
    result = get_cinii_product_identifier(data, "NAID", "DOI")
    test = [
        {"@value": "001122334455", "@type":"NAID"},
        {"@value": "10.12334/jkg.12.11_222", "@type":"DOI"},
    ]
    assert result == test

# def get_cinii_data_by_key(api, keyword):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_data_by_key -vv -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_data_by_key(app):
    api = {"response": {}}
    result = get_cinii_data_by_key(api, "key")
    assert result == {}

    api = {"response": None}
    result = get_cinii_data_by_key(api, "key")
    assert result == {}

    api = json_data("data/cinii_response_sample1.json")
    test = {
        "title": [
            {"@value": "テストタイトル", "@language": "ja"},
            {"@value": "test title", "@language": "en"},
            {"@value": "テストのタイトル", "@language": "ja"},
        ],
        "alternative": [
            {"@value": "other title", "@language": "en"},
            {"@value": "別タイトル", "@language": "ja"},
        ],
        "creator": [
            [
                {"@value": "テスト 太郎", "@language": "ja"},
                {"@value": "TEST Taro", "@language": "en"}
            ],
            [
                {"@value": "テスト 三郎", "@language": "ja"},
                {"@value": "TEST Saburo", "@language": "en"}
            ],
        ],
        "contributor": [
            [
                {"@value": "テスト 次郎", "@language": "ja"},
                {"@value": "TEST Ziro", "@language": "en"}
            ],
            [
                {"@value": "テスト 花子", "@language": "ja"},
                {"@value": "TEST Hanako", "@language": "en"}
            ],
        ],
        "description": [
            {"@value": "this is test abstract.", "@type": "Abstract", "@language": "en"},
            {"@value": "これはテストの抄録です。", "@type": "Abstract", "@language": "ja"},
            {"@value": "this is other abstract.", "@type": "Other", "@language": "en"},
            {"@value": "これはその他の抄録です。", "@type": "Other", "@language": "ja"},
        ],
        "subject": [
            {
                "@scheme": "Other",
                "@URI": "https://cir.nii.ac.jp/all?q=%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%83%87%E3%82%B6%E3%82%A4%E3%83%B3",
                "@value": "システムデザイン",
                "@language": "ja",
            },
            {
                "@scheme": "Other",
                "@URI": "https://cir.nii.ac.jp/all?q=%E6%A4%9C%E7%B4%A2%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%B3",
                "@value": "検索エンジン",
                "@language": "ja",
            }
        ],
        "sourceTitle": [
            {"@value": "テスト雑誌", "@language": "ja"},
            {"@value": "test journal", "@language": "en"}
        ],
        "volume": {"@value": "62"},
        "issue": {"@value": "11"},
        "pageStart": {"@value": "473"},
        "pageEnd": {"@value": "477"},
        "numPages": {"@value": "5"},
        "date": {"@value": "2012-11-02", "@type": "Issued"},
        "publisher": [
            {"@value": "test publisher", "@language": "en"},
            {"@value": "テスト公開", "@language": "ja"}
        ],
        "sourceIdentifier": [
            {"@value": "87654321", "@type": "ISSN"},
            {"@value": "AN34567890", "@type": "NCID"}
        ],
        "relation": [
            {"@value": "001122334455", "@type": "NAID"},
            {"@value": "10.12334/jkg.12.11_222", "@type": "DOI"},
        ],
    }
    result = get_cinii_data_by_key(api, "all")
    assert result == test

    result = get_cinii_data_by_key(api, "other_key")
    assert result == {}


# def get_crossref_title_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_title_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_title_data():
    data = "this is article title"
    result = get_crossref_title_data(data)
    assert result == [{"@value": "this is article title", "@language": "en"}]
    data = ["this is article title1", "this is article title2"]
    result = get_crossref_title_data(data)
    assert result == [
        {"@value": "this is article title1", "@language": "en"},
        {"@value": "this is article title2", "@language": "en"},
    ]


# def _build_name_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test__build_name_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test__build_name_data():
    data = [
        {"given": "A.", "family": "Test1"},
        {"given": "B. Test2"},
        {"family": "C. Test3"},
        {"other": "D. Test4"},
    ]
    test = [
        {"@value": "Test1 A.", "@language": "en"},
        {"@value": "B. Test2", "@language": "en"},
        {"@value": "C. Test3", "@language": "en"},
        {"@value": "", "@language": "en"},
    ]
    result = _build_name_data(data)
    assert result == test


# def get_crossref_creator_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_creator_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_creator_data(mocker):
    mocker.patch(
        "weko_items_autofill.utils._build_name_data",
        return_value=[{"@value": "Test1 A.", "@language": "en"}],
    )
    data = [{"given": "A.", "family": "Test1"}]
    result = get_crossref_creator_data(data)
    assert result == [{"@value": "Test1 A.", "@language": "en"}]


# def get_crossref_contributor_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_contributor_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_contributor_data(mocker):
    mocker.patch(
        "weko_items_autofill.utils._build_name_data",
        return_value=[{"@value": "Test1 A.", "@language": "en"}],
    )
    data = [{"given": "A.", "family": "Test1"}]
    result = get_crossref_contributor_data(data)
    assert result == [{"@value": "Test1 A.", "@language": "en"}]


# def get_start_and_end_page(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_start_and_end_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_start_and_end_page(app):
    data = "120"
    with patch(
        "weko_items_autofill.utils.pack_single_value_as_dict",
        side_effect=lambda x: {"@value": x},
    ):
        result = get_start_and_end_page(data)
        assert result == {"@value": "120"}

        result = get_start_and_end_page("error")
        assert result == {"@value": None}


# def get_crossref_issue_date(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_issue_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_issue_date():
    data = "test_data"
    result = get_crossref_issue_date(data)
    assert result == {"@value": "test_data", "@type": "Issued"}

    data = None
    result = get_crossref_issue_date(data)
    assert result == {"@value": None, "@type": None}


# def get_crossref_source_title_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_source_title_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_source_title_data():
    data = "test_title"
    result = get_crossref_source_title_data(data)
    assert result == {"@value": "test_title", "@language": "en"}


# def get_crossref_publisher_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_publisher_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_publisher_data():
    data = "test_data"
    result = get_crossref_publisher_data(data)
    assert result == {"@value": "test_data", "@language": "en"}


# def get_crossref_relation_data(isbn, doi):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_relation_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_relation_data(mocker):
    mocker.patch(
        "weko_items_autofill.utils.pack_single_value_as_dict",
        side_effect=lambda x: {"@value": x},
    )
    isbn = []
    doi = "test_doi"
    result = get_crossref_relation_data(isbn, doi)
    assert result == [{"@value": "test_doi", "@type": "DOI"}]

    isbn = ["test_isbn1", "test_isbn2"]
    doi = ""
    result = get_crossref_relation_data(isbn, doi)
    assert result == [
        {"@value": "test_isbn1", "@type": "ISBN"},
        {"@value": "test_isbn2", "@type": "ISBN"},
    ]

    isbn = []
    doi = ""
    result = get_crossref_relation_data(isbn, doi)
    assert result == {"@value": None}


# def get_crossref_source_data(data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_source_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_source_data():
    data = "test_data"
    result = get_crossref_source_data(data)
    assert result == [{"@value": "test_data", "@type": "ISSN"}]

    data = ""
    result = get_crossref_source_data(data)
    assert result == []


# def get_crossref_data_by_key(api, keyword):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_data_by_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_data_by_key(app, mocker):
    api = {"error": "exist_error"}
    result = get_crossref_data_by_key(api, "")
    assert result == None

    mocker.patch(
        "weko_items_autofill.utils.get_crossref_title_data",
        side_effect=lambda x: [{"@value": x, "@language": "en"}],
    )
    mocker.patch(
        "weko_items_autofill.utils.get_crossref_creator_data",
        side_effect=lambda x: [{"@value": x[0]["given"], "@language": "en"}],
    )
    mocker.patch(
        "weko_items_autofill.utils.get_crossref_contributor_data",
        side_effect=lambda x: [{"@value": x[0]["given"], "@language": "en"}],
    )
    mocker.patch(
        "weko_items_autofill.utils.get_crossref_source_title_data",
        side_effect=lambda x: {"@value": x, "@language": "en"},
    )
    mocker.patch(
        "weko_items_autofill.utils.pack_single_value_as_dict",
        side_effect=lambda x: {"@value": x},
    )
    mocker.patch(
        "weko_items_autofill.utils.get_start_and_end_page",
        side_effect=lambda x: {"@value": int(x)},
    )
    mocker.patch(
        "weko_items_autofill.utils.get_crossref_issue_date",
        side_effect=lambda x: {"@value": x, "@type": "Issued"},
    )
    mocker.patch(
        "weko_items_autofill.utils.get_crossref_relation_data",
        side_effect=lambda x, y: [{"@value": y, "@type": "DOI"}],
    )
    mocker.patch(
        "weko_items_autofill.utils.get_crossref_source_data",
        side_effect=lambda x: [{"@value": x, "@type": "ISSN"}],
    )

    data = {
        "article_title": "test_article_title",
        "author": [{"given": "A.Test1"}],
        "contributor": [{"given": "B.Test2"}],
        "journal_title": "test_journal_title",
        "volume": "47",
        "issue": "10",
        "first_page": "777",
        "last_page": "780",
        "year": "1935",
        "issn": "0031-899X",
        "doi": "10.1103/PhysRev.47.777",
    }
    api = {"error": "", "response": data}

    test = {
        "title": [{"@value": "test_article_title", "@language": "en"}],
        "creator": [{"@value": "A.Test1", "@language": "en"}],
        "contributor": [{"@value": "B.Test2", "@language": "en"}],
        "sourceTitle": {"@value": "test_journal_title", "@language": "en"},
        "sourceIdentifier": [{"@value": "0031-899X", "@type": "ISSN"}],
        "volume": {"@value": "47"},
        "issue": {"@value": "10"},
        "pageStart": {"@value": 777},
        "pageEnd": {"@value": 780},
        "date": {"@value": "1935", "@type": "Issued"},
        "relation": [{"@value": "10.1103/PhysRev.47.777", "@type": "DOI"}],
    }
    result = get_crossref_data_by_key(api, "all")
    assert result == test

    result = get_crossref_data_by_key(api, "other")
    assert result == {}


# def get_cinii_autofill_item(item_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_cinii_autofill_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_cinii_autofill_item(app, mocker):
    get_item = {
        "title": [{"title": {"@value": "test1_subitem1", "model_id": "test_item1"}}],
    }
    mocker.patch("weko_items_autofill.utils.get_item_id", return_value=get_item)
    result = get_cinii_autofill_item(1)
    assert result == {
        "title": [{"title": {"@value": "test1_subitem1", "model_id": "test_item1"}}]
    }


# def get_crossref_autofill_item(item_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_crossref_autofill_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_crossref_autofill_item(app, mocker):
    get_item = {
        "title": [{"title": {"@value": "test1_subitem1", "model_id": "test_item1"}}],
    }
    mocker.patch("weko_items_autofill.utils.get_item_id", return_value=get_item)
    result = get_crossref_autofill_item(1)
    assert result == {
        "title": [{"title": {"@value": "test1_subitem1", "model_id": "test_item1"}}]
    }

# def get_researchmap_autofill_item(item_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_researchmap_autofill_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_researchmap_autofill_item(app, mocker):
    item_id = 100
    test_jpcoar_item = {}

    # jpcoar_itemのkeyがconfig内にない場合
    with patch("weko_items_autofill.utils.get_item_id", return_value=test_jpcoar_item):
        result = get_researchmap_autofill_item(item_id)
        assert result == {}

    test_jpcoar_item = {"title":{"@value":"subitem_11111111","@attributes":{"xml:lang": "subitem_11111111"},"model_id": "item_11111111"}} 

    # jpcoar_itemのkeyがconfig内にある場合
    with patch("weko_items_autofill.utils.get_item_id", return_value=test_jpcoar_item):
        result = get_researchmap_autofill_item(item_id)
        assert result == {"title":{"@value":"subitem_11111111","@attributes":{"xml:lang": "subitem_11111111"},"model_id": "item_11111111"}} 

# def get_autofill_key_tree(schema_form, item, result=None):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_autofill_key_tree -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_autofill_key_tree(mocker):
    # item is not dict
    result = get_autofill_key_tree({}, "item")
    assert result == None

    data = json_data("data/itemtypes/mapping.json")
    item = {
        "title": [
            {
                "title": {
                    **data["test_item1"]["jpcoar_mapping"]["title"],
                    "model_id": "test_item1",
                }
            },
            {
                "title": {
                    **data["test_item2"]["jpcoar_mapping"]["title"],
                    "model_id": "test_item2",
                }
            },
            {
                "title": {
                    **data["test_item3"]["jpcoar_mapping"]["title"],
                    "model_id": "test_item3",
                }
            },
        ],
        "creator": {
            **data["test_item6"]["jpcoar_mapping"]["creator"],
            "model_id": "test_item6",
        },
        "contributor": {
            **data["test_item7"]["jpcoar_mapping"]["contributor"],
            "model_id": "test_item7",
        },
        "relation": {
            **data["test_item8"]["jpcoar_mapping"]["relation"],
            "model_id": "test_item8",
        },
        "pubdate": {"model_id": "pubdate"},
    }
    rtns = [
        {
            "@value": "test_item1.test1_subitem1",
            "@language": "test_item1.test1_subitem2",
        },
        {
            "@value": "test_item2.test1_subitem1",
            "@language": "test_item2.test1_subitem2",
        },
        {
            "@value": "test_item3.test1_subitem1",
            "@language": "test_item3.test1_subitem2",
        },
        {
            "@value": "test_item6.creatorNames.creatorName",
            "@language": "test_item6.creatorNames.creatorNameLang",
        },
        {
            "@value": "test_item7.contributorNames.contributorName",
            "@language": "test_item7.contributorNames.lang",
        },
        {
            "@value": "test_item8.test8_subitem1.test8_subitem2",
            "@type": "test_item8.test8_subitem1.test8_subitem3",
        },
    ]
    test = {
        "title": [
            {
                "title": {
                    "@value": "test_item1.test1_subitem1",
                    "@language": "test_item1.test1_subitem2",
                }
            },
            {
                "title": {
                    "@value": "test_item2.test1_subitem1",
                    "@language": "test_item2.test1_subitem2",
                }
            },
            {
                "title": {
                    "@value": "test_item3.test1_subitem1",
                    "@language": "test_item3.test1_subitem2",
                }
            },
        ],
        "creator": {
            "@value": "test_item6.creatorNames.creatorName",
            "@language": "test_item6.creatorNames.creatorNameLang",
        },
        "contributor": {
            "@value": "test_item7.contributorNames.contributorName",
            "@language": "test_item7.contributorNames.lang",
        },
        "relation": {
            "@value": "test_item8.test8_subitem1.test8_subitem2",
            "@type": "test_item8.test8_subitem1.test8_subitem3",
        },
    }
    mocker.patch("weko_items_autofill.utils.get_key_value", side_effect=rtns)
    result = get_autofill_key_tree({}, item)
    assert result == test

    # not exist creatorName, contributorName, relatedIdentifier, key_data
    # not dict and list
    item = {
        "creator": {"model_id": "test_item6"},
        "contributor": {"model_id": "test_item7"},
        "relation": {"model_id": "test_item8"},
        "str_key": "str_value",
    }
    result = get_autofill_key_tree({}, item)
    assert result == {}


# def sort_by_item_type_order(item_forms, autofill_key_tree):
#     def get_parent_key(_item):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_sort_by_item_type_order -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_sort_by_item_type_order():
    autofill_key_tree = {
        "title": [
            {"title": {"@language": "test_item2.test1_subitem2"}},
            {
                "title": {
                    "@value": "test_item1.test1_subitem1",
                    "@language": "test_item1.test1_subitem2",
                }
            },
        ],
        "creator": [
            {
                "@value": "test_item6.creatorNames.creatorName",
                "@language": "test_item6.creatorNames.creatorNameLang",
            },
        ],
        "contributor": {
            "@value": "test_item7.contributorNames.contributorName",
            "@language": "test_item7.contributorNames.lang",
        },
        "relation": [1, 2, 3, 4],
    }
    form = [{"key": "test_item1"}]
    test = {
        "title": [
            {
                "title": {
                    "@value": "test_item1.test1_subitem1",
                    "@language": "test_item1.test1_subitem2",
                }
            }
        ],
        "creator": [],
        "contributor": {
            "@value": "test_item7.contributorNames.contributorName",
            "@language": "test_item7.contributorNames.lang",
        },
        "relation": [],
    }
    sort_by_item_type_order(form, autofill_key_tree)
    assert autofill_key_tree == test


# def get_key_value(schema_form, val, parent_key):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_key_value -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_key_value():
    # item is not dict
    data = json_data("data/itemtypes/mapping.json")
    schema_form = {}
    # not exist @value
    with patch(
        "weko_items_autofill.utils.get_autofill_key_path",
        side_effect=[{"key": "test_item13.test13_subitem1"}],
    ):
        result = get_key_value(
            schema_form, data["test_item13"]["jpcoar_mapping"]["others"], "others"
        )
        assert result == {}
    # not exist @attributes
    with patch(
        "weko_items_autofill.utils.get_autofill_key_path",
        side_effect=[{"key": "test_item14.test14_subitem1"}],
    ):
        result = get_key_value(
            schema_form, data["test_item14"]["jpcoar_mapping"]["others"], "others"
        )
        assert result == {"@value": "test_item14.test14_subitem1"}

    def assert_test(item_name, parent_key, value_key, attributes_keys):
        mock_effect = [{"key": value_key}]
        mock_effect += [{"key": attributes_key} for attributes_key in attributes_keys.values()]
        with patch(
            "weko_items_autofill.utils.get_autofill_key_path",
            side_effect=mock_effect,
        ):
            result = get_key_value(
                schema_form, data[item_name]["jpcoar_mapping"][parent_key], parent_key
            )
            test = {"@value":value_key}
            test.update(attributes_keys)
            assert result == test


    # exist @attributes.xml:lang
    assert_test(
        item_name="test_item2",
        parent_key="title",
        value_key="test2_subitem1",
        attributes_keys={"@language":"test2_subitems"}
    )

    # exist @attributes.identifierType
    assert_test(
        item_name="test_item9",
        parent_key="identifier",
        value_key="subitem_identifier_uri",
        attributes_keys={"@type":"subitem_identifier_type"}
    )

    # exist @attributes.descriptionType
    assert_test(
        item_name="test_item10",
        parent_key="description",
        value_key="subitem_description",
        attributes_keys={"@language":"subitem10_lang","@type":"description_descriptionType"}
    )

    # exist @attributes.subjectSchema
    assert_test(
        item_name="test_item11",
        parent_key="subject",
        value_key="test11_subitem1",
        attributes_keys={"@language":"subject_lang","@scheme":"subject_subjectScheme","@URI":"subject_subjectURI"}
    )

    # exist @attributes.dateType
    assert_test(
        item_name="test_item12",
        parent_key="date",
        value_key="test12_subitem1",
        attributes_keys={"@type":"test12_subitem2"}
    )


# def get_autofill_key_path(schema_form, parent_key, child_key):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_autofill_key_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_autofill_key_path(app):
    data = json_data("data/itemtypes/forms.json")[:2]
    parent_key = "test_item5"
    child_key = "test5_subitem2"

    # nomal
    with patch(
        "weko_items_autofill.utils.get_specific_key_path",
        side_effect=[(True, "test_item5.test5_subitem2")],
    ):
        result = get_autofill_key_path(data, parent_key, child_key)
        assert result == {"key": "test_item5.test5_subitem2"}

    # not exist
    with patch(
        "weko_items_autofill.utils.get_specific_key_path",
        side_effect=[(False, None), (False, None)],
    ):
        result = get_autofill_key_path(data, parent_key, child_key)
        assert result == {"key": None}

    # raise Exception
    with patch(
        "weko_items_autofill.utils.get_specific_key_path",
        side_effect=Exception("test_error"),
    ):
        result = get_autofill_key_path(data, parent_key, child_key)
        assert result == {"key": None, "error": "test_error"}


# def get_specific_key_path(des_key, form):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_specific_key_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_specific_key_path():
    # form is dict
    des_key = ["test1_subitem1"]
    form = {"key": "test_item1[].test1_subitem1", "type": "text", "title": "Title"}
    existed, path_result = get_specific_key_path(des_key, form)
    assert existed == True
    assert path_result == "test_item1[].test1_subitem1"
    # form is list
    des_key = ["test1_subitem2"]
    form = {
        "key": "test_item1",
        "title": "Title",
        "items": [
            {"key": "test_item1[].test1_subitem1", "type": "text", "title": "Title"},
            {
                "key": "test_item1[].test1_subitem2",
                "type": "select",
                "title": "Language",
                "titleMap": [
                    {"name": "ja", "value": "ja"},
                    {"name": "en", "value": "en"},
                ],
            },
            {
                "key": "test_item1[].test1_subitem3",
                "type": "select",
                "title": "Language2",
                "titleMap": [
                    {"name": "ja", "value": "ja"},
                    {"name": "en", "value": "en"},
                ],
            },
        ],
    }
    existed, path_result = get_specific_key_path(des_key, form)
    assert existed == True
    assert path_result == "test_item1[].test1_subitem2"

    # not existed key in form
    form = {}
    existed, path_result = get_specific_key_path(des_key, form)
    assert existed == False
    assert path_result == None

    # not existed key
    form = []
    existed, path_result = get_specific_key_path(des_key, form)
    assert existed == False
    assert path_result == None

    # form is not list, not dict
    form = "test_form"
    existed, path_result = get_specific_key_path(des_key, form)
    assert existed == False
    assert path_result == None


# def build_record_model(item_autofill_key, api_data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_build_record_model -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_build_record_model(app):
    # not api_data,not item_autofill_key
    result = build_record_model([], [])
    assert result == []

    api_data = {
        "title": [{"@value": "test_article_title", "@language": "en"}],
        "creator": [{"@value": "A.Test1", "@language": "en"}],
        "contributor": [{"@value": "B.Test2", "@language": "en"}],
        "sourceTitle": {"@value": "test_journal_title", "@language": "en"},
        "sourceIdentifier": [{"@value": "0031-899X", "@type": "ISSN"}],
        "volume": {"@value": "47"},
        "issue": {"@value": "10"},
        "pageStart": {"@value": 777},
        "pageEnd": {"@value": 780},
        "date": {"@value": "1935", "@type": "Issued"},
        "relation": [{"@value": "10.1103/PhysRev.47.777", "@type": "DOI"}],
        "not_dict_list": {"@value": "value"},
    }
    item_autofill_key = {
        "title": [
            {
                "title": {
                    "@value": "test_item1.test1_subitem1",
                    "@language": "test_item1.test1_subitem2",
                }
            },
            {
                "title": {
                    "@value": "test_item2.test1_subitem1",
                    "@language": "test_item2.test1_subitem2",
                }
            },
            {
                "title": {
                    "@value": "test_item3.test1_subitem1",
                    "@language": "test_item3.test1_subitem2",
                }
            },
        ],
        "creator": {
            "@value": "test_item6.creatorNames.creatorName",
            "@language": "test_item6.creatorNames.creatorNameLang",
        },
        "contributor": {
            "@value": "test_item7.contributorNames.contributorName",
            "@language": "test_item7.contributorNames.lang",
        },
        "relation": {
            "@value": "test_item8.test8_subitem1.test8_subitem2",
            "@type": "test_item8.test8_subitem1.test8_subitem3",
        },
        "volume": {"@value": "test_item16.test16_subitem1"},
        "not_dict_list": "value",
    }
    test = [
        {
            "test_item1": {
                "test1_subitem1": "test_article_title",
                "test1_subitem2": "en",
            }
        },
        {
            "test_item6": {
                "creatorNames": {"creatorName": "A.Test1", "creatorNameLang": "en"}
            }
        },
        {
            "test_item7": {
                "contributorNames": {"contributorName": "B.Test2", "lang": "en"}
            }
        },
        {
            "test_item8": {
                "test8_subitem1": {
                    "test8_subitem2": "10.1103/PhysRev.47.777",
                    "test8_subitem3": "DOI",
                }
            }
        },
        {"test_item16": {"test16_subitem1": "47"}},
    ]
    result = build_record_model(item_autofill_key, api_data)
    assert result == test


# def build_model(form_model, form_key):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_build_model -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_build_model():
    # form_model is dict
    form_model = {}
    form_key = "test_item1[].test1_subitem1"
    build_model(form_model, form_key)
    assert form_model == {"test_item1.test1_subitem1": []}
    form_key = "test_item2.test2_subitem1"
    build_model(form_model, form_key)
    assert form_model == {
        "test_item1.test1_subitem1": [],
        "test_item2.test2_subitem1": {},
    }
    # form_model is list
    form_model = []
    form_key = "test_item1[].test1_subitem1"
    build_model(form_model, form_key)
    assert form_model == [{"test_item1.test1_subitem1": []}]
    form_key = "test_item2.test2_subitem1"
    build_model(form_model, form_key)
    assert form_model == [
        {"test_item1.test1_subitem1": []},
        {"test_item2.test2_subitem1": {}},
    ]


# def build_form_model(form_model, form_key, autofill_key=None):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_build_form_model -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_build_form_model():
    # form_key is dict
    form_model = {}
    form_key = {
        "@value": "test_item7.contributorNames.contributorName",
        "@language": "test_item7.contributorNames.lang",
        "not_str": ["not_str_value"],
    }
    test = {
        "@value": {"test_item7": {"contributorNames": {"contributorName": "@value"}}},
        "@language": {"test_item7": {"contributorNames": {"lang": "@language"}}},
    }
    build_form_model(form_model, form_key)
    assert form_model == test

    # form_key is list
    form_model = []
    form_key = ["test_item7", "contributorNames"]
    test = [{"test_item7": {"contributorNames": "test_key"}}]
    build_form_model(form_model, form_key, "test_key")
    assert form_model == test

    # form_key is list, form_key.length = 0
    form_model = []
    form_key = []
    test = []
    build_form_model(form_model, form_key, "test_key")
    assert form_model == test

    # form_key is list, form_key.length = 1
    ## form_model is list
    form_model = []
    form_key = ["test_item7"]
    test = [{"test_item7": "test_key"}]
    build_form_model(form_model, form_key, "test_key")
    assert form_model == test

    ## form_model is dict
    form_model = {}
    form_key = ["test_item7"]
    test = {"test_item7": "test_key"}
    build_form_model(form_model, form_key, "test_key")
    assert form_model == test

    ## form_model is not list, dict
    form_model = 123
    form_key = ["test_item7"]
    test = 123
    build_form_model(form_model, form_key, "test_key")
    assert form_model == test

    # form_key is not list, dict
    form_model = {}
    form_key = "str_key"
    test = {}
    build_form_model(form_model, form_key, "test_key")
    assert form_model == test


# def merge_dict(original_dict, merged_dict, over_write=True):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_merge_dict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_merge_dict(app):
    original_dict = [
        {
            "test_item2": {"test2_subitem1": {"test2_subitem2": "@language"}},
            "test_item3": {"test3_subitem1": {"test3_subitem2": "@value"}},
            "test_item4": "test1",
        }
    ]
    merged_dict = [
        {
            "test_item1": {
                "test1_subitem1": {"test1_subitem2": "@value"}
            },  # key not in original_dict
            "test_item2": {
                "test2_subitem1": {"test2_subitem3": "@value"}
            },  # key in original_dict
            "test_item3": {
                "test3_subitem1": {"test3_subitem2": "@value"}
            },  # orinal_dict=merge_dict
            "test_item4": "test4",  # conflict
        }
    ]
    test = [
        {
            "test_item2": {
                "test2_subitem1": {
                    "test2_subitem2": "@language",
                    "test2_subitem3": "@value",
                }
            },
            "test_item3": {"test3_subitem1": {"test3_subitem2": "@value"}},
            "test_item4": "test1",
            "test_item1": {"test1_subitem1": {"test1_subitem2": "@value"}},
        }
    ]
    merge_dict(original_dict, merged_dict, over_write=True)
    assert original_dict == test
    original_dict = [
        {
            "test_item2": {"test2_subitem1": {"test2_subitem2": "@language"}},
            "test_item3": {"test3_subitem1": {"test3_subitem2": "@value"}},
            "test_item4": "test1",
        }
    ]
    merged_dict = [
        {
            "test_item1": {
                "test1_subitem1": {"test1_subitem2": "@value"}
            },  # key not in original_dict
            "test_item2": {
                "test2_subitem1": {"test2_subitem3": "@value"}
            },  # key in original_dict
            "test_item3": {
                "test3_subitem1": {"test3_subitem2": "@value"}
            },  # orinal_dict=merge_dict
            "test_item4": "test4",  # conflict
        }
    ]
    test = [
        {
            "test_item2": {
                "test2_subitem1": {
                    "test2_subitem2": "@language",
                    "test2_subitem3": "@value",
                }
            },
            "test_item3": {"test3_subitem1": {"test3_subitem2": "@value"}},
            "test_item4": "test1",
            "test_item1": {"test1_subitem1": {"test1_subitem2": "@value"}},
        }
    ]
    merge_dict(original_dict, merged_dict, over_write=False)
    assert original_dict == test

    # over_write is False, raise conflict
    original_dict = {"test_item4": "test1"}
    merged_dict = {"test_item4": "test4"}
    test = ""
    merge_dict(original_dict, merged_dict, over_write=False)
    assert original_dict == {"test_item4": "test1"}

    # not type dict and dict, list and list
    original_dict = {"test_item2": {"test2_subitem1": {"test2_subitem2": "@language"}}}
    merged_dict = [{"test_item1": {"test1_subitem1": {"test1_subitem2": "@value"}}}]
    merge_dict(original_dict, merged_dict)
    assert original_dict == {
        "test_item2": {"test2_subitem1": {"test2_subitem2": "@language"}}
    }


# def deepcopy(original_object, new_object):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_deepcopy -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_deepcopy():
    original_object = ""
    new_object = ""
    result = deepcopy(original_object, new_object)
    assert result == None

    new_object = {}
    original_object = [
        {"test1": ["test1_1", "test1_2"], "test2": "value2"},
        {"test3": ["test3_1", "test3_2"], "test4": "value4"},
        "test_str",
    ]
    result = deepcopy(original_object, new_object)
    assert new_object == {
        "test1": ["test1_1", "test1_2"],
        "test2": "value2",
        "test3": ["test3_1", "test3_2"],
        "test4": "value4",
    }


# def fill_data(form_model, autofill_data, is_multiple_data=False):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_fill_data -vv -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_fill_data(app):
    # autofill_data is not dict, list
    form_model = ""
    autofill_data = ""
    result = fill_data(form_model, autofill_data)
    assert result == []
    
    # not multiple_data, form.get(key) is not list
    autofill_data = [{"@value": "A.Test1", "@language": "en"}]
    form_model = {
        "@value": {"test_item6": {"creatorNames": {"creatorName": "@value"}}},
        "@language": {"test_item6": {"creatorNames": {"creatorNameLang": "@language"}}},
    }
    test = {
        "@value": {"test_item6": {"creatorNames": {"creatorName": "A.Test1"}}},
        "@language": {"test_item6": {"creatorNames": {"creatorNameLang": "en"}}},
    }
    result = fill_data(form_model, autofill_data)
    #assert form_model == test
    assert result == test

    # not multiple_data, form.get(key) is list
    autofill_data = [{"@value": "A.Test1"}]
    form_model = {
        "@value": [{"test_item6": {"creatorNames": {"creatorName": "@value"}}}],
    }
    test = {"@value": [{"test_item6": {"creatorNames": {"creatorName": "A.Test1"}}}]}
    result = fill_data(form_model, autofill_data)
    assert result == test

    # multiple_data, form.get(key) is list
    autofill_data = [
        [{"@value": "TEST Taro", "@language": "en"},{"@value": "テスト 太郎", "@language": "ja"}],
        [{"@value": "TEST Ziro", "@language": "en"},{"@value": "テスト 次郎", "@language": "ja"}]
    ]
    form_model = {"item_xxx": [{"creatorNames":[{"creatorName": "@value", "creatorNameLang": "@language"}]}]}
    test = {"item_xxx": [
            {
                "creatorNames": [
                    {"creatorName": "TEST Taro", "creatorNameLang": "en"},
                    {"creatorName": "テスト 太郎", "creatorNameLang": "ja"}
                ]
            },
            {
                "creatorNames": [
                    {"creatorName": "TEST Ziro", "creatorNameLang": "en"},
                    {"creatorName": "テスト 次郎", "creatorNameLang": "ja"}
                ]
            }
        ]
    }
    result = fill_data(form_model, autofill_data)
    assert result == test

    # autofill_data is dict, form_model is {}
    autofill_data = {"@value": "47"}
    form_model = {}
    test = {}
    result = fill_data(form_model,autofill_data)
    assert result == test

    #
    autofill_data = {"@value": "47"}
    form_model = [
        {"@value": {"test_item16": {"test16_subitem1": "@value"}}},
        {"@value": {"test_item17": {"test17_subitem1": "@value"}}},
    ]
    test = [
        {"@value": {"test_item16": {"test16_subitem1": "47"}}},
        {"@value": {"test_item17": {"test17_subitem1": "47"}}},
    ]
    result = fill_data(form_model, autofill_data)
    assert result == test

    # form_model is not list, dict
    autofill_data = {"@value": "47"}
    form_model = "test"
    fill_data(form_model, autofill_data)

     # with schema and validate success
    autofill_data = [{'@value': 'タイトル', '@language': 'ja'}]
    form_model = {'item_30001_title0': [{'subitem_title': '@value', 'subitem_title_language': '@language'}]}
    schema ={
        "type": "object",
        "properties": {
            "item_30001_title0": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subitem_title": {
                            "type": "string",
                            "title": "タイトル",
                            "title_i18n": {
                                "en": "Title",
                                "ja": "タイトル"
                            }
                        },
                        "subitem_title_language": {
                            "enum": [
                                None,
                                "ja",
                            ],
                            "type": [
                                "null",
                                "string"
                            ],
                            "title": "言語",
                        }
                    }
                },
                "title": "Title",
            }
        }
    }
    expected = {'item_30001_title0': [{'subitem_title': 'タイトル', 'subitem_title_language': 'ja'}]}
    result = fill_data(form_model, autofill_data, schema)
    assert result == expected

    # with schema and validate fail
    autofill_data = [{'@value': 'タイトル', '@language': ''}]
    expected  = {'item_30001_title0': [{'subitem_title': 'タイトル'}]}
    result = fill_data(form_model, autofill_data, schema)
    assert result == expected

    # with invalid schema and skip validate
    autofill_data = [{'@value': 'タイトル', '@language': 'ja'}]
    schema["properties"]["item_30001_title0"]["type"] = "object"
    expected = {'item_30001_title0': [{'subitem_title': 'タイトル', 'subitem_title_language': 'ja'}]}
    result = fill_data(form_model, autofill_data, schema)
    assert result == expected

    # duplicate language
    autofill_data = [{"@value": "Title1", "@language": "en"}, {"@value": "Title2", "@language": "en"}]
    expected = {'item_30001_title0': [{'subitem_title': 'Title1', 'subitem_title_language': 'en'}]}
    result = fill_data(form_model, autofill_data, None, True)
    assert result == expected

    # schema with array items
    schema = {"type": "array", "items": {"type": "object", "properties": {"prop1": {"type": "string"}}}}
    autofill_data = [{"@value": "Title1"}]
    form_model = {"prop1": "@value"}
    result = fill_data(form_model, autofill_data, schema)
    assert result == {"prop1": "Title1"}

    # form_model is dict, autofill_data is str
    autofill_data = "test_data"
    form_model = {"test_key":"form_test"}
    test = {"test_key":"test_data"}
    result = fill_data(form_model, autofill_data)
    assert result == test

    # form_model is list, autofill_data is str
    autofill_data = "test_data"
    form_model = [{"test_key":"form_test"}]
    test = [{"test_key":"test_data"}]
    result = fill_data(form_model, autofill_data)
    assert result == test

    # form_model is list, autofill_data is str
    autofill_data = "test_data"
    form_model = [{"test_key":100}]
    test = [{"test_key":[]}]
    result = fill_data(form_model, autofill_data)
    assert result == test

    # form_model is list, autofill_data is int
    autofill_data = 111
    form_model = ""
    result = fill_data(form_model, autofill_data)
    assert result == None

# def is_multiple(form_model, autofill_data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_is_multiple -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_is_multiple():
    # autofill_data is not list
    form_model = {}
    autofill_data = {}
    result = is_multiple(form_model, autofill_data)
    assert result == False

    # autofill_data is list and form_model[0] is list
    form_model = {"test1": [1, 2, 3], "test2": "value2"}
    autofill_data = [1, 2, 3]
    result = is_multiple(form_model, autofill_data)
    assert result == True

    # autofill_data is list and form_model[0] is dict
    form_model = {"test1": "value2", "test2": [1, 2, 3]}
    autofill_data = [1, 2, 3]
    result = is_multiple(form_model, autofill_data)
    assert result == False

    # autofill_data is list and form_model.length = 0
    form_model = []
    autofill_data = [1, 2, 3]
    result = is_multiple(form_model, autofill_data)
    assert result == None


# def get_workflow_journal(activity_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_workflow_journal -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_workflow_journal(app, db, actions):
    action_journal = ActionJournal(
        activity_id=1, action_id=1, action_journal={"key": "value"}
    )
    db.session.add(action_journal)
    db.session.commit()

    # not exist journal
    result = get_workflow_journal(str(100))
    assert result == None

    # exist journal
    result = get_workflow_journal(str(1))
    assert result == {"key": "value"}


# def convert_crossref_xml_data_to_dictionary(api_data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_convert_crossref_xml_data_to_dictionary -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_convert_crossref_xml_data_to_dictionary(mocker):
    data = (
        "<body>"
        '<doi type="journal_article">10.1103/PhysRev.47.777</doi>'
        '<issn type="print">0031-899X</issn>'
        "<issn>0031-899Y</issn>"
        "<contributors>"
        '<contributor sequence="first" contributor_role="editor">'
        "<given_name>A.</given_name>"
        "<surname>Test1</surname>"
        "</contributor>"
        "</contributors>"
        '<year media_type="online">1935</year>'
        '<year media_type="print">1936</year>'
        "<article_title>this is article title</article_title>"
        "<other_key>this is other key</other_key>"
        "</body>"
    )
    data = '<?xml version="1.0" encoding="UTF-8"?>\n' + data

    def mock_cont_data(elem, roles, rtn_data):
        rtn_data.update({"contributor": [{"given": "A.", "family": "Test1"}]})

    mocker.patch(
        "weko_items_autofill.utils._get_contributor_and_author_names",
        side_effect=mock_cont_data,
    )
    test = {
        "response": {
            "doi": "10.1103/PhysRev.47.777",
            "issn": "0031-899X",
            "contributor": [{"given": "A.", "family": "Test1"}],
            "year": "1936",
            "article_title": "this is article title",
        },
        "error": "",
    }
    result = convert_crossref_xml_data_to_dictionary(data)
    assert result == test

    result = convert_crossref_xml_data_to_dictionary(data,'utf-8')
    assert result == test

    data = '<?xml version="1.0" encoding="UTF-8"?>\n<crossref_result xmlns="http://www.crossref.org/qrschema/2.0" version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.crossref.org/qrschema/2.0 https://www.crossref.org/schema/crossref_query_output2.0.xsd"><query_result><head><doi_batch_id>none</doi_batch_id></head><body><query status="resolved" fl_count="0"><doi type="journal_article">xxx/yyy</doi><issn type="electronic">1234567</issn><journal_title>journal title</journal_title><contributors><contributor sequence="first" contributor_role="author"><given_name>John</given_name><surname>Doe</surname></contributor></contributors><year media_type="online">2018</year><publication_type>full_text</publication_type><article_title>article title</article_title></query></body></query_result></crossref_result>'
    result = convert_crossref_xml_data_to_dictionary(data)
    assert result == {'error': '','response': {'article_title': 'article title','contributor': [{'family': 'Test1', 'given': 'A.'}],'doi': 'xxx/yyy','journal_title': 'journal title'}}

    data = '<?xml version="1.0" encoding="UTF-8"?>\n<crossref_result xmlns="http://www.crossref.org/qrschema/2.0" version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.crossref.org/qrschema/2.0 https://www.crossref.org/schema/crossref_query_output2.0.xsd"><query_result><head><doi_batch_id>none</doi_batch_id></head><body></body></query_result></crossref_result>'
    result = convert_crossref_xml_data_to_dictionary(data)
    assert result == {'error': '', 'response': {}}

    data = '<crossref_result xmlns="http://www.crossref.org/qrschema/2.0" version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.crossref.org/qrschema/2.0 https://www.crossref.org/schema/crossref_query_output2.0.xsd"><query_result><head><doi_batch_id>none</doi_batch_id></head><body></body></query_result></crossref_result>'
    result = convert_crossref_xml_data_to_dictionary(data)
    assert result == {'error': '', 'response': {}}

    error_data = '<?xml version="1.0" encoding="UTF-8"?>\n<crossref_result xmlns="http://www.crossref.org/qrschema/2.0" version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.crossref.org/qrschema/2.0 https://www.crossref.org/schema/crossref_query_output2.0.xsd"><query_result><head><doi_batch_id>none</doi_batch_id></head><body></query_result></crossref_result>'
    result = convert_crossref_xml_data_to_dictionary(error_data)
    assert result == {'error': 'Opening and ending tag mismatch: body line 2 and query_result, line 2, column 331 (<string>, line 2)','response': {}}



# def _get_contributor_and_author_names(elem, contributor_roles, rtn_data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_contributor_and_author_names -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_contributor_and_author_names():
    data1 = (
        '<contributor sequence="first" contributor_role="editor">'
        "<surname>A. Test1</surname>"
        "</contributor>"
    )
    data2 = (
        '<contributor sequence="additional" contributor_role="editor">'
        "<given_name>B.Test2</given_name>"
        "</contributor>"
    )
    data3 = (
        '<contributor sequence="additional" contributor_role="author">'
        "<given_name>C.</given_name>"
        "<surname>Test3</surname>"
        "</contributor>"
    )
    data4 = (
        '<contributor sequence="additional" contributor_role="author">'
        "<given_name>D.</given_name>"
        "<surname>Test4</surname>"
        "</contributor>"
    )
    result = {}
    roles = ["editor", "chair", "translator"]

    elem = etree.fromstring(data1)
    _get_contributor_and_author_names(elem, roles, result)
    assert result == {"contributor": [{"family": "A. Test1"}]}

    elem = etree.fromstring(data2)
    _get_contributor_and_author_names(elem, roles, result)
    assert result == {"contributor": [{"family": "A. Test1"}, {"given": "B.Test2"}]}

    elem = etree.fromstring(data3)
    _get_contributor_and_author_names(elem, roles, result)
    assert result == {
        "contributor": [{"family": "A. Test1"}, {"given": "B.Test2"}],
        "author": [{"given": "C.", "family": "Test3"}],
    }

    elem = etree.fromstring(data4)
    _get_contributor_and_author_names(elem, roles, result)
    assert result == {
        "contributor": [{"family": "A. Test1"}, {"given": "B.Test2"}],
        "author": [
            {"given": "C.", "family": "Test3"},
            {"given": "D.", "family": "Test4"},
        ],
    }


# def get_wekoid_record_data(recid, item_type_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_wekoid_record_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_wekoid_record_data(app, client, users, records, itemtypes):
    item_type_id = itemtypes[2][0].id
    recid = records[0][0].pid_value
    # raise permission error
    with pytest.raises(ValueError) as e:
        get_wekoid_record_data(recid, item_type_id)
        assert (
            str(e)
            == "The item cannot be copied because you do not have permission to view it."
        )

    login(app, client, obj=users[0]["obj"])
    test = [
        {
            "item_1617186331708": [
                {"subitem_1551255647225": "title", "subitem_1551255648112": "ja"}
            ]
        },
        {"item_1617186476635": {"subitem_1600958577026": "test_access_url"}},
        {
            "item_1617258105262": {
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                "resourcetype": "conference paper",
            }
        },
    ]
    result = get_wekoid_record_data(recid, item_type_id)
    assert result == test
    logout(app, client)

# def get_researchmapid_record_data(parmalink, achievement_type ,achievement_id ,item_type_id) -> list:
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_researchmapid_record_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_researchmapid_record_data(app, db, itemtypes):
    data = json_data("data/researchmap_test_data.json")
    data = json.dumps(data)

    test =  [{'item_1617186331708': [{'subitem_1551255647225': 'full-schema', 'subitem_1551255648112': 'en'}, {'subitem_1551255647225': '満艦飾', 'subitem_1551255648112': 'ja'}]}, {'item_1617186419668': [{'creatorNames': [{'creatorName': 'WEKO, 太郎', 'creatorNameLang': 'ja'}]}]}, {'item_1617186626617': [{'subitem_description': '描写', 'subitem_description_language': 'ja', 'subitem_description_type': ''}]}, {'item_1617186643794': [{'subitem_1522300316516': '出版者●●', 'subitem_1522300295150': 'ja'}]}, {'item_1617186660861': [{'subitem_1522300722591': '2024-02-05', 'subitem_1522300695726': '2024-02-05'}]}, {'item_1617186702042': [{'subitem_1551255818386': 'jpn'}]}, {'item_1617258105262': {'resourcetype': 'article'}}, {'item_1617186959569': {'subitem_1551256328147': '123'}}, {'item_1617186981471': {'subitem_1551256294723': '456'}}, {'item_1617187024783': {'subitem_1551256198917': '1'}}, {'item_1617187045071': {'subitem_1551256185532': '10'}}]
    with patch("weko_items_autofill.utils.Researchmap.get_data", return_value=data):
        result,_ = get_researchmapid_record_data("M1cQhPtdmlrSRFo4", "published_papers", 1358081, 3)
        assert result == test

    data_2 = json_data("data/researchmap_test_data_2.json")
    data_2 = json.dumps(data_2)
    test =  [{'item_1617186331708': [{'subitem_1551255647225': 'aaaaa', 'subitem_1551255648112': 'en'}, {'subitem_1551255647225': 'ああああ', 'subitem_1551255648112': 'ja'}]}, {'item_1617186419668': [{'creatorNames': [{'creatorName': 'Author English', 'creatorNameLang': 'en'}]}]}, {'item_1617186626617': [{'subitem_description': '国際・国内誌概要(英語)', 'subitem_description_language': 'en', 'subitem_description_type': ''}, {'subitem_description': '国際・国内誌概要(日本語)', 'subitem_description_language': 'ja', 'subitem_description_type': ''}]}, {'item_1617186643794': [{'subitem_1522300316516': 'pub_english', 'subitem_1522300295150': 'en'}, {'subitem_1522300316516': '出版者・発行元(日本語)', 'subitem_1522300295150': 'ja'}]}, {'item_1617186660861': [{'subitem_1522300722591': '2010-10-10', 'subitem_1522300695726': '2010-10-10'}]}, {'item_1617186702042': [{'subitem_1551255818386': 'eng'}]}, {'item_1617258105262': {'resourcetype': 'conference paper'}}, {'item_1617353299429': [{'subitem_1522306287251': {'subitem_1522306436033': '10.11501/3140078', 'subitem_1522306382014': 'DOI'}}]}, {'item_1617186941041': [{'subitem_1522650091861': 'aaaaa', 'subitem_1522650068558': 'en'}, {'subitem_1522650091861': 'ああああ', 'subitem_1522650068558': 'ja'}]}, {'item_1617186959569': {'subitem_1551256328147': '123'}}, {'item_1617186981471': {'subitem_1551256294723': '456'}}, {'item_1617187024783': {'subitem_1551256198917': '1'}}, {'item_1617187045071': {'subitem_1551256185532': '10'}}]
    with patch("weko_items_autofill.utils.Researchmap.get_data", return_value=data_2):
        result,_ = get_researchmapid_record_data("M1cQhPtdmlrSRFo4", "published_papers", 1356383, 3)
        assert result == test

        result,_ = get_researchmapid_record_data("M1cQhPtdmlrSRFo4", "published_papers", 1356383, 99999)
        assert result == []

        result,_ = get_researchmapid_record_data("M1cQhPtdmlrSRFo4", "published_papers", 1356383, 4)
        assert result == []
            
    data = {
    "error": "not_found",
    "error_description": "ページが見つかりません。"
    }
    data = json.dumps(data)
    with patch("weko_items_autofill.utils.Researchmap.get_data", return_value=data):
        with pytest.raises(Exception):
            result,_ = get_researchmapid_record_data("M1cQhPtdmlrSRFo4", "published_papers", 999999, 3)

    with patch("weko_items_autofill.utils.Researchmap.get_data", return_value=data_2):
        app.config.update(WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS = [{ 'type' : 'xxx' , "rm_name" : 'paper_title', "jpcore_name" : 'dc:title' , "weko_name" :"title"}])
        result,_ = get_researchmapid_record_data("M1cQhPtdmlrSRFo4", "published_papers", 1356383, 3)
        assert result == []
        
    with patch("weko_items_autofill.utils.Researchmap.get_data", return_value=data_2):
        app.config.update(WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS=WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS)
        app.config.update(WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_TYPE_MAPPINGS= [{'achievement_type' : 'xxx','detail_type_name':'','JPCOAR_resource_type':'article'}])
        test = [{'item_1617186331708': [{'subitem_1551255647225': 'aaaaa', 'subitem_1551255648112': 'en'}, {'subitem_1551255647225': 'ああああ', 'subitem_1551255648112': 'ja'}]}, {'item_1617186419668': [{'creatorNames': [{'creatorName': 'Author English', 'creatorNameLang': 'en'}]}]}, {'item_1617186626617': [{'subitem_description': '国際・国内誌概要(英語)', 'subitem_description_language': 'en', 'subitem_description_type': ''}, {'subitem_description': '国際・国内誌概要(日本語)', 'subitem_description_language': 'ja', 'subitem_description_type': ''}]}, {'item_1617186643794': [{'subitem_1522300316516': 'pub_english', 'subitem_1522300295150': 'en'}, {'subitem_1522300316516': '出版者・発行元(日本語)', 'subitem_1522300295150': 'ja'}]}, {'item_1617186660861': [{'subitem_1522300722591': '2010-10-10', 'subitem_1522300695726': '2010-10-10'}]}, {'item_1617186702042': [{'subitem_1551255818386': 'eng'}]}, {'item_1617353299429': [{'subitem_1522306287251': {'subitem_1522306436033': '10.11501/3140078', 'subitem_1522306382014': 'DOI'}}]}, {'item_1617186941041': [{'subitem_1522650091861': 'aaaaa', 'subitem_1522650068558': 'en'}, {'subitem_1522650091861': 'ああああ', 'subitem_1522650068558': 'ja'}]}, {'item_1617186959569': {'subitem_1551256328147': '123'}}, {'item_1617186981471': {'subitem_1551256294723': '456'}}, {'item_1617187024783': {'subitem_1551256198917': '1'}}, {'item_1617187045071': {'subitem_1551256185532': '10'}}]
        result,_ = get_researchmapid_record_data("M1cQhPtdmlrSRFo4", "published_papers", 1356383, 3)
        assert result == test


# def build_record_model_for_wekoid(item_type_id, item_map_data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_build_record_model_for_wekoid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_build_record_model_for_wekoid(db):
    schema = {
        "properties": {
            "item01": {},  # not existed props
            "item02": {
                "properties": {
                    "subitem02_1": {"title": "SubItem02_1"},
                    "subitem02_2": {"title": "SubItem02_1"},
                }
            },  # is_multiple_item is false, props existed
            "item03": {
                "items": {
                    "properties": {
                        "subitem03_1": {"title": "SubItem03_1"},
                        "subitem03_2": {"title": "SubItem03_2"},
                    }
                }
            },  # is_multiple_item is true, props existed
            "item04": {},  # not in item_has_val
        }
    }

    itemtype_name = ItemTypeName(
        id=1, name="テスト", has_site_license=True, is_active=True
    )
    itemtype = ItemType(
        id=1,
        name_id=itemtype_name.id,
        harvesting_type=True,
        schema=schema,
        form={},
        render={},
        tag=1,
        version_id=1,
        is_deleted=False,
    )
    db.session.add(itemtype_name)
    db.session.add(itemtype)
    db.session.commit()

    item_map_data = {"item01": [], "item02.subitem02_1": [], "item03.subitem03_1": []}
    result = build_record_model_for_wekoid(itemtype.id, item_map_data)
    test = [
        {"item01": {}},
        {"item02": {"subitem02_1": {}, "subitem02_2": {}}},
        {"item03": [{"subitem03_1": {}, "subitem03_2": {}}]},
    ]
    assert result == test


# def is_multiple_item(val):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_is_multiple_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_is_multiple_item():
    # val is not dict
    val = ["val1", "val2"]
    result = is_multiple_item(val)
    assert result == False

    # exist val.items.properties
    val = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "sub_item_0001": {"type": "string", "title": "Title"},
                "sub_item_0002": {"type": ["null", "string"], "title": "Language"},
            },
        },
    }
    result = is_multiple_item(val)
    assert result == True
    # not exist val.items.properties
    val = {
        "type": "object",
        "title": "Identifier Registration",
        "properties": {
            "sub_item_0001": {"type": "string", "title": "ID登録"},
            "subitem_0002": {"type": ["null", "string"], "title": "ID登録タイプ"},
        },
    }
    result = is_multiple_item(val)
    assert result == False


# def get_record_model(res_temp, key, properties):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_record_model -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_record_model():
    res_temp = {"key1": []}
    key = "key1"
    properties = {
        "prop1": {
            "items": {
                "properties": {  # is multiple
                    "name": "Prop1",
                    "prop1_1": {"name": "Prop1_1"},
                }
            }
        },
        "prop2": {
            "properties": {  # is not multiple
                "name": "prop2",
                "prop2_1": {
                    "items": {"properties": {"prop2_1_1": {"name": "Prop2_1_1"}}}
                },
                "prop2_2": {"properties": {"name": "Prop2_2"}},
            }
        },
        "prop3": {"name": "Prop3"},
        "propx": "value2",
    }
    get_record_model(res_temp, key, properties)
    test = {
        "key1": [
            {
                "prop1": [{"prop1_1": {}}],
                "prop2": {"prop2_1": [{"prop2_1_1": {}}], "prop2_2": {}},
                "prop3": {},
            }
        ]
    }
    assert res_temp == test

    res_temp = [{"key2": [], "key3": {}}, {"key1": [], "key2": []}]
    test = [
        {"key2": [], "key3": {}},
        {
            "key1": [],
            "key2": [],
            "prop1": [{"prop1_1": {}}],
            "prop2": {"prop2_1": [{"prop2_1_1": {}}], "prop2_2": {}},
            "prop3": {},
        },
    ]
    get_record_model(res_temp, key, properties)
    assert res_temp == test

    res_temp = [{"key2": [], "key3": {}}, {"key2": [], "key3": {}}, {}]
    test = [
        {"key2": [], "key3": {}},
        {"key2": [], "key3": {}},
        {
            "prop1": [{"prop1_1": {}}],
            "prop2": {"prop2_1": [{"prop2_1_1": {}}], "prop2_2": {}},
            "prop3": {},
        },
    ]
    get_record_model(res_temp, key, properties)
    assert res_temp == test


# def set_val_for_record_model(record_model, item_map_data):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_set_val_for_record_model -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_set_val_for_record_model():
    map_data = {
        "item_1617186331708.subitem_1551255647225": ["title"],
        "item_1617186331708.subitem_1551255648112": ["ja"],
        "item_1617258105262.resourcetype": ["conference paper"],
        "item_1617258105262.resourceuri": ["http://purl.org/coar/resource_type/c_5794"],
    }
    model = [
        {
            "item_1617186331708": [
                {"subitem_1551255647225": {}, "subitem_1551255648112": {}}
            ]
        },
        {"item_1617258105262": {"resourceuri": {}, "resourcetype": {}}},
    ]

    model = [
        {"key1": {"key1": {}, "subkey1_1": {}}},
        {
            "key2": [
                {"subkey2_1": {}},
                {"subkey2_2": {"subkey2_1": {}}},
            ]
        },
    ]
    map_data = {"key1.subkey1_1": ["value1"], "key2.subkey2_1": ["value1", "value2"]}
    test = [
        {"key1": {"subkey1_1": "value1"}},
        {"key2": [{"subkey2_1": "value1"}, {"subkey2_2": {"subkey2_1": "value2"}}]},
    ]
    record_model = set_val_for_record_model(model, map_data)
    assert record_model == test


# def set_val_for_all_child(keys, models, values):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_set_val_for_all_child -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_set_val_for_all_child():
    # model_temp is dict
    keys = ["key1", "subkey1_1"]
    values = ["value1"]
    models = [{"key1": {"key1": {}, "subkey1_1": {}}}]
    test = [{"key1": {"key1": {}, "subkey1_1": "value1"}}]
    set_val_for_all_child(keys, models, values)
    assert models == test

    # model_temp is list
    ## len(model_temp) = len(values)
    keys = ["key2", "subkey2_1"]
    values = ["value1", "value2", "value3", "value4"]
    models = [
        {
            "key2": [
                {"subkey2_1": {}},
                {"subkey2_2": {"subkey2_1": {}}},
                {"subkey2_3": [{"subkey2_1": {}}]},
                {"subkey2_4": ""},
            ]
        }
    ]
    test = [
        {
            "key2": [
                {"subkey2_1": "value1"},
                {"subkey2_2": {"subkey2_1": "value2"}},
                {"subkey2_3": [{"subkey2_1": "value3"}]},
                {"subkey2_4": ""},
            ]
        }
    ]
    set_val_for_all_child(keys, models, values)
    assert models == test

    ## len(model_temp) != len(volumes)
    ### not temp.get(keys[-1]) is None and temp[keys[-1]].get(keys[-1]) is None:
    keys = ["key3", "subkey3_1"]
    values = ["value1", "value2", "value3"]
    models = [{"key3": [{"subkey3_1": {}}]}]
    test = [
        {
            "key3": [
                {"subkey3_1": "value1"},
                {"subkey3_1": "value2"},
                {"subkey3_1": "value3"},
            ]
        }
    ]
    set_val_for_all_child(keys, models, values)
    assert models == test

    ### not(not temp.get(keys[-1]) is None and temp[keys[-1]].get(keys[-1]) is None:)
    #### v is list
    keys = ["key4", "subkey4_1"]
    values = ["value1", "value2", "value3"]
    models = [{"key4": [{"subkey4_2": [{"subkey4_1": ""}]}]}]
    test = [
        {
            "key4": [
                {"subkey4_2": [{"subkey4_1": "value1"}]},
                {"subkey4_2": [{"subkey4_1": "value2"}]},
                {"subkey4_2": [{"subkey4_1": "value3"}]},
            ]
        }
    ]
    set_val_for_all_child(keys, models, values)
    assert models == test

    #### v is dict
    keys = ["key5", "subkey5_1_1"]
    values = ["value1", "value2", "value3"]
    models = [{"key5": [{"subkey5_1": {"subkey5_1_1": {}}}]}]
    test = [
        {
            "key5": [
                {"subkey5_1": {"subkey5_1_1": "value1"}},
                {"subkey5_1": {"subkey5_1_1": "value2"}},
                {"subkey5_1": {"subkey5_1_1": "value3"}},
            ]
        }
    ]
    set_val_for_all_child(keys, models, values)
    assert models == test


# def remove_sub_record_model_no_value(item, condition):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_remove_sub_record_model_no_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_remove_sub_record_model_no_value():
    models = []
    condition = [[], {}, [{}], ""]

    models = [{"key1": [], "key2": {"key2_1": "value2_1", "key2_2": ""}}]
    test = [{"key2": {"key2_1": "value2_1"}}]
    remove_sub_record_model_no_value(models, condition)
    assert models == test
