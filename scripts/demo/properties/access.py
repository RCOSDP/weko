# coding:utf-8
"""Definition of access property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.ACCESS
multiple_flag = False
name_ja = "アクセス制限（日本語統制語彙）"
name_en = "Access J"
mapping = config.DEFAULT_MAPPING
access = [None, "オープンアクセス", "制約付きアクセス ", "メタデータのみ", "エンバーゴ期間中"]
lnag = [
    None,
    "ja"
]


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
                "subitem_access": {
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": access,
                    "title": "アクセス制限（日本語統制語彙）",
                },
                "subitem_access_language": {
                    "editAble": True,
                    "type": ["null", "string"],
                    "format": "select",
                    "enum": lnag,
                    "title": "言語",
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
                    "key": "{}.subitem_access".format(key),
                    "title": "アクセス制限（日本語統制語彙）",
                    "title_i18n": {"en": "Access J", "ja": "アクセス制限（日本語統制語彙）"},
                    "titleMap": get_select_value(access),
                    "type": "select",
                },
                {
                    "key": "{}.subitem_access_language".format(key),
                    "title": "言語",
                    "title_i18n": {"en": "Language", "ja": "言語"},
                    "titleMap": get_select_value(lnag),
                    "type": "select",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
