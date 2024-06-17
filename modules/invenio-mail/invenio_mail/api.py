# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Template based messages."""

from flask import render_template
from flask_mail import Message


class TemplatedMessage(Message):
    """Siplify creation of templated messages."""

    def __init__(self, template_body=None, template_html=None, ctx=None, **kwargs):
        r"""Build message body and HTML based on provided templates.

        Provided templates can use keyword arguments ``body`` and ``html``
        respectively.

        :param template_body: Path to the text template.
        :param template_html: Path to the html template.
        :param ctx: A mapping containing additional information passed to the
            template.
        :param \*\*kwargs: Keyword arguments as defined in
            :class:`flask_mail.Message`.
        """
        ctx = ctx if ctx else {}
        if template_body:
            kwargs["body"] = render_template(
                template_body, body=kwargs.get("body"), **ctx
            )
        if template_html:
            kwargs["html"] = render_template(
                template_html, html=kwargs.get("html"), **ctx
            )
        super(TemplatedMessage, self).__init__(**kwargs)
