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


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop("option")
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop("mapping", True):
        post_data["table_row_map"]["mapping"][key] = {
            "display_lang_type": "",
            "jpcoar_v1_mapping": {},
            "jpcoar_mapping": {
                "publisher": {
                    "@attributes": {"xml:lang": "publisher_language"},
                    "@value": "publisher",
                }
            },
            "junii2_mapping": "",
            "lido_mapping": "",
            "lom_mapping": "",
            "oai_dc_mapping": {"publisher": {"@value": "publisher"}},
            "spase_mapping": "",
        }
    else:
        post_data["table_row_map"]["mapping"][key] = config.DEFAULT_MAPPING


def schema(title="", multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        """Schema text."""
        _d = {
            "type": "object",
            "format": "object",
            'title':'catalog',
            "properties": {
                "catalog_contributor": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "contributor_type": {
                            "type": "string",
                            "format": "select",
                            "enum": ["HostingInstitution"],
                            "currentEnum": ["HostingInstitution"],
                            "title": "Contributor Type",
                            "title_i18n": {"ja": "提供機関", "en": "Contributor Type"},
                        },
                        "contributor_name": {
                            "type": "array",
                            "format": "array",
                            "items":{
                            "properties": {
                                "contributor_name_contributor_name": {
                                    "type": "string",
                                    "format": "text",
                                    "title": "Contributor Name",
                                    "title_i18n": {"ja": "提供機関名", "en": "Contributor Name"},
                                },
                                "contributor_name_language": {
                                    "type": "string",
                                    "format": "select",
                                    "enum": config.LANGUAGE_VAL2_1,
                                    "currentEnum": config.LANGUAGE_VAL2_1,
                                    "title": "Language",
                                    "title_i18n": {"ja": "言語", "en": "Language"},
                                },
                            },},
                            "title": "Contributor Name",
                        },
                    },
                    "title": "Contributor",
                },
                "catalog_identifier": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_identifier_identifier": {
                            "type": "string",
                            "format": "text",
                            "title": "Identifier",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_identifier_type": {
                            "type": "string",
                            "format": "select",
                            "enum": ["DOI", "HDL", "URI"],
                            "currentEnum": ["DOI", "HDL", "URI"],
                            "title": "Identifier Type",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                    },
                    "title": "Identifier",
                },
                "catalog_title": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_title_title": {
                            "type": "string",
                            "format": "text",
                            "title": "Title",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_title_language": {
                            "type": "string",
                            "format": "select",
                            "enum": config.LANGUAGE_VAL2_1,
                            "currentEnum": config.LANGUAGE_VAL2_1,
                            "title": "Language",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                    },
                    "title": "Title",
                },
                "catalog_description": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_description_description": {
                            "type": "string",
                            "format": "text",
                            "title": "Description",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_description_language": {
                            "type": "string",
                            "format": "select",
                            "enum": config.LANGUAGE_VAL2_1,
                            "currentEnum": config.LANGUAGE_VAL2_1,
                            "title": "Language",
                            "title_i18n": {"ja": "", "en": ""},
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
                            "title_i18n": {"ja": "", "en": ""},
                        },
                    },
                    "title": "Description",
                },
                "catalog_subject": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_subject_subject": {
                            "type": "string",
                            "format": "text",
                            "title": "Subject",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_subject_language": {
                            "type": "string",
                            "format": "select",
                            "enum": config.LANGUAGE_VAL2_1,
                            "currentEnum": config.LANGUAGE_VAL2_1,
                            "title": "Language",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_subject_uri": {
                            "type": "string",
                            "format": "text",
                            "title": "Subject URI",
                            "title_i18n": {"ja": "", "en": ""},
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
                            "title_i18n": {"ja": "", "en": ""},
                        },
                    },
                    "title": "Subject",
                },
                "catalog_license": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_license_license": {
                            "type": "string",
                            "format": "text",
                            "title": "License",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_license_language": {
                            "type": "string",
                            "format": "select",
                            "enum": config.LANGUAGE_VAL2_1,
                            "currentEnum": config.LANGUAGE_VAL2_1,
                            "title": "Language",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_license_type": {
                            "type": "string",
                            "format": "select",
                            "enum": ["file", "metadata", "thumbnail"],
                            "currentEnum": ["file", "metadata", "thumbnail"],
                            "title": "License Type",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_license_rdf_resource": {
                            "type": "string",
                            "format": "text",
                            "title": "RDF Resource",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                    },
                    "title": "License",
                },
                "catalog_rights": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_rights_rights": {
                            "type": "string",
                            "format": "text",
                            "title": "Rights",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_rights_language": {
                            "type": "string",
                            "format": "select",
                            "enum": config.LANGUAGE_VAL2_1,
                            "currentEnum": config.LANGUAGE_VAL2_1,
                            "title": "Language",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_rights_rdf_resource": {
                            "type": "string",
                            "format": "text",
                            "title": "RDF Resource",
                            "title_i18n": {"ja": "", "en": ""},
                        },
                    },
                    "title": "Rights",
                },
                "catalog_access_rights": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "catalog_access_rights_access_rights": {
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
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_access_rights_rdf_resource": {
                            "type": "string",
                            "format": "text",
                            "title": "RDF Resource",
                            "title_i18n": {"ja": "", "en": ""},
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
                            "title_i18n": {"ja": "", "en": ""},
                        },
                        "catalog_file_object_type": {
                            "type": "string",
                            "format": "select",
                            "enum": ["thumbnail"],
                            "currentEnum": ["thumbnail"],
                            "title": "Object Type",
                            "title_i18n": {"ja": "", "en": ""},
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
                    "key": "{}.catalog_contributor".format(key),
                    "type": "fieldset",
                    "title": "Contributor",
                    "items": [
                        {
                            "key": "{}.catalog_contributor.contributor_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Contributor Type",
                            "titleMap": [
                                {
                                    "value": "HostingInstitution",
                                    "name": "HostingInstitution",
                                }
                            ],
                        },
                        {
                            "key": "{}.catalog_contributor.contributor_name".format(
                                key
                            ),
                            "type": "fieldset",
                            "title": "Contributor Name",
                            "items": [
                                {
                                    "key": "{}.catalog_contributor.contributor_name.contributor_name_contributor_name".format(
                                        key
                                    ),
                                    "type": "text",
                                    "title": "Contributor Name",
                                },
                                {
                                    "key": "{}.catalog_contributor.contributor_name.contributor_name_language".format(
                                        key
                                    ),
                                    "type": "select",
                                    "title": "Language",
                                    "titleMap": get_select_value(
                                        config.LANGUAGE_VAL2_1
                                    ),
                                },
                            ],
                        },
                    ],
                },
                {
                    "key": "{}.catalog_identifier".format(key),
                    "type": "fieldset",
                    "title": "Identifier",
                    "items": [
                        {
                            "key": "{}.catalog_identifier.catalog_identifier_identifier".format(
                                key
                            ),
                            "type": "text",
                            "title": "Identifier",
                        },
                        {
                            "key": "{}.catalog_identifier.catalog_identifier_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Identifier Type",
                            "titleMap": [
                                {"value": "DOI", "name": "DOI"},
                                {"value": "HDL", "name": "HDL"},
                                {"value": "URI", "name": "URI"},
                            ],
                        },
                    ],
                },
                {
                    "key": "{}.catalog_title".format(key),
                    "type": "fieldset",
                    "title": "Title",
                    "items": [
                        {
                            "key": "{}.catalog_title.catalog_title_title".format(
                                key
                            ),
                            "type": "text",
                            "title": "Title",
                        },
                        {
                            "key": "{}.catalog_title.catalog_title_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                    ],
                },
                {
                    "key": "{}.catalog_description".format(key),
                    "type": "fieldset",
                    "title": "Description",
                    "items": [
                        {
                            "key": "{}.catalog_description.catalog_description_description".format(
                                key
                            ),
                            "type": "text",
                            "title": "Description",
                        },
                        {
                            "key": "{}.catalog_description.catalog_description_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_description.catalog_description_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Description Type",
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
                    "key": "{}.catalog_subject".format(key),
                    "type": "fieldset",
                    "title": "Subject",
                    "items": [
                        {
                            "key": "{}.catalog_subject.catalog_subject_subject".format(
                                key
                            ),
                            "type": "text",
                            "title": "Subject",
                        },
                        {
                            "key": "{}.catalog_subject.catalog_subject_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_subject.catalog_subject_uri".format(
                                key
                            ),
                            "type": "text",
                            "title": "Subject URI",
                        },
                        {
                            "key": "{}.catalog_subject.catalog_subject_scheme".format(
                                key
                            ),
                            "type": "select",
                            "title": "Subject Scheme",
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
                    "key": "{}.catalog_license".format(key),
                    "type": "fieldset",
                    "title": "License",
                    "items": [
                        {
                            "key": "{}.catalog_license.catalog_license_license".format(
                                key
                            ),
                            "type": "text",
                            "title": "License",
                        },
                        {
                            "key": "{}.catalog_license.catalog_license_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_license.catalog_license_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "License Type",
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
                        },
                    ],
                },
                {
                    "key": "{}.catalog_rights".format(key),
                    "type": "fieldset",
                    "title": "Rights",
                    "items": [
                        {
                            "key": "{}.catalog_rights.catalog_rights_rights".format(
                                key
                            ),
                            "type": "text",
                            "title": "Rights",
                        },
                        {
                            "key": "{}.catalog_rights.catalog_rights_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                        {
                            "key": "{}.catalog_rights.catalog_rights_rdf_resource".format(
                                key
                            ),
                            "type": "text",
                            "title": "RDF Resource",
                        },
                    ],
                },
                {
                    "key": "{}.catalog_access_rights".format(key),
                    "type": "fieldset",
                    "title": "Access Rights",
                    "items": [
                        {
                            "key": "{}.catalog_access_rights.catalog_access_rights_access_rights".format(
                                key
                            ),
                            "type": "select",
                            "title": "Access Rights",
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
                            "key": "{}.catalog_access_rights.catalog_access_rights_rdf_resource".format(
                                key
                            ),
                            "type": "text",
                            "title": "RDF Resource",
                        },
                    ],
                },
                {
                    "key": "{}.catalog_file".format(key),
                    "type": "fieldset",
                    "title": "File",
                    "items": [
                        {
                            "key": "{}.catalog_file.catalog_file_uri".format(
                                key
                            ),
                            "type": "text",
                            "title": "File URI",
                        },
                        {
                            "key": "{}.catalog_file.catalog_file_object_type".format(
                                key
                            ),
                            "type": "select",
                            "title": "Object Type",
                            "titleMap": [{"value": "thumbnail", "name": "thumbnail"}],
                        },
                    ],
                },
            ],
            "key": key.replace("[]", ""),
           
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
