# coding:utf-8
"""Definition of system identifier property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.S_IDENTIFIER
multiple_flag = False
name = name_ja = name_en = "S_Identifier"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "system_identifier": {
            "@value": "subitem_systemidt_identifier",
            "@attributes": {"identifierType": "subitem_systemidt_identifier_type"},
        }
    },
    "jpcoar_mapping": {
        "system_identifier": {
            "@value": "subitem_systemidt_identifier",
            "@attributes": {"identifierType": "subitem_systemidt_identifier_type"},
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {
        "system_identifier": {
            "@value": "subitem_systemidt_identifier",
            "@attributes": {"identifierType": "subitem_systemidt_identifier_type"},
        }
    },
    "spase_mapping": "",
}
id_type = ["DOI", "HDL", "URI"]


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = {
        "crtf": False,
        "hidden": True,
        "oneline": False,
        "multiple": False,
        "required": False,
        "showlist": False,
    }
    kwargs["sys_property"] = True
    set_post_data(post_data, property_id, name, key, option, form, schema, **kwargs)

    post_data["table_row_map"]["mapping"][key] = mapping


def schema(title="", multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        """Schema text."""
        _d = {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_systemidt_identifier": {
                    "type": "string",
                    "title": "SYSTEMIDT Identifier",
                    "format": "text",
                },
                "subitem_systemidt_identifier_type": {
                    "enum": id_type,
                    "currentEnum": id_type,
                    "type": "string",
                    "title": "SYSTEMIDT Identifier Type",
                    "format": "select",
                },
            },
            "system_prop": True,
        }
        return _d

    return get_property_schema(title, _schema, multi_flag)


def form(key="", title="", title_ja="", title_en="", multi_flag=multiple_flag):
    """Get form text of item type."""

    def _form(key):
        """Form text."""
        _d = {
            "key": key.replace("[]", ""),
            "type": "fieldset",
            "items": [
                {
                    "key": "{}.subitem_systemidt_identifier".format(key),
                    "type": "text",
                    "title": "SYSTEMIDT Identifier",
                },
                {
                    "key": "{}.subitem_systemidt_identifier_type".format(key),
                    "type": "select",
                    "title": "SYSTEMIDT Identifier Type",
                    "titleMap": get_select_value(id_type),
                },
            ],
        }

        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
