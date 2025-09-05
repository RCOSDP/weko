import pytest
from demo.properties.dcndl_original_language import (
    add,
    schema,
    form,
)
from demo.properties import property_config as config
from .conftest import default_post_data, default_schema, title_map, language_val3

# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp

# 54097-1
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_add_not_exists_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
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
        "schemaeditor": {"schema": {}},
        "edit_notes": {}
    }
    key = "item_original_lang"

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
        title="原文の言語",
        title_ja="原文の言語",
        title_en="Original Language",
        sys_property=False,
    )
    assert post_data == default_post_data

# 54097-2
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_add_mapping_false -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
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
    key = "item_original_lang"

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
        mapping=False,
	    title="原文の言語",
	    title_ja="原文の言語",
	    title_en="Original Language",
	    sys_property=False
    )
    expected_post_data = default_post_data
    expected_post_data["table_row_map"]["mapping"][key] = config.DEFAULT_MAPPING
    
    assert post_data == expected_post_data

# 54097-10～12、14～19
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_add_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_add_exception():
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
        "schemaeditor": {"schema": {}},
        "edit_notes": {}
    }
    key = "item_original_lang"

    with pytest.raises(KeyError):
        add(
            post_data,
            key,
            title="原文の言語",
            title_ja="原文の言語",
            title_en="Original Language",
            sys_property=False,
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
            title="原文の言語",
            title_ja="原文の言語",
            title_en="Original Language",
            sys_property=False
        )
    
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
    with pytest.raises(KeyError):
        add(
            post_data,
            key,
            option={
                "multiple": True,
                "hidden": False,
                "showlist": False,
                "crtf": False,
                "oneline": False
            },
            title="原文の言語",
            title_ja="原文の言語",
            title_en="Original Language",
            sys_property=True
        )

    with pytest.raises(KeyError):
        add(
            post_data,
            key,
            option={
                "required": False,
                "hidden": False,
                "showlist": False,
                "crtf": False,
                "oneline": False
            },
            title="原文の言語",
            title_ja="原文の言語",
            title_en="Original Language",
            sys_property=True
        )

    with pytest.raises(KeyError):
        add(
            post_data,
            key,
            option={
                "required": False,
                "multiple": True,
                "showlist": False,
                "crtf": False,
                "oneline": False
            },
            title="原文の言語",
            title_ja="原文の言語",
            title_en="Original Language",
            sys_property=True
        )

    with pytest.raises(KeyError):
        add(
            post_data,
            key,
            option={
                "required": False,
                "multiple": True,
                "hidden": False,
                "crtf": False,
                "oneline": False
            },
            title="原文の言語",
            title_ja="原文の言語",
            title_en="Original Language",
            sys_property=True
        )

    with pytest.raises(KeyError):
        add(
            post_data,
            key,
            option={
                "required": False,
                "multiple": True,
                "hidden": False,
                "showlist": False,
                "oneline": False
            },
            title="原文の言語",
            title_ja="原文の言語",
            title_en="Original Language",
            sys_property=True
        )

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
            },
            title="原文の言語",
            title_ja="原文の言語",
            title_en="Original Language",
            sys_property=True
        )
    

# 54097-3
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_schema_title_empty -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_schema_title_empty():
    title = ""
    multi_flag = True
    rtn = schema(title, multi_flag)
    
    assert rtn == default_schema

    multi_flag = False
    rtn = schema(title, multi_flag)
    
    assert rtn == default_schema

# 54097-4,5
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_schema_multi_flag_true_or_false -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_schema_multi_flag_true_or_false():
    title = "Original Language"
    multi_flag = True
    rtn = schema(title, multi_flag)

    expected_schema = {
        "type": "array",
        "title": title,
        "minItems": "1",
        "maxItems": "9999",
        "items": default_schema,
    }
    
    assert rtn == expected_schema

    multi_flag = False
    rtn = schema(title, multi_flag)

    expected_schema = default_schema
    expected_schema["title"] = title
    
    assert rtn == expected_schema

# 54097-20
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_schema_not_exists_language_val3 -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_schema_not_exists_language_val3():
    delattr(config, "LANGUAGE_VAL3")
    with pytest.raises(AttributeError):
        schema()
    setattr(config, "LANGUAGE_VAL3", language_val3)

# 54097-6,7
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_form_key_empty -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_form_key_empty():
    key = ""
    multi_flag = True
    rtn = form(key=key, multi_flag=multi_flag)
    
    assert rtn == {
        "add": "New",
        "style": {"add": "btn-success"},
        "title_i18n": {"ja": "原文の言語", "en": "Original Language"},
        "items": [
            {
                "key": "parentkey[].original_language",
                "type": "select",
                "title": "原文の言語",
                "title_i18n": {"ja": "原文の言語", "en": "Original Language"},
                "titleMap": title_map
            }
        ],
        "key": "parentkey",
    }

    multi_flag = False
    rtn = form(key=key, multi_flag=multi_flag)
    
    assert rtn == {
        "items": [
            {
                "key": "parentkey.original_language",
                "type": "select",
                "title": "原文の言語",
                "title_i18n": {"ja": "原文の言語", "en": "Original Language"},
                "titleMap": title_map
            }
        ],
        "key": "parentkey",
        "type": "fieldset",
        "title_i18n": {"ja": "原文の言語", "en": "Original Language"},
    }

# 54097-8,9
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_form_multi_flag_true_or_false -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_form_multi_flag_true_or_false():
    key = "item_original_lang"
    multi_flag = True
    title = "言語"
    title_ja = "言語"
    title_en = "Language"
    rtn = form(key=key, title=title, title_ja=title_ja, title_en=title_en, multi_flag=multi_flag)
    
    assert rtn == {
        "add": "New",
        "style": {"add": "btn-success"},
        "title": title,
        "title_i18n": {"ja": title_ja, "en": title_en},
        "items": [
            {
                "key": "item_original_lang[].original_language",
                "type": "select",
                "title": "原文の言語",
                "title_i18n": {"ja": "原文の言語", "en": "Original Language"},
                "titleMap": title_map
            }
        ],
        "key": key
    }

    multi_flag = False
    rtn = form(key=key, multi_flag=multi_flag)
    
    assert rtn == {
        "type": "fieldset",
        "title": "",
        "title_i18n": {"ja": "原文の言語", "en": "Original Language"},
        "items": [
            {
                "key": "item_original_lang.original_language",
                "type": "select",
                "title": "原文の言語",
                "title_i18n": {"ja": "原文の言語", "en": "Original Language"},
                "titleMap": title_map
            }
        ],
        "key": key
    }

# 54097-21
# .tox/c1/bin/pytest --cov=demo/properties tests/test_dcndl_original_language.py::test_form_not_exists_language_val3 -vv -s --cov-branch --cov-report=term --basetemp=/code/scripts/.tox/c1/tmp
def test_form_not_exists_language_val3():
    delattr(config, "LANGUAGE_VAL3")
    with pytest.raises(AttributeError):
        form()
    setattr(config, "LANGUAGE_VAL3", language_val3)