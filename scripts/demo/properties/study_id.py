# coding:utf-8
"""Definition of study id property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.STUDY_ID
multiple_flag = False
name_ja = "調査番号"
name_en = "Study ID"
mapping = config.DEFAULT_MAPPING


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
                "subitem_study_id": {
                    "format": "text",
                    "title": "調査番号",
                    "title_i18n": {"en": "Study ID", "ja": "調査番号"},
                    "type": "string",
                },
                "subitem_study_id_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": config.LANGUAGE_VAL2_2,
                    "currentEnum": config.LANGUAGE_VAL2_2[1:],
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                },
                "subitem_study_id_agency": {
                    "format": "text",
                    "title": "調査番号付与機関",
                    "title_i18n": {"en": "ID Agency", "ja": "調査番号付与機関"},
                    "type": ["null", "string"],
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
            "key": key.replace("[]", ""),
            "items": [
                {
                    "key": "{}.subitem_study_id".format(key),
                    "title": "調査番号",
                    "title_i18n": {"en": "Study ID", "ja": "調査番号"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_study_id_language".format(key),
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                    "titleMap": get_select_value(config.LANGUAGE_VAL2_2),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_study_id_agency".format(key),
                    "title": "調査番号付与機関",
                    "title_i18n": {"en": "ID Agency", "ja": "調査番号付与機関"},
                    "type": "text",
                },
            ],
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
