# coding:utf-8
"""Definition of rights property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.RIGHTS
multiple_flag = True
name_ja = "権利情報"
name_en = "Rights"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "rights": {
            "@attributes": {
                "rdf:resource": "subitem_rights_resource",
                "xml:lang": "subitem_rights_language",
            },
            "@value": "subitem_rights",
        }
    },
    "jpcoar_mapping": {
        "rights": {
            "@attributes": {
                "rdf:resource": "subitem_rights_resource",
                "xml:lang": "subitem_rights_language",
            },
            "@value": "subitem_rights",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"rights": {"@value": "subitem_rights"}},
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
            "properties": {
                "subitem_rights": {"format": "text", "title": "権利情報", "type": "string"},
                "subitem_rights_resource": {
                    "format": "text",
                    "title": "権利情報Resource",
                    "type": "string",
                },
                "subitem_rights_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": config.LANGUAGE_VAL2_1,
                    "title": "言語",
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
                    "key": "{}.subitem_rights_resource".format(key),
                    "title": "権利情報Resource",
                    "title_i18n": {"en": "Rights Resource", "ja": "権利情報Resource"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_rights".format(key),
                    "title": "権利情報",
                    "title_i18n": {"en": "Rights", "ja": "権利情報"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_rights_language".format(key),
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                    "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
