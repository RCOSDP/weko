# coding:utf-8
"""Definition of system file property."""
from .property_func import (
    get_property_schema,
    get_property_form,
    set_post_data,
    get_select_value,
)
from . import property_config as config

property_id = config.S_FILE
multiple_flag = False
name = name_ja = name_en = "S_File"
mapping = {
    "display_lang_type": "",
    "jpcoar_v1_mapping": {
        "system_file": {
            "URI": {
                "@value": "subitem_systemfile_filename_uri",
                "@attributes": {
                    "label": "subitem_systemfile_filename_label",
                    "objectType": "subitem_systemfile_filename_type",
                },
            },
            "date": {
                "@value": "subitem_systemfile_datetime_date",
                "@attributes": {"dateType": "subitem_systemfile_datetime_type"},
            },
            "extent": {"@value": "subitem_systemfile_size"},
            "version": {"@value": "subitem_systemfile_version"},
            "mimeType": {"@value": "subitem_systemfile_mimetype"},
        }
    },
    "jpcoar_mapping": {
        "system_file": {
            "URI": {
                "@value": "subitem_systemfile_filename_uri",
                "@attributes": {
                    "label": "subitem_systemfile_filename_label",
                    "objectType": "subitem_systemfile_filename_type",
                },
            },
            "date": {
                "@value": "subitem_systemfile_datetime_date",
                "@attributes": {"dateType": "subitem_systemfile_datetime_type"},
            },
            "extent": {"@value": "subitem_systemfile_size"},
            "version": {"@value": "subitem_systemfile_version"},
            "mimeType": {"@value": "subitem_systemfile_mimetype"},
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}
date_type = [
    "Accepted",
    "Available",
    "Collected",
    "Copyrighted",
    "Created",
    "Issued",
    "Submitted",
    "Updated",
    "Valid",
]
filename_type = ["Abstract", "Fulltext", "Summary", "Thumbnail", "Other"]


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = {
        "crtf": False,
        "hidden": True,
        "oneline": False,
        "multiple": False,
        "required": False,
        "showlist": False,
    }
    kwargs["sys_property"] = True
    set_post_data(post_data, property_id, name, key, option, form, schema, **kwargs)

    post_data["table_row_map"]["mapping"][key] = mapping


def schema(title="", multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        """Schema text."""
        _d = {
            "format": "object",
            "properties": {
                "subitem_systemfile_datetime": {
                    "format": "array",
                    "items": {
                        "format": "object",
                        "properties": {
                            "subitem_systemfile_datetime_date": {
                                "format": "datetime",
                                "title": "SYSTEMFILE DateTime Date",
                                "type": "string",
                            },
                            "subitem_systemfile_datetime_type": {
                                "enum": [
                                    "Accepted",
                                    "Available",
                                    "Collected",
                                    "Copyrighted",
                                    "Created",
                                    "Issued",
                                    "Submitted",
                                    "Updated",
                                    "Valid",
                                ],
                                "format": "select",
                                "title": "SYSTEMFILE DateTime Type",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                    "title": "SYSTEMFILE DateTime",
                    "type": "array",
                },
                "subitem_systemfile_filename": {
                    "format": "array",
                    "items": {
                        "format": "object",
                        "properties": {
                            "subitem_systemfile_filename_label": {
                                "format": "text",
                                "title": "SYSTEMFILE Filename Label",
                                "type": "string",
                            },
                            "subitem_systemfile_filename_type": {
                                "enum": [
                                    "Abstract",
                                    "Fulltext",
                                    "Summary",
                                    "Thumbnail",
                                    "Other",
                                ],
                                "format": "select",
                                "title": "SYSTEMFILE Filename Type",
                                "type": "string",
                            },
                            "subitem_systemfile_filename_uri": {
                                "format": "text",
                                "title": "SYSTEMFILE Filename URI",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                    "title": "SYSTEMFILE Filename",
                    "type": "array",
                },
                "subitem_systemfile_mimetype": {
                    "format": "text",
                    "title": "SYSTEMFILE MimeType",
                    "type": "string",
                },
                "subitem_systemfile_size": {
                    "format": "text",
                    "title": "SYSTEMFILE Size",
                    "type": "string",
                },
                "subitem_systemfile_version": {
                    "format": "text",
                    "title": "SYSTEMFILE Version",
                    "type": "string",
                },
            },
            "system_prop": True,
            "title": "File Information",
            "type": "object",
        }
        return _d

    return get_property_schema(title, _schema, multi_flag)


def form(key="", title="", title_ja="", title_en="", multi_flag=multiple_flag):
    """Get form text of item type."""

    def _form(key):
        """Form text."""
        _d = {
            "items": [
                {
                    "add": "New",
                    "items": [
                        {
                            "key": "{}.subitem_systemfile_filename[].subitem_systemfile_filename_label".format(key),
                            "title": "SYSTEMFILE Filename Label",
                            "type": "text",
                        },
                        {
                            "key": "{}.subitem_systemfile_filename[].subitem_systemfile_filename_type".format(key),
                            "title": "SYSTEMFILE Filename Type",
                            "titleMap": [
                                {"name": "Abstract", "value": "Abstract"},
                                {"name": "Fulltext", "value": "Fulltext"},
                                {"name": "Summary", "value": "Summary"},
                                {"name": "Thumbnail", "value": "Thumbnail"},
                                {"name": "Other", "value": "Other"},
                            ],
                            "type": "select",
                        },
                        {
                            "key": "{}.subitem_systemfile_filename[].subitem_systemfile_filename_uri".format(key),
                            "title": "SYSTEMFILE Filename URI",
                            "type": "text",
                        },
                    ],
                    "key": "{}.subitem_systemfile_filename".format(key),
                    "style": {"add": "btn-success"},
                    "title": "SYSTEMFILE Filename",
                },
                {
                    "key": "{}.subitem_systemfile_mimetype".format(key),
                    "title": "SYSTEMFILE MimeType",
                    "type": "text",
                },
                {
                    "key": "{}.subitem_systemfile_size".format(key),
                    "title": "SYSTEMFILE Size",
                    "type": "text",
                },
                {
                    "add": "New",
                    "items": [
                        {
                            "format": "yyyy-MM-dd",
                            "key": "{}.subitem_systemfile_datetime[].subitem_systemfile_datetime_date".format(key),
                            "templateUrl": "/static/templates/weko_deposit/datepicker.html",
                            "title": "SYSTEMFILE DateTime Date",
                            "type": "template",
                        },
                        {
                            "key": "{}.subitem_systemfile_datetime[].subitem_systemfile_datetime_type".format(key),
                            "title": "SYSTEMFILE DateTime Type",
                            "titleMap": [
                                {"name": "Accepted", "value": "Accepted"},
                                {"name": "Available", "value": "Available"},
                                {"name": "Collected", "value": "Collected"},
                                {"name": "Copyrighted", "value": "Copyrighted"},
                                {"name": "Created", "value": "Created"},
                                {"name": "Issued", "value": "Issued"},
                                {"name": "Submitted", "value": "Submitted"},
                                {"name": "Updated", "value": "Updated"},
                                {"name": "Valid", "value": "Valid"},
                            ],
                            "type": "select",
                        },
                    ],
                    "key": "{}.subitem_systemfile_datetime".format(key),
                    "style": {"add": "btn-success"},
                    "title": "SYSTEMFILE DateTime",
                },
                {
                    "key": "{}.subitem_systemfile_version".format(key),
                    "title": "SYSTEMFILE Version",
                    "type": "text",
                },
            ],
            "key": key.replace("[]", ""),
            "title": "File Information",
            "title_i18n": {"en": "File Information", "ja": "ファイル情報"},
            "type": "fieldset",
        }

        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
