# coding:utf-8
"""Definition of date property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.DATE_LITERAL
multiple_flag = True
name_ja = "日付（リテラル）"
name_en = "Date(Literal)"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": "",
    "jpcoar_mapping": {
        "date_dcterms": {
            "@value": "subitem_dcterms_date",
            "@attributes": {"xml:lang": "subitem_dcterms_date_language"},
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"date": {"@value": "subitem_dcterms_date"}},
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
            "system_prop": False,
            "type": "object",
            "title": "dcterms_date",
            "properties": {
                "subitem_dcterms_date": {
                    "type": "string",
                    "format": "text",
                    "title": "日付（リテラル）",
                    "title_i18n": {"en": "Date Literal", "ja": "日付（リテラル）"},
                },
                "subitem_dcterms_date_language": {
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
                    "key": "{}.subitem_dcterms_date".format(key),
                    "type": "text",
                    "title": "日付（リテラル）",
                    "title_i18n": {"en": "Date Literal", "ja": "日付（リテラル）"},
                },
                {
                    "key": "{}.subitem_dcterms_date_language".format(key),
                    "title": "言語",
                    "title_i18n": {"ja": "言語", "en": "Language"},
                    "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
