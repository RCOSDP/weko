# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

from invenio_pidstore.models import PersistentIdentifier,PIDStatus
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_db import db

import ldnlib
import re
import uuid
from .config import PAYLOAD_TEMPLATE, INBOX_VERIFY_TLS_CERTIFICATE, NOTIFY_ACTION
from flask import request, current_app

def publish_notification(record):
    """send item publication notification to inbox

    :param Record record: published record
    """
    # TODO: 配置場所の調査
    data = get_payloaddata_publish(record)
    payload = create_payload(data, 'ANNOUNCE_STANDALONE', NOTIFY_ACTION.ENDORSEMENT.value)
    send_notification_inbox(payload)

def get_payloaddata_publish(record):
    """Get the data needed to create the peyload 
    for item publication notifications.

    :param Record record: published record
    :return: data
    :rtype: dict
    """
    data = dict()
    data['audience'] = {'id':str(record['_deposit'].get('owner')),'type':'Person'}
    data['actor'] = {'id':str(record['_deposit'].get('created_by')),'type':'Person'}
    recid_p = get_recid_p(record.get('recid'))
    item_url = '{host_url}records/{recid}'.\
        format(host_url=get_url_root(), recid = recid_p)
    doi = get_record_permalink(recid_p)
    print(doi)
    data['object'] = {'id':item_url, 'ietf:cite-as':doi, 'type':['Page','sorg:WebPage']}
    data['context'] = data['object']
    data['origin'] = {'id':get_url_root(), 'inbox':get_url_inbox(), 'type':'Service'}
    data['target'] = data['origin']
    print(data)
    return data

def get_recid_p(recid):
    # recidから"."以下を排除
    try:
        c_recid = PersistentIdentifier.get('recid', str(recid))
    except PIDDoesNotExistError:
        c_recid = None
    if c_recid:
        recid_version = PIDVersioning(child=c_recid)
        if recid_version.has_parents:
            print("has parents")
            print(recid_version.parent.pid_value.replace("parent:",""))
            return recid_version.parent.pid_value.replace("parent:","")
        else:
            print("not has parent")
            return recid


def create_payload(data, notification_pattern, notification_type):
    """Create a notification payload

    :param dict data: data for create payload
    :param str notification_pattern: notification pattern stipulated by COAR Notify
                                     select in [
                                         OFFER, UNDO, ACCEPT, REJECT, 
                                         ANNOUNCE_STANDALONE, ANNOUNCE_OFFER
                                         ]
    :param str notification_type: notification type
    :return: notification payload
    :rtype: dict
    """
    payload = getattr(PAYLOAD_TEMPLATE,notification_pattern).template
    for key, value in data.items():
        payload[key] = value
    payload["id"] = str(uuid.uuid4())
    payload["type"].append(notification_type)
    print(payload)
    return payload

def send_notification_inbox(payload):
    """send notification to inbox

    :param dict payload: notification payload
    """
    sender = ldnlib.Sender(allow_localhost = True)
    inbox = payload['target']['inbox']
    
    sender.send(inbox, payload,verify = INBOX_VERIFY_TLS_CERTIFICATE)
    
def get_record_permalink(recid_p):
    """
    そのレコードの親要素のuuidを取得し、それに紐づいているdoiのuriを取得
    """
    
    uuid_p=PersistentIdentifier.get('parent','parent:'+str(recid_p)).object_uuid
    try:
        return PersistentIdentifier.query.filter_by(
            pid_type="doi",
            object_uuid=uuid_p,
            status=PIDStatus.REGISTERED
        ).order_by(
            db.desc(PersistentIdentifier.created)
        ).first().pid_value
    except PIDDoesNotExistError as e:
        pass
    
    return '{host_url}records/{recid}'.format(host_url=get_url_root(),recid=recid_p)

def get_url_root():
    """Check a DOI is existed.
    
    weko_workflow.utils.get_url_rootのコピペ
    :return: url root.
    """
    site_url = current_app.config['THEME_SITEURL'] + '/'
    return request.host_url if request else site_url


def get_url_inbox():
    """Create inbox url.
    :return : inbox url
    """

    #inbox = str()
    #if request:
    #    print("exist request")
    #    root = request.host_url
    #    print("exist request:"+root)
    #    inbox = re.sub(":([0-9]+)/",":8000/",root)+"inbox"
    #    return inbox
    #else:
    #    print("not exist request")
    #    inbox = current_app.config['THEME_SITEURL']+'/inbox'
    inbox = current_app.config['INBOX_URL']
    return inbox
        
def create_url_inbox(uri):
    return re.sub("https://(.*)/inbox",current_app.config['INBOX_URL'],uri)
