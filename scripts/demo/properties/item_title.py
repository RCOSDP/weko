# coding:utf-8
"""Definition of item title property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.ITEM_TITLE
multiple_flag = False
name_ja = "アイテムタイトル"
name_en = "Item Title"
mapping = config.DEFAULT_MAPPING


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop("option")
    mapping_switch = kwargs["mapping_switch"]  # title, alternative
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop("mapping", True):
        post_data["table_row_map"]["mapping"][key] = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        mapping_switch: {"@value": "subitem_restricted_access_item_title"}
    },
    "jpcoar_mapping": {
        mapping_switch: {"@value": "subitem_restricted_access_item_title"}
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}
    else:
        post_data["table_row_map"]["mapping"][key] = config.DEFAULT_MAPPING


def schema(title="", multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        """Schema text."""
        _d = {
            "system_prop": True,
            "type": "object",
            "properties": {
                "subitem_restricted_access_item_title": {
                    "format": "text",
                    "title": "アイテムタイトル",
                    "type": "string",
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
                    "key": "{}.subitem_restricted_access_item_title".format(key),
                    "title": "アイテムタイトル",
                    "title_i18n": {"en": "Item Title", "ja": "アイテムタイトル"},
                    "type": "text",
                }
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
