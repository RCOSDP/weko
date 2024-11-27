# coding:utf-8
"""Definition of rights holder property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
    make_title_map
)
from . import property_config as config

property_id = config.RIGHTS_HOLDER
multiple_flag = True
name_ja = "権利者情報"
name_en = "Right Holder"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "rightsHolder": {
            "rightsHolderName": {
                "@attributes": {"xml:lang": "rightHolderNames.rightHolderLanguage"},
                "@value": "rightHolderNames.rightHolderName",
            },
            "nameIdentifier": {
                "@attributes": {
                    "nameIdentifierScheme": "nameIdentifiers.nameIdentifierScheme",
                    "nameIdentifierURI": "nameIdentifiers.nameIdentifierURI",
                },
                "@value": "nameIdentifiers.nameIdentifier",
            },
        }
    },
    "jpcoar_mapping": {
        "rightsHolder": {
            "rightsHolderName": {
                "@attributes": {"xml:lang": "rightHolderNames.rightHolderLanguage"},
                "@value": "rightHolderNames.rightHolderName",
            },
            "nameIdentifier": {
                "@attributes": {
                    "nameIdentifierScheme": "nameIdentifiers.nameIdentifierScheme",
                    "nameIdentifierURI": "nameIdentifiers.nameIdentifierURI",
                },
                "@value": "nameIdentifiers.nameIdentifier",
            },
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
            "system_prop": True,
            "type": "object",
            "properties": {
                "nameIdentifiers": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "nameIdentifierScheme": {
                                "type": ["null", "string"],
                                "format": "select",
                                "title": "権利者識別子Scheme",
                                "enum": config.CREATOR_IDENTIFIER_SCHEMA_VAL,
                            },
                            "nameIdentifier": {
                                "format": "text",
                                "title": "権利者識別子",
                                "type": "string",
                            },
                            "nameIdentifierURI": {
                                "format": "text",
                                "title": "権利者識別子URI",
                                "type": "string",
                            },
                        },
                    },
                    "title": "権利者識別子",
                },
                "rightHolderNames": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "rightHolderLanguage": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                            "rightHolderName": {
                                "format": "text",
                                "title": "権利者名",
                                "type": "string",
                            },
                        },
                    },
                    "title": "権利者名",
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
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifierScheme".format(
                                key
                            ),
                            "title": "権利者識別子Scheme",
                            "title_i18n": {
                                "en": "Right Holder Name Identifier Scheme",
                                "ja": "権利者識別子Scheme",
                            },
                            "titleMap": make_title_map(config.CREATOR_IDENTIFIER_SCHEMA_LBL, config.CREATOR_IDENTIFIER_SCHEMA_VAL),
                            "type": "select",
                        },

                        {
                            "key": "{}.nameIdentifiers[].nameIdentifier".format(key),
                            "title": "権利者識別子",
                            "title_i18n": {
                                "en": "Right Holder Name Identifier",
                                "ja": "権利者識別子",
                            },
                            "type": "text",
                        },
                                                {
                            "key": "{}.nameIdentifiers[].nameIdentifierURI".format(key),
                            "title": "権利者識別子URI",
                            "title_i18n": {
                                "en": "Right Holder Name Identifier URI",
                                "ja": "権利者識別子URI",
                            },
                            "type": "text",
                        },
                    ],
                    "key": "{}.nameIdentifiers".format(key),
                    "style": {"add": "btn-success"},
                    "title": "権利者識別子",
                    "title_i18n": {"en": "Right Holder Identifier", "ja": "権利者識別子"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.rightHolderNames[].rightHolderName".format(key),
                            "title": "権利者名",
                            "title_i18n": {"en": "Right Holder Name", "ja": "権利者名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.rightHolderNames[].rightHolderLanguage".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.rightHolderNames".format(key),
                    "style": {"add": "btn-success"},
                    "title": "権利者名",
                    "title_i18n": {"en": "Right Holder Name", "ja": "権利者名"},
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
