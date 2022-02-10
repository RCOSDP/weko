# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-inbox-sender."""

from enum import Enum

class PROPERTIES(Enum):
    AT_CONTEXT=('@context',['https://www.w3.org/ns/activitystreams','https://purl.org/coar/notify'])
    ACTOR = ('actor','__actor__')
    CONTEXT = ('context','__context__')
    ID = ('id','__id__')
    INREPLYTO = ('inReplyTo','__inReplyTo__')
    OBJECT = ('object','__object__')
    ORIGIN = ('origin','__origin__')
    TARGET = ('target','__target__')
    TYPE = ('type','__type__')
    
    def __init__(self, pro,val):
        self.pro=pro
        self.val=val
    
class PAYLOAD_TEMPLATE(Enum):
    OFFER = ([PROPERTIES.AT_CONTEXT,
             PROPERTIES.ACTOR,
             PROPERTIES.ID,
             PROPERTIES.OBJECT,
             PROPERTIES.ORIGIN,
             PROPERTIES.TARGET,
             PROPERTIES.TYPE
            ],'Offer')
    UNDO = ([PROPERTIES.AT_CONTEXT,
             PROPERTIES.ACTOR,
             PROPERTIES.CONTEXT,
             PROPERTIES.ID,
             PROPERTIES.OBJECT,
             PROPERTIES.ORIGIN,
             PROPERTIES.TARGET,
             PROPERTIES.TYPE
            ],'Undo')
    ACCEPT = ([PROPERTIES.AT_CONTEXT,
             PROPERTIES.ACTOR,
             PROPERTIES.CONTEXT,
             PROPERTIES.ID,
             PROPERTIES.INREPLYTO,
             PROPERTIES.OBJECT,
             PROPERTIES.ORIGIN,
             PROPERTIES.TARGET,
             PROPERTIES.TYPE
            ],'Accept')
    REJECT = ([PROPERTIES.AT_CONTEXT,
             PROPERTIES.ACTOR,
             PROPERTIES.CONTEXT,
             PROPERTIES.ID,
             PROPERTIES.INREPLYTO,
             PROPERTIES.OBJECT,
             PROPERTIES.ORIGIN,
             PROPERTIES.TARGET,
             PROPERTIES.TYPE
            ],'Reject')
    ANNOUNCE_STANDALONE = ([PROPERTIES.AT_CONTEXT,
             PROPERTIES.ACTOR,
             PROPERTIES.CONTEXT,
             PROPERTIES.ID,
             PROPERTIES.OBJECT,
             PROPERTIES.ORIGIN,
             PROPERTIES.TARGET,
             PROPERTIES.TYPE
            ],'Announce')
    ANNOUNCE_OFFER = ([PROPERTIES.AT_CONTEXT,
             PROPERTIES.ACTOR,
             PROPERTIES.CONTEXT,
             PROPERTIES.ID,
            PROPERTIES.INREPLYTO,
             PROPERTIES.OBJECT,
             PROPERTIES.ORIGIN,
             PROPERTIES.TARGET,
             PROPERTIES.TYPE
            ],'Announce')
    
    def __init__(self, properties, notification_type):
        self.properties = properties
        self.notification_type = notification_type
        
    @property
    def template(self):
        template = dict()
        properties = self.properties
        for p in properties:
            if p.pro == 'type':
                template[p.pro] = [self.notification_type]
            else:
                template[p.pro] = p.val
        return template
    
class Notify_ACTION(Enum):
    ENDORSEMENT = "coar-notify:EndorsementAction"
    
    
INBOX_VERIFY_TLS_CERTIFICATE = False
""" If True, verify the server’s TLS certificate """