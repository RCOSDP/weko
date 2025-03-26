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

property_id = config.PUBLISHERINFO
multiple_flag = True
name_ja = "出版者情報"
name_en = "Publisher Information"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": "",
    "jpcoar_mapping": {
        "publisher_jpcoar": {
            "publisherDescription": {
                "@value": "publisher_descriptions.publisher_description",
                "@attributes": {
                    "xml:lang": "publisher_descriptions.publisher_description_language"
                },
            },
            "location": {"@value": "publisher_locations.publisher_location"},
            "publicationPlace": {"@value": "publication_places.publication_place"},
            "publisherName": {
                "@value": "publisher_names.publisher_name",
                "@attributes": {"xml:lang": "publisher_names.publisher_name_language"},
            },
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"publisher": {"@value": "subitem_publisher"}},
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
            "title": "publisher_information",
            "properties": {
                "publisher_names": {
                    "type": "array",
                    "format": "array",
                    "title": "出版者名",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "publisher_name": {
                                "type": "string",
                                "format": "text",
                                "title": "出版者名",
                                "title_i18n": {"ja": "出版者名", "en": "Publisher Name"},
                            },
                            "publisher_name_language": {
                                "type": "string",
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                        },
                    },
                },
                "publisher_descriptions": {
                    "type": "array",
                    "format": "array",
                    "title": "出版者注記",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "publisher_description": {
                                "type": "string",
                                "format": "text",
                                "title": "出版者注記",
                                "title_i18n": {
                                    "ja": "出版者注記",
                                    "en": "Publisher Description",
                                },
                            },
                            "publisher_description_language": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "currentEnum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                                "title_i18n": {"ja": "言語", "en": "Language"},
                            },
                        },
                    },
                },
                "publisher_locations": {
                    "type": "array",
                    "format": "array",
                    "title": "出版地",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "publisher_location": {
                                "type": "string",
                                "format": "text",
                                "title": "出版地",
                                "title_i18n": {"ja": "出版地", "en": "Publication Place"},
                            }
                        },
                    },
                },
                "publication_places": {
                    "type": "array",
                    "format": "array",
                    "title": "出版地（国名コード）",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "publication_place": {
                                "type": "string",
                                "format": "text",
                                "title": "出版地（国名コード）",
                                "title_i18n": {
                                    "ja": "出版地（国名コード）",
                                    "en": "Publication Place (Country code)",
                                },
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
                    "key": "{}.publisher_names".format(key),
                    "title": "出版者名",
                    "title_i18n": {"ja": "出版者名", "en": "Publisher Name"},
                    "items": [
                        {
                            "key": "{}.publisher_names[].publisher_name".format(key),
                            "type": "text",
                            "title": "出版者名",
                            "title_i18n": {"ja": "出版者名", "en": "Publisher Name"},
                        },
                        {
                            "key": "{}.publisher_names[].publisher_name_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "言語",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                    ],
                    "style": {"add": "btn-success"},
                },
                {
                    "add": "New",
                    "key": "{}.publisher_descriptions".format(key),
                    "title": "Publisher Description",
                    "title_i18n": {
                        "ja": "出版者注記",
                        "en": "Publisher Description",
                    },
                    "items": [
                        {
                            "key": "{}.publisher_descriptions[].publisher_description".format(
                                key
                            ),
                            "type": "text",
                            "title": "出版者注記",
                            "title_i18n": {
                                "ja": "出版者注記",
                                "en": "Publisher Description",
                            },
                        },
                        {
                            "key": "{}.publisher_descriptions[].publisher_description_language".format(
                                key
                            ),
                            "type": "select",
                            "title": "言語",
                            "title_i18n": {"ja": "言語", "en": "Language"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                        },
                    ],
                    "style": {"add": "btn-success"},
                },
                {
                    "add": "New",
                    "key": "{}.publisher_locations".format(key),
                    "title": "出版地",
                    "title_i18n": {"ja": "出版地", "en": "Publication Place"},
                    "items": [
                        {
                            "key": "{}.publisher_locations[].publisher_location".format(
                                key
                            ),
                            "type": "text",
                            "title": "出版地",
                            "title_i18n": {"ja": "出版地", "en": "Publication Place"},
                        }
                    ],
                    "style": {"add": "btn-success"},
                },
                {
                    "add": "New",
                    "key": "{}.publication_places".format(key),
                    "title": "出版地（国名コード）",
                    "title_i18n": {
                        "ja": "出版地（国名コード）",
                        "en": "Publication Place (Country code)",
                    },
                    "items": [
                        {
                            "key": "{}.publication_places[].publication_place".format(
                                key
                            ),
                            "type": "text",
                            "title": "出版地（国名コード）",
                            "title_i18n": {
                                "ja": "出版地（国名コード）",
                                "en": "Publication Place (Country code)",
                            },
                        }
                    ],
                    "style": {"add": "btn-success"},
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
