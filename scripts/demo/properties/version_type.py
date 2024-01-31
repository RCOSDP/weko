# coding:utf-8
"""Definition of version type property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.VERSION_TYPE
multiple_flag = False
name_ja = "出版タイプ"
name_en = "Version Type"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "versiontype": {
            "@attributes": {"rdf:resource": "subitem_version_resource"},
            "@value": "subitem_version_type",
        }
    },
    "jpcoar_mapping": {
        "versiontype": {
            "@attributes": {"rdf:resource": "subitem_version_resource"},
            "@value": "subitem_version_type",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"type": {"@value": "subitem_version_type"}},
    "spase_mapping": "",
}
version_type = [None, "AO", "SMUR", "AM", "P", "VoR", "CVoR", "EVoR", "NA"]


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
            "system_prop": True,
            "type": "object",
            "properties": {
                "subitem_version_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": version_type,
                    "currentEnum": version_type[1:],
                    "title": "出版タイプ",
                    "title_i18n": {"en": "Version Type", "ja": "出版タイプ"},
                },
                "subitem_version_resource": {
                    "format": "text",
                    "title": "出版タイプResource",
                    "title_i18n": {
                        "en": "Version Type Resource",
                        "ja": "出版タイプResource",
                    },
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
                    "key": "{}.subitem_version_type".format(key),
                    "onChange": "changedVersionType(this, modelValue)",
                    "title": "出版タイプ",
                    "title_i18n": {"en": "Version Type", "ja": "出版タイプ"},
                    "titleMap": get_select_value(version_type),
                    "type": "select",
                },
                {
                    "fieldHtmlClass": "txt-version-resource",
                    "key": "{}.subitem_version_resource".format(key),
                    "readonly": True,
                    "title": "出版タイプResource",
                    "title_i18n": {
                        "en": "Version Type Resource",
                        "ja": "出版タイプResource",
                    },
                    "type": "text",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
