# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test package API."""

from invenio_mail.api import TemplatedMessage


def test_templated_message(email_api_app, email_params, email_ctx):
    """Test that all the fields given are inside the message."""
    with email_api_app.app_context():
        msg = TemplatedMessage(
            template_body="invenio_mail/base.txt",
            template_html="invenio_mail/base.html",
            ctx=email_ctx,
            **email_params
        )

        for key in email_params:
            assert email_params[key] == getattr(msg, key), key

        # let's check that the body and html are correctly formatted
        assert "<p>Dear {0},</p>".format(email_ctx["user"]) in msg.html
        assert "Dear {0},".format(email_ctx["user"]) in msg.body
        assert "<p>{0}</p>".format(email_ctx["content"]) in msg.html
        assert "{0}".format(email_ctx["content"]) in msg.body
        assert email_ctx["sender"] in msg.html
        assert email_ctx["sender"] in msg.body


def test_simple_templated_message(email_api_app):
    """Test that defaults are sane."""
    with email_api_app.app_context():
        msg = TemplatedMessage(
            template_body="invenio_mail/base.txt",
            template_html="invenio_mail/base.html",
        )
        assert msg
