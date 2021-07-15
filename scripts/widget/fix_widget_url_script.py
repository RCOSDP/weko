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

OLD_COM_ID = '0'
NEW_COM_ID = 'Root Index'


def replace_widget_url(description_data: str) -> str:
    """Replace widget URL.

    Args:
        description_data (str): Widget description.

    Returns:
        str: Widget description.
    """

    def replace_str(match_obj) -> str:
        """Replace String.

        Args:
            match_obj: MAtch Object

        Returns:
            str: String is replaced.
        """
        return match_obj.group(1) + '/' + \
            match_obj.group(3).replace(OLD_COM_ID, NEW_COM_ID) + \
            '/' + match_obj.group(2)

    regex = r'(\/widget\/uploaded)\/(.[^\/]+\.[A-Za-z]{2,4})\/(0)'
    return re.sub(regex, replace_str, description_data)


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


def change_object_version_key_of_widget():
    """Change object version key of widget in case pre-migration environment."""
    print("START replace URL for change_object_version_key_of_widget")
    with db.session.begin_nested():
        db.session.execute(
            'update files_object set key= regexp_replace(key, :old_key, :new_key) where bucket_id = :bucket_id',
            {
                'bucket_id': '517f7d98-ab2c-4736-91ea-54ba34e7905d',
                'old_key': '^' + OLD_COM_ID + '_',
                'new_key': NEW_COM_ID + '_',
            }
        )
    db.session.commit()
    print("END replace URL for change_object_version_key_of_widget")


if __name__ == '__main__':
    try:
        # Replace Widget URL.
        page_id_lst = []
        replace_widget_url_for_widget_design_setting()
        replace_widget_url_for_widget_design_page(page_id_lst)
        replace_widget_url_for_widget_multi_lang_data()

        # Replace Object version key.
        change_object_version_key_of_widget()

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
