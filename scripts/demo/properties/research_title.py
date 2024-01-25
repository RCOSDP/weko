# coding:utf-8
"""Definition of research title property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.RESEARCH_TITLE
multiple_flag = False
name_ja = "研究題目"
name_en = "Research Title"
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
            "system_prop": True,
            "type": "object",
            "properties": {
                "subitem_research_title": {
                    "title": "研究題目",
                    "type": "string",
                    "format": "text",
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
                    "key": "{}.subitem_research_title".format(key),
                    "title": "研究題目",
                    "title_i18n": {"en": "Research Title", "ja": "研究題目"},
                    "type": "text",
                }
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
