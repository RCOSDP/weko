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

from weko_user_profiles import UserProfile
from invenio_accounts.models import User
from sqlalchemy import Table, MetaData
from invenio_db import db


def get_list_username():
    """
    Get list username
    Query database to get all available username

    return: list of username
    """
    user_index = 1
    result = list()
    while True:
        try:
            userinfo = UserProfile.get_by_userid(user_index)
            result.append(userinfo._username)
            user_index = user_index + 1
        except:
            break
    return result


def get_list_email():
    """
    Get list email:
    Query database to get all available email

    return: list of email
    """
    result = list()
    try:
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            result.append(item[1])
    except Exception as e:
        result = str(e)

    return result


def get_user_info_by_username(username):
    """
    Get user information by username:
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
    """
    Validate user information:
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
        user_id = user.user_id

        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if item[1] == email:
                if item[0] == user_id:
                    user_info = dict()
                    user_info['username'] = username
                    user_info['user_id'] = user_id
                    user_info['email'] = item[1]
                    result['results'] = user_info
                    result['validation'] = True
                    return result
        return result
    except Exception as e:
        result['error'] = str(e)

    return result


def get_user_info_by_email(email):
    """
    Get user information by email:
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
                result['username'] = user._username
                result['user_id'] = item[0]
                result['email'] = email
                return result
        return None
    except Exception as e:
        result['error'] = str(e)
