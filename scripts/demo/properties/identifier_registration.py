# coding:utf-8
"""Definition of identifier registration property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.IDENTIFIER_REGISTRATION
multiple_flag = False
name_ja = "ID登録"
name_en = "Identifier Registration"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "identifierRegistration": {
            "@attributes": {"identifierType": "subitem_identifier_reg_type"},
            "@value": "subitem_identifier_reg_text",
        }
    },
    "jpcoar_mapping": {
        "identifierRegistration": {
            "@attributes": {"identifierType": "subitem_identifier_reg_type"},
            "@value": "subitem_identifier_reg_text",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

id_type = [None, "JaLC", "Crossref", "DataCite", "PMID"]


def add(post_data, key, **kwargs):
    """Add to a item type."""
    if "option" in kwargs:
        kwargs.pop("option")
    option = {
        "required": False,
        "multiple": multiple_flag,
        "hidden": False,
        "showlist": False,
        "crtf": False,
        "oneline": False,
    }
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop("mapping", True):
        post_data["table_row_map"]["mapping"][key] = mapping
    else:
        post_data["table_row_map"]["mapping"][key] = config.DEFAULT_MAPPING


def schema(title="", multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        """Schema text."""
        _d = {
            "type": "object",
            "title": "identifier_registration",
            "properties": {
                "subitem_identifier_reg_text": {
                    "format": "text",
                    "title": "ID登録",
                    "title_i18n": {"en": "Identifier Registration", "ja": "ID登録"},
                    "type": "string",
                },
                "subitem_identifier_reg_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": id_type,
                    "currentEnum": id_type[1:],
                    "title": "ID登録タイプ",
                    "title_i18n": {
                        "en": "Identifier Registration Type",
                        "ja": "ID登録タイプ",
                    },
                },
            },
        }
        return _d

    return get_property_schema(title, _schema, multi_flag)


def form(
    key="", title="", title_ja=name_ja, title_en=name_en, multi_flag=multiple_flag
):
    """Get form text of item type."""

    def _form(key):
        """Form text."""
        _d = {
            "items": [
                {
                    "key": "{}.subitem_identifier_reg_text".format(key),
                    "readonly": True,
                    "title": "ID登録",
                    "title_i18n": {"en": "Identifier Registration", "ja": "ID登録"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_identifier_reg_type".format(key),
                    "readonly": True,
                    "title": "ID登録タイプ",
                    "title_i18n": {
                        "en": "Identifier Registration Type",
                        "ja": "ID登録タイプ",
                    },
                    "titleMap": get_select_value(id_type),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
