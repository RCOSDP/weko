# coding:utf-8
"""Definition of related study property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.RELATED_STUDY
multiple_flag = False
name_ja = "関連研究"
name_en = "Related Study"
mapping = config.DEFAULT_MAPPING
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
    "ISSN",
    "NAID",
    "NCID",
    "PMID",
    "PURL",
    "SCOPUS",
    "URI",
    "WOS",
]
relation_type = [
    None,
    "isVersionOf",
    "isPartOf",
    "references",
    "isFormatOf",
    "hasFormat",
    "isReplacedBy",
    "replaces",
    "isSupplementedBy",
    "isDerivedFrom",
    "isSourceOf",
]


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
            "type": "object",
            "properties": {
                "subitem_related_study_titles": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "subitem_related_study_title": {
                                "format": "text",
                                "title": "関連研究タイトル",
                                "type": "string",
                            },
                            "subitem_related_study_title_language": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_2,
                                "title": "言語",
                            },
                        },
                    },
                    "title": "関連研究タイトル",
                },
                "subitem_related_study_identifiers": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "subitem_related_study_identifier": {
                            "title": "関連研究識別子",
                            "type": "string",
                            "format": "text",
                        },
                        "subitem_related_study_identifier_type": {
                            "type": ["null", "string"],
                            "format": "select",
                            "enum": id_type,
                            "title": "関連研究識別子タイプ",
                        },
                    },
                    "title": "関連研究識別子",
                },
                "subitem_related_study_relation_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": relation_type,
                    "title": "(JPCOAR対応用)関連タイプ",
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
                            "key": "{}.subitem_related_study_titles[].subitem_related_study_title".format(
                                key
                            ),
                            "title": "関連研究タイトル",
                            "title_i18n": {
                                "en": "Related Study Title",
                                "ja": "関連研究タイトル",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_related_study_titles[].subitem_related_study_title_language".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_2),
                            "type": "select",
                        },
                    ],
                    "key": "{}.subitem_related_study_titles".format(key),
                    "style": {"add": "btn-success"},
                    "title": "関連研究タイトル",
                    "title_i18n": {"en": "Related Study Title", "ja": "関連研究タイトル"},
                },
                {
                    "items": [
                        {
                            "key": "{}.subitem_related_study_identifiers.subitem_related_study_identifier".format(
                                key
                            ),
                            "title": "関連研究識別子",
                            "title_i18n": {
                                "en": "Related Study Identifier",
                                "ja": "関連研究識別子",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_related_study_identifiers.subitem_related_study_identifier_type".format(
                                key
                            ),
                            "title": "関連研究識別子タイプ",
                            "title_i18n": {
                                "en": "Related Study Identifier Type",
                                "ja": "関連研究識別子タイプ",
                            },
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_related_study_identifiers".format(key),
                    "type": "fieldset",
                    "title": "関連研究識別子",
                    "title_i18n": {"en": "Related Study Identifier", "ja": "関連研究識別子"},
                },
                {
                    "key": "{}.subitem_related_study_relation_type".format(key),
                    "title": "(JPCOAR対応用)関連タイプ",
                    "title_i18n": {
                        "en": "(for JPCOAR)Relation Type",
                        "ja": "(JPCOAR対応用)関連タイプ",
                    },
                    "type": "text",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
