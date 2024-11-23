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

property_id = config.JPCOAR_HOLDING_AGENT
multiple_flag = False
name_ja = "所蔵機関"
name_en = "Holding Agent"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": "",
    "jpcoar_mapping": {
        "holdingAgent": {
            "holdingAgentName": {
                "@value": "holding_agent_names.holding_agent_name",
                "@attributes": {
                    "xml:lang": "holding_agent_names.holding_agent_name_language"
                },
            },
            "holdingAgentNameIdentifier": {
                "@value": "holding_agent_name_identifier.holding_agent_name_identifier_value",
                "@attributes": {
                    "nameIdentifierScheme": "holding_agent_name_identifier.holding_agent_name_identifier_scheme",
                    "nameIdentifierURI": "holding_agent_name_identifier.holding_agent_name_identifier_uri",
                },
            },
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping":"",
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
            "title": "holding_agent_name",
            "properties": {
                "holding_agent_names": {
                    "type": "array",
                    "format": "array",
                    "title": "所蔵機関名",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "holding_agent_name": {
                                "type": "string",
                                "format": "text",
                                "title": "所蔵機関名",
                                "title_i18n": {
                                    "ja": "所蔵機関名",
                                    "en": "Holding Agent Name",
                                },
                            },
                            "holding_agent_name_language": {
                                "type": "string",
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": config.LANGUAGE_VAL2_1,
                                "title": "Language",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                        },
                    },
                },
                "holding_agent_name_identifier": {
                    "type": "object",
                    "format": "object",
                    "title": "所蔵機関識別子",
                    "properties": {
                        "holding_agent_name_identifier_value": {
                            "type": "string",
                            "format": "text",
                            "title": "所蔵機関識別子",
                            "title_i18n": {
                                "ja": "所蔵機関識別子",
                                "en": "Holding Agent Name Identifier",
                            },
                        },
                        "holding_agent_name_identifier_scheme": {
                            "type": "string",
                            "format": "select",
                            "enum": config.HOLDING_AGENT_NAMEID_SCHEMA_VAL,
                            "currentEnum": config.HOLDING_AGENT_NAMEID_SCHEMA_VAL,
                            "title": "所蔵機関識別子スキーマ",
                            "title_i18n": {
                                "ja": "所蔵機関識別子スキーマ",
                                "en": "Holding Agent Name Identifier Schema",
                            },
                        },
                        "holding_agent_name_identifier_uri": {
                            "type": "string",
                            "format": "text",
                            "title": "所蔵機関識別子URI",
                            "title_i18n": {
                                "ja": "所蔵機関識別子URI",
                                "en": "Holding Agent Name Identifier URI",
                            },
                        },
                    },
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
                    "key": "{}.holding_agent_names".format(key),
                    "items": [
                        {
                            "key": "{}.holding_agent_names[].holding_agent_name".format(
                                key
                            ),
                            "type": "text",
                            "title": "所蔵機関名",
                            "title_i18n": {
                                "ja": "所蔵機関名",
                                "en": "Holding Agent Name",
                            },
                        },
                        {
                            "key": "{}.holding_agent_names[].holding_agent_name_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "Language",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                    ],
                    "style": {"add": "btn-success"},
                    "title": "所蔵機関",
                    "title_i18n": {
                        "ja": "所蔵機関",
                        "en": "Holding Agent",
                    },
                },
                {
                    "key": "{}.holding_agent_name_identifier".format(key),
                    "items": [
                        {
                            "key": "{}.holding_agent_name_identifier.holding_agent_name_identifier_value".format(
                                key
                            ),
                            "type": "text",
                            "title": "所蔵機関識別子",
                            "title_i18n": {
                                "ja": "所蔵機関識別子",
                                "en": "Holding Agent Name Identifier",
                            },
                        },
                        {
                            "key": "{}.holding_agent_name_identifier.holding_agent_name_identifier_scheme".format(
                                key
                            ),
                            "type": "select",
                            "title": "所蔵機関識別子スキーマ",
                            "title_i18n": {
                                "ja": "所蔵機関識別子スキーマ",
                                "en": "Holding Agent Name Identifier Schema",
                            },
                            "titleMap": make_title_map(
                                config.HOLDING_AGENT_NAMEID_SCHEMA_LBL,
                                config.HOLDING_AGENT_NAMEID_SCHEMA_VAL,
                            ),
                        },
                        {
                            "key": "{}.holding_agent_name_identifier.holding_agent_name_identifier_uri".format(
                                key
                            ),
                            "type": "text",
                            "title": "所蔵機関識別子URI",
                            "title_i18n": {
                                "ja": "所蔵機関識別子URI",
                                "en": "Holding Agent Name Identifier URI",
                            },
                        },
                    ],
                    "title": "所蔵機関識別子",
                    "title_i18n": {
                        "ja": "所蔵機関識別子",
                        "en": "Holding Agent Name Identifier",
                    },
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
