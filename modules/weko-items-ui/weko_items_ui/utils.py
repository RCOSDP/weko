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

"""Module of weko-items-ui utils.."""
from datetime import datetime

from flask_login import current_user
from invenio_db import db
from sqlalchemy import MetaData, Table
from weko_user_profiles import UserProfile
from weko_workflow.models import Action as _Action
from copy import deepcopy


def get_list_username():
    """Get list username.

    Query database to get all available username
    return: list of username
    """
    current_user_id = current_user.get_id()
    user_index = 1
    result = list()
    while True:
        try:
            if (int(current_user_id) == user_index):
                pass
            else:
                user_info = UserProfile.get_by_userid(user_index)
                result.append(user_info.get_username)
            user_index = user_index + 1
        except Exception:
            break

    return result


def get_list_email():
    """Get list email.

    Query database to get all available email
    return: list of email
    """
    current_user_id = current_user.get_id()
    result = list()
    try:
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if (int(current_user_id) == item[0]):
                pass
            else:
                result.append(item[1])
    except Exception as e:
        result = str(e)

    return result


def get_user_info_by_username(username):
    """Get user information by username.

    Query database to get user id by using username
    Get email from database using user id
    Pack response data: user id, user name, email

    parameter:
        username: The username
    return: response pack
    """
    result = dict()
    try:
        user = UserProfile.get_by_username(username)
        user_id = user.user_id

        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if item[0] == user_id:
                result['username'] = username
                result['user_id'] = user_id
                result['email'] = item[1]
                return result
        return None
    except Exception as e:
        result['error'] = str(e)


def validate_user(username, email):
    """Validate user information.

    Get user id from database using username
    Get user id from database using email
    Compare 2 user id to validate user information
    Pack responde data:
        results: user information (username, user id, email)
        validation: username is match with email or not
        error: null if no error occurs

    param:
        username: The username
        email: The email
    return: response data
    """
    result = {
        'results': '',
        'validation': False,
        'error': ''
    }
    try:
        user = UserProfile.get_by_username(username)
        user_id = 0

        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if item[1] == email:
                user_id = item[0]
                break

        if user.user_id == user_id:
            user_info = dict()
            user_info['username'] = username
            user_info['user_id'] = user_id
            user_info['email'] = email
            result['results'] = user_info
            result['validation'] = True
        return result
    except Exception as e:
        result['error'] = str(e)

    return result


def get_user_info_by_email(email):
    """
    Get user information by email.

    Query database to get user id by using email
    Get username from database using user id
    Pack response data: user id, user name, email

    parameter:
        email: The email
    return: response
    """
    result = dict()
    try:
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()
        for item in data:
            if item[1] == email:
                user = UserProfile.get_by_userid(item[0])
                if user is None:
                    result['username'] = ""
                else:
                    result['username'] = user.get_username
                result['user_id'] = item[0]
                result['email'] = email
                return result
        return None
    except Exception as e:
        result['error'] = str(e)


def get_user_information(user_id):
    """
    Get user information user_id.

    Query database to get email by using user_id
    Get username from database using user id
    Pack response data: user id, user name, email

    parameter:
        user_id: The user_id
    return: response
    """
    result = {
        'username': '',
        'email': ''
    }
    user_info = UserProfile.get_by_userid(user_id)
    if user_info is not None:
        result['username'] = user_info.get_username

    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table_name = 'accounts_user'

    user_table = Table(table_name, metadata)
    record = db.session.query(user_table)

    data = record.all()

    for item in data:
        if item[0] == user_id:
            result['email'] = item[1]
            return result

    return result


def get_user_permission(user_id):
    """
    Get user permission user_id.

    Compare current id with id of current user
    parameter:
        user_id: The user_id
    return: true if current id is the same with id of current user.
    If not return false
    """
    current_id = current_user.get_id()
    if current_id is None:
        return False
    if str(user_id) == current_id:
        return True
    return False


def get_current_user():
    """
    Get user id of user currently login.

    parameter:
    return: current_id
    """
    current_id = current_user.get_id()
    return current_id


def get_actionid(endpoint):
    """
    Get action_id by action_endpoint.

    parameter:
    return: action_id
    """
    with db.session.no_autoflush:
        action = _Action.query.filter_by(
            action_endpoint=endpoint).one_or_none()
        if action:
            return action.id
        else:
            return None


def parse_ranking_results(results, display_rank, list_name='all',
                          title_key='title', count_key=None, pid_key=None,
                          search_key=None, date_key=None):
    """Parse the raw stats results to be usable by the view."""
    ranking_list = []
    if pid_key:
        url = '../records/{0}'
        key = pid_key
    elif search_key:
        url = '../search?page=1&size=20&search_type=1&q={0}'
        key = search_key
    else:
        url = None

    if results and list_name in results:
        rank = 1
        count = 0
        date = ''
        for item in results[list_name]:
            t = {}
            if count_key:
                if not count == int(item[count_key]):
                    rank = len(ranking_list) + 1
                    count = int(item[count_key])
                t['rank'] = rank
                t['count'] = count
            elif date_key:
                new_date = \
                    datetime.utcfromtimestamp(
                        item[date_key]).strftime('%Y-%m-%d')
                if new_date == date:
                    t['date'] = ''
                else:
                    t['date'] = new_date
                    date = new_date
            title = item[title_key]
            if title_key == 'user_id':
                user_info = UserProfile.get_by_userid(title)
                if user_info:
                    title = user_info.username
                else:
                    title = 'None'
            t['title'] = title
            t['url'] = url.format(item[key]) if url and key in item else None
            ranking_list.append(t)
            if len(ranking_list) == display_rank:
                break
    return ranking_list


def parse_required_item_in_schema(json_schema):
    """Get required item and split to sub items.

    Arguments:
        json_schema {dictionary} -- The schema data

    Returns:
        dictionary -- The schema after parse

    """
    data = deepcopy(json_schema)
    required = deepcopy(data.get('required'))
    if 'pubdate' in required:
        required.remove('pubdate')
    if len(required) == 0:
        return None
    properties = data.get('properties')
    if not properties:
        return None
    for item in required:
        required_data = add_required_subitem(properties.get(item))
        if required_data:
            properties[item] = required_data
    return data


def add_required_subitem(data):
    """Get schema after add required.

    Arguments:
        data {dictionary} -- item in schema

    Returns:
        dictionary -- data after add required

    """
    if not data:
        return None
    item = deepcopy(data)
    has_item = False
    if 'items' in item.keys():
        has_item = True
        sub_item = item.get('items')
    else:
        sub_item = item

    properties = sub_item.get('properties')
    list_required_item = []
    if not properties:
        return None
    if 'required' in sub_item.keys():
        for k, v in properties.items():
            if is_properties_exist_in_item(v):
                sub_data = add_required_subitem(v)
                properties[k] = sub_data
            else:
                list_required_item.append(str(k))
        sub_item['required'] = list_required_item
    else:
        for k, v in properties.items():
            if not add_required_subitem(v, k):
                return None
            else:
                sub_data = add_required_subitem(v)
                properties[k] = sub_data
    if has_item:
        item['items'] = sub_item
        return item
    else:
        return sub_item


def is_properties_exist_in_item(data):
    """Check item have children or not.

    Arguments:
        data {dictionary} -- Item data

    Returns:
        boolean -- True if child is exists

    """
    if data.get('properties') or data.get('items'):
        return True
    return False
