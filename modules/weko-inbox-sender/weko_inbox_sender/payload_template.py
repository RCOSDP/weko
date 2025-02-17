# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

from enum import Enum


class PROPERTIES(Enum):
    AT_CONTEXT = ('@context',
                  [
                    'https://www.w3.org/ns/activitystreams',
                    'https://purl.org/coar/notify'
                  ]
                  )
    ACTOR = ('actor', None)
    CONTEXT = ('context', None)
    ID = ('id', None)
    INREPLYTO = ('inReplyTo', None)
    OBJECT = ('object', None)
    ORIGIN = ('origin', None)
    TARGET = ('target', None)
    TYPE = ('type', None)

    def __init__(self, pro, val):
        self.pro = pro
        self.val = val


class PAYLOAD_TEMPLATE(Enum):
    OFFER = ([PROPERTIES.AT_CONTEXT,
             PROPERTIES.ACTOR,
             PROPERTIES.ID,
             PROPERTIES.OBJECT,
             PROPERTIES.ORIGIN,
             PROPERTIES.TARGET,
             PROPERTIES.TYPE
              ], 'Offer')

    UNDO = ([PROPERTIES.AT_CONTEXT,
             PROPERTIES.ACTOR,
             PROPERTIES.CONTEXT,
             PROPERTIES.ID,
             PROPERTIES.OBJECT,
             PROPERTIES.ORIGIN,
             PROPERTIES.TARGET,
             PROPERTIES.TYPE
             ], 'Undo')

    ACCEPT = ([PROPERTIES.AT_CONTEXT,
               PROPERTIES.ACTOR,
               PROPERTIES.CONTEXT,
               PROPERTIES.ID,
               PROPERTIES.INREPLYTO,
               PROPERTIES.OBJECT,
               PROPERTIES.ORIGIN,
               PROPERTIES.TARGET,
               PROPERTIES.TYPE
               ], 'Accept')

    REJECT = ([PROPERTIES.AT_CONTEXT,
               PROPERTIES.ACTOR,
               PROPERTIES.CONTEXT,
               PROPERTIES.ID,
               PROPERTIES.INREPLYTO,
               PROPERTIES.OBJECT,
               PROPERTIES.ORIGIN,
               PROPERTIES.TARGET,
               PROPERTIES.TYPE
               ], 'Reject')

    ANNOUNCE_STANDALONE = ([PROPERTIES.AT_CONTEXT,
                            PROPERTIES.ACTOR,
                            PROPERTIES.CONTEXT,
                            PROPERTIES.ID,
                            PROPERTIES.OBJECT,
                            PROPERTIES.ORIGIN,
                            PROPERTIES.TARGET,
                            PROPERTIES.TYPE
                            ], 'Announce')

    ANNOUNCE_OFFER = ([PROPERTIES.AT_CONTEXT,
                       PROPERTIES.ACTOR,
                       PROPERTIES.CONTEXT,
                       PROPERTIES.ID,
                       PROPERTIES.INREPLYTO,
                       PROPERTIES.OBJECT,
                       PROPERTIES.ORIGIN,
                       PROPERTIES.TARGET,
                       PROPERTIES.TYPE
                       ], 'Announce')

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
