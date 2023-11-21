# coding:utf-8
"""Definition of collection method property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.COLLECTION_METHOD
multiple_flag = False
name_ja = "調査方法（英語統制語彙）"
name_en = "Collection Method E"
mapping = config.DEFAULT_MAPPING
col_method = [
    None,
    "Interview",
    "Face-to-face interview",
    "Face-to-face interview: Computer-assisted (CAPI/CAMI)",
    "Face-to-face interview: Paper-and-pencil (PAPI)",
    "Telephone interview",
    "Telephone interview: Computer-assisted (CATI)",
    "E-mail interview",
    "Web-based interview",
    "Self-administered questionnaire",
    "Self-administered questionnaire: E-mail",
    "Self-administered questionnaire: Paper",
    "Self-administered questionnaire: Messaging (SMS/MMS)",
    "Self-administered questionnaire: Web-based (CAWI)",
    "Self-administered questionnaire: Computer-assisted (CASI)",
    "Focus group",
    "Face-to-face focus group",
    "Telephone focus group",
    "Online focus group",
    "Self-administered writings and/or diaries",
    "Self-administered writings and/or diaries: E-mail",
    "Self-administered writings and/or diaries: Paper",
    "Self-administered writings and/or diaries: Web-based",
    "Observation",
    "Field observation",
    "Participant field observation",
    "Non-participant field observation",
    "Laboratory observation",
    "Participant laboratory observation",
    "Non-participant laboratory observation",
    "Computer-based observation",
    "Experiment",
    "Laboratory experiment",
    "Field/Intervention experiment",
    "Web-based experiment",
    "Recording",
    "Content coding",
    "Transcription",
    "Compilation/Synthesis",
    "Summary",
    "Aggregation",
    "Simulation",
    "Measurements and tests",
    "Educational measurements and tests",
    "Physical measurements and tests",
    "Psychological measurements and tests",
    "Other",
]
lnag = [None, "en"]
description_type = [None, "Methods"]


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
                "subitem_collection_method": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": col_method,
                    "title": "調査方法（英語統制語彙）",
                },
                "subitem_collection_method_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": lnag,
                    "title": "言語",
                },
                "subitem_collection_method_description_type": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": description_type,
                    "title": "(JPCOAR対応用)記述タイプ",
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
                    "key": "{}.subitem_collection_method".format(key),
                    "title": "調査方法（英語統制語彙）",
                    "title_i18n": {"en": "Collection Method E", "ja": "調査方法（英語統制語彙）"},
                    "titleMap": get_select_value(col_method),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_collection_method_language".format(key),
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                    "titleMap": get_select_value(lnag),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_collection_method_description_type".format(key),
                    "title": "(JPCOAR対応用)記述タイプ",
                    "title_i18n": {
                        "en": "(for JPCOAR)Description Type",
                        "ja": "(JPCOAR対応用)記述タイプ",
                    },
                    "titleMap": get_select_value(description_type),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
