# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test package API."""

from __future__ import absolute_import, print_function

from unittest.mock import patch
from smtplib import SMTPServerDisconnected
from invenio_mail.api import TemplatedMessage, send_mail

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_invenio_mail_api.py::test_TempatedMessage -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
def test_TempatedMessage(app,email_params, email_ctx):
    msg = TemplatedMessage(template_body='invenio_mail_test/base.txt',
                               template_html='invenio_mail_test/base.html',
                               ctx=email_ctx, **email_params)
    for key in email_params:
        assert email_params[key] == getattr(msg, key), key

    # let's check that the body and html are correctly formatted
    assert '<p>Dear {0},</p>'.format(email_ctx['user']) in msg.html
    assert 'Dear {0},'.format(email_ctx['user']) in msg.body
    assert '<p>{0}</p>'.format(email_ctx['content']) in msg.html
    assert '{0}'.format(email_ctx['content']) in msg.body
    assert email_ctx['sender'] in msg.html
    assert email_ctx['sender'] in msg.body

    # template_body is None, template_html is None
    msg = TemplatedMessage()
    assert msg.html == None
    assert msg.body == None

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_invenio_mail_api.py::test_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
def test_send_mail(app, mail_configs):
    # success mail sending
    mock_send = patch('flask_mail._Mail.send')
    result = send_mail("test_subject",['test@mail.nii.ac.jp'],"test_body","test_html")
    assert result == None
    args,kwargs=mock_send.call_args
    msg = args[0]
    assert msg.subject == "test_subject"
    assert msg.html == "test_html"

    # failed mail sending
    mock_send = patch('flask_mail._Mail.send', side_effect=SMTPServerDisconnected())
    result = send_mail("test_subject",['test@mail.nii.ac.jp'],"test_body","test_html")
    assert type(result) == SMTPServerDisconnected
    args,kwargs=mock_send.call_args
    msg = args[0]
    assert msg.subject == "test_subject"
    assert msg.html == "test_html"
