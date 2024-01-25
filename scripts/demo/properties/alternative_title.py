# coding:utf-8
"""Definition of alternative title property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.ALTERNATIVE_TITLE
multiple_flag = True
name_ja = "その他のタイトル"
name_en = "Alternative Title"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "alternative": {
            "@attributes": {"xml:lang": "subitem_alternative_title_language"},
            "@value": "subitem_alternative_title",
        }
    },
    "jpcoar_mapping": {
        "alternative": {
            "@attributes": {"xml:lang": "subitem_alternative_title_language"},
            "@value": "subitem_alternative_title",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"title": {"@value": "subitem_alternative_title"}},
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
                "subitem_alternative_title": {
                    "format": "text",
                    "title": "その他のタイトル",
                    "type": "string",
                    "title_i18n": {"en": "Alternative Title", "ja": "その他のタイトル"},
                },
                "subitem_alternative_title_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "currentEnum": (config.LANGUAGE_VAL2_1)[1:],
                    "enum": config.LANGUAGE_VAL2_1,
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
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
                    "key": "{}.subitem_alternative_title".format(key),
                    "title": "その他のタイトル",
                    "title_i18n": {"en": "Alternative Title", "ja": "その他のタイトル"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_alternative_title_language".format(key),
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
