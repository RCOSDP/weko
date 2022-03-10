# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Consumer is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

import os
from flask import Blueprint, request, make_response, jsonify, current_app
from flask_login import current_user, login_required
from flask_babelex import gettext as _
import ldnlib
from datetime import datetime, timedelta
import json
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.errors import PIDDoesNotExistError

from .config import DATE_FORMAT, \
    DEFAULT_NOTIFY_RETENTION_DAYS, INBOX_VERIFY_TLS_CERTIFICATE
from weko_signpostingclient.api import request_signposting
from weko_inbox_sender.actions import NOTIFY_ACTION
from weko_inbox_sender.utils import inbox_url

from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from weko_inbox_sender.api import publish_notification
from weko_inbox_sender.utils import get_records_pid


blueprint_api = Blueprint('weko_inbox_consumer',
                          __name__,
                          )


@blueprint_api.route('/publish', methods=['GET'])
def check_inbox_publish():
    """Check if there is an item publivcation notification in inbox

    :return: response
    :rtype: Response
    """

    user_id = current_user.get_id()
    inbox = inbox_url()
    send_cookie = dict()
    latest_get = request.cookies.get('LatestGet', None)
    if latest_get:
        latest_get_users = json.loads(latest_get)
        send_cookie = latest_get_users
        if user_id in latest_get_users.keys():
            latest_get = latest_get_users[user_id]
        else:
            latest_get = None
    if (latest_get is None) or \
        ((datetime.now() - datetime.strptime(latest_get, DATE_FORMAT))
         .days >= DEFAULT_NOTIFY_RETENTION_DAYS):
        latest_get = \
            (datetime.now()-timedelta(days=DEFAULT_NOTIFY_RETENTION_DAYS))\
            .strftime(DATE_FORMAT)
    notifications = \
        get_notification_filter(inbox,
                                latest_get,
                                user=user_id,
                                action=NOTIFY_ACTION.ENDORSEMENT.value,
                                target=request.host_url
                                )
    send_data = list()
    for notification in notifications:
        record_url = notification['object']['id']
        data = create_push_data(request_signposting(record_url))
        push_data = dict()
        push_data['title'] = _('Item release')
        push_data['body'] = _('Items awaiting approval have been published.')
        push_data['data'] = data
        push_data['url'] = record_url
        send_data.append(push_data)
        current_app.logger.debug(data)
    response = make_response(jsonify(send_data))
    send_cookie[user_id] = datetime.now().strftime(DATE_FORMAT)
    response.set_cookie('LatestGet', value=json.dumps(send_cookie))
    return response


def get_notification_filter(inbox, latest_get, user, action, target):
    """Create a list of item publication notifications filtered be date and user

    :param str inbox: uri of inbox
    :param str user: now user
    :param str action: notification action
    :param str latest_get: Last acquisition date
    :return: notification list
    :rtype: list
    """
    all_notify = get_notifications(inbox, latest_get)
    notifications = list()
    for n_url in all_notify:
        notification = get_notification(inbox_url(n_url))
        if notification.get('audience') is None:
            continue
        if (action in notification['type']) and \
                (notification['target']['id'] == target) and \
                (user == notification['audience']['id']):
            notifications.append(notification)
    return notifications


def get_notifications(inbox, latest_get):
    """Create a notification list in inbox, filtered by date

    :param str inbox: uri of inbox
    :param str latest_get: last acquisition date
    :return: notification list
    :rtype: list
    """
    consumer = ldnlib.Consumer(allow_localhost=True)
    notifications = \
        consumer.notifications(inbox_url(inbox),
                               headers={'accept': 'application/ld+json',
                                        'LatestGet': latest_get
                                        },
                               verify=INBOX_VERIFY_TLS_CERTIFICATE
                               )
    return notifications


def get_notification(uri):
    """Get notification payload from inbox

    :param list uri: uri of notification
    :return: notification payload
    :rtype: dict
    """
    consumer = ldnlib.Consumer(allow_localhost=True)
    notification = \
        consumer.notification(uri,
                              headers={'accept': 'application/ld+json'},
                              verify=INBOX_VERIFY_TLS_CERTIFICATE
                              )
    return notification


def create_push_data(data):
    """Format the data obtained from signposting
    into the data to create push notification.

    :param dict data: data
    :return: data for notification
    :rtype: dict
    """
    push_data = dict()
    metadatas = dict()
    oad = current_app.config.get('OAISERVER_METADATA_FORMATS', {})
    for d in data:
        if d['rel'] == 'cite-as':
            push_data['cite-as'] = d['url']
        elif d['rel'] == 'describedby':
            if d['type'] == 'application/json':
                metadatas['json'] = d['url']
            elif d['type'] == 'application/x-bibtex':
                metadatas['bibtex'] = d['url']
            else:
                metadatas[get_oai_format(oad, d['formats'])] = d['url']
        else:
            push_data[d['rel']] = d['url']
    push_data['metadata'] = metadatas
    return push_data


def get_oai_format(oad, namespace):
    """Output the format name from namespace uri.

    :param dict oad: format data
    :param str data: namespace uri
    :return: format name
    :rtype: str
    """
    for _format, _object in oad.items():
        if _object['namespace'] == namespace:
            return _format
    return None


@blueprint_api.route('/push_data', methods=['POST'])
def get_data_from_push():
    """Get the data sent from javascript

    :return: response
    :rtype: Response
    """
    data = request.json
    current_app.logger.debug(data)
    return make_response()
