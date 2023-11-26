# coding:utf-8
"""Definition of wf issued date property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.WF_ISSUED_DATE
multiple_flag = False
name_ja = "WF起票日"
name_en = "WF Issued Date"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "date": {
            "@attributes": {
                "dateType": "subitem_restricted_access_wf_issued_date_type"
            },
            "@value": "subitem_restricted_access_wf_issued_date",
        }
    },
    "jpcoar_mapping": {
        "date": {
            "@attributes": {
                "dateType": "subitem_restricted_access_wf_issued_date_type"
            },
            "@value": "subitem_restricted_access_wf_issued_date",
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

date_type = ["Created"]


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
            "properties": {
                "subitem_restricted_access_wf_issued_date": {
                    "format": "datetime",
                    "title": "WF起票日",
                    "type": "string",
                },
                "subitem_restricted_access_wf_issued_date_type": {
                    "type": "string",
                    "format": "select",
                    "enum": date_type,
                    "title": "WF起票日タイプ",
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
                    "format": "yyyy-MM-dd",
                    "key": "{}.subitem_restricted_access_wf_issued_date".format(key),
                    "templateUrl": config.DATEPICKER_MULTI_FORMAT_URL,
                    "title": "WF起票日",
                    "title_i18n": {"ja": "WF起票日", "en": "WF Issued Date"},
                    "type": "template",
                },
                {
                    "key": "{}.subitem_restricted_access_wf_issued_date_type".format(
                        key
                    ),
                    "title": "WF起票日タイプ",
                    "title_i18n": {"ja": "WF起票日タイプ", "en": "WF Issued Date Type"},
                    "titleMap": get_select_value(date_type),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
