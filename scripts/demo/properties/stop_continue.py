# coding:utf-8
"""Definition of stop/continue property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.STOP_CONTINUE
multiple_flag = False
name_ja = "終了／継続"
name_en = "Stop/Continue"
mapping = config.DEFAULT_MAPPING
stop_continue = {"Stop": "終了", "Continue": "継続"}


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
            "system_prop": True,
            "type": "object",
            "properties": {
                "subitem_restricted_access_stop/continue": {
                    "title": "終了／継続",
                    "type": "string",
                    "format": "radios",
                    "enum": list(stop_continue.keys()),
                }
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
                    "key": "{}.subitem_restricted_access_stop/continue".format(key),
                    "title": "終了／継続",
                    "title_i18n": {"en": "Stop/Continue", "ja": "終了／継続"},
                    "titleMap": get_select_value(stop_continue),
                    "type": "radios",
                }
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
