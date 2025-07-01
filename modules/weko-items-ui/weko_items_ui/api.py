# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

"""API for item login."""

from flask import current_app, json, session, url_for
from weko_authors.utils import update_data_for_weko_link
from weko_records.api import ItemTypes
from weko_records.utils import find_items
from weko_workflow.api import WorkActivity

from .utils import is_schema_include_key


def item_login(item_type_id: int = 0):
    """Return information that item register need.

    Args:
        item_type_id (int, optional): Item type ID.. Defaults to 0.

    Returns:
        _type_: _description_
    """
    activity_id = None
    allow_multi_thumbnail = False
    endpoints = {}
    files = []
    files_thumbnail = []
    item_save_uri = url_for("weko_items_ui.iframe_save_model")
    json_schema = ""
    need_billing_file = False
    need_file = False
    need_thumbnail = False
    record = {}
    schema_form = ""
    template_url = "weko_items_ui/iframe/item_edit.html"
    cris_linkage = {"researchmap" : False}
    try:
        item_type = (
            ItemTypes.get_by_id(item_type_id)
            if ItemTypes.get_by_id(item_type_id)
            else "weko_items_ui/iframe/error.html"
        )
        json_schema = "/items/jsonschema/{}".format(item_type_id)
        schema_form = "/items/schemaform/{}".format(item_type_id)

        if session.get("activity_info"):
            activity_id = session["activity_info"].get("activity_id")
        if activity_id:
            activity = WorkActivity()
            metadata = activity.get_activity_metadata(activity_id)
            if metadata:
                item_json = json.loads(metadata)
                if "metainfo" in item_json:
                    record = item_json.get("metainfo")
                if "files" in item_json:
                    files = item_json.get("files")
                    files_thumbnail = [
                        i
                        for i in files
                        if "is_thumbnail" in i.keys() and i["is_thumbnail"]
                    ]
                if "endpoints" in item_json:
                    endpoints = item_json.get("endpoints")
                if "weko_link" in item_json:
                    weko_link = item_json.get("weko_link")
                    update_data_for_weko_link(item_json.get("metainfo"), weko_link)
                if "cris_linkage" in item_json:
                    cris_linkage = item_json.get("cris_linkage")

        need_file, need_billing_file = is_schema_include_key(item_type.schema)

        if "subitem_thumbnail" in json.dumps(item_type.schema):
            need_thumbnail = True
            key = [
                i[0].split(".")[0]
                for i in find_items(item_type.form)
                if "subitem_thumbnail" in i[0]
            ]

            option = (
                item_type.render.get("meta_list", {})
                .get(key[0].split("[")[0], {})
                .get("option")
            )
            if option:
                allow_multi_thumbnail = option.get("multiple")
    except Exception as e:
        template_url = "weko_items_ui/iframe/error.html"
        current_app.logger.error(e)

    return (
        template_url,
        need_file,
        need_billing_file,
        record,
        json_schema,
        schema_form,
        item_save_uri,
        files,
        endpoints,
        need_thumbnail,
        files_thumbnail,
        allow_multi_thumbnail,
        cris_linkage,
    )
