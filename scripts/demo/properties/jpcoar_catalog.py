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
multiple_flag = False
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
                "@value": "catalog_rights.catalog_right",
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
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

contributorType = [None, "HostingInstitution"]
identifierType = [None, "DOI", "HDL", "URI"]
description_type = [
    None,
    "Abstract",
    "Methods",
    "TableOfContents",
    "TechnicalInfo",
    "Other",
]
subject_schema = [
    None,
    "BSH",
    "DDC",
    "e-Rad_field",
    "JEL",
    "LCC",
    "LCSH",
    "MeSH",
    "NDC",
    "NDLC",
    "NDLSH",
    "SciVal",
    "UDC",
    "Other",
]

licenseType = [None, "file", "metadata", "thumbnail"]
access_rights = [
    None,
    "embargoed access",
    "metadata only access",
    "open access",
    "restricted access",
]
objectType = [None, "thumbnail"]


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
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": contributorType,
                                "title": "Hosting Institution Type",
                                "title_i18n": {
                                    "ja": "提供機関タイプ",
                                    "en": "Hosting Institution Type",
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
                                            "title": "Hosting Institution Name",
                                            "title_i18n": {
                                                "ja": "提供機関名",
                                                "en": "Hosting Institution Name",
                                            },
                                        },
                                        "contributor_name_language": {
                                            "type": ["null", "string"],
                                            "format": "select",
                                            "enum": config.LANGUAGE_VAL2_1,
                                            "title": "Language",
                                            "title_i18n": {
                                                "ja": "言語",
                                                "en": "Language",
                                            },
                                        },
                                    },
                                },
                                "title": "Hosting Institution Name",
                            },
                        },
                    },
                    "title": "Hosting Institution",
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
                                "enum": identifierType,
                                "title": "Identifier Type",
                                "title_i18n": {
                                    "ja": "識別子タイプ",
                                    "en": "Identifier Type",
                                },
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
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                        },
                    },
                    "title": "Title",
                },
                "catalog_descriptions": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "catalog_description": {
                                "type": "string",
                                "format": "textarea",
                                "title": "Description",
                                "title_i18n": {"ja": "内容記述", "en": "Description"},
                            },
                            "catalog_description_language": {
                                "type": "string",
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                            "catalog_description_type": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": description_type,
                                "title": "Description Type",
                                "title_i18n": {
                                    "ja": "内容記述タイプ",
                                    "en": "Description Type",
                                },
                            },
                        },
                    },
                    "title": "Descriptions",
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
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": subject_schema,
                                "title": "Subject Scheme",
                                "title_i18n": {
                                    "ja": "主題スキーマ",
                                    "en": "Subject Scheme",
                                },
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
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                            "catalog_license_type": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": licenseType,
                                "title": "License Type",
                                "title_i18n": {
                                    "ja": "ライセンスタイプ",
                                    "en": "License Type",
                                },
                            },
                            "catalog_license_rdf_resource": {
                                "type": "string",
                                "format": "text",
                                "title": "RDF Resource",
                                "title_i18n": {
                                    "ja": "RDFリソース",
                                    "en": "RDF Resource",
                                },
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
                            "catalog_right": {
                                "type": "string",
                                "format": "text",
                                "title": "Rights",
                                "title_i18n": {"ja": "権利情報", "en": "Rights"},
                            },
                            "catalog_right_language": {
                                "type": "string",
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                            "catalog_right_rdf_resource": {
                                "type": "string",
                                "format": "text",
                                "title": "RDF Resource",
                                "title_i18n": {
                                    "ja": "RDFリソース",
                                    "en": "RDF Resource",
                                },
                            },
                        },
                    },
                    "title": "Rights",
                },
                "catalog_access_rights": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "system_prop": True,
                        "type": "object",
                        "title": "アクセス権",
                        "properties": {
                            "catalog_access_right": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": access_rights,
                                "currentEnum": access_rights[1:],
                                "title": "アクセス権",
                                "title_i18n": {
                                    "en": "Access Rights",
                                    "ja": "アクセス権",
                                },
                            },
                            "catalog_access_right_rdf_resource": {
                                "format": "text",
                                "title": "アクセス権URI",
                                "title_i18n": {
                                    "en": "Access Rights URI",
                                    "ja": "アクセス権URI",
                                },
                                "type": "string",
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
                            "title": "Thumbnail URI",
                            "title_i18n": {"ja": "代表画像URI", "en": "Thumbnail URI"},
                        },
                        "catalog_file_object_type": {
                            "type": "string",
                            "format": "select",
                            "enum": objectType,
                            "title": "Object Type",
                            "title_i18n": {
                                "ja": "オブジェクトタイプ",
                                "en": "Object Type",
                            },
                        },
                    },
                    "title": "Thumbnail",
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
                    "title": "Hosting Institution",
                    "title_i18n": {"ja": "提供機関", "en": "Hosting Institution"},
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.catalog_contributors[].contributor_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Hosting Institution Type",
                            "title_i18n": {"ja": "提供機関タイプ", "en": "Hosting Institution Type"},
                            "titleMap": get_select_value(contributorType),
                        },
                        {
                            "key": "{}.catalog_contributors[].contributor_names".format(
                                key
                            ),
                            "title": "Hosting Institution Name",
                            "title_i18n": {"ja": "提供機関名", "en": "Hosting Institution Name"},
                            "add": "New",
                            "items": [
                                {
                                    "key": "{}.catalog_contributors[].contributor_names[].contributor_name".format(
                                        key
                                    ),
                                    "type": "text",
                                    "title": "Hosting Institution Name",
                                    "title_i18n": {
                                        "ja": "提供機関名",
                                        "en": "Hosting Institution Name",
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
                    "title_i18n": {"ja": "識別子", "en": "Identifier"},
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.catalog_identifiers[].catalog_identifier_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Identifier Type",
                            "title_i18n": {
                                "ja": "識別子タイプ",
                                "en": "Identifier Type",
                            },
                            "titleMap": get_select_value(identifierType),
                        },
                        {
                            "key": "{}.catalog_identifiers[].catalog_identifier".format(
                                key
                            ),
                            "type": "text",
                            "title": "Identifier",
                            "title_i18n": {"ja": "識別子", "en": "Identifier"},
                        },
                    ],
                    "style": {"add": "btn-success"},
                },
                {
                    "key": "{}.catalog_titles".format(key),
                    "title": "Title",
                    "title_i18n": {"ja": "タイトル", "en": "Title"},
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
                    "title_i18n": {"ja": "内容記述", "en": "Description"},
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_descriptions[].catalog_description_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Description Type",
                            "title_i18n": {
                                "ja": "内容記述タイプ",
                                "en": "Description Type",
                            },
                            "titleMap": get_select_value(description_type),
                        },
                        {
                            "key": "{}.catalog_descriptions[].catalog_description".format(
                                key
                            ),
                            "type": "textarea",
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
                    ],
                },
                {
                    "key": "{}.catalog_subjects".format(key),
                    "title": "Subject",
                    "title_i18n": {"ja": "主題", "en": "Subject"},
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
                            "key": "{}.catalog_subjects[].catalog_subject_scheme".format(
                                key
                            ),
                            "type": "select",
                            "title": "Subject Scheme",
                            "title_i18n": {
                                "ja": "主題スキーマ",
                                "en": "Subject Scheme",
                            },
                            "titleMap": get_select_value(subject_schema),
                        },
                        {
                            "key": "{}.catalog_subjects[].catalog_subject_uri".format(
                                key
                            ),
                            "type": "text",
                            "title": "Subject URI",
                            "title_i18n": {"ja": "主題URI", "en": "Subject URI"},
                        },
                    ],
                },
                {
                    "key": "{}.catalog_licenses".format(key),
                    "title": "License",
                    "title_i18n": {"ja": "ライセンス", "en": "License"},
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
                            "key": "{}.catalog_licenses[].catalog_license_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_licenses[].catalog_license_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "License Type",
                            "title_i18n": {
                                "ja": "ライセンスタイプ",
                                "en": "License Type",
                            },
                            "titleMap": get_select_value(licenseType),
                        },
                        {
                            "key": "{}.catalog_licenses[].catalog_license_rdf_resource".format(
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
                    "title_i18n": {"ja": "アクセス権", "en": "Access Rights"},
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_rights[].catalog_right".format(key),
                            "type": "text",
                            "title": "Rights",
                            "title_i18n": {"ja": "権利情報", "en": "Rights"},
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
                    "title_i18n": {"ja": "アクセス権", "en": "Access Rights"},
                    "add": "New",
                    "style": {"add": "btn-success"},
                    "items": [
                        {
                            "key": "{}.catalog_access_rights[].catalog_access_right".format(key),
                            "onChange": "changedAccessRights(this, modelValue)",
                            "title": "アクセス権",
                            "title_i18n": {"en": "Access Rights", "ja": "アクセス権"},
                            "titleMap": get_select_value(access_rights),
                            "type": "select",
                        },
                        {
                            "fieldHtmlClass": "txt-access-rights-uri",
                            "key": "{}.catalog_access_rights[].catalog_access_right_rdf_resource".format(key),
                            "readonly": True,
                            "title": "アクセス権URI",
                            "title_i18n": {
                                "en": "Access Rights URI",
                                "ja": "アクセス権URI",
                            },
                            "type": "text",
                        },
                    ],
                },
                {
                    "key": "{}.catalog_file".format(key),
                    "type": "fieldset",
                    "title": "Thumbnail",
                    "title_i18n": {"ja": "代表画像", "en": "Thumbnail"},
                    "items": [
                        {
                            "key": "{}.catalog_file.catalog_file_uri".format(key),
                            "type": "text",
                            "title": "Thumbnail URI",
                            "title_i18n": {"ja": "代表画像URI", "en": "Thumbnail URI"},
                        },
                        {
                            "key": "{}.catalog_file.catalog_file_object_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Object Type",
                            "title_i18n": {
                                "ja": "オブジェクトタイプ",
                                "en": "Object Type",
                            },
                            "titleMap": get_select_value(objectType),
                        },
                    ],
                },
            ],
            "key": key.replace("[]", ""),
            "title": "カタログ",
            "title_i18n": {"en": "", "ja": "カタログ"},
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
