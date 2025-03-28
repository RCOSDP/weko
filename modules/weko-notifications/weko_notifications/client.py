# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

import ldnlib

class NotificationClient:
    """Notification client class."""
    def __init__(self, inbox):
        """Initialize notification client.

        Args:
            inbox (str): Inbox URL.
        """
        self.inbox = inbox

    def send(self, notification):
        """Send notification.

        Args:
            notification (Notification): Notification object.
        Returns:
            str: Notification ID sent.
        """
        notification.validate() if not notification._is_validated else None
        sender = ldnlib.Sender()
        sender.send(self.inbox, notification.payload)
        return notification.id

    def notifications(self):
        """
        Returns:
            list[str]: List of notification IDs.
        """
        consumer = ldnlib.Consumer()
        notifications = consumer.notifications(
            self.inbox, accept="application/ld+json"
        )
        return notifications

