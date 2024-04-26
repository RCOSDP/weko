# coding:utf-8
"""Definition of publisher property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
    make_title_map,
)
from . import property_config as config

property_id = config.DCNDL_VOLUME_TITLE
multiple_flag = True
name_ja = "部編名"
name_en = "Volume Title"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": "",
    "jpcoar_mapping": {
        "volumeTitle": {
            "@value": "volume_title",
            "@attributes": {"xml:lang": "volume_title_language"},
        }
    },
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
            "format": "object",
            "title": "volume_title",
            "properties": {
                "volume_title": {
                    "type": "string",
                    "format": "text",
                    "title": "部編名",
                    "title_i18n": {"ja": "部編名", "en": "Volume Title"},
                },
                "volume_title_language": {
                    "type": "string",
                    "format": "select",
                    "enum": config.LANGUAGE_VAL2_1,
                    "currentEnum": config.LANGUAGE_VAL2_1,
                    "title": "Language",
                    "title_i18n": {"ja": "言語", "en": "Language"},
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
                    "key": "{}.volume_title".format(key),
                    "type": "text",
                    "title": "Edition",
                },
                {
                    "key": "{}.volume_title_language".format(key),
                    "type": "select",
                    "title": "Language",
                    "title_i18n": {"ja": "言語", "en": "Language"},
                    "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
