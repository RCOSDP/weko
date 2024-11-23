# coding:utf-8
"""Definition of end page property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.END_PAGE
multiple_flag = False
name_ja = "終了ページ"
name_en = "End Page"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {"pageEnd": {"@value": "subitem_end_page"}},
    "jpcoar_mapping": {"pageEnd": {"@value": "subitem_end_page"}},
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
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
            "title": "終了ページ",
            "properties": {
                "subitem_end_page": {
                    "format": "text",
                    "title": "終了ページ",
                    "title_i18n": {"en": "End Page", "ja": "終了ページ"},
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
                    "key": "{}.subitem_end_page".format(key),
                    "title": "終了ページ",
                    "title_i18n": {"en": "End Page", "ja": "終了ページ"},
                    "type": "text",
                }
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
