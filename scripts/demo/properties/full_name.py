# coding:utf-8
"""Definition of full name property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.FULL_NAME
multiple_flag = True
name_ja = "氏名"
name_en = "Full Name"
mapping = config.DEFAULT_MAPPING


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop("option")
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    kwargs.pop("mapping", True)
    post_data["table_row_map"]["mapping"][key] = mapping


def schema(title="", multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        """Schema text."""
        _d = {
            "system_prop": True,
            "type": "object",
            "properties": {
                "alternatives": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "alternativeLang": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                            "alternative": {
                                "format": "text",
                                "title": "別名",
                                "type": "string",
                            },
                        },
                    },
                    "title": "別名",
                },
                "names": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "nameLang": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                            "name": {"format": "text", "title": "姓名", "type": "string"},
                        },
                    },
                    "title": "姓名",
                },
                "nameIdentifiers": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "nameIdentifierScheme": {
                                "type": "string",
                                "format": "text",
                                "title": "識別子Scheme",
                            },
                            "nameIdentifier": {
                                "format": "text",
                                "title": "識別子",
                                "type": "string",
                            },
                            "nameIdentifierURI": {
                                "format": "text",
                                "title": "識別子URI",
                                "type": "string",
                            },
                        },
                    },
                    "title": "識別子",
                },
                "affiliations": {
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
                                            "enum": config.AFFILIATION_SCHEME_VAL,
                                            "title": "所属機関識別子Scheme",
                                        },
                                        "affiliationNameIdentifier": {
                                            "format": "text",
                                            "title": "所属機関識別子",
                                            "type": "string",
                                        },
                                        "affiliationNameIdentifierURI": {
                                            "format": "text",
                                            "title": "所属機関識別子URI",
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
                                            "type": "string",
                                        },
                                        "affiliationNameLang": {
                                            "editAble": True,
                                            "type": ["null", "string"],
                                            "format": "select",
                                            "enum": config.LANGUAGE_VAL2_1,
                                            "title": "言語",
                                        },
                                    },
                                },
                                "title": "所属機関名",
                            },
                        },
                    },
                    "title": "所属",
                },
                "mails": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "mail": {
                                "format": "text",
                                "title": "メールアドレス",
                                "type": "string",
                            }
                        },
                    },
                    "title": "メールアドレス",
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
                                "title": "言語",
                            },
                            "givenName": {
                                "format": "text",
                                "title": "名",
                                "type": "string",
                            },
                        },
                    },
                    "title": "名",
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
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                            "familyName": {
                                "format": "text",
                                "title": "姓",
                                "type": "string",
                            },
                        },
                    },
                    "title": "姓",
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
                            "title": "識別子Scheme",
                            "title_i18n": {
                                "en": "Name Identifier Scheme",
                                "ja": "識別子Scheme",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifier".format(key),
                            "title": "識別子",
                            "title_i18n": {"en": "Name Identifier", "ja": "識別子"},
                            "type": "text",
                        },
                        {
                            "key": "{}.nameIdentifiers[].nameIdentifierURI".format(key),
                            "title": "識別子URI",
                            "title_i18n": {"en": "Name Identifier URI", "ja": "識別子URI"},
                            "type": "text",
                        },
                    ],
                    "key": "{}.nameIdentifiers".format(key),
                    "style": {"add": "btn-success"},
                    "title": "識別子",
                    "title_i18n": {"en": "Name Identifier", "ja": "識別子"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.names[].name".format(key),
                            "title": "姓名",
                            "title_i18n": {"en": "Name", "ja": "姓名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.names[].nameLang".format(key),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.names".format(key),
                    "style": {"add": "btn-success"},
                    "title": "姓名",
                    "title_i18n": {"en": "Name", "ja": "姓名"},
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
                    "title": "姓",
                    "title_i18n": {"en": "Family Name", "ja": "姓"},
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
                    "title": "名",
                    "title_i18n": {"en": "Given Name", "ja": "名"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.alternatives[].alternative".format(key),
                            "title": "別名",
                            "title_i18n": {"en": "Alternative Name", "ja": "別名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.alternatives[].alternativeLang".format(key),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.alternatives".format(key),
                    "style": {"add": "btn-success"},
                    "title": "別名",
                    "title_i18n": {"en": "Alternative Name", "ja": "別名"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "add": "New",
                            "items": [
                                {
                                    "key": "{}.affiliations[].affiliationNameIdentifiers[].affiliationNameIdentifierScheme".format(
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
                                    "key": "{}.affiliations[].affiliationNameIdentifiers[].affiliationNameIdentifier".format(
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
                                    "key": "{}.affiliations[].affiliationNameIdentifiers[].affiliationNameIdentifierURI".format(
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
                            "key": "{}.affiliations[].affiliationNameIdentifiers".format(
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
                                    "key": "{}.affiliations[].affiliationNames[].affiliationName".format(
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
                                    "key": "{}.affiliations[].affiliationNames[].affiliationNameLang".format(
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
                            "key": "{}.affiliations[].affiliationNames".format(key),
                            "style": {"add": "btn-success"},
                            "title": "所属機関名",
                            "title_i18n": {"en": "Affiliation Names", "ja": "所属機関名"},
                        },
                    ],
                    "key": "{}.affiliations".format(key),
                    "style": {"add": "btn-success"},
                    "title": "所属",
                    "title_i18n": {"en": "Affiliation", "ja": "所属"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.mails[].mail".format(key),
                            "title": "メールアドレス",
                            "title_i18n": {"en": "Email Address", "ja": "メールアドレス"},
                            "type": "text",
                        }
                    ],
                    "key": "{}.mails".format(key),
                    "style": {"add": "btn-success"},
                    "title": "メールアドレス",
                    "title_i18n": {"en": "Email Address", "ja": "メールアドレス"},
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
