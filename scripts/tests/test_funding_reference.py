import pytest
import copy
from ..demo.properties.funding_reference import (
    add,
    schema,
    form,
)
from ..demo.properties import property_config as config
from .conftest import default_post_data_funding, default_schema_funding

def set_expected_form(key):
    rtn = {
    	"add": "New",
    	"style": {"add": "btn-success"},
    	"title_i18n": {"ja": "助成情報", "en": "Funder"},
    	"items": [
    		{
    			"items": [
    				{
    					"key": "{}.subitem_funder_identifiers.subitem_funder_identifier_type".format(key),
    					"title": "助成機関識別子タイプ",
    					"title_i18n": {
    						"en": "Funder Identifier Type",
    						"ja": "助成機関識別子タイプ",
    					},
    					"titleMap": [
    						{"name": "Crossref Funder", "value": "Crossref Funder"},
    						{"name": "e-Rad_funder", "value": "e-Rad_funder"},
    						{"name": "GRID【非推奨】", "value": "GRID"},
    						{"name": "ISNI", "value": "ISNI"},
    						{"name": "ROR", "value": "ROR"},
    						{"name": "Other", "value": "Other"}
    					],
    					"type": "select",
    				},
    				{
    					"key": "{}.subitem_funder_identifiers.subitem_funder_identifier_type_uri".format(key),
    					"title": "助成機関識別子URI",
    					"title_i18n": {
    						"en": "Funder Identifier Type URI",
    						"ja": "助成機関識別子タイプURI",
    					},
    					"type": "text",
    				},
    				{
    					"key": "{}.subitem_funder_identifiers.subitem_funder_identifier".format(key),
    					"title": "助成機関識別子",
    					"title_i18n": {"en": "Funder Identifier", "ja": "助成機関識別子"},
    					"type": "text",
    				},
    			],
    			"key": "{}.subitem_funder_identifiers".format(key),
    			"type": "fieldset",
    			"title": "助成機関識別子",
    			"title_i18n": {"en": "Funder Identifier", "ja": "助成機関識別子"},
    		},
    		{
    			"add": "New",
    			"items": [
    				{
    					"key": "{}.subitem_funder_names[].subitem_funder_name".format(key),
    					"title": "助成機関名",
    					"title_i18n": {"en": "Funder Name", "ja": "助成機関名"},
    					"type": "text",
    				},
    				{
    					"key": "{}.subitem_funder_names[].subitem_funder_name_language".format(key),
    					"title": "言語",
    					"title_i18n": {"en": "Language", "ja": "言語"},
    					"titleMap": [
    						{"name": "ja", "value": "ja"},
    						{"name": "ja-Kana", "value": "ja-Kana"},
    						{"name": "ja-Latn", "value": "ja-Latn"},
    						{"name": "en", "value": "en"},
    						{"name": "fr", "value": "fr"},
    						{"name": "it", "value": "it"},
    						{"name": "de", "value": "de"},
    						{"name": "es", "value": "es"},
    						{"name": "zh-cn", "value": "zh-cn"},
    						{"name": "zh-tw", "value": "zh-tw"},
    						{"name": "ru", "value": "ru"},
    						{"name": "la", "value": "la"},
    						{"name": "ms", "value": "ms"},
    						{"name": "eo", "value": "eo"},
    						{"name": "ar", "value": "ar"},
    						{"name": "el", "value": "el"},
    						{"name": "ko", "value": "ko"}
    					],
    					"type": "select",
    				},
    			],
    			"key": "{}.subitem_funder_names".format(key),
    			"style": {"add": "btn-success"},
    			"title": "助成機関名",
    			"title_i18n": {"en": "Funder Name", "ja": "助成機関名"},
    		},
    		{
    			"items": [
    				{
    					"key": "{}.subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type".format(key),
    					"title": "プログラム情報識別子タイプ",
    					"title_i18n": {
    						"en": "Funding Stream Identifier Type",
    						"ja": "プログラム情報識別子タイプ",
    					},
    					"titleMap": [
    						{"name": "Crossref Funder", "value": "Crossref Funder"},
    						{"name": "JGN_fundingStream", "value": "JGN_fundingStream"}
    					],
    					"type": "select",
    				},
    				{
    					"key": "{}.subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type_uri".format(key),
    					"title": "プログラム情報識別子タイプURI",
    					"title_i18n": {
    						"en": "Funding Stream Identifier Type URI",
    						"ja": "プログラム情報識別子タイプURI",
    					},
    					"type": "text",
    				},
    				{
    					"key": "{}.subitem_funding_stream_identifiers.subitem_funding_stream_identifier".format(key),
    					"title": "プログラム情報識別子",
    					"title_i18n": {
    						"en": "Funding Stream Identifier",
    						"ja": "プログラム情報識別子",
    					},
    					"type": "text",
    				},
    			],
    			"key": "{}.subitem_funding_stream_identifiers".format(key),
    			"title": "プログラム情報識別子",
    			"title_i18n": {
    				"en": "Funding Stream Identifiers",
    				"ja": "プログラム情報識別子",
    			},
    		},
    		{
    			"add": "New",
    			"items": [
    				{
    					"key": "{}.subitem_funding_streams[].subitem_funding_stream_language".format(key),
    					"title": "言語",
    					"title_i18n": {"en": "Language", "ja": "言語"},
    					"titleMap": [
    						{"name": "ja", "value": "ja"},
    						{"name": "ja-Kana", "value": "ja-Kana"},
    						{"name": "ja-Latn", "value": "ja-Latn"},
    						{"name": "en", "value": "en"},
    						{"name": "fr", "value": "fr"},
    						{"name": "it", "value": "it"},
    						{"name": "de", "value": "de"},
    						{"name": "es", "value": "es"},
    						{"name": "zh-cn", "value": "zh-cn"},
    						{"name": "zh-tw", "value": "zh-tw"},
    						{"name": "ru", "value": "ru"},
    						{"name": "la", "value": "la"},
    						{"name": "ms", "value": "ms"},
    						{"name": "eo", "value": "eo"},
    						{"name": "ar", "value": "ar"},
    						{"name": "el", "value": "el"},
    						{"name": "ko", "value": "ko"}
    					],
    					"type": "select",
    				},
    				{
    					"key": "{}.subitem_funding_streams[].subitem_funding_stream".format(key),
    					"title": "プログラム情報",
    					"title_i18n": {
    						"en": "Funding Stream",
    						"ja": "プログラム情報",
    					},
    					"type": "text",
    				},
    			],
    			"key": "{}.subitem_funding_streams".format(key),
    			"style": {"add": "btn-success"},
    			"title": "プログラム情報",
    			"title_i18n": {"en": "Funding Streams", "ja": "プログラム情報"},
    		},
    		{
    			"items": [
    				{
    					"key": "{}.subitem_award_numbers.subitem_award_uri".format(key),
    					"title": "研究課題番号URI",
    					"title_i18n": {"en": "Award Number URI", "ja": "研究課題番号URI"},
    					"type": "text",
    				},
    				{
    					"key": "{}.subitem_award_numbers.subitem_award_number".format(key),
    					"title": "研究課題番号",
    					"title_i18n": {"en": "Award Number", "ja": "研究課題番号"},
    					"type": "text",
    				},
    				{
    					"key": "{}.subitem_award_numbers.subitem_award_number_type".format(key),
    					"title": "研究課題番号タイプ",
    					"title_i18n": {
    						"en": "Award Number Type",
    						"ja": "研究課題番号タイプ",
    					},
    					"titleMap": [
    						{"name": "JGN", "value": "JGN"}
    					],
    					"type": "select",
    				},
    			],
    			"key": "{}.subitem_award_numbers".format(key),
    			"title": "研究課題番号",
    			"title_i18n": {"en": "Award Number", "ja": "研究課題番号"},
    		},
    		{
    			"add": "New",
    			"items": [
    				{
    					"key": "{}.subitem_award_titles[].subitem_award_title".format(key),
    					"title": "研究課題名",
    					"title_i18n": {"en": "Award Title", "ja": "研究課題名"},
    					"type": "text",
    				},
    				{
    					"key": "{}.subitem_award_titles[].subitem_award_title_language".format(key),
    					"title": "言語",
    					"title_i18n": {"en": "Language", "ja": "言語"},
    					"titleMap": [
    						{"name": "ja", "value": "ja"},
    						{"name": "ja-Kana", "value": "ja-Kana"},
    						{"name": "ja-Latn", "value": "ja-Latn"},
    						{"name": "en", "value": "en"},
    						{"name": "fr", "value": "fr"},
    						{"name": "it", "value": "it"},
    						{"name": "de", "value": "de"},
    						{"name": "es", "value": "es"},
    						{"name": "zh-cn", "value": "zh-cn"},
    						{"name": "zh-tw", "value": "zh-tw"},
    						{"name": "ru", "value": "ru"},
    						{"name": "la", "value": "la"},
    						{"name": "ms", "value": "ms"},
    						{"name": "eo", "value": "eo"},
    						{"name": "ar", "value": "ar"},
    						{"name": "el", "value": "el"},
    						{"name": "ko", "value": "ko"}
    					],
    					"type": "select",
    				},
    			],
    			"key": "{}.subitem_award_titles".format(key),
    			"style": {"add": "btn-success"},
    			"title": "研究課題名",
    			"title_i18n": {"en": "Award Title", "ja": "研究課題名"},
    		},
    	],
    	"key": key.replace("[]", ""),
    }
    return rtn

# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp

# 54104-1
# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py::test_add_not_exists_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_add_not_exists_mapping():
    post_data = {
    	"table_row_map": {
    		"form": [],
    		"schema": {
    			"properties": {},
    			"required": []
    		},
    		"mapping": {}
    	},
    	"table_row": [],
    	"meta_system": {},
    	"meta_list": {},
    	"schemaeditor": {
    		"schema": {}
    	},
    	"edit_notes": {}
    }
    key = "item_funding_reference"

    add(
        post_data,
        key,
        option={
            "required": False,
            "multiple": True,
            "hidden": False,
            "showlist": False,
            "crtf": False,
            "oneline": False,
        },
        title="助成情報",
	    title_ja="助成情報",
	    title_en="Funder",
        sys_property=False,
    )
    assert post_data == default_post_data_funding

# 54104-2
# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py::test_add_mapping_false -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_add_mapping_false():
    post_data = {
    	"table_row_map": {
    		"form": [],
    		"schema": {
    			"properties": {},
    			"required": []
    		},
    		"mapping": {}
    	},
    	"table_row": [],
    	"meta_system": {},
    	"meta_list": {},
    	"schemaeditor": {
    		"schema": {}
    	},
    	"edit_notes": {}
    }
    key = "item_funding_reference"

    add(
        post_data,
        key,
        option={
            "required": False,
            "multiple": True,
            "hidden": False,
            "showlist": False,
            "crtf": False,
            "oneline": False,
        },
        mapping=False,
        title="助成情報",
	    title_ja="助成情報",
	    title_en="Funder",
        sys_property=False,
    )
    expected_post_data = copy.deepcopy(default_post_data_funding)
    expected_post_data["table_row_map"]["mapping"][key] = {
        "display_lang_type": "",
        "jpcoar_v1_mapping": "",
        "jpcoar_mapping": "",
        "junii2_mapping": "",
        "lido_mapping": "",
        "lom_mapping": "",
        "oai_dc_mapping": "",
        "spase_mapping": "",
    }
    assert post_data == expected_post_data

# 54104-10～12
# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py::test_add_invalid_parameter -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_add_invalid_parameter():
    post_data = {
    	"table_row_map": {
    		"form": [],
    		"schema": {
    			"properties": {},
    			"required": []
    		},
    		"mapping": {}
    	},
    	"table_row": [],
    	"meta_system": {},
    	"meta_list": {},
    	"schemaeditor": {
    		"schema": {}
    	},
    	"edit_notes": {}
    }
    key = "item_funding_reference"

    with pytest.raises(KeyError):
        add(
            post_data,
            key
        )

    post_data = {}
    with pytest.raises(KeyError):
        add(
            post_data,
            key,
            option={
                "required": False,
                "multiple": True,
                "hidden": False,
                "showlist": False,
                "crtf": False,
                "oneline": False
            }
        )
    
    post_data = {
    	"table_row_map": {
    		"form": {},
    		"schema": {
    			"properties": {},
    			"required": []
    		},
    		"mapping": {}
    	},
    	"table_row": [],
    	"meta_system": {},
    	"meta_list": {},
    	"schemaeditor": {
    		"schema": {}
    	},
    	"edit_notes": {}
    }

    with pytest.raises(AttributeError):
        add(
            post_data,
            key,
            option={
                "required": False,
                "multiple": True,
                "hidden": False,
                "showlist": False,
                "crtf": False,
                "oneline": False
            },
            mapping=True,
            title="助成情報",
            title_ja="助成情報",
            title_en="Funder",
            sys_property=False
        )

@pytest.mark.parametrize("option", [
    {"multiple": True, "hidden": False, "showlist": False, "crtf": False, "oneline": False},
    {"required": False, "hidden": False, "showlist": False, "crtf": False, "oneline": False},
    {"required": False, "multiple": True, "showlist": False, "crtf": False, "oneline": False},
    {"required": False, "multiple": True, "hidden": False, "crtf": False, "oneline": False},
    {"required": False, "multiple": True, "hidden": False, "showlist": False, "oneline": False},
    {"required": False, "multiple": True, "hidden": False, "showlist": False, "crtf": False},
])
# 54104-14～19
# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py::test_add_option_missing_keys -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_add_option_missing_keys(option):
    post_data = {
        "table_row_map": {
            "form": [],
            "schema": {
                "properties": {},
                "required": []
            },
            "mapping": {}
        },
        "table_row": [],
        "meta_system": {},
        "meta_list": {},
        "schemaeditor": {
            "schema": {}
        },
        "edit_notes": {}
    }
    key = "item_funding_reference"
    with pytest.raises(KeyError):
        add(
            post_data,
            key,
            option=option,
            mapping=False,
            title="助成情報",
            title_ja="助成情報",
            title_en="Funder",
            sys_property=False,
        )

# 54104-3
# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py::test_schema_title_empty -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_schema_title_empty():
    title = ""
    multi_flag = True
    rtn = schema(title, multi_flag)
    expexted_schema = copy.deepcopy(default_schema_funding)
    expexted_schema["format"] = "object"

    assert rtn == expexted_schema

    multi_flag = False
    rtn = schema(title, multi_flag)

    assert rtn == expexted_schema

# 54104-4,5
# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py::test_schema_multi_flag_true_or_false -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_schema_multi_flag_true_or_false():
    title = "助成情報"
    multi_flag = True
    rtn = schema(title, multi_flag)

    expected_schema = {
        "type": "array",
        "title": title,
        "minItems": "1",
        "maxItems": "9999",
        "items": default_schema_funding,
    }

    assert rtn == expected_schema

    multi_flag = False
    rtn = schema(title, multi_flag)

    expected_schema = default_schema_funding
    expected_schema["title"] = title

    assert rtn == expected_schema

# 54097-6,7
# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py::test_form_key_empty -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_form_key_empty():
    key = ""
    multi_flag = True
    rtn = form(key=key, multi_flag=multi_flag)
    expected = set_expected_form("parentkey[]")

    assert rtn == expected

    multi_flag = False
    rtn = form(key=key, multi_flag=multi_flag)
    expected = set_expected_form("parentkey")
    expected.pop("style", None)
    expected.pop("add", None)
    expected["type"] = "fieldset"

    assert rtn == expected

# 54097-8,9
# .tox/c1/bin/pytest --cov=demo/properties tests/test_funding_reference.py::test_form_multi_flag_true_or_false -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_form_multi_flag_true_or_false():
    key = "item_funding_reference"
    multi_flag = True
    title = "助成情報資料"
    title_ja = "助成"
    title_en = "Funder Reference"
    rtn = form(key=key, title=title, title_ja=title_ja, title_en=title_en, multi_flag=multi_flag)
    expected = set_expected_form("item_funding_reference[]")
    expected["title"] = title
    expected["title_i18n"] = {"ja": title_ja, "en": title_en}

    assert rtn == expected

    multi_flag = False
    rtn = form(key=key, multi_flag=multi_flag)
    expected = set_expected_form("item_funding_reference")
    expected.pop("style", None)
    expected.pop("add", None)
    expected["type"] = "fieldset"
    expected["title"] = ""

    assert rtn == expected