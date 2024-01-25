# coding:utf-8
"""Definition of time period property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.TIME_PERIOD
multiple_flag = False
name_ja = "開始時点／終了時点"
name_en = "Time Period Event"
mapping = config.DEFAULT_MAPPING
event = [None, "start", "end"]


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
            "system_prop": True,
            "type": "object",
            "properties": {
                "subitem_time_period": {
                    "format": "datetime",
                    "title": "開始時点／終了時点",
                    "type": "string",
                },
                "subitem_time_period_event": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": event,
                    "title": "イベント",
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
                    "key": "{}.subitem_time_period".format(key),
                    "templateUrl": config.DATEPICKER_MULTI_FORMAT_URL,
                    "title": "開始時点／終了時点",
                    "title_i18n": {"ja": "開始時点／終了時点", "en": "Start Time／End Time"},
                    "type": "template",
                },
                {
                    "key": "{}.subitem_time_period_event".format(key),
                    "title": "イベント",
                    "title_i18n": {"en": "Event", "ja": "イベント"},
                    "titleMap": get_select_value(event),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
