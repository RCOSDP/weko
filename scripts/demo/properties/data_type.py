# coding:utf-8
"""Definition of data type property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.DATA_TYPE
multiple_flag = False
name_ja = "データタイプ（英語統制語彙）"
name_en = "Data Type E"
mapping = config.DEFAULT_MAPPING
data_type = [
    None,
    "quantatitive research",
    "quantitative research : micro data",
    "quantitative research : tabular data",
    "quantitative research : other",
    "official statistics",
    "official statistics : micro data",
    "official statistics : tabular data",
    "official statistics : other",
    "qualitative research",
    "qualitative research : digital audio data",
    "qualitative research : digital video data",
    "qualitative research : text data",
    "other",
]
lnag = [None, "en"]
description_type = [None, "Other"]


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop("option")
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    kwargs.pop("mapping", True)
    post_data["table_row_map"]["mapping"][key] = mapping


def schema(title="", multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        """Schema text."""
        _d = {
            "type": "object",
            "properties": {
                "subitem_data_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": data_type,
                    "title": "データタイプ（英語統制語彙）",
                },
                "subitem_data_type_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": lnag,
                    "title": "言語",
                },
                "subitem_data_type_description_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": description_type,
                    "title": "(JPCOAR対応用)記述タイプ",
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
                    "key": "{}.subitem_data_type".format(key),
                    "title": "データタイプ（英語統制語彙）",
                    "title_i18n": {"en": "Data Type E", "ja": "データタイプ（英語統制語彙）"},
                    "titleMap": get_select_value(data_type),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_data_type_language".format(key),
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                    "titleMap": get_select_value(lnag),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_data_type_description_type".format(key),
                    "title": "(JPCOAR対応用)記述タイプ",
                    "title_i18n": {
                        "en": "(for JPCOAR)Description Type",
                        "ja": "(JPCOAR対応用)記述タイプ",
                    },
                    "titleMap": get_select_value(description_type),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
