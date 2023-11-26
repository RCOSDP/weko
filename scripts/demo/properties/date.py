# coding:utf-8
"""Definition of date property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
    make_title_map,
)
from . import property_config as config

property_id = config.DATE
multiple_flag = True
name_ja = "日付"
name_en = "Date"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "date": {
            "@attributes": {"dateType": "subitem_date_issued_type"},
            "@value": "subitem_date_issued_datetime",
        }
    },
    "jpcoar_mapping": {
        "date": {
            "@attributes": {"dateType": "subitem_date_issued_type"},
            "@value": "subitem_date_issued_datetime",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"date": {"@value": "subitem_date_issued_datetime"}},
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
                "subitem_date_issued_datetime": {
                    "format": "datetime",
                    "title": "日付",
                    "type": "string",
                },
                "subitem_date_issued_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "currentEnum": config.DATE_TYPE_VAL,
                    "enum": config.DATE_TYPE_VAL,
                    "title": "日付タイプ",
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
                    "format": "yyyy-MM-dd",
                    "key": "{}.subitem_date_issued_datetime".format(key),
                    "templateUrl": config.DATEPICKER_MULTI_FORMAT_URL,
                    "title": "日付",
                    "title_i18n": {"ja": "日付", "en": "Date"},
                    "type": "template",
                },
                {
                    "key": "{}.subitem_date_issued_type".format(key),
                    "title": "日付タイプ",
                    "title_i18n": {"ja": "日付タイプ", "en": "Date Type"},
                    "titleMap": make_title_map(
                        config.DATE_TYPE_Label, config.DATE_TYPE_VAL
                    ),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
