# coding:utf-8
"""Definition of degree grantor property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.DEGREE_GRANTOR
multiple_flag = True
name_ja = "学位授与機関"
name_en = "Degree Grantor"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "degreeGrantor": {
            "degreeGrantorName": {
                "@attributes": {
                    "xml:lang": "subitem_degreegrantor."
                    "subitem_degreegrantor_language"
                },
                "@value": "subitem_degreegrantor.subitem_degreegrantor_name",
            },
            "nameIdentifier": {
                "@attributes": {
                    "nameIdentifierScheme": "subitem_degreegrantor_identifier."
                    "subitem_degreegrantor_identifier_scheme"
                },
                "@value": "subitem_degreegrantor_identifier."
                "subitem_degreegrantor_identifier_name",
            },
        }
    },
    "jpcoar_mapping": {
        "degreeGrantor": {
            "degreeGrantorName": {
                "@attributes": {
                    "xml:lang": "subitem_degreegrantor."
                    "subitem_degreegrantor_language"
                },
                "@value": "subitem_degreegrantor.subitem_degreegrantor_name",
            },
            "nameIdentifier": {
                "@attributes": {
                    "nameIdentifierScheme": "subitem_degreegrantor_identifier."
                    "subitem_degreegrantor_identifier_scheme"
                },
                "@value": "subitem_degreegrantor_identifier."
                "subitem_degreegrantor_identifier_name",
            },
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {
        "description": {"@value": "subitem_degreegrantor.subitem_degreegrantor_name"}
    },
    "spase_mapping": "",
}
id_scheme = [None, "kakenhi"]


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
                "subitem_degreegrantor": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "subitem_degreegrantor_name": {
                                "format": "text",
                                "title": "学位授与機関名",
                                "type": "string",
                            },
                            "subitem_degreegrantor_language": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                        },
                    },
                    "title": "学位授与機関名",
                },
                "subitem_degreegrantor_identifier": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "subitem_degreegrantor_identifier_name": {
                                "format": "text",
                                "title": "学位授与機関識別子",
                                "type": "string",
                            },
                            "subitem_degreegrantor_identifier_scheme": {
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": id_scheme,
                                "title": "学位授与機関識別子Scheme",
                            },
                        },
                    },
                    "title": "学位授与機関識別子",
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
                            "key": "{}.subitem_degreegrantor_identifier[].subitem_degreegrantor_identifier_scheme".format(
                                key
                            ),
                            "title": "学位授与機関識別子Scheme",
                            "title_i18n": {
                                "en": "Degree Grantor Name Identifier Scheme",
                                "ja": "学位授与機関識別子Scheme",
                            },
                            "titleMap": get_select_value(id_scheme),
                            "type": "select",
                        },
                        {
                            "key": "{}.subitem_degreegrantor_identifier[].subitem_degreegrantor_identifier_name".format(
                                key
                            ),
                            "title": "学位授与機関識別子",
                            "title_i18n": {
                                "en": "Degree Grantor Name Identifier",
                                "ja": "学位授与機関識別子",
                            },
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_degreegrantor_identifier".format(key),
                    "title": "学位授与機関識別子",
                    "title_i18n": {
                        "en": "Degree Grantor Name Identifier",
                        "ja": "学位授与機関識別子",
                    },
                    "style": {"add": "btn-success"},
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.subitem_degreegrantor[].subitem_degreegrantor_name".format(
                                key
                            ),
                            "title": "学位授与機関名",
                            "title_i18n": {
                                "en": "Degree Grantor Name",
                                "ja": "学位授与機関名",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_degreegrantor[].subitem_degreegrantor_language".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.subitem_degreegrantor".format(key),
                    "style": {"add": "btn-success"},
                    "title": "学位授与機関名",
                    "title_i18n": {"en": "Degree Grantor Name", "ja": "学位授与機関名"},
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
