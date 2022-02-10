# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Consumer is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

from flask import Blueprint, request, make_response
from flask_login import current_user
import ldnlib

from config import DATE_FORMAT, DEFAULT_NOTIFY_RETENTION_DAYS
from weko_signpostingclient.api import request_signposting
from weko_inbox_sender.config import NOTIFY_ACTION
from weko_inbox_sender.api import get_url_inbox

blueprint_api = Blueprint('check_inbox',
                      __name__,
                      url_prefix='/')

@blueprint_api.route('/publish', methods = ['GET'])
def check_inbox_publish():
    """Check if there is an item publivcation notification in inbox

    :return: response
    :rtype: Response
    """
    user_id = current_user.get_id()
    inbox=get_url_inbox()
    send_cookie = dict()
    latest_get = request.cookies.get('LatestGet', None)
    if latest_get:
        send_cookie=latest_get
        latest_get_users = json.loads(latest_get)
        if user_id in latest_get_users.keys():
            latest_get = latest_get_users[user_id]
        else:
            latest_get = None
    if (latest_get == None) or ((datetime.now() - datetime.strptime(latest_get, DATE_FORMAT)).days >= DEFAULT_NOTIFY_RETENTION_DAYS):
        latest_get = (datetime.strptime(latest_get, DATE_FORMAT)-timedelta(days=DEFAULT_NOTIFY_RETENTION_DAYS)).strftime(DATA_FORMAT)
    notifications = get_notification_in_user_and_action(inbox, user_id, NOTIFY_ACTION.ENDORSEMENT.value, latest_get)
    send_data = list()
    for notification in notifications:
        record_url = notification['object']['id']
        data = create_push_data(request_signposting(record_url))
        push_data = dict()
        push_data["title"] = "notification title"
        push_data["body"] = "notification body"
        push_data["data"] = data
        send_data.append(push_data)
    response = make_response(jsonify(send_data))
    send_cookie[user_id]=datetime.now().strftime(DATEFORMAT)
    response.set_cookie("LatestGet",value=json.dumps(send_cookie))
    return response

def get_notification_in_user_and_action(inbox, user, action, latest_get):
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
        notification = get_notification(n_url)
        if (user_id == notification['audience']['id']) and (action in notification['type']):
            notifications.append(notification)
    return notifications

def get_notifications(inbox, latest_get):
    """Create a notification list in inbox, filtered by date

    :param str inbox: uri of inbox
    :param str latest_get: last acquisition date
    :return: notification list
    :rtype: list
    """
    consumer = ldnlib.Consumer()
    notifications = consumer.notifications(inbox,headers={"accept":"application/ld+json","LatestGet":latest_get},verify=INBOX_VERIFY_TLS_CERTIFICATE)
    return notifications

def get_notification(uri):
    """Get notification payload from inbox

    :param list uri: uri of notification
    :return: notification payload
    :rtype: dict
    """
    consumer = ldnlib.Consumer()
    notification = consumer.notification(uri,headers={"accept":"application/ld+json"},verify=INBOX_VERIFY_TLS_CERTIFICATE)
    return notification

def create_push_data(data):
    """Format the data obtained from signposting into the data to create push notification.

    :param dict data: data
    :return: data for notification
    :rtype: dict
    """
    push_data = dict()
    metadatas=dict()
    oad = current_app.config.get("OAISERVER_METADATA_FORMATS",{})
    for d in data:
        if d["rel"] == "cite-as":
            push_data["cite-as"] = d["url"]
        elif d["rel"] == "describedby":
            if d["type"] == "application/json":
                metadatas["json"] = d["url"]
            elif d["type"] == "application/x-bibtex":
                metadatas["bibtex"] = d["url"]
            else:
                metadatas[get_oai_format(oad,d['formats'])] = d["url"]
        else:
            push_data[d["rel"]] = d["url"]
    push_data["metadata"] = metadatas
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