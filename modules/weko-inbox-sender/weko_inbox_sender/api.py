# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

import ldnlib
import re
import uuid
from config import PAYLOAD_TEMPLATE, INBOX_VERIFY_TLS_CERTIFICATE, NOTIFY_ACTION

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
    data['audience'] = {'id':record['_deposit']['owner'],'type':'Person'}
    data['actor'] = {'id':record['_deposit']['created_by'],'type':'Person'}
    item_url = '{host_url}/records/{recid}'.format(host_url=get_url_root(), recid = record.get('id'))
    pid = get_record_permalink(record)
    data['object'] = {'id':item_url, 'ietf:cite-as':pid, 'type':['Page','sorg:WebPage']}
    data['context'] = data['object']
    data['origin'] = {'id':get_url_root(), 'inbox':get_url_inbox(), 'type':'Service'}
    data['target'] = data['origin']
    return data

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
        payload[key] = vlaue
    payload["id"] = str(uuid.uuid4())
    payload["type"].append(notification_type)
    return payload

def send_notification_inbox(payload):
    """send notification to inbox

    :param dict payload: notification payload
    """
    sender = ldnlib.Sender()
    inbox = payload['target']['inbox']
    
    sender.send(inbox, payload,verify = INBOX_VERIFY_TLS_CERTIFICATE)
    
def get_record_permalink(record):
    """
    Recordインスタンスから識別子を取得する。存在しない場合アイテムurlを返す。
    weko_records_ui.utils.get_record_permalinkと処理は一緒。
    wekoのメソッドを使っていいなら排除
    """
    doi = record.pid_doi
    cnri = record.pid_cnri
    
    if doi or cnri:
        return doi.pid_value if doi else cnri.pid_value
    
    return '{host_url}/records/{recid}'.format(host_url=get_url_root(),recid=record.get('id'))

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
    # TODO :ポートがnginxとinboxで違うため、root/inboxだと無理
    # rootのurlから":"以降（ポート）をinboxのポートに置き換え。その後/inboxを追加？
    # ただしrootの部分はrequestがなかったら設定値のものを使う
    # :以降のものをどうやって発見するか
    # 1. 正規表現 ":([0-9]+)/"
    # 2. 設定値から特定の数値の取得 "800"(それが設定値として与えられているかの要確認)
    #return get_url_root()+"/inbox"
    
    if request:
        root = request.host_url
        
        