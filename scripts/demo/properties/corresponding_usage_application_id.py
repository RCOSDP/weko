# coding:utf-8
"""Definition of corresponding usage application id property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.CORRESPONDING_USAGE_APPLICATION_ID
multiple_flag = True
name_ja = "対応する利用申請のID"
name_en = "Corresponding Usage Application ID"
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
                "subitem_corresponding_usage_application_id": {
                    "title": "対応する利用申請のID",
                    "type": ["null", "string"],
                    "format": "string",
                    "enum": [],
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
                    "key": "{}.subitem_corresponding_usage_application_id".format(key),
                    "title": "対応する利用申請のID",
                    "title_i18n": {
                        "en": "Corresponding Usage Application ID",
                        "ja": "対応する利用申請のID",
                    },
                    "type": "text",
                }
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
