# coding:utf-8
"""Definition of source title property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.SOURCE_TITLE
multiple_flag = False
name_ja = "収録物名"
name_en = "Source Title"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "sourceTitle": {
            "@attributes": {"xml:lang": "subitem_source_title_language"},
            "@value": "subitem_source_title",
        }
    },
    "jpcoar_mapping": {
        "sourceTitle": {
            "@attributes": {"xml:lang": "subitem_source_title_language"},
            "@value": "subitem_source_title",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"identifier": {"@value": "subitem_source_title"}},
    "spase_mapping": "",
}


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
                "subitem_source_title": {
                    "format": "text",
                    "title": "収録物名",
                    "type": "string",
                },
                "subitem_source_title_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": config.LANGUAGE_VAL2_1,
                    "title": "言語",
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
                    "key": "{}.subitem_source_title".format(key),
                    "title": "収録物名",
                    "title_i18n": {"en": "Source Title", "ja": "収録物名"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_source_title_language".format(key),
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                    "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
