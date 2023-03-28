# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from __future__ import absolute_import, print_function

import os
import time

import pkg_resources
from flask_mail import Attachment

from invenio_mail.tasks import send_email


def test_send_message_outbox(email_task_app):
    """Test sending a message using Task module."""
    with email_task_app.app_context():
        with email_task_app.extensions['mail'].record_messages() as outbox:
            msg = {
                'subject': 'Test1',
                'sender': 'test1@test1.test1',
                'recipients': ['test1@test1.test1']
            }

            send_email.delay(msg)

            assert len(outbox) == 1
            sent_msg = outbox[0]
            assert sent_msg.subject == 'Test1'
            assert sent_msg.sender == 'test1@test1.test1'
            assert sent_msg.recipients == ['test1@test1.test1']


def test_send_message_stream(email_task_app):
    """Test sending a message using Task module."""
    with email_task_app.app_context():
        with email_task_app.extensions['mail'].record_messages() as outbox:
            msg = {
                'subject': 'Test2',
                'sender': 'test2@test2.test2',
                'recipients': ['test2@test2.test2']
            }

            send_email.delay(msg)

            result_stream = email_task_app.extensions['invenio-mail'].stream
            assert result_stream.getvalue().find(
                'From: test2@test2.test2') != -1
            assert result_stream.getvalue().find('To: test2@test2.test2') != -1
            assert result_stream.getvalue().find('Subject: Test2') != -1


def test_send_message_with_attachments(email_task_app):
    """Test sending a message with attachments."""
    with email_task_app.app_context():
        filename = pkg_resources.resource_filename(
            __name__, os.path.join('attachments', 'invenio.svg'))
        content_type = 'image/svg+xml'
        data = pkg_resources.resource_string(
            __name__, os.path.join('attachments', 'invenio.svg'))

        attachments = [Attachment(filename, content_type, data)]
        msg = {
            'subject': 'Test3',
            'sender': 'test3@test3.test3',
            'recipients': ['test3@test3.test3'],
            'attachments': attachments
        }

        # send_email.delay(msg)

        # result_stream = email_task_app.extensions['invenio-mail'].stream
        # assert result_stream.getvalue().find(
        #     'Content-Transfer-Encoding: base64') != -1
        # assert result_stream.getvalue().find(
        #     'Content-Disposition: attachment;') != -1


def test_send_message_with_date(email_task_app):
    """Test sending a message with a date."""
    with email_task_app.app_context():
        msg = {
            'subject': 'Test4',
            'sender': 'test4@test4.test4',
            'recipients': ['test4@test4.test4'],
            'date': 1456242014.398119
        }

        os.environ['TZ'] = 'Europe/London'
        time.tzset()
        send_email.delay(msg)
        result_stream = email_task_app.extensions['invenio-mail'].stream
        assert result_stream.getvalue().find('Date: Tue, 23 Feb 2016') != -1
