# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

from flask import current_app
from flask_login import current_user

import ldnlib
import uuid
from .config import INBOX_VERIFY_TLS_CERTIFICATE
from .utils import inbox_url, get_url_root, \
    get_record_permalink, get_recid_p
from .payload_template import PAYLOAD_TEMPLATE
from .actions import NOTIFY_ACTION


def publish_notification(record):
    """send item publication notification to inbox

    :param Record record: published record
    """
    data = get_payloaddata_publish(record)
    payload = create_payload(data, 'ANNOUNCE_STANDALONE',
                             NOTIFY_ACTION.ENDORSEMENT.value)
    send_notification_inbox(payload)


def get_payloaddata_publish(record):
    """Get the data needed to create the peyload
    for item publication notifications.

    :param Record record: published record
    :return: data
    :rtype: dict
    """
    data = dict()
    root_url = get_url_root()
    data['audience'] = \
        {'id': str(record['_deposit'].get('created_by')), 'type': 'Person'}
    data['actor'] = {'id': str(current_user.get_id()), 'type': 'Person'}
    recid_p = get_recid_p(record.get('recid'))
    item_url = '{host_url}records/{recid}'.\
        format(host_url=root_url, recid=recid_p)
    doi = get_record_permalink(recid_p)
    data['object'] = \
        {'id': item_url, 'ietf:cite-as': doi, 'type': ['Page', 'sorg:WebPage']}
    data['context'] = data['object']
    data['origin'] = \
        {'id': root_url, 'inbox': root_url+'inbox', 'type': 'Service'}
    data['target'] = data['origin']
    current_app.logger.debug(data)
    return data


def create_payload(data, notification_pattern, notification_type):
    """Create a notification payload

    :param dict data: data for create payload
    :param str notification_pattern:
        notification pattern stipulated by COAR Notify
            select in [
             OFFER, UNDO, ACCEPT, REJECT,
             ANNOUNCE_STANDALONE, ANNOUNCE_OFFER
            ]
    :param str notification_type: notification type
    :return: notification payload
    :rtype: dict
    """
    payload = getattr(PAYLOAD_TEMPLATE, notification_pattern).template
    for key, value in data.items():
        payload[key] = value
    payload['id'] = str(uuid.uuid4())
    payload['type'].append(notification_type)
    return payload


def send_notification_inbox(payload):
    """send notification to inbox

    :param dict payload: notification payload
    """
    sender = ldnlib.Sender(allow_localhost=True)
    inbox = inbox_url(payload['target']['inbox'])
    sender.send(inbox, payload, verify=INBOX_VERIFY_TLS_CERTIFICATE)
