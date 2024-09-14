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

property_id = config.JPCOAR_DATASET_SERIES
multiple_flag = False
name_ja = "データセットシリーズ"
name_en = "Dataset Series"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": "",
    "jpcoar_mapping": {"datasetSeries": {"@value": "jpcoar_dataset_series"}},
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
            "title": "dataset_series",
            "properties": {
                "jpcoar_dataset_series": {
                    "type": "string",
                    "format": "select",
                    "enum": ["True", "False"],
                    "currentEnum": [None, "True", "False"],
                    "title": "Dataset Series",
                    "title_i18n": {"ja": "データセットシリーズ", "en": "Dataset Series"},
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
                    "key": "{}.jpcoar_dataset_series".format(key),
                    "type": "select",
                    "title": "Dataset Series",
                    "title_i18n": {"ja": "データセットシリーズ", "en": "Dataset Series"},
                    "titleMap": [
                        {"value": "True", "name": "True"},
                        {"value": "False", "name": "False"},
                    ],
                },
            ],
            "key": key.replace("[]", ""),
            "type": "fieldset",
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
