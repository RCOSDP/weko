# coding:utf-8
"""Definition of source identifier property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.SOURCE_ID
multiple_flag = True
name_ja = "収録物識別子"
name_en = "Source Identifier"
mapping = {
    "display_lang_type": "",
    "jpcoar_mapping": {
        "sourceIdentifier": {
            "@attributes": {"identifierType": "subitem_source_identifier_type"},
            "@value": "subitem_source_identifier",
        }
    },
    "jpcoar_v1_mapping": {
        "sourceIdentifier": {
            "@attributes": {"identifierType": "subitem_source_identifier_type"},
            "@value": "subitem_source_identifier",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping":"",
    "spase_mapping": "",
}
id_type = [None, "PISSN", "EISSN", "ISSN", "NCID"]


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop("option")
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
            "properties": {
                "subitem_source_identifier": {
                    "format": "text",
                    "title": "収録物識別子",
                    "type": "string",
                },
                "subitem_source_identifier_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": id_type,
                    "title": "収録物識別子タイプ",
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
                    "key": "{}.subitem_source_identifier_type".format(key),
                    "title": "収録物識別子タイプ",
                    "title_i18n": {"en": "Source Identifier Type", "ja": "収録物識別子タイプ"},
                    "titleMap": get_select_value(id_type),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_source_identifier".format(key),
                    "title": "収録物識別子",
                    "title_i18n": {"en": "Source Identifier", "ja": "収録物識別子"},
                    "type": "text",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
