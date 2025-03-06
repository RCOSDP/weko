# coding:utf-8
"""Definition of checkbox property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.RADIOBUTTON
multiple_flag = True
name_ja = "ラジオボタン"
name_en = "Radio Button"
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
            "format": "object",
            "properties": {
                "subitem_radio_item": {
                    "enum": [None],
                    "type": "string",
                    "title": "値",
                    "format": "radios",
                    "editAble": True,
                },
                "subitem_radio_language": {
                    "enum": config.LANGUAGE_VAL2_1,
                    "type": ["null", "string"],
                    "title": "言語",
                    "format": "select",
                    "editAble": True,
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
                    "key": "{}.subitem_radio_language".format(key),
                    "type": "select",
                    "title": "言語",
                    "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                    "title_i18n": {"en": "Language", "ja": "言語"},
                },
                {
                    "key": "{}.subitem_radio_item".format(key),
                    "type": "radios",
                    "title": "値",
                    "titleMap": [],
                    "title_i18n": {"en": "Value", "ja": "値"},
                },
            ],
        }

        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
