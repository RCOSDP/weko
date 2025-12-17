# coding:utf-8
"""Definition of relation property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
    make_title_map,
)
from . import property_config as config

property_id = config.RELATION
multiple_flag = True
name_ja = "関連情報"
name_en = "Relation"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "relation": {
            "@attributes": {"relationType": "subitem_relation_type"},
            "relatedIdentifier": {
                "@attributes": {
                    "identifierType": "subitem_relation_type_id.subitem_relation_type_select"
                },
                "@value": "subitem_relation_type_id.subitem_relation_type_id_text",
            },
            "relatedTitle": {
                "@attributes": {
                    "xml:lang": "subitem_relation_name.subitem_relation_name_language"
                },
                "@value": "subitem_relation_name.subitem_relation_name_text",
            },
        }
    },
    "jpcoar_mapping": {
        "relation": {
            "@attributes": {"relationType": "subitem_relation_type"},
            "relatedIdentifier": {
                "@attributes": {
                    "identifierType": "subitem_relation_type_id.subitem_relation_type_select"
                },
                "@value": "subitem_relation_type_id.subitem_relation_type_id_text",
            },
            "relatedTitle": {
                "@attributes": {
                    "xml:lang": "subitem_relation_name.subitem_relation_name_language"
                },
                "@value": "subitem_relation_name.subitem_relation_name_text",
            },
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {
        "relation": {
            "@value": "subitem_relation_name.subitem_relation_name_text"
        }
    },
    "spase_mapping": "",
}
relation_type = [
    None,
    "isVersionOf",
    "hasVersion",
    "isPartOf",
    "hasPart",
    "isReferencedBy",
    "references",
    "isFormatOf",
    "hasFormat",
    "isReplacedBy",
    "replaces",
    "isRequiredBy",
    "requires",
    "isSupplementedBy",
    "isSupplementTo",
    "isIdenticalTo",
    "isDerivedFrom",
    "isSourceOf",
    "isCitedBy",
    "Cites",
    "inSeries",
]
id_type = [
    None,
    "ARK",
    "arXiv",
    "DOI",
    "HDL",
    "ICHUSHI",
    "ISBN",
    "J-GLOBAL",
    "Local",
    "PISSN",
    "EISSN",
    "ISSN【非推奨】",
    "NAID",
    "NCID",
    "PMID",
    "PURL",
    "SCOPUS",
    "URI",
    "WOS",
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
            "type": "object",
            "properties": {
                "subitem_relation_name": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "subitem_relation_name_language": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                            "subitem_relation_name_text": {
                                "format": "text",
                                "title": "関連名称",
                                "type": "string",
                            },
                        },
                    },
                    "title": "関連名称",
                },
                "subitem_relation_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": relation_type,
                    "currentEnum": relation_type,
                    "title": "関連タイプ",
                },
                "subitem_relation_type_id": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "subitem_relation_type_id_text": {
                            "format": "text",
                            "title": "関連識別子",
                            "type": "string",
                        },
                        "subitem_relation_type_select": {
                            "type": ["null", "string"],
                            "format": "select",
                            "enum": config.RELATION_ID_TYPE_VAL,
                            "currentEnum": config.RELATION_ID_TYPE_VAL,
                            "title": "識別子タイプ",
                        },
                    },
                    "title": "関連識別子",
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
                    "key": "{}.subitem_relation_type".format(key),
                    "title": "関連タイプ",
                    "title_i18n": {"en": "Relation Type", "ja": "関連タイプ"},
                    "titleMap": get_select_value(relation_type),
                    "type": "select",
                },
                {
                    "items": [
                        {
                            "key": "{}.subitem_relation_type_id.subitem_relation_type_select".format(
                                key
                            ),
                            "title": "識別子タイプ",
                            "title_i18n": {"en": "Identifier Type", "ja": "識別子タイプ"},
                            "titleMap": make_title_map(
                                config.RELATION_ID_TYPE_LBL, config.RELATION_ID_TYPE_VAL
                            ),
                            "type": "select",
                        },
                        {
                            "key": "{}.subitem_relation_type_id.subitem_relation_type_id_text".format(
                                key
                            ),
                            "title": "関連識別子",
                            "title_i18n": {"en": "Related Identifier", "ja": "関連識別子"},
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_relation_type_id".format(key),
                    "title": "関連識別子",
                    "title_i18n": {"en": "Related Identifier", "ja": "関連識別子"},
                    "type": "fieldset",
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.subitem_relation_name[].subitem_relation_name_language".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                        {
                            "key": "{}.subitem_relation_name[].subitem_relation_name_text".format(
                                key
                            ),
                            "title": "関連名称",
                            "title_i18n": {"en": "Related Title", "ja": "関連名称"},
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_relation_name".format(key),
                    "style": {"add": "btn-success"},
                    "title": "関連名称",
                    "title_i18n": {"en": "Related Title", "ja": "関連名称"},
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
