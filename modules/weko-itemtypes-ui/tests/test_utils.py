
from flask_login import login_user,logout_user
import pytest
from copy import deepcopy
from weko_records.models import ItemType, ItemTypeName
from weko_itemtypes_ui.utils import (
    remove_xsd_prefix,
    fix_json_schema,
    fix_min_max_multiple_item,
    parse_required_item_in_schema,
    helper_remove_empty_enum,
    add_required_subitem,
    is_properties_exist_in_item,
    has_system_admin_access,
    get_lst_mapping,
    get_detail_node,
    get_all_mapping,
    check_duplicate_mapping,
    update_required_schema_not_exist_in_form,
    update_text_and_textarea
)


# def remove_xsd_prefix(jpcoar_lists):
#     def remove_prefix(jpcoar_src, jpcoar_dst):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_remove_xsd_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_remove_xsd_prefix():
    data = {
        "dc:test1":{
            "type":{
                "test_type1":1,
                "test_type2":2,
            }
        }
    }
    test = {"test1":{"type":{"test_type1":1,"test_type2":2}}}
    result = remove_xsd_prefix(data)
    assert result == test
    
# def fix_json_schema(json_schema):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_fix_json_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_fix_json_schema():
    pass

# def fix_min_max_multiple_item(json_schema):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_fix_min_max_multiple_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_fix_min_max_multiple_item(client):
    data = {
        "properties":{
            "item1":{
                "maxItems":None
            },
            "item2":{
                "maxItems":"9999"
            },
            "item3":{
                "minItems":None
            },
            "item4":{
                "minItems":"1"
            }
        }
    }
    test = {"properties":{"item1":{"maxItems":None},"item2":{"maxItems":9999},"item3":{"minItems":None},"item4":{"minItems":1}}}
    result = fix_min_max_multiple_item(data)
    assert result == test
    data = {"properties":{"item1":{"maxItems":"can not perse"}}}
    result = fix_min_max_multiple_item(data)
    assert result == None
    
    data = {"properties":{"item1":{"minItems":"can not perse"}}}
    result = fix_min_max_multiple_item(data)
    assert result == None
    
# def parse_required_item_in_schema(json_schema):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_parse_required_item_in_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_parse_required_item_in_schema():
    data = {
        "test":"value"
    }
    # not exist required
    result = parse_required_item_in_schema(data)
    assert result == {"test":"value"}
    
    # required is only pubdate
    data = {
        "required":["pubdate"],
        "test":"value"
    }
    result = parse_required_item_in_schema(data)
    assert result == {"required":["pubdate"],"test":"value"}
    
    # not properties
    data = {
        "required":["item_12345"]
    }
    result = parse_required_item_in_schema(data)
    assert result == None
    
# def helper_remove_empty_enum(data):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_helper_remove_empty_enum -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_helper_remove_empty_enum():
    data = {
        "properties":{
            "key1":{"enum":"test","key1_1":"value1_1"},
            "key2":{"enum":None,"key2_1":"value2_1"},
            "key3":None,
            "key4":{"items":{"enum":"test","key4_1":"value4_1"}}
        }
    }
    test = {
        "properties":{
            "key1":{"enum":"test","key1_1":"value1_1"},
            "key2":{"key2_1":"value2_1"},
            "key3":None,
            "key4":{"items":{"enum":"test","key4_1":"value4_1"}}
        }
    }
    helper_remove_empty_enum(data)
    assert data == test
# def add_required_subitem(data):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_add_required_subitem -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_add_required_subitem():
    # not data
    result = add_required_subitem({})
    assert result == None
    
    # not exist properties
    data = {"items":{}}
    result = add_required_subitem(data)
    assert result == None
    
    data = {
        "items":{
            "type":"object",
            "text":"in type is object",
            "properties":{
                "key1":{"type":"text","test1":"value1","text":"is_properties_exist_in_item is false"},
                "key2":{
                    "type":"text",
                    "text":"sub_data is None",
                    "properties":{
                        "key2_1":None
                    }
                },
                "key3":{
                    "type":"object",
                    "text":"sub_data is not None",
                    "properties":{
                        "key3_1":{"type":"object","test3_1":"value3_1"}
                    }
                },
                "key4":{
                    "type":"text",
                    "properties":{
                        "key4_1":{
                            "type":"object",
                            "properties":{"test4_1":{"type":"object","test4_1_1":"value4_1_1"}}
                        }
                    }
                }
            }
        }
    }
    test = {
        "items":{
            "type":"object",
            "text":"in type is object",
            "properties":{
                "key1":{"type":"text","test1":"value1","text":"is_properties_exist_in_item is false"},
                "key2":{"type":"text","text":"sub_data is None","properties":{"key2_1":None}},
                "key3":{
                    "type":"object",
                    "text":"sub_data is not None",
                    "properties":{"key3_1":{"type":"object","test3_1":"value3_1"}},
                    "required":["key3_1"]
                },
                "key4":{
                    "type":"text",
                    "properties":{
                        "key4_1":{
                            "type":"object",
                            "properties":{"test4_1":{"type":"object","test4_1_1":"value4_1_1"}},
                            "required":["test4_1"]
                        }
                    }
                }
            },
            "required":["key1","key2"]
        }
    }
    result = add_required_subitem(data)
    assert result == test
    
# def is_properties_exist_in_item(data):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_is_properties_exist_in_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_is_properties_exist_in_item():
    # exist properties or items
    data = {"properties":"data"}
    result = is_properties_exist_in_item(data)
    assert result == True
    
    # not exist properties or items
    data = {"not_properties":"data"}
    result = is_properties_exist_in_item(data)
    assert result == False
# def has_system_admin_access():
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_has_system_admin_access -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_has_system_admin_access(app,users):
    with app.test_request_context():
        login_user(users[7]["obj"])
        result = has_system_admin_access()
        assert result == False
        logout_user()
        login_user(users[0]["obj"])
        result = has_system_admin_access()
        assert result == True
# def get_lst_mapping(current_checking, parent_node=[]):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_get_lst_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_get_lst_mapping():
    data = {
        "key1":{
            "key1_1":"value1_1"
        },
        "key2":"value2_2"
    }
    iters = iter(get_lst_mapping(data))
    assert next(iters) == "key1.key1_1"
    assert next(iters) == "key2"
    with pytest.raises(StopIteration):
        next(iters)
# def get_detail_node(lst_data, idx, meta_list):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_get_detail_node -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_get_detail_node():
    data = [{"title":["title.value","title.sub_title"]}]
    idx = 0
    meta_list={"title":{
      "title": "タイトル",
      "option": {
        "crtf": True,
        "hidden": False,
        "oneline": False,
        "multiple": False,
        "required": True,
        "showlist": True
      },
      "input_type": "text",
      "title_i18n": { "en": "Title (ja)", "ja": "タイトル（日）" },
      "input_value": "",
      "input_maxItems": "9999",
      "input_minItems": "1"
    }}
    key,val,lst_values,input_type = get_detail_node(data,idx,meta_list)
    assert key == "title"
    assert val == ["title.value","title.sub_title"]
    assert lst_values == ["title.sub_title","title.value"]
    assert input_type == "text"

# def get_all_mapping(item_value, mapping_type):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_get_all_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_get_all_mapping(mocker):
    mocker.patch("weko_itemtypes_ui.utils.get_lst_mapping",return_value=["jpcoar.key1.key1_1","jpcoar.key2"])
    data = {
        "jpcoar":{
            "key1":{
                "key1_1":"value1_1"
            },
            "key2":"value2"
        },
        "oai_dc":""
    }
    mapping_type="jpcoar"
    result = get_all_mapping(data,mapping_type)
    assert result == ["jpcoar.key1.key1_1","jpcoar.key2"]
# def check_duplicate_mapping(
#     def process_overlap():
#  .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_check_duplicate_mapping -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_check_duplicate_mapping(db_itemtype6):
    item_type = db_itemtype6['item_type']
    data_mapping = {'item_test': {'display_lang_type': '', 'jpcoar_mapping': {'title': {'@attributes': {'xml:lang': 'subitem_1551255648112'}, '@value': 'subitem_1551255647225'}}, 'jpcoar_v1_mapping': {'title': {'@attributes': {'xml:lang': 'subitem_test'}, '@value': 'subitem_1551255647225'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264308487': {'display_lang_type': '', 'jpcoar_mapping': {'title': {'@attributes': {'xml:lang': 'subitem_1551255648112'}, '@value': 'subitem_1551255647225'}}, 'jpcoar_v1_mapping': {'title': {'@attributes': {'xml:lang': 'subitem_1551255648112'}, '@value': 'subitem_1551255647225'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264326373': {'display_lang_type': '', 'jpcoar_mapping': {'alternative': {'@attributes': {'xml:lang': 'subitem_1551255721061'}, '@value': 'subitem_1551255720400'}}, 'jpcoar_v1_mapping': {'alternative': {'@attributes': {'xml:lang': 'subitem_1551255721061'}, '@value': 'subitem_1551255720400'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264340087': {'display_lang_type': '', 'jpcoar_mapping': {'creator': {'affiliation': {'affiliationName': {'@attributes': {'xml:lang': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259899'}, '@value': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259183'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256145018', 'nameIdentifierURI': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256147368'}, '@value': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256097891'}}, 'creatorAlternative': {'@attributes': {'xml:lang': 'subitem_1551256025394.subitem_1551256055588'}, '@value': 'subitem_1551256025394.subitem_1551256035730'}, 'creatorName': {'@attributes': {'xml:lang': 'subitem_1551255898956.subitem_1551255907416'}, '@value': 'subitem_1551255898956.subitem_1551255905565'}, 'familyName': {'@attributes': {'xml:lang': 'subitem_1551255929209.subitem_1551255964991'}, '@value': 'subitem_1551255929209.subitem_1551255938498'}, 'givenName': {'@attributes': {'xml:lang': 'subitem_1551255991424.subitem_1551256007414'}, '@value': 'subitem_1551255991424.subitem_1551256006332'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551255789000.subitem_1551255794292', 'nameIdentifierURI': 'subitem_1551255789000.subitem_1551255795486'}, '@value': 'subitem_1551255789000.subitem_1551255793478'}}}, 'jpcoar_v1_mapping': {'creator': {'affiliation': {'affiliationName': {'@attributes': {'xml:lang': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259899'}, '@value': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259183'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256145018', 'nameIdentifierURI': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256147368'}, '@value': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256097891'}}, 'creatorAlternative': {'@attributes': {'xml:lang': 'subitem_1551256025394.subitem_1551256055588'}, '@value': 'subitem_1551256025394.subitem_1551256035730'}, 'creatorName': {'@attributes': {'xml:lang': 'subitem_1551255898956.subitem_1551255907416'}, '@value': 'subitem_1551255898956.subitem_1551255905565'}, 'familyName': {'@attributes': {'xml:lang': 'subitem_1551255929209.subitem_1551255964991'}, '@value': 'subitem_1551255929209.subitem_1551255938498'}, 'givenName': {'@attributes': {'xml:lang': 'subitem_1551255991424.subitem_1551256007414'}, '@value': 'subitem_1551255991424.subitem_1551256006332'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551255789000.subitem_1551255794292', 'nameIdentifierURI': 'subitem_1551255789000.subitem_1551255795486'}, '@value': 'subitem_1551255789000.subitem_1551255793478'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264418667': {'display_lang_type': '', 'jpcoar_mapping': {'contributor': {'@attributes': {'contributorType': 'subitem_1551257036415'}, 'affiliation': {'affiliationName': {'@attributes': {'xml:lang': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261546333'}, '@value': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261542403'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261485670', 'nameIdentifierURI': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261493409'}, '@value': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261472867'}}, 'contributorAlternative': {'@attributes': {'xml:lang': 'subitem_1551257372442.subitem_1551257375939'}, '@value': 'subitem_1551257372442.subitem_1551257374288'}, 'contributorName': {'@attributes': {'xml:lang': 'subitem_1551257245638.subitem_1551257279831'}, '@value': 'subitem_1551257245638.subitem_1551257276108'}, 'familyName': {'@attributes': {'xml:lang': 'subitem_1551257272214.subitem_1551257316910'}, '@value': 'subitem_1551257272214.subitem_1551257314588'}, 'givenName': {'@attributes': {'xml:lang': 'subitem_1551257339190.subitem_1551257343979'}, '@value': 'subitem_1551257339190.subitem_1551257342360'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257150927.subitem_1551257172531', 'nameIdentifierURI': 'subitem_1551257150927.subitem_1551257228080'}, '@value': 'subitem_1551257150927.subitem_1551257152742'}}}, 'jpcoar_v1_mapping': {'contributor': {'@attributes': {'contributorType': 'subitem_1551257036415'}, 'affiliation': {'affiliationName': {'@attributes': {'xml:lang': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261546333'}, '@value': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261542403'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261485670', 'nameIdentifierURI': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261493409'}, '@value': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261472867'}}, 'contributorAlternative': {'@attributes': {'xml:lang': 'subitem_1551257372442.subitem_1551257375939'}, '@value': 'subitem_1551257372442.subitem_1551257374288'}, 'contributorName': {'@attributes': {'xml:lang': 'subitem_1551257245638.subitem_1551257279831'}, '@value': 'subitem_1551257245638.subitem_1551257276108'}, 'familyName': {'@attributes': {'xml:lang': 'subitem_1551257272214.subitem_1551257316910'}, '@value': 'subitem_1551257272214.subitem_1551257314588'}, 'givenName': {'@attributes': {'xml:lang': 'subitem_1551257339190.subitem_1551257343979'}, '@value': 'subitem_1551257339190.subitem_1551257342360'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257150927.subitem_1551257172531', 'nameIdentifierURI': 'subitem_1551257150927.subitem_1551257228080'}, '@value': 'subitem_1551257150927.subitem_1551257152742'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264447183': {'display_lang_type': '', 'jpcoar_mapping': {'accessRights': {'@attributes': {'rdf:resource': 'subitem_1551257578398'}, '@value': 'subitem_1551257553743'}}, 'jpcoar_v1_mapping': {'accessRights': {'@attributes': {'rdf:resource': 'subitem_1551257578398'}, '@value': 'subitem_1551257553743'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264605515': {'display_lang_type': '', 'jpcoar_mapping': {'apc': {'@value': 'subitem_1551257776901'}}, 'jpcoar_v1_mapping': {'apc': {'@value': 'subitem_1551257776901'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264629907': {'display_lang_type': '', 'jpcoar_mapping': {'rights': {'@attributes': {'rdf:resource': 'subitem_1551257030435', 'xml:lang': 'subitem_1551257025236.subitem_1551257047388'}, '@value': 'subitem_1551257025236.subitem_1551257043769'}}, 'jpcoar_v1_mapping': {'rights': {'@attributes': {'rdf:resource': 'subitem_1551257030435', 'xml:lang': 'subitem_1551257025236.subitem_1551257047388'}, '@value': 'subitem_1551257025236.subitem_1551257043769'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264767789': {'display_lang_type': '', 'jpcoar_mapping': {'rightsHolder': {'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257143244.subitem_1551257156244', 'nameIdentifierURI': 'subitem_1551257143244.subitem_1551257232980'}, '@value': 'subitem_1551257143244.subitem_1551257145912'}, 'rightsHolderName': {'@attributes': {'xml:lang': 'subitem_1551257249371.subitem_1551257257683'}, '@value': 'subitem_1551257249371.subitem_1551257255641'}}}, 'jpcoar_v1_mapping': {'rightsHolder': {'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257143244.subitem_1551257156244', 'nameIdentifierURI': 'subitem_1551257143244.subitem_1551257232980'}, '@value': 'subitem_1551257143244.subitem_1551257145912'}, 'rightsHolderName': {'@attributes': {'xml:lang': 'subitem_1551257249371.subitem_1551257257683'}, '@value': 'subitem_1551257249371.subitem_1551257255641'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264822581': {'display_lang_type': '', 'jpcoar_mapping': {'subject': {'@attributes': {'subjectScheme': 'subitem_1551257329877', 'subjectURI': 'subitem_1551257343002', 'xml:lang': 'subitem_1551257323812'}, '@value': 'subitem_1551257315453'}}, 'jpcoar_v1_mapping': {'subject': {'@attributes': {'subjectScheme': 'subitem_1551257329877', 'subjectURI': 'subitem_1551257343002', 'xml:lang': 'subitem_1551257323812'}, '@value': 'subitem_1551257315453'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264846237': {'display_lang_type': '', 'jpcoar_mapping': {'description': {'@attributes': {'descriptionType': 'subitem_1551255637472', 'xml:lang': 'subitem_1551255592625'}, '@value': 'subitem_1551255577890'}}, 'jpcoar_v1_mapping': {'description': {'@attributes': {'descriptionType': 'subitem_1551255637472', 'xml:lang': 'subitem_1551255592625'}, '@value': 'subitem_1551255577890'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264917614': {'display_lang_type': '', 'jpcoar_mapping': {'publisher': {'@attributes': {'xml:lang': 'subitem_1551255710277'}, '@value': 'subitem_1551255702686'}}, 'jpcoar_v1_mapping': {'publisher': {'@attributes': {'xml:lang': 'subitem_1551255710277'}, '@value': 'subitem_1551255702686'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264974654': {'display_lang_type': '', 'jpcoar_mapping': {'date': {'@attributes': {'dateType': 'subitem_1551255775519'}, '@value': 'subitem_1551255753471'}}, 'jpcoar_v1_mapping': {'date': {'@attributes': {'dateType': 'subitem_1551255775519'}, '@value': 'subitem_1551255753471'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265002099': {'display_lang_type': '', 'jpcoar_mapping': {'language': {'@value': 'subitem_1551255818386'}}, 'jpcoar_v1_mapping': {'language': {'@value': 'subitem_1551255818386'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265032053': {'display_lang_type': '', 'jpcoar_mapping': {'type': {'@attributes': {'rdf:resource': 'resourceuri'}, '@value': 'resourcetype'}}, 'jpcoar_v1_mapping': {'type': {'@attributes': {'rdf:resource': 'resourceuri'}, '@value': 'resourcetype'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265118680': {'display_lang_type': '', 'jpcoar_mapping': {'versionType': {'@value': 'subitem_1551256025676'}}, 'jpcoar_v1_mapping': {'versionType': {'@value': 'subitem_1551256025676'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265227803': {'display_lang_type': '', 'jpcoar_mapping': {'relation': {'@attributes': {'relationType': 'subitem_1551256388439'}, 'relatedIdentifier': {'@attributes': {'identifierType': 'subitem_1551256465077.subitem_1551256629524'}, '@value': 'subitem_1551256465077.subitem_1551256478339'}, 'relatedTitle': {'@attributes': {'xml:lang': 'subitem_1551256480278.subitem_1551256513476'}, '@value': 'subitem_1551256480278.subitem_1551256498531'}}}, 'jpcoar_v1_mapping': {'relation': {'@attributes': {'relationType': 'subitem_1551256388439'}, 'relatedIdentifier': {'@attributes': {'identifierType': 'subitem_1551256465077.subitem_1551256629524'}, '@value': 'subitem_1551256465077.subitem_1551256478339'}, 'relatedTitle': {'@attributes': {'xml:lang': 'subitem_1551256480278.subitem_1551256513476'}, '@value': 'subitem_1551256480278.subitem_1551256498531'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265302120': {'display_lang_type': '', 'jpcoar_mapping': {'temporal': {'@attributes': {'xml:lang': 'subitem_1551256920086'}, '@value': 'subitem_1551256918211'}}, 'jpcoar_v1_mapping': {'temporal': {'@attributes': {'xml:lang': 'subitem_1551256920086'}, '@value': 'subitem_1551256918211'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265326081': {'display_lang_type': '', 'jpcoar_mapping': {'geoLocation': {'geoLocationBox': {'eastBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256831892'}, 'northBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256840435'}, 'southBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256834732'}, 'westBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256824945'}}, 'geoLocationPlace': {'@value': 'subitem_1551256842196.subitem_1570008213846'}, 'geoLocationPoint': {'pointLatitude': {'@value': 'subitem_1551256778926.subitem_1551256814806'}, 'pointLongitude': {'@value': 'subitem_1551256778926.subitem_1551256783928'}}}}, 'jpcoar_v1_mapping': {'geoLocation': {'geoLocationBox': {'eastBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256831892'}, 'northBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256840435'}, 'southBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256834732'}, 'westBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256824945'}}, 'geoLocationPlace': {'@value': 'subitem_1551256842196.subitem_1570008213846'}, 'geoLocationPoint': {'pointLatitude': {'@value': 'subitem_1551256778926.subitem_1551256814806'}, 'pointLongitude': {'@value': 'subitem_1551256778926.subitem_1551256783928'}}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265385290': {'display_lang_type': '', 'jpcoar_mapping': {'fundingReference': {'awardNumber': {'@attributes': {'awardURI': 'subitem_1551256665850.subitem_1551256679403'}, '@value': 'subitem_1551256665850.subitem_1551256671920'}, 'awardTitle': {'@attributes': {'xml:lang': 'subitem_1551256688098.subitem_1551256694883'}, '@value': 'subitem_1551256688098.subitem_1551256691232'}, 'funderIdentifier': {'@attributes': {'funderIdentifierType': 'subitem_1551256454316.subitem_1551256619706'}, '@value': 'subitem_1551256454316.subitem_1551256614960'}, 'funderName': {'@attributes': {'xml:lang': 'subitem_1551256462220.subitem_1551256657859'}, '@value': 'subitem_1551256462220.subitem_1551256653656'}}}, 'jpcoar_v1_mapping': {'fundingReference': {'awardNumber': {'@attributes': {'awardURI': 'subitem_1551256665850.subitem_1551256679403'}, '@value': 'subitem_1551256665850.subitem_1551256671920'}, 'awardTitle': {'@attributes': {'xml:lang': 'subitem_1551256688098.subitem_1551256694883'}, '@value': 'subitem_1551256688098.subitem_1551256691232'}, 'funderIdentifier': {'@attributes': {'funderIdentifierType': 'subitem_1551256454316.subitem_1551256619706'}, '@value': 'subitem_1551256454316.subitem_1551256614960'}, 'funderName': {'@attributes': {'xml:lang': 'subitem_1551256462220.subitem_1551256657859'}, '@value': 'subitem_1551256462220.subitem_1551256653656'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265409089': {'display_lang_type': '', 'jpcoar_mapping': {'sourceIdentifier': {'@attributes': {'identifierType': 'subitem_1551256409644'}, '@value': 'subitem_1551256405981'}}, 'jpcoar_v1_mapping': {'sourceIdentifier': {'@attributes': {'identifierType': 'subitem_1551256409644'}, '@value': 'subitem_1551256405981'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265438256': {'display_lang_type': '', 'jpcoar_mapping': {'sourceTitle': {'@attributes': {'xml:lang': 'subitem_1551256350188'}, '@value': 'subitem_1551256349044'}}, 'jpcoar_v1_mapping': {'sourceTitle': {'@attributes': {'xml:lang': 'subitem_1551256350188'}, '@value': 'subitem_1551256349044'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265463411': {'display_lang_type': '', 'jpcoar_mapping': {'volume': {'@value': 'subitem_1551256328147'}}, 'jpcoar_v1_mapping': {'volume': {'@value': 'subitem_1551256328147'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265520160': {'display_lang_type': '', 'jpcoar_mapping': {'issue': {'@value': 'subitem_1551256294723'}}, 'jpcoar_v1_mapping': {'issue': {'@value': 'subitem_1551256294723'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265553273': {'display_lang_type': '', 'jpcoar_mapping': {'numPages': {'@value': 'subitem_1551256248092'}}, 'jpcoar_v1_mapping': {'numPages': {'@value': 'subitem_1551256248092'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265569218': {'display_lang_type': '', 'jpcoar_mapping': {'pageStart': {'@value': 'subitem_1551256198917'}}, 'jpcoar_v1_mapping': {'pageStart': {'@value': 'subitem_1551256198917'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265603279': {'display_lang_type': '', 'jpcoar_mapping': {'pageEnd': {'@value': 'subitem_1551256185532'}}, 'jpcoar_v1_mapping': {'pageEnd': {'@value': 'subitem_1551256185532'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265738931': {'display_lang_type': '', 'jpcoar_mapping': {'dissertationNumber': {'@value': 'subitem_1551256171004'}}, 'jpcoar_v1_mapping': {'dissertationNumber': {'@value': 'subitem_1551256171004'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265790591': {'display_lang_type': '', 'jpcoar_mapping': {'degreeName': {'@attributes': {'xml:lang': 'subitem_1551256129013'}, '@value': 'subitem_1551256126428'}}, 'jpcoar_v1_mapping': {'degreeName': {'@attributes': {'xml:lang': 'subitem_1551256129013'}, '@value': 'subitem_1551256126428'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265811989': {'display_lang_type': '', 'jpcoar_mapping': {'dateGranted': {'@value': 'subitem_1551256096004'}}, 'jpcoar_v1_mapping': {'dateGranted': {'@value': 'subitem_1551256096004'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265903092': {'display_lang_type': '', 'jpcoar_mapping': {'degreeGrantor': {'degreeGrantorName': {'@attributes': {'xml:lang': 'subitem_1551256037922.subitem_1551256047619'}, '@value': 'subitem_1551256037922.subitem_1551256042287'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551256015892.subitem_1551256029891'}, '@value': 'subitem_1551256015892.subitem_1551256027296'}}}, 'jpcoar_v1_mapping': {'degreeGrantor': {'degreeGrantorName': {'@attributes': {'xml:lang': 'subitem_1551256037922.subitem_1551256047619'}, '@value': 'subitem_1551256037922.subitem_1551256042287'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551256015892.subitem_1551256029891'}, '@value': 'subitem_1551256015892.subitem_1551256027296'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1570703628633': {'display_lang_type': '', 'jpcoar_mapping': {'file': {'URI': {'@attributes': {'label': 'subitem_1551259623304.subitem_1551259762549', 'objectType': 'subitem_1551259623304.subitem_1551259670908'}, '@value': 'subitem_1551259623304.subitem_1551259665538'}, 'date': {'@attributes': {'dateType': 'subitem_1551259970148.subitem_1551259979542'}, '@value': 'subitem_1551259970148.subitem_1551259972522'}, 'extent': {'@value': 'subitem_1551259960284.subitem_1570697598267'}, 'mimeType': {'@value': 'subitem_1551259906932'}}}, 'jpcoar_v1_mapping': {'file': {'URI': {'@attributes': {'label': 'subitem_1551259623304.subitem_1551259762549', 'objectType': 'subitem_1551259623304.subitem_1551259670908'}, '@value': 'subitem_1551259623304.subitem_1551259665538'}, 'date': {'@attributes': {'dateType': 'subitem_1551259970148.subitem_1551259979542'}, '@value': 'subitem_1551259970148.subitem_1551259972522'}, 'extent': {'@value': 'subitem_1551259960284.subitem_1570697598267'}, 'mimeType': {'@value': 'subitem_1551259906932'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1581495656289': {'display_lang_type': '', 'jpcoar_mapping': {'identifierRegistration': {'@attributes': {'identifierType': 'subitem_1551256259586'}, '@value': 'subitem_1551256250276'}}, 'jpcoar_v1_mapping': {'identifierRegistration': {'@attributes': {'identifierType': 'subitem_1551256259586'}, '@value': 'subitem_1551256250276'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1663165432106': {'jpcoar_mapping': {'title': {'@attributes': {'xml:lang': '='}, '@value': 'interim'}}, 'jpcoar_v1_mapping': {'title': {'@value': 'interim', '@attributes': {'xml:lang': '=ja'}}}}, 'pubdate': {'display_lang_type': '', 'jpcoar_mapping': {'date': {'@value': 'interim'}}, 'jpcoar_v1_mapping': {'date': {'@value': 'interim'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'system_file': {'display_lang_type': '', 'jpcoar_mapping': {'system_file': {'URI': {'@attributes': {'label': 'subitem_systemfile_filename_label', 'objectType': 'subitem_systemfile_filename_type'}, '@value': 'subitem_systemfile_filename_uri'}, 'date': {'@attributes': {'dateType': 'subitem_systemfile_datetime_type'}, '@value': 'subitem_systemfile_datetime_date'}, 'extent': {'@value': 'subitem_systemfile_size'}, 'mimeType': {'@value': 'subitem_systemfile_mimetype'}, 'version': {'@value': 'subitem_systemfile_version'}}}, 'jpcoar_v1_mapping': {'system_file': {'URI': {'@attributes': {'label': 'subitem_systemfile_filename_label', 'objectType': 'subitem_systemfile_filename_type'}, '@value': 'subitem_systemfile_filename_uri'}, 'date': {'@attributes': {'dateType': 'subitem_systemfile_datetime_type'}, '@value': 'subitem_systemfile_datetime_date'}, 'extent': {'@value': 'subitem_systemfile_size'}, 'mimeType': {'@value': 'subitem_systemfile_mimetype'}, 'version': {'@value': 'subitem_systemfile_version'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'system_identifier_doi': {'display_lang_type': '', 'jpcoar_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'jpcoar_v1_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'system_identifier_hdl': {'display_lang_type': '', 'jpcoar_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'jpcoar_v1_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'system_identifier_uri': {'display_lang_type': '', 'jpcoar_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'jpcoar_v1_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}}
    meta_system = {'system_file': {'title': 'File Information', 'option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_131', 'title_i18n': {'en': 'File Information', 'ja': 'ファイル情報'}, 'input_value': ''}, 'system_identifier_doi': {'title': 'Persistent Identifier(DOI)', 'option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_130', 'title_i18n': {'en': 'Persistent Identifier(DOI)', 'ja': '永続識別子（DOI）'}, 'input_value': ''}, 'system_identifier_hdl': {'title': 'Persistent Identifier(HDL)', 'option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_130', 'title_i18n': {'en': 'Persistent Identifier(HDL)', 'ja': '永続識別子（HDL）'}, 'input_value': ''}, 'system_identifier_uri': {'title': 'Persistent Identifier(URI)', 'option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_130', 'title_i18n': {'en': 'Persistent Identifier(URI)', 'ja': '永続識別子（URI）'}, 'input_value': ''}}
    mapping_type = 'jpcoar_v1_mapping'
    data_mapping_copy = deepcopy(data_mapping)
    assert check_duplicate_mapping(data_mapping_copy, meta_system, item_type, mapping_type)==[]
    assert data_mapping_copy == data_mapping.pop('item_test')

    data_mapping = {'item_1551264308487': {'display_lang_type': '', 'jpcoar_mapping': {'title': {'@attributes': {'xml:lang': 'subitem_1551255648112'}, '@value': 'subitem_1551255647225'}}, 'jpcoar_v1_mapping': {'title': {'@attributes': {'xml:lang': 'subitem_1551255648112'}, '@value': 'subitem_1551255647225'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264326373': {'display_lang_type': '', 'jpcoar_mapping': {'alternative': {'@attributes': {'xml:lang': 'subitem_1551255721061'}, '@value': 'subitem_1551255720400'}}, 'jpcoar_v1_mapping': {'alternative': {'@attributes': {'xml:lang': 'subitem_1551255721061'}, '@value': 'subitem_1551255720400'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264340087': {'display_lang_type': '', 'jpcoar_mapping': {'creator': {'affiliation': {'affiliationName': {'@attributes': {'xml:lang': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259899'}, '@value': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259183'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256145018', 'nameIdentifierURI': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256147368'}, '@value': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256097891'}}, 'creatorAlternative': {'@attributes': {'xml:lang': 'subitem_1551256025394.subitem_1551256055588'}, '@value': 'subitem_1551256025394.subitem_1551256035730'}, 'creatorName': {'@attributes': {'xml:lang': 'subitem_1551255898956.subitem_1551255907416'}, '@value': 'subitem_1551255898956.subitem_1551255905565'}, 'familyName': {'@attributes': {'xml:lang': 'subitem_1551255929209.subitem_1551255964991'}, '@value': 'subitem_1551255929209.subitem_1551255938498'}, 'givenName': {'@attributes': {'xml:lang': 'subitem_1551255991424.subitem_1551256007414'}, '@value': 'subitem_1551255991424.subitem_1551256006332'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551255789000.subitem_1551255794292', 'nameIdentifierURI': 'subitem_1551255789000.subitem_1551255795486'}, '@value': 'subitem_1551255789000.subitem_1551255793478'}}}, 'jpcoar_v1_mapping': {'creator': {'affiliation': {'affiliationName': {'@attributes': {'xml:lang': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259899'}, '@value': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259183'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256145018', 'nameIdentifierURI': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256147368'}, '@value': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256097891'}}, 'creatorAlternative': {'@attributes': {'xml:lang': 'subitem_1551256025394.subitem_1551256055588'}, '@value': 'subitem_1551256025394.subitem_1551256035730'}, 'creatorName': {'@attributes': {'xml:lang': 'subitem_1551255898956.subitem_1551255907416'}, '@value': 'subitem_1551255898956.subitem_1551255905565'}, 'familyName': {'@attributes': {'xml:lang': 'subitem_1551255929209.subitem_1551255964991'}, '@value': 'subitem_1551255929209.subitem_1551255938498'}, 'givenName': {'@attributes': {'xml:lang': 'subitem_1551255991424.subitem_1551256007414'}, '@value': 'subitem_1551255991424.subitem_1551256006332'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551255789000.subitem_1551255794292', 'nameIdentifierURI': 'subitem_1551255789000.subitem_1551255795486'}, '@value': 'subitem_1551255789000.subitem_1551255793478'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264418667': {'display_lang_type': '', 'jpcoar_mapping': {'contributor': {'@attributes': {'contributorType': 'subitem_1551257036415'}, 'affiliation': {'affiliationName': {'@attributes': {'xml:lang': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261546333'}, '@value': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261542403'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261485670', 'nameIdentifierURI': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261493409'}, '@value': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261472867'}}, 'contributorAlternative': {'@attributes': {'xml:lang': 'subitem_1551257372442.subitem_1551257375939'}, '@value': 'subitem_1551257372442.subitem_1551257374288'}, 'contributorName': {'@attributes': {'xml:lang': 'subitem_1551257245638.subitem_1551257279831'}, '@value': 'subitem_1551257245638.subitem_1551257276108'}, 'familyName': {'@attributes': {'xml:lang': 'subitem_1551257272214.subitem_1551257316910'}, '@value': 'subitem_1551257272214.subitem_1551257314588'}, 'givenName': {'@attributes': {'xml:lang': 'subitem_1551257339190.subitem_1551257343979'}, '@value': 'subitem_1551257339190.subitem_1551257342360'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257150927.subitem_1551257172531', 'nameIdentifierURI': 'subitem_1551257150927.subitem_1551257228080'}, '@value': 'subitem_1551257150927.subitem_1551257152742'}}}, 'jpcoar_v1_mapping': {'contributor': {'@attributes': {'contributorType': 'subitem_1551257036415'}, 'affiliation': {'affiliationName': {'@attributes': {'xml:lang': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261546333'}, '@value': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261542403'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261485670', 'nameIdentifierURI': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261493409'}, '@value': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261472867'}}, 'contributorAlternative': {'@attributes': {'xml:lang': 'subitem_1551257372442.subitem_1551257375939'}, '@value': 'subitem_1551257372442.subitem_1551257374288'}, 'contributorName': {'@attributes': {'xml:lang': 'subitem_1551257245638.subitem_1551257279831'}, '@value': 'subitem_1551257245638.subitem_1551257276108'}, 'familyName': {'@attributes': {'xml:lang': 'subitem_1551257272214.subitem_1551257316910'}, '@value': 'subitem_1551257272214.subitem_1551257314588'}, 'givenName': {'@attributes': {'xml:lang': 'subitem_1551257339190.subitem_1551257343979'}, '@value': 'subitem_1551257339190.subitem_1551257342360'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257150927.subitem_1551257172531', 'nameIdentifierURI': 'subitem_1551257150927.subitem_1551257228080'}, '@value': 'subitem_1551257150927.subitem_1551257152742'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264447183': {'display_lang_type': '', 'jpcoar_mapping': {'accessRights': {'@attributes': {'rdf:resource': 'subitem_1551257578398'}, '@value': 'subitem_1551257553743'}}, 'jpcoar_v1_mapping': {'accessRights': {'@attributes': {'rdf:resource': 'subitem_1551257578398'}, '@value': 'subitem_1551257553743'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264605515': {'display_lang_type': '', 'jpcoar_mapping': {'apc': {'@value': 'subitem_1551257776901'}}, 'jpcoar_v1_mapping': {'apc': {'@value': 'subitem_1551257776901'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264629907': {'display_lang_type': '', 'jpcoar_mapping': {'rights': {'@attributes': {'rdf:resource': 'subitem_1551257030435', 'xml:lang': 'subitem_1551257025236.subitem_1551257047388'}, '@value': 'subitem_1551257025236.subitem_1551257043769'}}, 'jpcoar_v1_mapping': {'rights': {'@attributes': {'rdf:resource': 'subitem_1551257030435', 'xml:lang': 'subitem_1551257025236.subitem_1551257047388'}, '@value': 'subitem_1551257025236.subitem_1551257043769'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264767789': {'display_lang_type': '', 'jpcoar_mapping': {'rightsHolder': {'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257143244.subitem_1551257156244', 'nameIdentifierURI': 'subitem_1551257143244.subitem_1551257232980'}, '@value': 'subitem_1551257143244.subitem_1551257145912'}, 'rightsHolderName': {'@attributes': {'xml:lang': 'subitem_1551257249371.subitem_1551257257683'}, '@value': 'subitem_1551257249371.subitem_1551257255641'}}}, 'jpcoar_v1_mapping': {'rightsHolder': {'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551257143244.subitem_1551257156244', 'nameIdentifierURI': 'subitem_1551257143244.subitem_1551257232980'}, '@value': 'subitem_1551257143244.subitem_1551257145912'}, 'rightsHolderName': {'@attributes': {'xml:lang': 'subitem_1551257249371.subitem_1551257257683'}, '@value': 'subitem_1551257249371.subitem_1551257255641'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264822581': {'display_lang_type': '', 'jpcoar_mapping': {'subject': {'@attributes': {'subjectScheme': 'subitem_1551257329877', 'subjectURI': 'subitem_1551257343002', 'xml:lang': 'subitem_1551257323812'}, '@value': 'subitem_1551257315453'}}, 'jpcoar_v1_mapping': {'subject': {'@attributes': {'subjectScheme': 'subitem_1551257329877', 'subjectURI': 'subitem_1551257343002', 'xml:lang': 'subitem_1551257323812'}, '@value': 'subitem_1551257315453'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264846237': {'display_lang_type': '', 'jpcoar_mapping': {'description': {'@attributes': {'descriptionType': 'subitem_1551255637472', 'xml:lang': 'subitem_1551255592625'}, '@value': 'subitem_1551255577890'}}, 'jpcoar_v1_mapping': {'description': {'@attributes': {'descriptionType': 'subitem_1551255637472', 'xml:lang': 'subitem_1551255592625'}, '@value': 'subitem_1551255577890'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264917614': {'display_lang_type': '', 'jpcoar_mapping': {'publisher': {'@attributes': {'xml:lang': 'subitem_1551255710277'}, '@value': 'subitem_1551255702686'}}, 'jpcoar_v1_mapping': {'publisher': {'@attributes': {'xml:lang': 'subitem_1551255710277'}, '@value': 'subitem_1551255702686'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551264974654': {'display_lang_type': '', 'jpcoar_mapping': {'date': {'@attributes': {'dateType': 'subitem_1551255775519'}, '@value': 'subitem_1551255753471'}}, 'jpcoar_v1_mapping': {'date': {'@attributes': {'dateType': 'subitem_1551255775519'}, '@value': 'subitem_1551255753471'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265002099': {'display_lang_type': '', 'jpcoar_mapping': {'language': {'@value': 'subitem_1551255818386'}}, 'jpcoar_v1_mapping': {'language': {'@value': 'subitem_1551255818386'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265032053': {'display_lang_type': '', 'jpcoar_mapping': {'type': {'@attributes': {'rdf:resource': 'resourceuri'}, '@value': 'resourcetype'}}, 'jpcoar_v1_mapping': {'type': {'@attributes': {'rdf:resource': 'resourceuri'}, '@value': 'resourcetype'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265118680': {'display_lang_type': '', 'jpcoar_mapping': {'versionType': {'@value': 'subitem_1551256025676'}}, 'jpcoar_v1_mapping': {'versionType': {'@value': 'subitem_1551256025676'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265227803': {'display_lang_type': '', 'jpcoar_mapping': {'relation': {'@attributes': {'relationType': 'subitem_1551256388439'}, 'relatedIdentifier': {'@attributes': {'identifierType': 'subitem_1551256465077.subitem_1551256629524'}, '@value': 'subitem_1551256465077.subitem_1551256478339'}, 'relatedTitle': {'@attributes': {'xml:lang': 'subitem_1551256480278.subitem_1551256513476'}, '@value': 'subitem_1551256480278.subitem_1551256498531'}}}, 'jpcoar_v1_mapping': {'relation': {'@attributes': {'relationType': 'subitem_1551256388439'}, 'relatedIdentifier': {'@attributes': {'identifierType': 'subitem_1551256465077.subitem_1551256629524'}, '@value': 'subitem_1551256465077.subitem_1551256478339'}, 'relatedTitle': {'@attributes': {'xml:lang': 'subitem_1551256480278.subitem_1551256513476'}, '@value': 'subitem_1551256480278.subitem_1551256498531'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265302120': {'display_lang_type': '', 'jpcoar_mapping': {'temporal': {'@attributes': {'xml:lang': 'subitem_1551256920086'}, '@value': 'subitem_1551256918211'}}, 'jpcoar_v1_mapping': {'temporal': {'@attributes': {'xml:lang': 'subitem_1551256920086'}, '@value': 'subitem_1551256918211'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265326081': {'display_lang_type': '', 'jpcoar_mapping': {'geoLocation': {'geoLocationBox': {'eastBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256831892'}, 'northBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256840435'}, 'southBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256834732'}, 'westBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256824945'}}, 'geoLocationPlace': {'@value': 'subitem_1551256842196.subitem_1570008213846'}, 'geoLocationPoint': {'pointLatitude': {'@value': 'subitem_1551256778926.subitem_1551256814806'}, 'pointLongitude': {'@value': 'subitem_1551256778926.subitem_1551256783928'}}}}, 'jpcoar_v1_mapping': {'geoLocation': {'geoLocationBox': {'eastBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256831892'}, 'northBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256840435'}, 'southBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256834732'}, 'westBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256824945'}}, 'geoLocationPlace': {'@value': 'subitem_1551256842196.subitem_1570008213846'}, 'geoLocationPoint': {'pointLatitude': {'@value': 'subitem_1551256778926.subitem_1551256814806'}, 'pointLongitude': {'@value': 'subitem_1551256778926.subitem_1551256783928'}}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265385290': {'display_lang_type': '', 'jpcoar_mapping': {'fundingReference': {'awardNumber': {'@attributes': {'awardURI': 'subitem_1551256665850.subitem_1551256679403'}, '@value': 'subitem_1551256665850.subitem_1551256671920'}, 'awardTitle': {'@attributes': {'xml:lang': 'subitem_1551256688098.subitem_1551256694883'}, '@value': 'subitem_1551256688098.subitem_1551256691232'}, 'funderIdentifier': {'@attributes': {'funderIdentifierType': 'subitem_1551256454316.subitem_1551256619706'}, '@value': 'subitem_1551256454316.subitem_1551256614960'}, 'funderName': {'@attributes': {'xml:lang': 'subitem_1551256462220.subitem_1551256657859'}, '@value': 'subitem_1551256462220.subitem_1551256653656'}}}, 'jpcoar_v1_mapping': {'fundingReference': {'awardNumber': {'@attributes': {'awardURI': 'subitem_1551256665850.subitem_1551256679403'}, '@value': 'subitem_1551256665850.subitem_1551256671920'}, 'awardTitle': {'@attributes': {'xml:lang': 'subitem_1551256688098.subitem_1551256694883'}, '@value': 'subitem_1551256688098.subitem_1551256691232'}, 'funderIdentifier': {'@attributes': {'funderIdentifierType': 'subitem_1551256454316.subitem_1551256619706'}, '@value': 'subitem_1551256454316.subitem_1551256614960'}, 'funderName': {'@attributes': {'xml:lang': 'subitem_1551256462220.subitem_1551256657859'}, '@value': 'subitem_1551256462220.subitem_1551256653656'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265409089': {'display_lang_type': '', 'jpcoar_mapping': {'sourceIdentifier': {'@attributes': {'identifierType': 'subitem_1551256409644'}, '@value': 'subitem_1551256405981'}}, 'jpcoar_v1_mapping': {'sourceIdentifier': {'@attributes': {'identifierType': 'subitem_1551256409644'}, '@value': 'subitem_1551256405981'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265438256': {'display_lang_type': '', 'jpcoar_mapping': {'sourceTitle': {'@attributes': {'xml:lang': 'subitem_1551256350188'}, '@value': 'subitem_1551256349044'}}, 'jpcoar_v1_mapping': {'sourceTitle': {'@attributes': {'xml:lang': 'subitem_1551256350188'}, '@value': 'subitem_1551256349044'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265463411': {'display_lang_type': '', 'jpcoar_mapping': {'volume': {'@value': 'subitem_1551256328147'}}, 'jpcoar_v1_mapping': {'volume': {'@value': 'subitem_1551256328147'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265520160': {'display_lang_type': '', 'jpcoar_mapping': {'issue': {'@value': 'subitem_1551256294723'}}, 'jpcoar_v1_mapping': {'issue': {'@value': 'subitem_1551256294723'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265553273': {'display_lang_type': '', 'jpcoar_mapping': {'numPages': {'@value': 'subitem_1551256248092'}}, 'jpcoar_v1_mapping': {'numPages': {'@value': 'subitem_1551256248092'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265569218': {'display_lang_type': '', 'jpcoar_mapping': {'pageStart': {'@value': 'subitem_1551256198917'}}, 'jpcoar_v1_mapping': {'pageStart': {'@value': 'subitem_1551256198917'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265603279': {'display_lang_type': '', 'jpcoar_mapping': {'pageEnd': {'@value': 'subitem_1551256185532'}}, 'jpcoar_v1_mapping': {'pageEnd': {'@value': 'subitem_1551256185532'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265738931': {'display_lang_type': '', 'jpcoar_mapping': {'dissertationNumber': {'@value': 'subitem_1551256171004'}}, 'jpcoar_v1_mapping': {'dissertationNumber': {'@value': 'subitem_1551256171004'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265790591': {'display_lang_type': '', 'jpcoar_mapping': {'degreeName': {'@attributes': {'xml:lang': 'subitem_1551256129013'}, '@value': 'subitem_1551256126428'}}, 'jpcoar_v1_mapping': {'degreeName': {'@attributes': {'xml:lang': 'subitem_1551256129013'}, '@value': 'subitem_1551256126428'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265811989': {'display_lang_type': '', 'jpcoar_mapping': {'dateGranted': {'@value': 'subitem_1551256096004'}}, 'jpcoar_v1_mapping': {'dateGranted': {'@value': 'subitem_1551256096004'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1551265903092': {'display_lang_type': '', 'jpcoar_mapping': {'degreeGrantor': {'degreeGrantorName': {'@attributes': {'xml:lang': 'subitem_1551256037922.subitem_1551256047619'}, '@value': 'subitem_1551256037922.subitem_1551256042287'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551256015892.subitem_1551256029891'}, '@value': 'subitem_1551256015892.subitem_1551256027296'}}}, 'jpcoar_v1_mapping': {'degreeGrantor': {'degreeGrantorName': {'@attributes': {'xml:lang': 'subitem_1551256037922.subitem_1551256047619'}, '@value': 'subitem_1551256037922.subitem_1551256042287'}, 'nameIdentifier': {'@attributes': {'nameIdentifierScheme': 'subitem_1551256015892.subitem_1551256029891'}, '@value': 'subitem_1551256015892.subitem_1551256027296'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1570703628633': {'display_lang_type': '', 'jpcoar_mapping': {'file': {'URI': {'@attributes': {'label': 'subitem_1551259623304.subitem_1551259762549', 'objectType': 'subitem_1551259623304.subitem_1551259670908'}, '@value': 'subitem_1551259623304.subitem_1551259665538'}, 'date': {'@attributes': {'dateType': 'subitem_1551259970148.subitem_1551259979542'}, '@value': 'subitem_1551259970148.subitem_1551259972522'}, 'extent': {'@value': 'subitem_1551259960284.subitem_1570697598267'}, 'mimeType': {'@value': 'subitem_1551259906932'}}}, 'jpcoar_v1_mapping': {'file': {'URI': {'@attributes': {'label': 'subitem_1551259623304.subitem_1551259762549', 'objectType': 'subitem_1551259623304.subitem_1551259670908'}, '@value': 'subitem_1551259623304.subitem_1551259665538'}, 'date': {'@attributes': {'dateType': 'subitem_1551259970148.subitem_1551259979542'}, '@value': 'subitem_1551259970148.subitem_1551259972522'}, 'extent': {'@value': 'subitem_1551259960284.subitem_1570697598267'}, 'mimeType': {'@value': 'subitem_1551259906932'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1581495656289': {'display_lang_type': '', 'jpcoar_mapping': {'identifierRegistration': {'@attributes': {'identifierType': 'subitem_1551256259586'}, '@value': 'subitem_1551256250276'}}, 'jpcoar_v1_mapping': {'identifierRegistration': {'@attributes': {'identifierType': 'subitem_1551256259586'}, '@value': 'subitem_1551256250276'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1663165432106': {'jpcoar_mapping': {'title': {'@attributes': {'xml:lang': '='}, '@value': 'interim'}}, 'jpcoar_v1_mapping': {'title': {'@attributes': {'xml:lang': '=ja'}, '@value': 'interim'}}}, 'pubdate': {'display_lang_type': '', 'jpcoar_mapping': {'date': {'@value': 'interim'}}, 'jpcoar_v1_mapping': {'date': {'@value': 'interim'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'system_file': {'display_lang_type': '', 'jpcoar_mapping': {'system_file': {'URI': {'@attributes': {'label': 'subitem_systemfile_filename_label', 'objectType': 'subitem_systemfile_filename_type'}, '@value': 'subitem_systemfile_filename_uri'}, 'date': {'@attributes': {'dateType': 'subitem_systemfile_datetime_type'}, '@value': 'subitem_systemfile_datetime_date'}, 'extent': {'@value': 'subitem_systemfile_size'}, 'mimeType': {'@value': 'subitem_systemfile_mimetype'}, 'version': {'@value': 'subitem_systemfile_version'}}}, 'jpcoar_v1_mapping': {'system_file': {'URI': {'@attributes': {'label': 'subitem_systemfile_filename_label', 'objectType': 'subitem_systemfile_filename_type'}, '@value': 'subitem_systemfile_filename_uri'}, 'date': {'@attributes': {'dateType': 'subitem_systemfile_datetime_type'}, '@value': 'subitem_systemfile_datetime_date'}, 'extent': {'@value': 'subitem_systemfile_size'}, 'mimeType': {'@value': 'subitem_systemfile_mimetype'}, 'version': {'@value': 'subitem_systemfile_version'}}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'system_identifier_doi': {'display_lang_type': '', 'jpcoar_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'jpcoar_v1_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'system_identifier_hdl': {'display_lang_type': '', 'jpcoar_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'jpcoar_v1_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'system_identifier_uri': {'display_lang_type': '', 'jpcoar_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'jpcoar_v1_mapping': {'identifier': {'@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}, '@value': 'subitem_systemidt_identifier'}}, 'junii2_mapping': '', 'lido_mapping': '', 'lom_mapping': '', 'oai_dc_mapping': '', 'spase_mapping': ''}, 'item_1663165460557': {'jpcoar_mapping': {'title': {'@value': 'interim', '@attributes': {'xml:lang': '=ja-kana'}}}}}
    mapping_type = "jpcoar_mapping"
    assert check_duplicate_mapping(data_mapping, meta_system, item_type, mapping_type)== [['タイトル（日）', 'タイトル（ヨミ）']]





# def update_required_schema_not_exist_in_form(schema, forms):
#     def get_form_by_key(key, forms):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_update_required_schema_not_exist_in_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_update_required_schema_not_exist_in_form():
    schema = {
        "properties":{
            "key1":{
                "items":{"required":["subkey2"]}
            },
            "key2":{
                "items":{"required":["subkey2"]}
            },
            "key3":{
                "items":{}
            }
        }
    }
    forms = [
        {
            "key":"key1",
            "items":[
                {"key":"key1.subkey1"},
                {"key":"key1.subkey2"}
            ]
        },
        {
            "key":"key2",
            "items":[{"key":"key2.subkey1"}]
        }
    ]
    test = {"properties":{
        "key1":{"items":{"required":["subkey2"]}},
        "key2":{"items":{}},
        "key3":{"items":{}}}}
    result = update_required_schema_not_exist_in_form(schema,forms)
    assert result == test
# def update_text_and_textarea(item_type_id, new_schema, new_form):
#     def is_text(prop):
#     def is_textarea(prop):
#     def is_text_or_textarea(prop):
#     def get_format_string(prop):
#     def is_multiple(prop):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_utils.py::test_update_text_and_textarea -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
def test_update_text_and_textarea(client,db):
    item_type_id = 10
    new_schema={
        "properties":{
            "key1":{
                "properties":{
                    "subitem_text_value":{"type":"string","title":"値","format":"text"},
                    "subitem_text_language":{"type":["null","string"],"title":"言語","format":"select","editAble":True}
                }
            },
            "key2":{
                "items":{
                    "properties":{
                        "subitem_text_value":{"type":"string","title":"値","format":"text"},
                        "subitem_text_language":{"type":["null","string"],"title":"言語","format":"select","editAble":True}
                    }
                },
                "maxItems":2
            }
        }
    }
    new_form=[
        {"key":"key1",
         "items":[
             {
                 "type":"text",
                 "key":""
             },
             {
                 "type":"select"
             }
         ]
         }
    ]
    
    old_schema = {
        "properties":{
            "key1":{
                "properties":{
                    "subitem_text_value":{"type":"string","title":"値","format":"text"},
                    "subitem_text_language":{"type":["null","string"],"title":"言語","format":"select","editAble":True}
                }
            },
            "key2":{
                "items":{
                    "properties":{
                        "subitem_text_value":{"type":"string","title":"値","format":"text"},
                        "subitem_text_language":{"type":["null","string"],"title":"言語","format":"select","editAble":True}
                    }
                },
                "maxItems":2
            },
            "key3":{
                "items":{
                    "properties":{}
                }
            }
        }
    }
    item_type_name = ItemTypeName(
            id=10, name="test_itemtype", has_site_license=True, is_active=True
        )
    db.session.add(item_type_name)
    db.session.commit()
    item_type = ItemType(
            id=10,
            name_id=item_type_name.id,
            harvesting_type=True,
            schema=old_schema,
            form={},
            render={},
            tag=1,
            version_id=1,
            is_deleted=False,
        )
    db.session.add(item_type)
    db.session.commit()
    
    ns,nf = update_text_and_textarea(item_type_id,new_schema,new_form)
    assert ns == {'properties': {'key1': {'properties': {'subitem_text_value': {'type': 'string', 'title': '値', 'format': 'text'}, 'subitem_text_language': {'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'editAble': True}}}, 'key2': {'items': {'properties': {'subitem_text_value': {'type': 'string', 'title': '値', 'format': 'text'}, 'subitem_text_language': {'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'editAble': True}}}, 'maxItems': 2}}}
    assert nf == [{'key': 'key1', 'items': [{'type': 'text', 'key': 'key1.subitem_text_value'}, {'type': 'select', 'key': 'key1.subitem_text_language'}]}]