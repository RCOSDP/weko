# coding:utf-8
"""Definition of apc property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.APC
multiple_flag = False
name_ja = "APC"
name_en = "APC"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {"apc": {"@value": "subitem_apc"}},
    "jpcoar_mapping": {"apc": {"@value": "subitem_apc"}},
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}
apc = [
    None,
    "Paid",
    "Partially waived",
    "Fully waived",
    "Not charged",
    "Not required",
    "Unknown",
]


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
                "subitem_apc": {
                    "title": "APC",
                    "title_i18n": {"en": "APC", "ja": "APC"},
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": apc,
                    "currentEnum": apc[1:],
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
                    "key": "{}.subitem_apc".format(key),
                    "title": "APC",
                    "title_i18n": {"en": "APC", "ja": "APC"},
                    "titleMap": get_select_value(apc),
                    "type": "select",
                }
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
