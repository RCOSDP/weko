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

property_id = config.JPCOAR_CATALOG
multiple_flag = True
name_ja = "カタログ"
name_en = "Catalog"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": "",
    "jpcoar_mapping": {
        "catalog": {
            "accessRights": {
                "@value": "catalog_access_rights.catalog_access_right",
                "@attributes": {
                    "rdf:resource": "catalog_access_rights.catalog_access_right_rdf_resource"
                },
            },
            "contributor": {
                "contributorName": {
                    "@value": "catalog_contributors.contributor_names.contributor_name",
                    "@attributes": {
                        "xml:lang": "catalog_contributors.contributor_names.contributor_name_language"
                    },
                },
                "@attributes": {
                    "contributorType": "catalog_contributors.contributor_type"
                },
            },
            "description": {
                "@value": "catalog_descriptions.catalog_description",
                "@attributes": {
                    "xml:lang": "catalog_descriptions.catalog_description_language",
                    "descriptionType": "catalog_descriptions.catalog_description_type",
                },
            },
            "file": {
                "URI": {
                    "@attributes": {
                        "objectType": "catalog_file.catalog_file_object_type"
                    },
                    "@value": "catalog_file.catalog_file_uri",
                }
            },
            "identifier": {
                "@value": "catalog_identifiers.catalog_identifier",
                "@attributes": {
                    "identifierType": "catalog_identifiers.catalog_identifier_type"
                },
            },
            "license": {
                "@value": "catalog_licenses.catalog_license",
                "@attributes": {
                    "xml:lang": "catalog_licenses.catalog_license_language",
                    "rdf:resource": "catalog_licenses.catalog_license_rdf_resource",
                    "licenseType": "catalog_licenses.catalog_license_type",
                },
            },
            "rights": {
                "@attributes": {
                    "xml:lang": "catalog_rights.catalog_right_language",
                    "rdf:resource": "catalog_rights.catalog_right_rdf_resource",
                },
                "@value": "catalog_rights.catalog_rights_right",
            },
            "subject": {
                "@value": "catalog_subjects.catalog_subject",
                "@attributes": {
                    "xml:lang": "catalog_subjects.catalog_subject_language",
                    "subjectScheme": "catalog_subjects.catalog_subject_scheme",
                    "subjectURI": "catalog_subjects.catalog_subject_uri",
                },
            },
            "title": {
                "@value": "catalog_titles.catalog_title",
                "@attributes": {"xml:lang": "catalog_titles.catalog_title_language"},
            },
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"publisher": {"@value": "publisher"}},
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
            "title": "catalog",
            "properties": {
                "catalog_contributors": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "contributor_type": {
                                "type": "string",
                                "format": "select",
                                "enum": ["HostingInstitution"],
                                "currentEnum": ["HostingInstitution"],
                                "title": "Contributor Type",
                                "title_i18n": {
                                    "ja": "提供機関タイプ",
                                    "en": "Contributor Type",
                                },
                            },
                            "contributor_names": {
                                "type": "array",
                                "format": "array",
                                "items": {
                                    "type": "object",
                                    "format": "object",
                                    "properties": {
                                        "contributor_name": {
                                            "type": "string",
                                            "format": "text",
                                            "title": "Contributor Name",
                                            "title_i18n": {
                                                "ja": "提供機関名",
                                                "en": "Contributor Name",
                                            },
                                        },
                                        "contributor_name_language": {
                                            "type": ["null", "string"],
                                            "format": "select",
                                            "enum": config.LANGUAGE_VAL2_1,
                                            "currentEnum": config.LANGUAGE_VAL2_1,
                                            "title": "Language",
                                            "title_i18n": {
                                                "ja": "言語",
                                                "en": "Language",
                                            },
                                        },
                                    },
                                },
                                "title": "Contributor Name",
                            },
                        },
                    },
                    "title": "Contributor",
                },
                "catalog_identifiers": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "catalog_identifier": {
                                "type": "string",
                                "format": "text",
                                "title": "Identifier",
                                "title_i18n": {"ja": "識別子", "en": "Identifier"},
                            },
                            "catalog_identifier_type": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": ["DOI", "HDL", "URI"],
                                "currentEnum": ["DOI", "HDL", "URI"],
                                "title": "Identifier Type",
                                "title_i18n": {"ja": "識別子タイプ", "en": "Identifier Type"},
                            },
                        },
                    },
                    "title": "Identifier",
                },
                "catalog_titles": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "catalog_title": {
                                "type": "string",
                                "format": "text",
                                "title": "Title",
                                "title_i18n": {"ja": "タイトル", "en": "Title"},
                            },
                            "catalog_title_language": {
                                "type": "string",
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": config.LANGUAGE_VAL2_1,
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                        },
                    },
                    "title": "Title",
                },
                "catalog_descriptions": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_description": {
                            "type": "string",
                            "format": "text",
                            "title": "Description",
                            "title_i18n": {"ja": "内容記述", "en": "Description"},
                        },
                        "catalog_description_language": {
                            "type": "string",
                            "format": "select",
                            "enum": config.LANGUAGE_VAL2_1,
                            "currentEnum": config.LANGUAGE_VAL2_1,
                            "title": "Language",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                        },
                        "catalog_description_type": {
                            "type": "string",
                            "format": "select",
                            "enum": [
                                "Abstract",
                                "Methods",
                                "TableOfContents",
                                "TechnicalInfo",
                                "Other",
                            ],
                            "currentEnum": [
                                "Abstract",
                                "Methods",
                                "TableOfContents",
                                "TechnicalInfo",
                                "Other",
                            ],
                            "title": "Description Type",
                            "title_i18n": {"ja": "内容記述タイプ", "en": "Description Type"},
                        },
                    },
                    "title": "Description",
                },
                "catalog_subjects": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "catalog_subject": {
                                "type": "string",
                                "format": "text",
                                "title": "Subject",
                                "title_i18n": {"ja": "主題", "en": "Subject"},
                            },
                            "catalog_subject_language": {
                                "type": "string",
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": config.LANGUAGE_VAL2_1,
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                            "catalog_subject_uri": {
                                "type": "string",
                                "format": "text",
                                "title": "Subject URI",
                                "title_i18n": {"ja": "主題URI", "en": "Subject URI"},
                            },
                            "catalog_subject_scheme": {
                                "type": "string",
                                "format": "select",
                                "enum": [
                                    "BSH",
                                    "DDC",
                                    "e-Rad",
                                    "LCC",
                                    "LCSH",
                                    "MeSH",
                                    "NDC",
                                    "NDLC",
                                    "NDLSH",
                                    "SciVal",
                                    "UDC",
                                    "Other",
                                ],
                                "currentEnum": [
                                    "BSH",
                                    "DDC",
                                    "e-Rad",
                                    "LCC",
                                    "LCSH",
                                    "MeSH",
                                    "NDC",
                                    "NDLC",
                                    "NDLSH",
                                    "SciVal",
                                    "UDC",
                                    "Other",
                                ],
                                "title": "Subject Scheme",
                                "title_i18n": {"ja": "主題スキーマ", "en": "Subject Scheme"},
                            },
                        },
                    },
                    "title": "Subject",
                },
                "catalog_licenses": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "catalog_license": {
                                "type": "string",
                                "format": "text",
                                "title": "License",
                                "title_i18n": {"ja": "ライセンス", "en": "License"},
                            },
                            "catalog_license_language": {
                                "type": "string",
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": config.LANGUAGE_VAL2_1,
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                            "catalog_license_type": {
                                "type": "string",
                                "format": "select",
                                "enum": ["file", "metadata", "thumbnail"],
                                "currentEnum": ["file", "metadata", "thumbnail"],
                                "title": "License Type",
                                "title_i18n": {"ja": "ライセンスタイプ", "en": "License Type"},
                            },
                            "catalog_license_rdf_resource": {
                                "type": "string",
                                "format": "text",
                                "title": "RDF Resource",
                                "title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"},
                            },
                        },
                    },
                    "title": "License",
                },
                "catalog_rights": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "catalog_rights_right": {
                                "type": "string",
                                "format": "text",
                                "title": "Rights",
                                "title_i18n": {"ja": "権利情報", "en": "Rights"},
                            },
                            "catalog_right_language": {
                                "type": "string",
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": config.LANGUAGE_VAL2_1,
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                            "catalog_right_rdf_resource": {
                                "type": "string",
                                "format": "text",
                                "title": "RDF Resource",
                                "title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"},
                            },
                        },
                    },
                    "title": "Rights",
                },
                "catalog_access_rights": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "catalog_access_right": {
                                "type": "string",
                                "format": "select",
                                "enum": [
                                    "embargoed access",
                                    "metadata only access",
                                    "restricted access",
                                    "open access",
                                ],
                                "currentEnum": [
                                    "embargoed access",
                                    "metadata only access",
                                    "restricted access",
                                    "open access",
                                ],
                                "title": "Access Rights",
                                "title_i18n": {"ja": "アクセス権", "en": "Access Rights"},
                            },
                            "catalog_access_right_rdf_resource": {
                                "type": "string",
                                "format": "text",
                                "title": "RDF Resource",
                                "title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"},
                            },
                        },
                    },
                    "title": "Access Rights",
                },
                "catalog_file": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_file_uri": {
                            "type": "string",
                            "format": "text",
                            "title": "File URI",
                            "title_i18n": {"ja": "ファイルURI", "en": "File URI"},
                        },
                        "catalog_file_object_type": {
                            "type": "string",
                            "format": "select",
                            "enum": ["thumbnail"],
                            "currentEnum": ["thumbnail"],
                            "title": "Object Type",
                            "title_i18n": {"ja": "オブジェクトタイプ", "en": "Object Type"},
                        },
                    },
                    "title": "File",
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
                    "key": "{}.catalog_contributors".format(key),
                    "title": "Contributor",
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.catalog_contributors[].contributor_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Contributor Type",
                            "title_i18n": {"ja": "提供機関タイプ", "en": "Contributor Type"},
                            "titleMap": [
                                {
                                    "value": "HostingInstitution",
                                    "name": "HostingInstitution",
                                }
                            ],
                        },
                        {
                            "key": "{}.catalog_contributors[].contributor_names".format(
                                key
                            ),
                            "title": "Contributor Name",
                            "add": "New",
                            "items": [
                                {
                                    "key": "{}.catalog_contributors[].contributor_names[].contributor_name".format(
                                        key
                                    ),
                                    "type": "text",
                                    "title": "Contributor Name",
                                    "title_i18n": {
                                        "ja": "提供機関名",
                                        "en": "Contributor Name",
                                    },
                                },
                                {
                                    "key": "{}.catalog_contributors[].contributor_names[].contributor_name_language".format(
                                        key
                                    ),
                                    "type": "select",
                                    "title": "Language",
                                    "title_i18n": {"ja": "言語", "en": "Language"},
                                    "titleMap": get_select_value(
                                        config.LANGUAGE_VAL2_1
                                    ),
                                },
                            ],
                            "style": {"add": "btn-success"},
                        },
                    ],
                    "style": {"add": "btn-success"},
                },
                {
                    "key": "{}.catalog_identifiers".format(key),
                    "title": "Identifier",
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.catalog_identifiers[].catalog_identifier".format(
                                key
                            ),
                            "type": "text",
                            "title": "Identifier",
                            "title_i18n": {"ja": "識別子", "en": "Identifier"},
                        },
                        {
                            "key": "{}.catalog_identifiers[].catalog_identifier_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Identifier Type",
                            "title_i18n": {"ja": "識別子タイプ", "en": "Identifier Type"},
                            "titleMap": [
                                {"value": "DOI", "name": "DOI"},
                                {"value": "HDL", "name": "HDL"},
                                {"value": "URI", "name": "URI"},
                            ],
                        },
                    ],
                    "style": {"add": "btn-success"},
                },
                {
                    "key": "{}.catalog_titles".format(key),
                    "title": "Title",
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_titles[].catalog_title".format(key),
                            "type": "text",
                            "title": "Title",
                            "title_i18n": {"ja": "タイトル", "en": "Title"},
                        },
                        {
                            "key": "{}.catalog_titles[].catalog_title_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                    ],
                },
                {
                    "key": "{}.catalog_descriptions".format(key),
                    "title": "Description",
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_descriptions[].catalog_description".format(
                                key
                            ),
                            "type": "text",
                            "title": "Description",
                            "title_i18n": {"ja": "内容記述", "en": "Description"},
                        },
                        {
                            "key": "{}.catalog_descriptions[].catalog_description_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_descriptions[].catalog_description_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Description Type",
                            "title_i18n": {"ja": "内容記述タイプ", "en": "Description Type"},
                            "titleMap": [
                                {"value": "Abstract", "name": "Abstract"},
                                {"value": "Methods", "name": "Methods"},
                                {"value": "TableOfContents", "name": "TableOfContents"},
                                {"value": "TechnicalInfo", "name": "TechnicalInfo"},
                                {"value": "Other", "name": "Other"},
                            ],
                        },
                    ],
                },
                {
                    "key": "{}.catalog_subjects".format(key),
                    "title": "Subject",
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_subjects[].catalog_subject".format(key),
                            "type": "text",
                            "title": "Subject",
                            "title_i18n": {"ja": "主題", "en": "Subject"},
                        },
                        {
                            "key": "{}.catalog_subjects[].catalog_subject_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_subjects[].catalog_subject_uri".format(
                                key
                            ),
                            "type": "text",
                            "title": "Subject URI",
                            "title_i18n": {"ja": "主題URI", "en": "Subject URI"},
                        },
                        {
                            "key": "{}.catalog_subjects[].catalog_subject_scheme".format(
                                key
                            ),
                            "type": "select",
                            "title": "Subject Scheme",
                            "title_i18n": {"ja": "主題スキーマ", "en": "Subject Scheme"},
                            "titleMap": [
                                {"value": "BSH", "name": "BSH"},
                                {"value": "DDC", "name": "DDC"},
                                {"value": "e-Rad", "name": "e-Rad"},
                                {"value": "LCC", "name": "LCC"},
                                {"value": "LCSH", "name": "LCSH"},
                                {"value": "", "name": ""},
                                {"value": "MeSH", "name": "MeSH"},
                                {"value": "NDC", "name": "NDC"},
                                {"value": "NDLC", "name": "NDLC"},
                                {"value": "NDLSH", "name": "NDLSH"},
                                {"value": "SciVal", "name": "SciVal"},
                                {"value": "UDC", "name": "UDC"},
                                {"value": "Other", "name": "Other"},
                            ],
                        },
                    ],
                },
                {
                    "key": "{}.catalog_licenses".format(key),
                    "title": "License",
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_licenses[].catalog_license".format(key),
                            "type": "text",
                            "title": "License",
                            "title_i18n": {"ja": "ライセンス", "en": "License"},
                        },
                        {
                            "key": "{}.catalog_license.catalog_license_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_license.catalog_license_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "License Type",
                            "title_i18n": {"ja": "ライセンスタイプ", "en": "License Type"},
                            "titleMap": [
                                {"value": "file", "name": "file"},
                                {"value": "metadata", "name": "metadata"},
                                {"value": "thumbnail", "name": "thumbnail"},
                            ],
                        },
                        {
                            "key": "{}.catalog_license.catalog_license_rdf_resource".format(
                                key
                            ),
                            "type": "text",
                            "title": "RDF Resource",
                            "title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"},
                        },
                    ],
                },
                {
                    "key": "{}.catalog_rights".format(key),
                    "title": "Rights",
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_rights[].catalog_right".format(key),
                            "type": "text",
                            "title": "Rights",
                            "title_i18n": {"ja": "アクセス権", "en": "Access Rights"},
                        },
                        {
                            "key": "{}.catalog_rights[].catalog_right_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_rights[].catalog_right_rdf_resource".format(
                                key
                            ),
                            "type": "text",
                            "title": "RDF Resource",
                            "title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"},
                        },
                    ],
                },
                {
                    "key": "{}.catalog_access_rights".format(key),
                    "title": "Access Rights",
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_access_rights[].catalog_access_right_access_rights".format(
                                key
                            ),
                            "type": "select",
                            "title": "Access Rights",
                            "title_i18n": {"ja": "アクセス権", "en": "Access Rights"},
                            "titleMap": [
                                {
                                    "value": "embargoed access",
                                    "name": "embargoed access",
                                },
                                {
                                    "value": "metadata only access",
                                    "name": "metadata only access",
                                },
                                {
                                    "value": "restricted access",
                                    "name": "restricted access",
                                },
                                {"value": "open access", "name": "open access"},
                            ],
                        },
                        {
                            "key": "{}.catalog_access_rights[].catalog_access_right_rdf_resource".format(
                                key
                            ),
                            "type": "text",
                            "title": "RDF Resource",
                            "title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"},
                        },
                    ],
                },
                {
                    "key": "{}.catalog_file".format(key),
                    "type": "fieldset",
                    "title": "File",
                    "items": [
                        {
                            "key": "{}.catalog_file.catalog_file_uri".format(key),
                            "type": "text",
                            "title": "File URI",
                            "title_i18n": {"ja": "ファイルURI", "en": "File URI"},
                        },
                        {
                            "key": "{}.catalog_file.catalog_file_object_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Object Type",
                            "title_i18n": {"ja": "オブジェクトタイプ", "en": "Object Type"},
                            "titleMap": [{"value": "thumbnail", "name": "thumbnail"}],
                        },
                    ],
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
