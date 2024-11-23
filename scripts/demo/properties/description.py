# coding:utf-8
"""Definition of description and identifier property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.DESCRIPTION
multiple_flag = True
name_ja = "内容記述"
name_en = "Description"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "description": {
            "@attributes": {
                "descriptionType": "subitem_description_type",
                "xml:lang": "subitem_description_language",
            },
            "@value": "subitem_description",
        }
    },
    "jpcoar_mapping": {
        "description": {
            "@attributes": {
                "descriptionType": "subitem_description_type",
                "xml:lang": "subitem_description_language",
            },
            "@value": "subitem_description",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"description": {"@value": "subitem_description"}},
    "spase_mapping": "",
}
description_type = [
    None,
    "Abstract",
    "Methods",
    "TableOfContents",
    "TechnicalInfo",
    "Other",
]


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
                "subitem_description": {
                    "format": "textarea",
                    "title": "内容記述",
                    "type": "string",
                },
                "subitem_description_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": config.LANGUAGE_VAL2_1,
                    "title": "言語",
                },
                "subitem_description_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": description_type,
                    "currentEnum": description_type[1:],
                    "title": "内容記述タイプ",
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
                    "key": "{}.subitem_description_type".format(key),
                    "title": "内容記述タイプ",
                    "title_i18n": {"en": "Description Type", "ja": "内容記述タイプ"},
                    "titleMap": get_select_value(description_type),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_description".format(key),
                    "title": "内容記述",
                    "title_i18n": {"en": "Description", "ja": "内容記述"},
                    "type": "textarea",
                },
                {
                    "key": "{}.subitem_description_language".format(key),
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
