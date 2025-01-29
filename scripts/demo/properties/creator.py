# coding:utf-8
"""Definition of creator property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
    make_title_map,
)
from . import property_config as config

property_id = config.CREATOR
multiple_flag = True
name_ja = "作成者"
name_en = "Creator"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "creator": {
            "affiliation": {
                "affiliationName": {
                    "@attributes": {
                        "xml:lang": "creatorAffiliations."
                        "affiliationNames."
                        "affiliationNameLang"
                    },
                    "@value": "creatorAffiliations."
                    "affiliationNames."
                    "affiliationName",
                },
                "nameIdentifier": {
                    "@attributes": {
                        "nameIdentifierScheme": "creatorAffiliations."
                        "affiliationNameIdentifiers."
                        "affiliationNameIdentifierScheme",
                        "nameIdentifierURI": "creatorAffiliations."
                        "affiliationNameIdentifiers."
                        "affiliationNameIdentifierURI",
                    },
                    "@value": "creatorAffiliations."
                    "affiliationNameIdentifiers."
                    "affiliationNameIdentifier",
                },
            },
            "creatorAlternative": {
                "@attributes": {
                    "xml:lang": "creatorAlternatives.creatorAlternativeLang"
                },
                "@value": "creatorAlternatives.creatorAlternative",
            },
            "creatorName": {
                "@attributes": {"xml:lang": "creatorNames.creatorNameLang"},
                "@value": "creatorNames.creatorName",
            },
            "familyName": {
                "@attributes": {"xml:lang": "familyNames.familyNameLang"},
                "@value": "familyNames.familyName",
            },
            "givenName": {
                "@attributes": {"xml:lang": "givenNames.givenNameLang"},
                "@value": "givenNames.givenName",
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
        "creator": {
            "@attributes": {"creatorType": "creatorType"},
            "affiliation": {
                "affiliationName": {
                    "@attributes": {
                        "xml:lang": "creatorAffiliations."
                        "affiliationNames."
                        "affiliationNameLang"
                    },
                    "@value": "creatorAffiliations."
                    "affiliationNames."
                    "affiliationName",
                },
                "nameIdentifier": {
                    "@attributes": {
                        "nameIdentifierScheme": "creatorAffiliations."
                        "affiliationNameIdentifiers."
                        "affiliationNameIdentifierScheme",
                        "nameIdentifierURI": "creatorAffiliations."
                        "affiliationNameIdentifiers."
                        "affiliationNameIdentifierURI",
                    },
                    "@value": "creatorAffiliations."
                    "affiliationNameIdentifiers."
                    "affiliationNameIdentifier",
                },
            },
            "creatorAlternative": {
                "@attributes": {
                    "xml:lang": "creatorAlternatives.creatorAlternativeLang"
                },
                "@value": "creatorAlternatives.creatorAlternative",
            },
            "creatorName": {
                "@attributes": {
                    "xml:lang": "creatorNames.creatorNameLang",
                    "nameType": "creatorNames.creatorNameType",
                },
                "@value": "creatorNames.creatorName",
            },
            "familyName": {
                "@attributes": {"xml:lang": "familyNames.familyNameLang"},
                "@value": "familyNames.familyName",
            },
            "givenName": {
                "@attributes": {"xml:lang": "givenNames.givenNameLang"},
                "@value": "givenNames.givenName",
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
    "oai_dc_mapping": {
        "creator": {"@value": "creatorNames.creatorName,nameIdentifiers.nameIdentifier"}
    },
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
                "iscreator": {"format": "text", "title": "iscreator", "type": "string"},
                "creatorType": {
                    "type": "string",
                    "format": "text",
                    "title": "作成者タイプ",
                    "title_i18n": {"en": "Creator Type", "ja": "作成者タイプ"},
                },
                "creatorAlternatives": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "creatorAlternativeLang": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": (config.LANGUAGE_VAL2_1)[1:],
                                "title": "言語",
                                "title_i18n": {"en": "Language", "ja": "言語"},
                            },
                            "creatorAlternative": {
                                "format": "text",
                                "title": "別名",
                                "title_i18n": {"en": "Alternative Name", "ja": "別名"},
                                "type": "string",
                            },
                        },
                    },
                    "title": "作成者別名",
                },
                "creatorNames": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "creatorNameLang": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": (config.LANGUAGE_VAL2_1)[1:],
                                "title": "言語",
                                "title_i18n": {"en": "Language", "ja": "言語"},
                            },
                            "creatorNameType": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.NAME_TYPE_VAL,
                                "currentEnum": (config.NAME_TYPE_VAL)[1:],
                                "title": "名前タイプ",
                                "title_i18n": {"en": "Name Type", "ja": "名前タイプ"},
                            },
                            "creatorName": {
                                "format": "text",
                                "title": "姓名",
                                "type": "string",
                                "title_i18n": {"en": "Name", "ja": "姓名"},
                            },
                        },
                    },
                    "title": "作成者姓名",
                },
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
                                "enum": [],
                                # "currentEnum": [],
                                # "enum": config.CREATOR_IDENTIFIER_SCHEMA_VAL,
                                # "currentEnum": (
                                #                 config.CREATOR_IDENTIFIER_SCHEMA_VAL
                                #             )[1:],
                                "title": "作成者識別子Scheme",
                                "title_i18n": {
                                    "en": "IdentifierScheme",
                                    "ja": "作成者識別子Scheme",
                                },
                            },
                            "nameIdentifier": {
                                "format": "text",
                                "title": "作成者識別子",
                                "title_i18n": {
                                    "en": "Creator Name Identifier",
                                    "ja": "作成者識別子",
                                },
                                "type": "string",
                            },
                            "nameIdentifierURI": {
                                "format": "text",
                                "title": "作成者識別子URI",
                                "title_i18n": {
                                    "en": "Creator Name Identifier URI",
                                    "ja": "作成者識別子URI",
                                },
                                "type": "string",
                            },
                        },
                    },
                    "title": "作成者識別子",
                },
                "creatorAffiliations": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "affiliationNameIdentifiers": {
                                "type": "array",
                                "format": "array",
                                "items": {
                                    "type": "object",
                                    "format": "object",
                                    "properties": {
                                        "affiliationNameIdentifierScheme": {
                                            "type": ["null", "string"],
                                            "format": "select",
                                            # "enum": [],
                                            # "currentEnum": [],
                                            "enum": config.AFFILIATION_SCHEME_VAL,
                                            "currentEnum": (
                                                config.AFFILIATION_SCHEME_VAL
                                            )[1:],
                                            "title": "所属機関識別子Scheme",
                                            "title_i18n": {
                                                "en": "Affiliation Name Identifier Scheme",
                                                "ja": "所属機関識別子Scheme",
                                            },
                                        },
                                        "affiliationNameIdentifier": {
                                            "format": "text",
                                            "title": "所属機関識別子",
                                            "title_i18n": {
                                                "en": "Affiliation Name Identifier",
                                                "ja": "所属機関識別子",
                                            },
                                            "type": "string",
                                        },
                                        "affiliationNameIdentifierURI": {
                                            "format": "text",
                                            "title": "所属機関識別子URI",
                                            "title_i18n": {
                                                "en": "Affiliation Name Identifier URI",
                                                "ja": "所属機関識別子URI",
                                            },
                                            "type": "string",
                                        },
                                    },
                                },
                                "title": "所属機関識別子",
                            },
                            "affiliationNames": {
                                "type": "array",
                                "format": "array",
                                "items": {
                                    "type": "object",
                                    "format": "object",
                                    "properties": {
                                        "affiliationName": {
                                            "format": "text",
                                            "title": "所属機関名",
                                            "title_i18n": {
                                                "en": "Affiliation Name",
                                                "ja": "所属機関名",
                                            },
                                            "type": "string",
                                        },
                                        "affiliationNameLang": {
                                            "editAble": True,
                                            "type": ["null", "string"],
                                            "format": "select",
                                            "enum": config.LANGUAGE_VAL2_1,
                                            "currentEnum": (config.LANGUAGE_VAL2_1)[1:],
                                            "title": "言語",
                                            "title_i18n": {
                                                "en": "Language",
                                                "ja": "言語",
                                            },
                                        },
                                    },
                                },
                                "title": "所属機関名",
                            },
                        },
                    },
                    "title": "作成者所属",
                },
                "creatorMails": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "creatorMail": {
                                "format": "text",
                                "title": "メールアドレス",
                                "title_i18n": {"en": "Email Address", "ja": "メールアドレス"},
                                "type": "string",
                            }
                        },
                    },
                    "title": "作成者メールアドレス",
                },
                "givenNames": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "givenNameLang": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": (config.LANGUAGE_VAL2_1)[1:],
                                "title": "言語",
                                "title_i18n": {"en": "Language", "ja": "言語"},
                            },
                            "givenName": {
                                "format": "text",
                                "title": "名",
                                "title_i18n": {"en": "Given Name", "ja": "名"},
                                "type": "string",
                            },
                        },
                    },
                    "title": "作成者名",
                },
                "familyNames": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "familyNameLang": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": (config.LANGUAGE_VAL2_1)[1:],
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                                "title_i18n": {"en": "Language", "ja": "言語"},
                            },
                            "familyName": {
                                "format": "text",
                                "title": "姓",
                                "type": "string",
                                "title_i18n": {"en": "Family Name", "ja": "姓"},
                            },
                        },
                    },
                    "title": "作成者姓",
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
                    "key": "{}.creatorType".format(key),
                    "type": "text",
                    "title": "作成者タイプ",
                    "title_i18n": {"en": "Creator Type", "ja": "作成者タイプ"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifierScheme".format(
                                key
                            ),
                            "title": "作成者識別子Scheme",
                            "title_i18n": {
                                "en": "Creator Name Identifier Scheme",
                                "ja": "作成者識別子Scheme",
                            },
                            "titleMap": [], # make_title_map(config.CREATOR_IDENTIFIER_SCHEMA_LBL, config.CREATOR_IDENTIFIER_SCHEMA_VAL),
                            "type": "select",
                        },
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifierURI".format(key),
                            "title": "作成者識別子URI",
                            "title_i18n": {
                                "en": "Creator Name Identifier URI",
                                "ja": "作成者識別子URI",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifier".format(key),
                            "title": "作成者識別子",
                            "title_i18n": {
                                "en": "Creator Name Identifier",
                                "ja": "作成者識別子",
                            },
                            "type": "text",
                        },
                    ],
                    "key": "{}.nameIdentifiers".format(key),
                    "style": {"add": "btn-success"},
                    "title": "作成者識別子",
                    "title_i18n": {"en": "Creator Name Identifier", "ja": "作成者識別子"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.creatorNames[].creatorName".format(key),
                            "title": "姓名",
                            "title_i18n": {"en": "Name", "ja": "姓名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.creatorNames[].creatorNameLang".format(key),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                        {
                            "key": "{}.creatorNames[].creatorNameType".format(key),
                            "title": "名前タイプ",
                            "title_i18n": {"en": "Name Type", "ja": "名前タイプ"},
                            "titleMap": get_select_value(config.NAME_TYPE_VAL),
                            "type": "select",
                        },
                    ],
                    "key": "{}.creatorNames".format(key),
                    "style": {"add": "btn-success"},
                    "title": "作成者姓名",
                    "title_i18n": {"en": "Creator Name", "ja": "作成者姓名"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.familyNames[].familyName".format(key),
                            "title": "姓",
                            "title_i18n": {"en": "Family Name", "ja": "姓"},
                            "type": "text",
                        },
                        {
                            "key": "{}.familyNames[].familyNameLang".format(key),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.familyNames".format(key),
                    "style": {"add": "btn-success"},
                    "title": "作成者姓",
                    "title_i18n": {"en": "Creator Family Name", "ja": "作成者姓"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.givenNames[].givenName".format(key),
                            "title": "名",
                            "title_i18n": {"en": "Given Name", "ja": "名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.givenNames[].givenNameLang".format(key),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.givenNames".format(key),
                    "style": {"add": "btn-success"},
                    "title": "作成者名",
                    "title_i18n": {"en": "Creator Given Name", "ja": "作成者名"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.creatorAlternatives[].creatorAlternative".format(
                                key
                            ),
                            "title": "別名",
                            "title_i18n": {"en": "Alternative Name", "ja": "別名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.creatorAlternatives[].creatorAlternativeLang".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.creatorAlternatives".format(key),
                    "style": {"add": "btn-success"},
                    "title": "作成者別名",
                    "title_i18n": {"en": "Creator Alternative Name", "ja": "作成者別名"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "add": "New",
                            "items": [
                                {
                                    "key": "{}.creatorAffiliations[].affiliationNameIdentifiers[].affiliationNameIdentifier".format(
                                        key
                                    ),
                                    "title": "所属機関識別子",
                                    "title_i18n": {
                                        "en": "Affiliation Name Identifier",
                                        "ja": "所属機関識別子",
                                    },
                                    "type": "text",
                                },
                                {
                                    "key": "{}.creatorAffiliations[].affiliationNameIdentifiers[].affiliationNameIdentifierScheme".format(
                                        key
                                    ),
                                    "title": "所属機関識別子Scheme",
                                    "title_i18n": {
                                        "en": "Affiliation Name Identifier Scheme",
                                        "ja": "所属機関識別子Scheme",
                                    },
                                    "titleMap": make_title_map(
                                        config.AFFILIATION_SCHEME_LBL,config.AFFILIATION_SCHEME_VAL
                                    ),
                                    "type": "select",
                                },
                                {
                                    "key": "{}.creatorAffiliations[].affiliationNameIdentifiers[].affiliationNameIdentifierURI".format(
                                        key
                                    ),
                                    "title": "所属機関識別子URI",
                                    "title_i18n": {
                                        "en": "Affiliation Name Identifier URI",
                                        "ja": "所属機関識別子URI",
                                    },
                                    "type": "text",
                                },
                            ],
                            "key": "{}.creatorAffiliations[].affiliationNameIdentifiers".format(
                                key
                            ),
                            "style": {"add": "btn-success"},
                            "title": "所属機関識別子",
                            "title_i18n": {
                                "en": "Affiliation Name Identifiers",
                                "ja": "所属機関識別子",
                            },
                        },
                        {
                            "add": "New",
                            "items": [
                                {
                                    "key": "{}.creatorAffiliations[].affiliationNames[].affiliationName".format(
                                        key
                                    ),
                                    "title": "所属機関名",
                                    "title_i18n": {
                                        "en": "Affiliation Name",
                                        "ja": "所属機関名",
                                    },
                                    "type": "text",
                                },
                                {
                                    "key": "{}.creatorAffiliations[].affiliationNames[].affiliationNameLang".format(
                                        key
                                    ),
                                    "title": "言語",
                                    "title_i18n": {"en": "Language", "ja": "言語"},
                                    "titleMap": get_select_value(
                                        config.LANGUAGE_VAL2_1
                                    ),
                                    "type": "select",
                                },
                            ],
                            "key": "{}.creatorAffiliations[].affiliationNames".format(
                                key
                            ),
                            "style": {"add": "btn-success"},
                            "title": "所属機関名",
                            "title_i18n": {"en": "Affiliation Names", "ja": "所属機関名"},
                        },
                    ],
                    "key": "{}.creatorAffiliations".format(key),
                    "style": {"add": "btn-success"},
                    "title": "作成者所属",
                    "title_i18n": {"en": "Affiliation", "ja": "作成者所属"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.creatorMails[].creatorMail".format(key),
                            "title": "メールアドレス",
                            "title_i18n": {"en": "Email Address", "ja": "メールアドレス"},
                            "type": "text",
                        }
                    ],
                    "key": "{}.creatorMails".format(key),
                    "style": {"add": "btn-success"},
                    "title": "作成者メールアドレス",
                    "title_i18n": {"en": "Creator Email Address", "ja": "作成者メールアドレス"},
                },
                {
                    "icon": "glyphicon glyphicon-search",
                    "key": "{}.authorInputButton".format(key),
                    "onClick": "searchAuthor('{}', true, form)".format(
                        key.replace("[]", "")
                    ),
                    "style": "btn-default pull-right m-top-5",
                    "title": "著者DBから入力",
                    "title_i18n": {"en": "Enter from DB", "ja": "著者DBから入力"},
                    "type": "button",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
