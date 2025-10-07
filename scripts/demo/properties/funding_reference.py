# coding:utf-8
"""Definition of funding reference property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
    make_title_map,
)
from . import property_config as config

property_id = config.FUNDING_REFERENCE
multiple_flag = True
name_ja = "助成情報"
name_en = "Funder"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "fundingReference": {
            "funderIdentifier": {
                "@attributes": {
                    "funderIdentifierType": "subitem_funder_identifiers.subitem_funder_identifier_type"
                },
                "@value": "subitem_funder_identifiers.subitem_funder_identifier",
            },
            "funderName": {
                "@attributes": {
                    "xml:lang": "subitem_funder_names.subitem_funder_name_language"
                },
                "@value": "subitem_funder_names.subitem_funder_name",
            },
            "awardNumber": {
                "@attributes": {
                    "awardURI": "subitem_award_numbers.subitem_award_uri",
                },
                "@value": "subitem_award_numbers.subitem_award_number",
            },
            "awardTitle": {
                "@attributes": {
                    "xml:lang": "subitem_award_titles.subitem_award_title_language"
                },
                "@value": "subitem_award_titles.subitem_award_title",
            },
        }
    },
    "jpcoar_mapping": {
        "fundingReference": {
            "funderIdentifier": {
                "@attributes": {
                    "funderIdentifierType": "subitem_funder_identifiers.subitem_funder_identifier_type",
                    "funderIdentifierTypeURI": "subitem_funder_identifiers.subitem_funder_identifier_type_uri",
                },
                "@value": "subitem_funder_identifiers.subitem_funder_identifier",
            },
            "funderName": {
                "@attributes": {
                    "xml:lang": "subitem_funder_names.subitem_funder_name_language"
                },
                "@value": "subitem_funder_names.subitem_funder_name",
            },
            "fundingStreamIdentifier": {
                "@attributes": {
                    "fundingStreamIdentifierType": "subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type",
                    "fundingStreamIdentifierTypeURI": "subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type_uri",
                },
                "@value": "subitem_funding_stream_identifiers.subitem_funding_stream_identifier",
            },
            "fundingStream": {
                "@attributes": {
                    "xml:lang": "subitem_funding_streams.subitem_funding_stream_language"
                },
                "@value": "subitem_funding_streams.subitem_funding_stream",
            },
            "awardNumber": {
                "@attributes": {
                    "awardURI": "subitem_award_numbers.subitem_award_uri",
                    "awardNumberType": "subitem_award_numbers.subitem_award_number_type",
                },
                "@value": "subitem_award_numbers.subitem_award_number",
            },
            "awardTitle": {
                "@attributes": {
                    "xml:lang": "subitem_award_titles.subitem_award_title_language"
                },
                "@value": "subitem_award_titles.subitem_award_title",
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
            "type": "object",
            "properties": {
                "subitem_funder_identifiers": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "subitem_funder_identifier_type": {
                            "type": ["null", "string"],
                            "format": "select",
                            "enum": config.FUNDER_IDENTIFIER_TYPE_VAL,
                            "title": "助成機関識別子タイプ",
                        },
                        "subitem_funder_identifier_type_uri": {
                            "format": "text",
                            "title": "助成機関識別子タイプURI",
                            "type": "string",
                        },
                        "subitem_funder_identifier": {
                            "format": "text",
                            "title": "助成機関識別子",
                            "type": "string",
                        },
                        "subitem_funder_identifier_type_uri": {
                            "format": "text",
                            "title": "助成機関識別子URI",
                            "type": "string",
                        },
                    },
                    "title": "助成機関識別子",
                },
                "subitem_funder_names": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "subitem_funder_name": {
                                "format": "text",
                                "title": "助成機関名",
                                "type": "string",
                            },
                            "subitem_funder_name_language": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                        },
                    },
                    "title": "助成機関名",
                },
                "subitem_funding_stream_identifiers": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "subitem_funding_stream_identifier_type": {
                            "type": ["null", "string"],
                            "format": "select",
                            "enum": config.FUNDING_STREAM_IDENTIFIER_TYPE,
                            "title": "プログラム情報識別子タイプ",
                        },
                        "subitem_funding_stream_identifier_type_uri": {
                            "format": "text",
                            "title": "プログラム情報識別子タイプURI",
                            "type": "string",
                        },
                        "subitem_funding_stream_identifier": {
                            "format": "text",
                            "title": "プログラム情報識別子",
                            "type": "string",
                        },
                    },
                    "title": "プログラム情報識別子",
                },
                "subitem_funding_streams": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "subitem_funding_stream": {
                                "format": "text",
                                "title": "プログラム情報",
                                "type": "string",
                            },
                            "subitem_funding_stream_language": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                        },
                    },
                    "title": "プログラム情報",
                },
                "subitem_award_numbers": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "subitem_award_uri": {
                            "format": "text",
                            "type": "string",
                            "title": "研究課題番号URI",
                        },
                        "subitem_award_number": {
                            "format": "text",
                            "title": "研究課題番号",
                            "type": "string",
                        },
                        "subitem_award_number_type": {
                            "type": ["null", "string"],
                            "format": "select",
                            "enum": config.AWARD_NUMBER_TYPE,
                            "title": "研究課題番号タイプ",
                        },
                    },
                    "title": "研究課題番号",
                },
                "subitem_award_titles": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "subitem_award_title": {
                                "format": "text",
                                "title": "研究課題名",
                                "type": "string",
                            },
                            "subitem_award_title_language": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                        },
                    },
                    "title": "研究課題名",
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
                    "items": [
                        {
                            "key": "{}.subitem_funder_identifiers.subitem_funder_identifier_type".format(
                                key
                            ),
                            "title": "助成機関識別子タイプ",
                            "title_i18n": {
                                "en": "Funder Identifier Type",
                                "ja": "助成機関識別子タイプ",
                            },
                            "titleMap": make_title_map(
                                config.FUNDER_IDENTIFIER_TYPE_LBL,
                                config.FUNDER_IDENTIFIER_TYPE_VAL,
                            ),
                            "type": "select",
                        },
                        {
                            "key": "{}.subitem_funder_identifiers.subitem_funder_identifier".format(
                                key
                            ),
                            "title": "助成機関識別子",
                            "title_i18n": {
                                "en": "Funder Identifier",
                                "ja": "助成機関識別子",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_funder_identifiers.subitem_funder_identifier_type_uri".format(
                                key
                            ),
                            "title": "助成機関識別子タイプURI",
                            "title_i18n": {
                                "en": "Funder Identifier Type URI",
                                "ja": "助成機関識別子タイプURI",
                            },
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_funder_identifiers".format(key),
                    "type": "fieldset",
                    "title": "助成機関識別子",
                    "title_i18n": {"en": "Funder Identifier", "ja": "助成機関識別子"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.subitem_funder_names[].subitem_funder_name".format(
                                key
                            ),
                            "title": "助成機関名",
                            "title_i18n": {"en": "Funder Name", "ja": "助成機関名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_funder_names[].subitem_funder_name_language".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.subitem_funder_names".format(key),
                    "style": {"add": "btn-success"},
                    "title": "助成機関名",
                    "title_i18n": {"en": "Funder Name", "ja": "助成機関名"},
                },
                {
                    "items": [
                        {
                            "key": "{}.subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type".format(
                                key
                            ),
                            "title": "プログラム情報識別子タイプ",
                            "title_i18n": {
                                "en": "Funding Stream Identifier Type",
                                "ja": "プログラム情報識別子タイプ",
                            },
                            "titleMap": get_select_value(
                                config.FUNDING_STREAM_IDENTIFIER_TYPE
                            ),
                            "type": "select",
                        },
                        {
                            "key": "{}.subitem_funding_stream_identifiers.subitem_funding_stream_identifier".format(
                                key
                            ),
                            "title": "研究課題番号タイプ",
                            "title_i18n": {
                                "en": "Funding Stream Identifier",
                                "ja": "研究課題番号タイプ",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type_uri".format(
                                key
                            ),
                            "title": "プログラム情報識別子タイプURI",
                            "title_i18n": {
                                "en": "Funding Stream Identifier Type URI",
                                "ja": "プログラム情報識別子タイプURI",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_funding_stream_identifiers.subitem_funding_stream_identifier".format(
                                key
                            ),
                            "title": "プログラム情報識別子",
                            "title_i18n": {
                                "en": "Funding Stream Identifier",
                                "ja": "プログラム情報識別子",
                            },
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_funding_stream_identifiers".format(key),
                    "title": "プログラム情報識別子",
                    "title_i18n": {
                        "en": "Funding Stream Identifiers",
                        "ja": "プログラム情報識別子",
                    },
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.subitem_funding_streams[].subitem_funding_stream_language".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                        {
                            "key": "{}.subitem_funding_streams[].subitem_funding_stream".format(
                                key
                            ),
                            "title": "プログラム情報",
                            "title_i18n": {
                                "en": "Funding Stream",
                                "ja": "プログラム情報",
                            },
                            "type": "text",
                        }
                    ],
                    "key": "{}.subitem_funding_streams".format(key),
                    "style": {"add": "btn-success"},
                    "title": "プログラム情報",
                    "title_i18n": {"en": "Funding Streams", "ja": "プログラム情報"},
                },
                {
                    "items": [
                        {
                            "key": "{}.subitem_award_numbers.subitem_award_number_type".format(
                                key
                            ),
                            "title": "研究課題番号タイプ",
                            "title_i18n": {
                                "en": "Award Number Type",
                                "ja": "研究課題番号タイプ",
                            },
                            "titleMap": get_select_value(config.AWARD_NUMBER_TYPE),
                            "type": "select",
                        },
                        {
                            "key": "{}.subitem_award_numbers.subitem_award_number".format(
                                key
                            ),
                            "title": "研究課題番号",
                            "title_i18n": {"en": "Award Number", "ja": "研究課題番号"},
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_award_numbers.subitem_award_uri".format(
                                key
                            ),
                            "title": "研究課題番号URI",
                            "title_i18n": {
                                "en": "Award Number URI",
                                "ja": "研究課題番号URI",
                            },
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_award_numbers".format(key),
                    "title": "研究課題番号",
                    "title_i18n": {"en": "Award Number", "ja": "研究課題番号"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.subitem_award_titles[].subitem_award_title".format(
                                key
                            ),
                            "title": "研究課題名",
                            "title_i18n": {"en": "Award Title", "ja": "研究課題名"},
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_award_titles[].subitem_award_title_language".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.subitem_award_titles".format(key),
                    "style": {"add": "btn-success"},
                    "title": "研究課題名",
                    "title_i18n": {"en": "Award Title", "ja": "研究課題名"},
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
