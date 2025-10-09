# coding:utf-8
"""Definition of contributor property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
    make_title_map,
)
from . import property_config as config

property_id = config.CONTRIBUTOR
multiple_flag = True
name_ja = "寄与者"
name_en = "Contributor"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "contributor": {
            "@attributes": {"contributorType": "contributorType"},
            "affiliation": {
                "affiliationName": {
                    "@attributes": {
                        "xml:lang": "contributorAffiliations."
                        "contributorAffiliationNames."
                        "contributorAffiliationNameLang"
                    },
                    "@value": "contributorAffiliations."
                    "contributorAffiliationNames."
                    "contributorAffiliationName",
                },
                "nameIdentifier": {
                    "@attributes": {
                        "nameIdentifierScheme": "contributorAffiliations."
                        "contributorAffiliationNameIdentifiers."
                        "contributorAffiliationScheme",
                        "nameIdentifierURI": "contributorAffiliations."
                        "contributorAffiliationNameIdentifiers."
                        "contributorAffiliationURI",
                    },
                    "@value": "contributorAffiliations."
                    "contributorAffiliationNameIdentifiers."
                    "contributorAffiliationNameIdentifier",
                },
            },
            "contributorAlternative": {
                "@attributes": {
                    "xml:lang": "contributorAlternatives.contributorAlternativeLang"
                },
                "@value": "contributorAlternatives.contributorAlternative",
            },
            "contributorName": {
                "@attributes": {"xml:lang": "contributorNames.lang"},
                "@value": "contributorNames.contributorName",
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
        "contributor": {
            "@attributes": {"contributorType": "contributorType"},
            "affiliation": {
                "affiliationName": {
                    "@attributes": {
                        "xml:lang": "contributorAffiliations."
                        "contributorAffiliationNames."
                        "contributorAffiliationNameLang"
                    },
                    "@value": "contributorAffiliations."
                    "contributorAffiliationNames."
                    "contributorAffiliationName",
                },
                "nameIdentifier": {
                    "@attributes": {
                        "nameIdentifierScheme": "contributorAffiliations."
                        "contributorAffiliationNameIdentifiers."
                        "contributorAffiliationScheme",
                        "nameIdentifierURI": "contributorAffiliations."
                        "contributorAffiliationNameIdentifiers."
                        "contributorAffiliationURI",
                    },
                    "@value": "contributorAffiliations."
                    "contributorAffiliationNameIdentifiers."
                    "contributorAffiliationNameIdentifier",
                },
            },
            "contributorAlternative": {
                "@attributes": {
                    "xml:lang": "contributorAlternatives.contributorAlternativeLang"
                },
                "@value": "contributorAlternatives.contributorAlternative",
            },
            "contributorName": {
                "@attributes": {
                    "xml:lang": "contributorNames.lang",
                    "nameType": "contributorNames.nameType",
                },
                "@value": "contributorNames.contributorName",
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
        "contributor": {
            "@value": "contributorNames.contributorName"
        }
    },
    "spase_mapping": "",
}
contributor_type = [
    None,
    "ContactPerson",
    "DataCollector",
    "DataCurator",
    "DataManager",
    "Distributor",
    "Editor",
    "HostingInstitution",
    "Producer",
    "ProjectLeader",
    "ProjectManager",
    "ProjectMember",
    "RelatedPerson",
    "Researcher",
    "ResearchGroup",
    "Sponsor",
    "Supervisor",
    "WorkPackageLeader",
    "Other",
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
            "system_prop": True,
            "type": "object",
            "properties": {
                "contributorType": {
                    "enum": contributor_type,
                    "format": "select",
                    "title": "寄与者タイプ",
                    "title_i18n": {"en": "Contributor Type", "ja": "寄与者タイプ"},
                    "type": ["null", "string"],
                },
                "nameIdentifiers": {
                    "format": "array",
                                    "type": "array",
                    "items": {
                        "format": "object",
                        "type": "object",
                        "properties": {
                            "nameIdentifier": {
                                "format": "text",
                                "title": "寄与者識別子",
                                "title_i18n": {
                                    "en": "Contributor Name Identifier",
                                    "ja": "寄与者識別子",
                                },
                                "type": "string",
                            },
                            "nameIdentifierScheme": {
                                "format": "select",
                                "title": "寄与者識別子Scheme",
                                "title_i18n": {
                                    "en": "Contributor Name Identifier Scheme",
                                    "ja": "寄与者識別子Scheme",
                                },
                                "type": ["null", "string"],
                                "enum": [],
                            },
                            "nameIdentifierURI": {
                                "format": "text",
                                "title": "寄与者識別子URI",
                                "title_i18n": {
                                    "en": "Contributor Name Identifier URI",
                                    "ja": "寄与者識別子URI",
                                },
                                "type": "string",
                            },
                        },
                    },
                    "title": "寄与者識別子",
    
                },
                "contributorNames": {
                    "format": "array",
                    "items": {
                        "format": "object",
                        "properties": {
                            "contributorName": {
                                "format": "text",
                                "title": "姓名",
                                "title_i18n": {"en": "Name", "ja": "姓名"},
                                "type": "string",
                            },
                            "lang": {
                                "editAble": True,
                                "enum": config.LANGUAGE_VAL2_1,
                                "format": "select",
                                "title": "言語",
                                "title_i18n": {"en": "Language", "ja": "言語"},
                                "type": ["null", "string"],
                            },
                            "nameType": {
                                "editAble": False,
                                "enum": config.NAME_TYPE_VAL,
                                "format": "select",
                                "title": "名前タイプ",
                                "title_i18n": {"en": "Name Type", "ja": "名前タイプ"},
                                "type": ["null", "string"],
                            },
                        },
                        "type": "object",
                    },
                    "title": "寄与者姓名",
                    "type": "array",
                },
                "familyNames": {
                    "format": "array",
                    "items": {
                        "format": "object",
                        "properties": {
                            "familyName": {
                                "format": "text",
                                "title": "姓",
                                "title_i18n": {"en": "Family Name", "ja": "姓"},
                                "type": "string",
                            },
                                                        "familyNameLang": {
                                "editAble": True,
                                "enum": config.LANGUAGE_VAL2_1,
                                "format": "select",
                                "title": "言語",
                                "title_i18n": {"en": "Language", "ja": "言語"},
                                "type": ["null", "string"],
                            },
                        },
                        "type": "object",
                    },
                    "title": "寄与者姓",
                    "type": "array",
                },
                "givenNames": {
                    "format": "array",
                    "items": {
                        "format": "object",
                        "properties": {
                            "givenName": {
                                "format": "text",
                                "title": "名",
                                "title_i18n": {"en": "Given Name", "ja": "名"},
                                "type": "string",
                            },
                            "givenNameLang": {
                                "editAble": True,
                                "enum": config.LANGUAGE_VAL2_1,
                                "format": "select",
                                "title": "言語",
                                "title_i18n": {"en": "Language", "ja": "言語"},
                                "type": ["null", "string"],
                            },
                        },
                        "type": "object",
                    },
                    "title": "寄与者名",
                    "type": "array",
                },
                "contributorAlternatives": {
                    "format": "array",
                    "items": {
                        "format": "object",
                        "properties": {
                            "contributorAlternative": {
                                "format": "text",
                                "title": "別名",
                                "title_i18n": {"en": "Alternative Name", "ja": "別名"},
                                "type": "string",
                            },
                            "contributorAlternativeLang": {
                                "editAble": True,
                                "enum": config.LANGUAGE_VAL2_1,
                                "format": "select",
                                "title": "言語",
                                "title_i18n": {"en": "Language", "ja": "言語"},
                                "type": ["null", "string"],
                            },
                        },
                        "type": "object",
                    },
                    "title": "寄与者別名",
                    "type": "array",
                },
                "contributorAffiliations": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "contributorAffiliationNameIdentifiers": {
                                "type": "array",
                                "format": "array",
                                "items": {
                                    "type": "object",
                                    "format": "object",
                                    "properties": {
                                        "contributorAffiliationScheme": {
                                            "type": ["null", "string"],
                                            "format": "select",
                                            # "enum": [],
                                            "enum": config.AFFILIATION_SCHEME_VAL,
                                            "currentEnum": config.AFFILIATION_SCHEME_VAL[
                                                1:
                                            ],
                                            "title": "所属機関識別子Scheme",
                                            "title_i18n": {
                                        "en": "Affiliation Name Identifier Scheme",
                                        "ja": "所属機関識別子Scheme",
                                    },
                                        },
                                        "contributorAffiliationNameIdentifier": {
                                            "format": "text",
                                            "title": "所属機関識別子",
                                            "title_i18n": {
                                "en": "Affiliation Name Identifiers",
                                "ja": "所属機関識別子",
                            },
                                            "type": "string",
                                        },
                                        "contributorAffiliationURI": {
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
                            "contributorAffiliationNames": {
                                "type": "array",
                                "format": "array",
                                "items": {
                                    "type": "object",
                                    "format": "object",
                                    "properties": {
                                        "contributorAffiliationName": {
                                            "format": "text",
                                            "title": "所属機関名",
                                            "title_i18n": {
                                        "en": "Affiliation Name",
                                        "ja": "所属機関名",
                                    },
                                            "type": "string",
                                        },
                                        "contributorAffiliationNameLang": {
                                            "editAble": True,
                                            "type": ["null", "string"],
                                            "format": "select",
                                            "enum": config.LANGUAGE_VAL2_1,
                                            "title": "言語",
                                            "title_i18n": {"en": "Language", "ja": "言語"},
                                        },
                                    },
                                },
                                "title": "所属機関名",
                            },
                        },
                    },
                    "title": "寄与者所属",
                },
                "contributorMails": {
                    "format": "array",
                    "items": {
                        "format": "object",
                        "properties": {
                            "contributorMail": {
                                "format": "text",
                                "title": "メールアドレス",
                                 "title_i18n": {
                                "en": "Email Address",
                                "ja": "メールアドレス",
                            },
                                "type": "string",
                            }
                        },
                        "type": "object",
                    },
                    "title": "寄与者メールアドレス",
                    "type": "array",
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
                    "key": "{}.contributorType".format(key),
                    "title": "Contributor Type",
                    "title_i18n": {"en": "Contributor Type", "ja": "寄与者タイプ"},
                    "titleMap": get_select_value(contributor_type),
                    "type": "select",
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifierScheme".format(
                                key
                            ),
                            "title": "寄与者識別子Scheme",
                            "title_i18n": {
                                "en": "Contributor Name Identifier Scheme",
                                "ja": "寄与者識別子Scheme",
                            },
                            "titleMap": make_title_map(
                                config.CREATOR_IDENTIFIER_SCHEMA_LBL,
                                config.CREATOR_IDENTIFIER_SCHEMA_VAL,
                            ),
                            "type": "select",
                        },
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifier".format(key),
                            "title": "寄与者識別子",
                            "title_i18n": {
                                "en": "Contributor Name Identifier",
                                "ja": "寄与者識別子",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifierURI".format(key),
                            "title": "寄与者識別子URI",
                            "title_i18n": {
                                "en": "Contributor Name Identifier URI",
                                "ja": "寄与者識別子URI",
                            },
                            "type": "text",
                        },
                    ],
                    "key": "{}.nameIdentifiers".format(key),
                    "style": {"add": "btn-success"},
                    "title": "寄与者識別子",
                    "title_i18n": {
                        "en": "Contributor Name Identifier",
                        "ja": "寄与者識別子",
                    },
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.contributorNames[].contributorName".format(key),
                            "title": "姓名",
                            "title_i18n": {"en": "Name", "ja": "姓名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.contributorNames[].lang".format(key),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                        {
                            "key": "{}.contributorNames[].nameType".format(key),
                            "title": "名前タイプ",
                            "title_i18n": {"en": "Name Type", "ja": "名前タイプ"},
                            "titleMap": get_select_value(config.NAME_TYPE_VAL),
                            "type": "select",
                        },
                    ],
                    "key": "{}.contributorNames".format(key),
                    "style": {"add": "btn-success"},
                    "title": "寄与者姓名",
                    "title_i18n": {"en": "Contributor Name", "ja": "寄与者姓名"},
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
                    "title": "寄与者姓",
                    "title_i18n": {"en": "Contributor Family Name", "ja": "寄与者姓"},
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
                    "title": "寄与者名",
                    "title_i18n": {"en": "Contributor Given Name", "ja": "寄与者名"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.contributorAlternatives[].contributorAlternative".format(
                                key
                            ),
                            "title": "別名",
                            "title_i18n": {"en": "Alternative Name", "ja": "別名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.contributorAlternatives[].contributorAlternativeLang".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.contributorAlternatives".format(key),
                    "style": {"add": "btn-success"},
                    "title": "寄与者別名",
                    "title_i18n": {
                        "en": "Contributor Alternative Name",
                        "ja": "寄与者別名",
                    },
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "add": "New",
                            "items": [
                                {
                                    "key": "{}.contributorAffiliations[].contributorAffiliationNameIdentifiers[].contributorAffiliationScheme".format(
                                        key
                                    ),
                                    "title": "所属機関識別子Scheme",
                                    "title_i18n": {
                                        "en": "Affiliation Name Identifier Scheme",
                                        "ja": "所属機関識別子Scheme",
                                    },
                                    "titleMap": get_select_value(
                                        config.AFFILIATION_SCHEME_VAL
                                    ),
                                    "type": "select",
                                },
                                {
                                    "key": "{}.contributorAffiliations[].contributorAffiliationNameIdentifiers[].contributorAffiliationNameIdentifier".format(
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
                                    "key": "{}.contributorAffiliations[].contributorAffiliationNameIdentifiers[].contributorAffiliationURI".format(
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
                            "key": "{}.contributorAffiliations[].contributorAffiliationNameIdentifiers".format(
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
                                    "key": "{}.contributorAffiliations[].contributorAffiliationNames[].contributorAffiliationName".format(
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
                                    "key": "{}.contributorAffiliations[].contributorAffiliationNames[].contributorAffiliationNameLang".format(
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
                            "key": "{}.contributorAffiliations[].contributorAffiliationNames".format(
                                key
                            ),
                            "style": {"add": "btn-success"},
                            "title": "所属機関名",
                            "title_i18n": {
                                "en": "Affiliation Names",
                                "ja": "所属機関名",
                            },
                        },
                    ],
                    "key": "{}.contributorAffiliations".format(key),
                    "style": {"add": "btn-success"},
                    "title": "寄与者所属",
                    "title_i18n": {"en": "Affiliation", "ja": "寄与者所属"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.contributorMails[].contributorMail".format(key),
                            "title": "メールアドレス",
                            "title_i18n": {
                                "en": "Email Address",
                                "ja": "メールアドレス",
                            },
                            "type": "text",
                        }
                    ],
                    "key": "{}.contributorMails".format(key),
                    "style": {"add": "btn-success"},
                    "title": "寄与者メールアドレス",
                    "title_i18n": {
                        "en": "Contributor Email Address",
                        "ja": "寄与者メールアドレス",
                    },
                },
                {
                    "icon": "glyphicon glyphicon-search",
                    "key": "{}.authorInputButton".format(key),
                    "onClick": "searchAuthor('{}', true, form)".format(key),
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
