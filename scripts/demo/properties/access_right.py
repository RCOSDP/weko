# coding:utf-8
"""Definition of access right property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.ACCESS_RIGHT
multiple_flag = False
name_ja = "アクセス権"
name_en = "Access Rights"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "accessRights": {
            "@attributes": {"rdf:resource": "subitem_access_right_uri"},
            "@value": "subitem_access_right",
        }
    },
    "jpcoar_mapping": {
        "accessRights": {
            "@attributes": {"rdf:resource": "subitem_access_right_uri"},
            "@value": "subitem_access_right",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"rights": {"@value": "subitem_access_right"}},
    "spase_mapping": "",
}

access_rights = [
    None,
    "embargoed access",
    "metadata only access",
    "open access",
    "restricted access",
]


def add(post_data, key, **kwargs):
    """Add to a item type."""
    if "option" in kwargs:
        kwargs.pop("option")
    option = {
        "required": False,
        "multiple": multiple_flag,
        "hidden": False,
        "showlist": False,
        "crtf": False,
        "oneline": False,
    }
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
                "subitem_access_right": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": access_rights,
                    "currentEnum": access_rights[1:],
                    "title": "アクセス権",
                    "title_i18n": {"en": "Access Rights", "ja": "アクセス権"},
                },
                "subitem_access_right_uri": {
                    "format": "text",
                    "title": "アクセス権URI",
                    "title_i18n": {"en": "Access Rights URI", "ja": "アクセス権URI"},
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
                    "key": "{}.subitem_access_right".format(key),
                    "onChange": "changedAccessRights(this, modelValue)",
                    "title": "アクセス権",
                    "title_i18n": {"en": "Access Rights", "ja": "アクセス権"},
                    "titleMap": get_select_value(access_rights),
                    "type": "select",
                },
                {
                    "fieldHtmlClass": "txt-access-rights-uri",
                    "key": "{}.subitem_access_right_uri".format(key),
                    "readonly": True,
                    "title": "アクセス権URI",
                    "title_i18n": {"en": "Access Rights URI", "ja": "アクセス権URI"},
                    "type": "text",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
