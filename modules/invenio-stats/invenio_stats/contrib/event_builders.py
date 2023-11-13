# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Signal receivers for certain events."""

from __future__ import absolute_import, print_function

import datetime
import uuid
from socket import gethostbyaddr, herror

from flask import request
from weko_accounts.utils import get_remote_addr

from ..utils import get_user, is_valid_access


def celery_task_event_builder(
    event, sender_app, exec_data=None, user_data=None, **kwargs
):
    """Build a celery-task event."""
    event.update(dict(
        # When:
        timestamp=datetime.datetime.utcnow().isoformat(),

        # What:
        task_id=exec_data['task_id'],
        task_name=exec_data['task_name'],
        task_state=exec_data['task_state'],
        start_time=exec_data['start_time'],
        end_time=exec_data['end_time'],
        total_records=exec_data['total_records'],
        repository_name=exec_data['repository_name'],
        execution_time=exec_data['execution_time'],

        # Who:
        # **get_user()
        # Must retrieve the user data from caller
        # Task has no access to request
        ip_address=user_data['ip_address'],
        user_agent=user_data['user_agent'],
        user_id=user_data['user_id'],
        session_id=user_data['session_id']
    ))
    return event


def file_download_event_builder(event, sender_app, obj=None, **kwargs):
    """Build a file-download event."""
    if is_valid_access():
        event.update(dict(
            # When:
            timestamp=datetime.datetime.utcnow().isoformat(),
            # What:
            bucket_id=str(obj.bucket_id),
            file_id=str(obj.file_id),
            root_file_id=str(obj.root_file_id),
            file_key=obj.key,
            size=obj.file.size,
            referrer=request.referrer,
            accessrole=obj.file.json.get('accessrole', ''),
            userrole=obj.userrole,
            site_license_name=obj.site_license_name,
            site_license_flag=obj.site_license_flag,
            index_list=obj.index_list,
            cur_user_id=obj.userid,
            item_id=obj.item_id,
            item_title=obj.item_title,
            remote_addr=get_remote_addr(),
            is_billing_item=obj.is_billing_item,
            billing_file_price=obj.billing_file_price,
            user_group_list=obj.user_group_list,
            # Who:
            **get_user()
        ))
        return event


def file_preview_event_builder(event, sender_app, obj=None, **kwargs):
    """Build a file-preview event."""
    if is_valid_access():
        event.update(dict(
            # When:
            timestamp=datetime.datetime.utcnow().isoformat(),
            # What:
            bucket_id=str(obj.bucket_id),
            file_id=str(obj.file_id),
            root_file_id=str(obj.root_file_id),
            file_key=obj.key,
            size=obj.file.size,
            referrer=request.referrer,
            accessrole=obj.file.json.get('accessrole', ''),
            userrole=obj.userrole,
            site_license_name=obj.site_license_name,
            site_license_flag=obj.site_license_flag,
            index_list=obj.index_list,
            cur_user_id=obj.userid,
            item_id=obj.item_id,
            item_title=obj.item_title,
            remote_addr=get_remote_addr(),
            is_billing_item=obj.is_billing_item,
            billing_file_price=obj.billing_file_price,
            user_group_list=obj.user_group_list,
            # Who:
            **get_user()
        ))
        return event


def build_celery_task_unique_id(doc):
    """Build celery task unique identifier."""
    key = '{0}_{1}_{2}'.format(
        doc['task_id'],
        doc['task_name'],
        doc['repository_name']
    )
    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))

    return doc


def build_file_unique_id(doc):
    """Build file unique identifier."""
    key = '{0}_{1}_{2}_{3}'.format(
        doc['bucket_id'],
        doc['file_id'],
        doc['remote_addr'],
        doc['unique_session_id']
    )
    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))
    doc['hostname'] = '{}'.format(resolve_address(doc['remote_addr']))

    return doc


def build_record_unique_id(doc):
    """Build record unique identifier."""
    key = '{0}_{1}_{2}_{3}_{4}'.format(
        doc['pid_type'],
        doc['pid_value'],
        doc['remote_addr'],
        doc['unique_session_id'],
        doc['visitor_id'])
    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))
    doc['hostname'] = '{}'.format(resolve_address(doc['remote_addr']))

    return doc


def copy_record_index_list(doc, aggregation_data=None):
    """Copy record index list."""
    record_index_names = ''
    list = doc['record_index_list']
    if list:
        agg_record_index_list = []
        for index in list:
            idx_name = index.get('index_name', '')
            if idx_name is not None:
                agg_record_index_list.append(idx_name)
                record_index_names = ", ".join(agg_record_index_list)
    return record_index_names


def copy_user_group_list(doc, aggregation_data=None):
    """Copy record index list."""
    group_names = ''
    groups = doc['user_group_list']
    if groups:
        group_names = ', '.join([g['group_name'] for g in groups])
    return group_names


def copy_search_keyword(doc, aggregation_data=None):
    """Copy search keyword to agg."""
    if 'search_key' in doc['search_detail']:
        return doc['search_detail']['search_key']
    return ''


def copy_search_type(doc, aggregation_data=None):
    """Copy search type to agg."""
    if 'search_type' in doc['search_detail']:
        return doc['search_detail']['search_type']
    return -1


def record_view_event_builder(event, sender_app, pid=None, record=None,
                              info=None, **kwargs):
    """Build a record-view event."""
    if is_valid_access():
        # get index information
        index_list = []

        for index in record.navi:
            index_list.append(dict(
                index_id=str(index[1]),
                index_name=index[3] if index[3] else index[4],
                index_name_en=index[4]
            ))

        cur_user = get_user()
        cur_user_id = cur_user['user_id'] if cur_user['user_id'] else 'guest'
        record_name = record.get(
            'item_title', '') if record is not None else ''

        event.update(dict(
            # When:
            timestamp=datetime.datetime.utcnow().isoformat(),
            # What:
            record_id=str(record.id),
            record_name=record_name,
            record_index_list=index_list,
            pid_type=pid.pid_type,
            pid_value=str(pid.pid_value),
            referrer=request.referrer,
            cur_user_id=cur_user_id,
            remote_addr=get_remote_addr(),
            site_license_flag=info['site_license_flag'],
            site_license_name=info['site_license_name'],
            # Who:
            **get_user()
        ))
        return event


def top_view_event_builder(event, sender_app, info=None, **kwargs):
    """Build a top-view event."""
    if is_valid_access():
        event.update(dict(
            # When:
            timestamp=datetime.datetime.utcnow().isoformat(),
            # What:
            referrer=request.referrer,
            remote_addr=get_remote_addr(),
            site_license_flag=info['site_license_flag'],
            site_license_name=info['site_license_name'],
            # Who:
            **get_user()
        ))
        return event


def build_top_unique_id(doc):
    """Build top unique identifier."""
    key = '{0}_{1}_{2}_{3}'.format(
        doc['site_license_name'],
        doc['remote_addr'],
        doc['unique_session_id'],
        doc['visitor_id'])

    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))
    doc['hostname'] = '{}'.format(resolve_address(doc['remote_addr']))

    return doc


def build_item_create_unique_id(doc):
    """Build item_create unique identifier."""
    doc['unique_id'] = '{0}_{1}_{2}'.format("item", "create", doc['pid_value'])
    doc['hostname'] = '{}'.format(resolve_address(doc['remote_addr']))
    return doc


def resolve_address(addr):
    """Resolve the ip address string addr and return its DNS name.

    If no name is found, return None.
    """
    ret = None
    try:
        if addr is not None:
            record = gethostbyaddr(addr)
            ret = record[0]
    except herror:
        # print('an error occurred while resolving ', addr, ': ', exc)
        ret = None

    return ret


def search_event_builder(event, sender_app, search_args=None,
                         info=None, **kwargs):
    """Build a search event."""
    if is_valid_access():
        event.update(dict(
            # When:
            timestamp=datetime.datetime.utcnow().isoformat(),
            # What:
            referrer=request.referrer,
            search_detail=search_args.to_dict(flat=False),
            site_license_name=info['site_license_name'],
            site_license_flag=info['site_license_flag'],
            # Who:
            **get_user()
        ))
        return event


def build_search_unique_id(doc):
    """Build search unique identifier."""
    search_key = ''
    search_type = -1
    if 'search_detail' in doc and doc['search_detail']:
        search_key = copy_search_keyword(doc)
        search_type = copy_search_type(doc)
    key = '{0}_{1}_{2}_{3}'.format(
        search_key,
        search_type,
        doc['site_license_name'],
        doc['unique_session_id']
    )
    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))

    return doc


def build_search_detail_condition(doc):
    """Build search detail condition."""
    search_detail = {}
    for key, value in doc['search_detail'].items():
        if isinstance(value, list):
            str_val = ' '.join(value)
        else:
            str_val = value
        if key == 'q':
            search_detail['search_key'] = str_val
        elif len(value) > 0:
            search_detail[key] = str_val

    doc['search_detail'] = search_detail
    return doc


def item_create_event_builder(event, sender_app, user_id=-1,
                              item_id=None, item_title=None, admin_action=None, **kwargs):
    """Build a item-create event."""
    if is_valid_access():
        if admin_action:
            _referrer = admin_action
            _remote_addr = "localhost"
        else:
            _referrer = request.referrer
            _remote_addr = get_remote_addr()

        event.update(dict(
            # When:
            timestamp=datetime.datetime.utcnow().isoformat(),
            # What:
            referrer=_referrer,
            remote_addr=_remote_addr,
            cur_user_id=user_id,
            pid_type=item_id.pid_type,
            pid_value=str(item_id.pid_value),
            record_name=item_title,
            # Who:
            **get_user()
        ))
        return event
