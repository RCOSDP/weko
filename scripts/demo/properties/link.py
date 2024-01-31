# coding:utf-8
"""Definition of link property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.LINK
multiple_flag = True
name_ja = "リンク"
name_en = "Link"
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
                "subitem_link_text": {
                    "format": "text",
                    "title": "表示名",
                    "type": "string",
                },
                "subitem_link_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": config.LANGUAGE_VAL2_1,
                    "title": "言語",
                },
                "subitem_link_url": {
                    "format": "text",
                    "title": "URL",
                    "type": "string",
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
                    "key": "{}.subitem_link_language".format(key),
                    "title": "言語",
                    "title_i18n": {"ja": "言語", "en": "Language"},
                    "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_link_text".format(key),
                    "title": "表示名",
                    "title_i18n": {"ja": "表示名", "en": "Link Text"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_link_url".format(key),
                    "title": "URL",
                    "title_i18n": {"ja": "URL", "en": "URL"},
                    "type": "text",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
