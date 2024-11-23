# coding:utf-8
"""Definition of subject property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
    make_title_map,
)
from . import property_config as config

property_id = config.SUBJECT
multiple_flag = True
name_ja = "主題"
name_en = "Subject"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "subject": {
            "@attributes": {
                "subjectScheme": "subitem_subject_scheme",
                "subjectURI": "subitem_subject_uri",
                "xml:lang": "subitem_subject_language",
            },
            "@value": "subitem_subject",
        }
    },
    "jpcoar_mapping": {
        "subject": {
            "@attributes": {
                "subjectScheme": "subitem_subject_scheme",
                "subjectURI": "subitem_subject_uri",
                "xml:lang": "subitem_subject_language",
            },
            "@value": "subitem_subject",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": {"subject": {"@value": "subitem_subject"}},
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
                "subitem_subject": {
                    "format": "text",
                    "title": "主題",
                    "title_i18n": {"en": "Subject", "ja": "主題"},
                    "type": "string",
                },
                "subitem_subject_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": config.LANGUAGE_VAL2_1,
                    "currentEnum": config.LANGUAGE_VAL2_1[1:],
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                },
                "subitem_subject_scheme": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": config.SUBJECT_SCHEME_VAL,
                    "currentEnum": config.SUBJECT_SCHEME_VAL[1:],
                    "title": "主題Scheme",
                    "title_i18n": {"en": "Subject Scheme", "ja": "主題Scheme"},
                },
                "subitem_subject_uri": {
                    "format": "text",
                    "title": "主題URI",
                    "title_i18n": {"en": "Subject URI", "ja": "主題URI"},
                    "type": "string",
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
                    "key": "{}.subitem_subject_language".format(key),
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                    "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_subject_scheme".format(key),
                    "title": "主題Scheme",
                    "title_i18n": {"en": "Subject Scheme", "ja": "主題Scheme"},
                    "titleMap": make_title_map(
                        config.SUBJECT_SCHEME_LBL, config.SUBJECT_SCHEME_VAL
                    ),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_subject".format(key),
                    "title": "主題",
                    "title_i18n": {"en": "Subject", "ja": "主題"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_subject_uri".format(key),
                    "title": "主題URI",
                    "title_i18n": {"en": "Subject URI", "ja": "主題URI"},
                    "type": "text",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
