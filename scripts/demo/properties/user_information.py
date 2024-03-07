# coding:utf-8
"""Definition of user information property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.USER_INFORMATION
multiple_flag = False
name_ja = "登録者情報"
name_en = "User Information"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "creator": {
            "affiliation": {
                "affiliationName": {"@value": "subitem_university/institution"}
            },
            "creatorName": {"@value": "subitem_fullname"},
        }
    },
    "jpcoar_mapping": {
        "creator": {
            "affiliation": {
                "affiliationName": {"@value": "subitem_university/institution"}
            },
            "creatorName": {"@value": "subitem_fullname"},
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
            "system_prop": True,
            "type": "object",
            "properties": {
                "subitem_affiliated_division/department": {
                    "title": "所属部局・部署",
                    "type": "string",
                    "format": "text",
                },
                "subitem_affiliated_institution": {
                    "type": "array",
                    "format": "array",
                    "items": {
                        "type": "object",
                        "format": "object",
                        "properties": {
                            "subitem_affiliated_institution_name": {
                                "format": "text",
                                "title": "学会名",
                                "type": "string",
                            },
                            "subitem_affiliated_institution_position": {
                                "format": "text",
                                "title": "学会役職",
                                "type": "string",
                            },
                        },
                    },
                    "title": "所属学会",
                },
                "subitem_fullname": {
                    "title": "氏名",
                    "type": "string",
                    "format": "text",
                },
                "subitem_mail_address": {
                    "title": "メールアドレス",
                    "type": "string",
                    "format": "text",
                    "pattern": "^\\S+@\\S+$",
                },
                "subitem_phone_number": {
                    "title": "電話番号",
                    "type": "string",
                    "format": "text",
                    "pattern": "\\d+",
                },
                "subitem_position": {
                    "title": "役職",
                    "type": "string",
                    "format": "text",
                },
                "subitem_position(others)": {
                    "title": "役職（その他）",
                    "type": "string",
                    "format": "text",
                },
                "subitem_university/institution": {
                    "title": "大学・機関",
                    "type": "string",
                    "format": "text",
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
                    "key": "{}.subitem_affiliated_division/department".format(key),
                    "title": "所属部局・部署",
                    "title_i18n": {
                        "en": "Affiliated Division/Department",
                        "ja": "所属部局・部署",
                    },
                    "type": "text",
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.subitem_affiliated_institution[].subitem_affiliated_institution_name".format(
                                key
                            ),
                            "title": "学会名",
                            "title_i18n": {
                                "en": "Affiliated Institution Name",
                                "ja": "学会名",
                            },
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_affiliated_institution[].subitem_affiliated_institution_position".format(
                                key
                            ),
                            "title": "学会役職",
                            "title_i18n": {"en": "Institution Position", "ja": "学会役職"},
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_affiliated_institution".format(key),
                    "style": {"add": "btn-success"},
                    "title": "所属学会",
                    "title_i18n": {"en": "Affiliated Institution", "ja": "所属学会"},
                },
                {
                    "key": "{}.subitem_fullname".format(key),
                    "title": "氏名",
                    "title_i18n": {"en": "Full name", "ja": "氏名"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_mail_address".format(key),
                    "title": "メールアドレス",
                    "title_i18n": {"en": "Mail Address", "ja": "メールアドレス"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_phone_number".format(key),
                    "title": "電話番号",
                    "title_i18n": {"en": "Phone number", "ja": "電話番号"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_position".format(key),
                    "title": "役職",
                    "title_i18n": {"en": "Position", "ja": "役職"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_position(others)".format(key),
                    "title": "役職（その他）",
                    "title_i18n": {"en": "Position(Others)", "ja": "役職（その他）"},
                    "type": "text",
                },
                {
                    "key": "{}.subitem_university/institution".format(key),
                    "title": "大学・機関",
                    "title_i18n": {"en": "University/Institution", "ja": "大学・機関"},
                    "type": "text",
                },
            ],
            "key": key.replace("[]", ""),
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
