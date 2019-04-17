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
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Utilities for convert response json."""

from . import config
from .models import WidgetType, WidgetDesignSetting

def get_repository_list():
    result = {
        "repositories": [],
        "error": ""
    }
    try:
        from invenio_communities.models import Community
        communities = Community.query.all()
        if communities:
            for community in communities:
                community_result = dict()
                community_result['id'] = community.id
                community_result['title'] = community.title
                result['repositories'].append(community_result)
    except Exception as e:
        result['error'] = str(e)

    return result


def get_widget_list():
    result = {
        "widget-list": [
            {
                "widgetId": "id1",
                "widgetLabel": "Widget 1"
            },
            {
                "widgetId": "id2",
                "widgetLabel": "Widget 2"
            },
            {
                "widgetId": "id3",
                "widgetLabel": "Widget 3"
            },
            {
                "widgetId": "id4",
                "widgetLabel": "Widget 4"
            }
        ],
        "error": ""
    }

    return result


def get_widget_design_setting(repository_id):
    result = {
        "widget-settings": [
        ],
        "error": ""
    }
    try:
        widget_setting = WidgetDesignSetting.select_by_repository_id(repository_id)
        if widget_setting:
            result["widget-settings"] = widget_setting.get('settings')
        else:
            result["widget-settings"] = [
                {
                    "x": 0,
                    "y": 0,
                    "width": 8,
                    "height": 1,
                    "id": "id1",
                    "name": "Free Description"
                },
                {
                    "x": 0,
                    "y": 1,
                    "width": 8,
                    "height": 4,
                    "id": "id2",
                    "name": "Main Contents"
                },
                {
                    "x": 8,
                    "y": 0,
                    "width": 2,
                    "height": 1,
                    "id": "id3",
                    "name": "New arrivals"
                },
                {
                    "x": 8,
                    "y": 1,
                    "width": 2,
                    "height": 2,
                    "id": "id4",
                    "name": "Notice"
                },
                {
                    "x": 8,
                    "y": 3,
                    "width": 2,
                    "height": 2,
                    "id": "id5",
                    "name": "Access counter"
                }
            ]
    except Exception as e:
        result['error'] = str(e)

    return result


def update_widget_layout_setting(data):
    result = {
        "result": False,
        "error": ''
    }
    repository_id = data.get('repository_id')
    setting_data = data.get('settings')
    try:
        if repository_id:
            if WidgetDesignSetting.select_by_repository_id(repository_id):
                result["result"] = WidgetDesignSetting.update(repository_id, setting_data)
            else:
                result["result"] = WidgetDesignSetting.create(repository_id, setting_data)
    except Exception as e:
        result['error'] = str(e)
    return result


def get_widget_type_list():
    """Get all Widget types.

    :param: None
    :return: options json
    """
    widget_types = WidgetType.get_all_widget_types()
    options = []
    for widget_type in widget_types:
        option = {}
        option["text"] = widget_type.type_name
        option["value"] = widget_type.type_id
        options.append(option)
    result = {"options": options}

    return result

def update_widget_item_setting(data):
    result = {
        "result": '',
        "error": ''
    }

    return result
