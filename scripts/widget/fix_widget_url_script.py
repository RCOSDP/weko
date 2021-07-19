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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO3 module docstring."""
import re
from copy import deepcopy

from invenio_db import db
from weko_gridlayout.models import WidgetDesignPage, WidgetDesignSetting, \
    WidgetMultiLangData
from weko_gridlayout.utils import delete_widget_cache


def replace_widget_url(description_data: str) -> str:
    """Replace widget URL.

    Args:
        description_data (str): Widget description.

    Returns:
        str: Widget description.
    """

    def replace_str(match_obj):
        return match_obj.group(1) + match_obj.group(2) + match_obj.group(
            3).replace('/0', '/Root Index')

    pattern = r'(\/widget\/uploaded)(\/.[^\/]+\.[A-Za-z]{2,4})(\/0)'
    return re.sub(pattern, replace_str, description_data)


def replace_settings_url(settings_data):
    """Replace settings URL.

    Args:
        settings_data (dict|list): Widget settings.
    """
    if isinstance(settings_data, dict):
        for k, v in settings_data.items():
            if isinstance(v, str):
                settings_data[k] = replace_widget_url(v)
            elif isinstance(v, (dict, list)):
                replace_settings_url(v)
    elif isinstance(settings_data, list):
        for setting in settings_data:
            replace_settings_url(setting)


def replace_widget_url_for_widget_design_setting():
    """Replace URL for widget_design_setting table."""
    print("START replace URL for widget_design_setting")
    widget_design_setting_lst = WidgetDesignSetting.query.all()
    with db.session.begin_nested():
        for widget_design_setting in widget_design_setting_lst:
            if widget_design_setting.settings is not None:
                settings = deepcopy(widget_design_setting.settings)
                replace_settings_url(settings)
                widget_design_setting.settings = settings
                db.session.merge(widget_design_setting)
    db.session.commit()
    print("END replace URL for widget_design_setting")


def replace_widget_url_for_widget_design_page(page_ids: list):
    """Replace URL for widget_design_page table.

    Args:
        page_ids (list): Widget settings.
    """
    print("START replace URL for widget_design_page")
    widget_design_page_lst = WidgetDesignPage.query.all()
    with db.session.begin_nested():
        for widget_design_page in widget_design_page_lst:
            if widget_design_page.settings is not None:
                settings = deepcopy(widget_design_page.settings)
                replace_settings_url(settings)
                widget_design_page.settings = settings
                db.session.merge(widget_design_page)
                page_ids.append(widget_design_page.id)
    db.session.commit()
    print("END replace URL for widget_design_page")


def replace_widget_url_for_widget_multi_lang_data():
    """Replace URL for widget_multi_lang_data table."""
    print("START replace URL for widget_multi_lang_data")
    widget_multi_lang_data_lst = WidgetMultiLangData.query.all()
    with db.session.begin_nested():
        for widget_multi_lang in widget_multi_lang_data_lst:
            if isinstance(widget_multi_lang.description_data,
                          dict) and 'description' in widget_multi_lang.description_data:
                widget_multi_lang.description_data = {
                    "description": replace_widget_url(
                        widget_multi_lang.description_data['description'])}
                db.session.merge(widget_multi_lang)
    db.session.commit()
    print("END replace URL for widget_multi_lang_data")


if __name__ == '__main__':
    try:
        # Replace Widget URL.
        page_id_lst = []
        replace_widget_url_for_widget_design_setting()
        replace_widget_url_for_widget_design_page(page_id_lst)
        replace_widget_url_for_widget_multi_lang_data()
        # Clear Widget cache.
        delete_widget_cache('Root Index')
        # Clear Widget page cache.
        for page_id in page_id_lst:
            delete_widget_cache('', page_id)
        print("Complete!!!")
    except Exception as ex:
        print(ex)
        db.session.rollback()

# How to run this file
# docker-compose exec -T web invenio shell /code/scripts/widget/fix_widget_url_script.py
