# coding:utf-8
"""Definition of bibliographic info property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.BIBLIO_INFO
multiple_flag = False
name_ja = "書誌情報"
name_en = "Bibliographic Information"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "issue": {"@value": "bibliographicIssueNumber"},
        "pageEnd": {"@value": "bibliographicPageEnd"},
        "pageStart": {"@value": "bibliographicPageStart"},
        "sourceTitle": {
            "@attributes": {"xml:lang": "bibliographic_titles.bibliographic_titleLang"},
            "@value": "bibliographic_titles.bibliographic_title",
        },
        "volume": {"@value": "bibliographicVolumeNumber"},
        "numPages": {"@value": "bibliographicNumberOfPages"},
        "date": {
            "@attributes": {
                "dateType": "bibliographicIssueDates.bibliographicIssueDateType"
            },
            "@value": "bibliographicIssueDates.bibliographicIssueDate",
        },
    },
    "jpcoar_mapping": {
        "issue": {"@value": "bibliographicIssueNumber"},
        "pageEnd": {"@value": "bibliographicPageEnd"},
        "pageStart": {"@value": "bibliographicPageStart"},
        "sourceTitle": {
            "@attributes": {"xml:lang": "bibliographic_titles.bibliographic_titleLang"},
            "@value": "bibliographic_titles.bibliographic_title",
        },
        "volume": {"@value": "bibliographicVolumeNumber"},
        "numPages": {"@value": "bibliographicNumberOfPages"},
        "date": {
            "@attributes": {
                "dateType": "bibliographicIssueDates.bibliographicIssueDateType"
            },
            "@value": "bibliographicIssueDates.bibliographicIssueDate",
        },
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}
date_type = [None, "", "Issued"]


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
            "system_prop": True,
            "type": "object",
            "title": "bibliographic_information",
            "properties": {
                "bibliographic_titles": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "bibliographic_titleLang": {
                                "editAble": True,
                                "type": ["null", "string"],
                                "format": "select",
                                "enum": config.LANGUAGE_VAL2_1,
                                "title": "言語",
                            },
                            "bibliographic_title": {
                                "format": "text",
                                "title": "タイトル",
                                "type": "string",
                            },
                        },
                    },
                    "title": "雑誌名",
                },
                "bibliographicPageEnd": {
                    "format": "text",
                    "title": "終了ページ",
                    "type": "string",
                },
                "bibliographicIssueNumber": {
                    "format": "text",
                    "title": "号",
                    "type": "string",
                },
                "bibliographicPageStart": {
                    "format": "text",
                    "title": "開始ページ",
                    "type": "string",
                },
                "bibliographicVolumeNumber": {
                    "format": "text",
                    "title": "巻",
                    "type": "string",
                },
                "bibliographicNumberOfPages": {
                    "format": "text",
                    "title": "ページ数",
                    "type": "string",
                },
                "bibliographicIssueDates": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "bibliographicIssueDate": {
                            "format": "datetime",
                            "title": "日付",
                            "type": "string",
                        },
                        "bibliographicIssueDateType": {
                            "type": ["null", "string"],
                            "format": "select",
                            "currentEnum": date_type,
                            "enum": date_type,
                            "title": "日付タイプ",
                        },
                    },
                    "title": "発行日",
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
                            "key": "{}.bibliographic_titles[].bibliographic_title".format(
                                key
                            ),
                            "title": "タイトル",
                            "title_i18n": {"en": "Title", "ja": "タイトル"},
                            "type": "text",
                        },
                        {
                            "key": "{}.bibliographic_titles[].bibliographic_titleLang".format(
                                key
                            ),
                            "title": "言語",
                            "title_i18n": {"en": "Language", "ja": "言語"},
                            "titleMap": get_select_value(config.LANGUAGE_VAL2_1),
                            "type": "select",
                        },
                    ],
                    "key": "{}.bibliographic_titles".format(key),
                    "style": {"add": "btn-success"},
                    "title": "雑誌名",
                    "title_i18n": {"en": "Journal Title", "ja": "雑誌名"},
                },
                {
                    "key": "{}.bibliographicVolumeNumber".format(key),
                    "title": "巻",
                    "title_i18n": {"en": "Volume Number", "ja": "巻"},
                    "type": "text",
                },
                {
                    "key": "{}.bibliographicIssueNumber".format(key),
                    "title": "号",
                    "title_i18n": {"en": "Issue Number", "ja": "号"},
                    "type": "text",
                },
                {
                    "key": "{}.bibliographicPageStart".format(key),
                    "title": "開始ページ",
                    "title_i18n": {"en": "Page Start", "ja": "開始ページ"},
                    "type": "text",
                },
                {
                    "key": "{}.bibliographicPageEnd".format(key),
                    "title": "終了ページ",
                    "title_i18n": {"en": "Page End", "ja": "終了ページ"},
                    "type": "text",
                },
                {
                    "key": "{}.bibliographicNumberOfPages".format(key),
                    "title": "ページ数",
                    "title_i18n": {"en": "Number of Page", "ja": "ページ数"},
                    "type": "text",
                },
                {
                    "items": [
                        {
                            "key": "{}.bibliographicIssueDates.bibliographicIssueDate".format(
                                key
                            ),
                            "title": "日付",
                            "title_i18n": {"en": "Date", "ja": "日付"},
                            "type": "template",
                            "format": "yyyy-MM-dd",
                            "templateUrl": config.DATEPICKER_MULTI_FORMAT_URL,
                        },
                        {
                            "key": "{}.bibliographicIssueDates.bibliographicIssueDateType".format(
                                key
                            ),
                            "title": "日付タイプ",
                            "title_i18n": {"en": "Date Type", "ja": "日付タイプ"},
                            "titleMap": get_select_value(date_type),
                            "type": "select",
                        },
                    ],
                    "key": "{}.bibliographicIssueDates".format(key),
                    "type": "fieldset",
                    "title": "発行日",
                    "title_i18n": {"en": "Issue Date", "ja": "発行日"},
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
