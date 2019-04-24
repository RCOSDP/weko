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
import json

from flask import jsonify, make_response

from .api import WidgetItems
from .models import WidgetDesignSetting, WidgetItem, WidgetType


def get_repository_list():
    """Get repository list from Community table.

    :return: Repository list.
    """
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


def get_widget_list(repository_id):
    """Get Widget list.

    :param repository_id: Identifier of the repository.
    :return: Widget list.
    """
    result = {
        "widget-list": [],
        "error": ""
    }
    try:
        widget_item_list = WidgetItem.query.filter_by(
            repository_id=repository_id, is_enabled=True
        ).all()
        if widget_item_list:
            for widget_item in widget_item_list:
                data = dict()
                data["widgetId"] = widget_item.repository_id
                data["widgetType"] = widget_item.widget_type
                data["widgetLabel"] = widget_item.label
                result["widget-list"].append(data)
    except Exception as e:
        result["error"] = str(e)

    return result


def get_widget_design_setting(repository_id):
    """Get Widget design setting by repository id.

    :param repository_id: Identifier of the repository
    :return: Widget design setting json.
    """
    result = {
        "widget-settings": [
        ],
        "error": ""
    }
    try:
        widget_setting = WidgetDesignSetting.select_by_repository_id(
            repository_id)
        if widget_setting:
            settings = widget_setting.get('settings')
            if settings:
                result["widget-settings"] = json.loads(settings)
    except Exception as e:
        result['error'] = str(e)

    return result


def update_widget_design_setting(data):
    """Update Widget layout setting.

    :param data: json data is submitted from client side.
    :return: result json.
    """
    result = {
        "result": False,
        "error": ''
    }
    repository_id = data.get('repository_id')
    setting_data = data.get('settings')

    try:
        if repository_id and setting_data:
            if WidgetDesignSetting.select_by_repository_id(repository_id):
                result["result"] = WidgetDesignSetting.update(repository_id,
                                                              setting_data)
            else:
                result["result"] = WidgetDesignSetting.create(repository_id,
                                                              setting_data)
        else:
            result['error'] = "Fail to save Widget design. Please check again."
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
        option = dict()
        option["text"] = widget_type.type_name
        option["value"] = widget_type.type_id
        options.append(option)
    result = {"options": options}

    return result


def update_admin_widget_item_setting(data):
    """Create/update widget item.

    :param: widget item data
    :return: options json
    """
    status = 201
    success = True

    flag = data.get('flag_edit')
    data_result = data.get('data')
    data_id = data.get('data_id')
    if not data_result:
        # raise WidgetItemInvalidDataRESTError()
        success = True
        msg = 'Invalid data.'
    if flag:
        if data_result.get('repository') != data_id.get('repository')\
                or data_result.get('widget_type') != data_id.get('widget_type')\
                or data_result.get('label') != data_id.get('label'):
            if WidgetItems.is_existed(data_result):
                success = False
                msg = 'Fail to udpate. Data input to update is exist!'

        if success:
            if WidgetItems.is_existed(data_id):
                if not WidgetItems.update(data_result, data_id):
                    # raise WidgetItemUpdatedRESTError()
                    success = False
                    msg = 'Update widget item fail.'
                else:
                    msg = 'Widget item updated successfully.'
            else:
                msg = 'Fail to udpate. Can not find Widget item to edit'
    else:
        if WidgetItems.is_existed(data_result):
            success = False
            msg = 'Fail to create. Data input to create is exist!'
        else:
            if not WidgetItems.create(data_result):
                # raise WidgetItemAddedRESTError()
                success = False
                msg = 'Create widget item fail.'
            else:
                msg = 'Widget item created successfully.'

    return make_response(
        jsonify({'status': status,
                 'success': success,
                 'message': msg}), status)
