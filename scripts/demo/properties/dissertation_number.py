# coding:utf-8
"""Definition of dissertation number property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.DISSERTATION_NUMBER
multiple_flag = False
name_ja = "学位授与番号"
name_en = "Dissertation Number"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "dissertationNumber": {"@value": "subitem_dissertationnumber"}
    },
    "jpcoar_mapping": {"dissertationNumber": {"@value": "subitem_dissertationnumber"}},
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"identifier": {"@value": "subitem_dissertationnumber"}},
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
            "title": "dissertation_number",
            "properties": {
                "subitem_dissertationnumber": {
                    "format": "text",
                    "title": "学位授与番号",
                    "title_i18n": {"en": "Dissertation Number", "ja": "学位授与番号"},
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
                    "key": "{}.subitem_dissertationnumber".format(key),
                    "title": "学位授与番号",
                    "title_i18n": {"en": "Dissertation Number", "ja": "学位授与番号"},
                    "type": "text",
                }
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
