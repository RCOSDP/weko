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
import smtplib
from flask import current_app, render_template
from flask_mail import Message, _MailMixin, _Mail, Mail, Connection

from .admin import _load_mail_cfg_from_db, _set_flask_mail_cfg


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

class _DomainMailMixin(_MailMixin):
    def connect(self):
        app = getattr(self, "app", None) or current_app
        try:
            return DomainConnection(app.extensions['mail'])
        except KeyError:
            raise RuntimeError("The curent application was not configured with Flask-Mail")

class _DomainMail(_Mail, _DomainMailMixin):
    def __init__(self, server, username, password, port, use_tls, use_ssl,
                 default_sender, debug, max_emails, suppress, local_hostname,
                 ascii_attachments=False):
        super().__init__(server, username, password, port, use_tls, use_ssl,
                 default_sender, debug, max_emails, suppress,
                 ascii_attachments)
        self.local_hostname = local_hostname

class DomainMail(Mail, _DomainMailMixin):
    def init_mail(self, config, debug=False, testing=False):
        return _DomainMail(
            config.get('MAIL_SERVER', '127.0.0.1'),
            config.get('MAIL_USERNAME'),
            config.get('MAIL_PASSWORD'),
            config.get('MAIL_PORT', 25),
            config.get('MAIL_USE_TLS', False),
            config.get('MAIL_USE_SSL', False),
            config.get('MAIL_DEFAULT_SENDER'),
            int(config.get('MAIL_DEBUG', debug)),
            config.get('MAIL_MAX_EMAILS'),
            config.get('MAIL_SUPPRESS_SEND', testing),
            config.get('MAIL_LOCAL_HOSTNAME'),
            config.get('MAIL_ASCII_ATTACHMENTS', False)
        )

class DomainConnection(Connection):
    
    def configure_host(self):
        if self.mail.use_ssl:
            if self.mail.local_hostname:
                host = smtplib.SMTP_SSL(self.mail.server, self.mail.port,local_hostname=self.mail.local_hostname)
            else:
                host = smtplib.SMTP_SSL(self.mail.server, self.mail.port)
        else:
            if self.mail.local_hostname:
                host = smtplib.SMTP(self.mail.server, self.mail.port, local_hostname=self.mail.local_hostname)
            else:
                host = smtplib.SMTP(self.mail.server, self.mail.port)

        host.set_debuglevel(int(self.mail.debug))

        if self.mail.use_tls:
            host.starttls()
        if self.mail.username and self.mail.password:
            host.login(self.mail.username, self.mail.password)

        return host

def send_mail(subject: str, recipient_list: list, body=None, html=None,
              attachments: list = []):
    """Send mail."""
    try:
        mail_cfg = _load_mail_cfg_from_db()
        _set_flask_mail_cfg(mail_cfg)
        msg = Message()
        msg.subject = subject
        msg.recipients = recipient_list
        msg.body = body
        msg.html = html
        msg.attachments = attachments
        current_app.extensions['mail'].send(msg)
        return None
    except Exception as ex:
        current_app.logger.error('Unable to send email: {} - {}'.format(
            subject, ex))
        return ex
