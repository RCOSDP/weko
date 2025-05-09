# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015, 2016, 2017 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Utils for communities."""

from __future__ import absolute_import, print_function

import os
from io import SEEK_END, SEEK_SET
from math import ceil
from uuid import UUID

from flask import current_app
from flask_login import current_user
from invenio_db import db
from invenio_files_rest.errors import FilesException
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_records.api import Record


class Pagination(object):
    """Helps with rendering pagination list."""

    def __init__(self, page, per_page, total_count):
        """Init pagination."""
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        """Return number of pages."""
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        """Return true if it has previous page."""
        return self.page > 1

    @property
    def has_next(self):
        """Return true if it has next page."""
        return self.page < self.pages

    def iter_pages(self, left_edge=1, left_current=1, right_current=3,
                   right_edge=1):
        """Iterate the pages."""
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1
                and num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


def render_template_to_string(input, _from_string=False, **context):
    """Render a template from the template folder with the given context.

    Code based on
    `<https://github.com/mitsuhiko/flask/blob/master/flask/templating.py>`_
    :param input: the string template, or name of the template to be
                  rendered, or an iterable with template names
                  the first one existing will be rendered
    :param context: the variables that should be available in the
                    context of the template.
    :return: a string
    """
    if _from_string:
        template = current_app.jinja_env.from_string(input)
    else:
        template = current_app.jinja_env.get_or_select_template(input)
    return template.render(context)


def save_and_validate_logo(logo_stream, logo_filename, community_id):
    """Validate if communities logo is in limit size and save it."""
    cfg = current_app.config

    logos_bucket_id = cfg['COMMUNITIES_BUCKET_UUID']
    logo_max_size = cfg['COMMUNITIES_LOGO_MAX_SIZE']
    logos_bucket = Bucket.query.get(logos_bucket_id)
    ext = os.path.splitext(logo_filename)[1]
    ext = ext[1:] if ext.startswith('.') else ext

    logo_stream.seek(SEEK_SET, SEEK_END)  # Seek from beginning to end
    logo_size = logo_stream.tell()
    if logo_size > logo_max_size:
        return None

    if ext in cfg['COMMUNITIES_LOGO_EXTENSIONS']:
        key = "{0}/logo.{1}".format(community_id, ext)
        logo_stream.seek(0)  # Rewind the stream to the beginning
        ObjectVersion.create(logos_bucket, key, stream=logo_stream,
                             size=logo_size)
        return ext
    else:
        return None


def initialize_communities_bucket():
    """Initialize the communities file bucket.

    :raises: `invenio_files_rest.errors.FilesException`
    """
    bucket_id = UUID(current_app.config['COMMUNITIES_BUCKET_UUID'])

    if Bucket.query.get(bucket_id):
        raise FilesException("Bucket with UUID {} already exists.".format(
            bucket_id))
    else:
        storage_class = current_app.config['FILES_REST_DEFAULT_STORAGE_CLASS']
        try:
            location = Location.get_default()
            bucket = Bucket(id=bucket_id,
                            location=location,
                            default_storage_class=storage_class)
            db.session.add(bucket)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()


def format_request_email_templ(increq, template, **ctx):
    """Format the email message element for inclusion request notification.

    Formats the message according to the provided template file, using
    some default fields from 'increq' object as default context.
    Arbitrary context can be provided as keywords ('ctx'), and those will
    not be overwritten by the fields from 'increq' object.

    :param increq: Inclusion request object for which the request is made.
    :type increq: `invenio_communities.models.InclusionRequest`
    :param template: relative path to jinja template.
    :type template: str
    :param ctx: Optional extra context parameters passed to formatter.
    :type ctx: dict.
    :returns: Formatted message.
    :rtype: str
    """
    # Add minimal information to the contex (without overwriting).
    curate_link = '{site_url}/communities/{id}/curate/'.format(
        site_url=current_app.config['THEME_SITEURL'],
        id=increq.community.id)

    min_ctx = dict(
        record=Record.get_record(increq.record.id),
        requester=increq.user,
        community=increq.community,
        curate_link=curate_link,
    )
    for k, v in min_ctx.items():
        if k not in ctx:
            ctx[k] = v

    msg_element = render_template_to_string(template, **ctx)
    return msg_element


def format_request_email_title(increq, **ctx):
    """Format the email message title for inclusion request notification.

    :param increq: Inclusion request object for which the request is made.
    :type increq: `invenio_communities.models.InclusionRequest`
    :param ctx: Optional extra context parameters passed to formatter.
    :type ctx: dict.
    :returns: Email message title.
    :rtype: str
    """
    template = current_app.config["COMMUNITIES_REQUEST_EMAIL_TITLE_TEMPLATE"],
    return format_request_email_templ(increq, template, **ctx)


def format_request_email_body(increq, **ctx):
    """Format the email message body for inclusion request notification.

    :param increq: Inclusion request object for which the request is made.
    :type increq: `invenio_communities.models.InclusionRequest`
    :param ctx: Optional extra context parameters passed to formatter.
    :type ctx: dict.
    :returns: Email message body.
    :rtype: str
    """
    template = current_app.config["COMMUNITIES_REQUEST_EMAIL_BODY_TEMPLATE"],
    return format_request_email_templ(increq, template, **ctx)


def send_community_request_email(increq):
    """Signal for sending emails after community inclusion request."""
    from flask_mail import Message
    from invenio_mail.tasks import send_email

    msg_body = format_request_email_body(increq)
    msg_title = format_request_email_title(increq)

    sender = current_app.config['COMMUNITIES_REQUEST_EMAIL_SENDER']

    msg = Message(
        msg_title,
        sender=sender,
        recipients=[increq.community.owner_user.email, ],
        body=msg_body
    )

    send_email.delay(msg.__dict__)


def get_user_role_ids():
    """Get role.id of current user.

    :returns role_ids: List of role.id.
    """
    role_ids = []
    if current_user and current_user.is_authenticated:
        role_ids = [role.id for role in current_user.roles]

    return role_ids


def get_repository_id_by_item_id(item_id):
    """Get repository_id by item_id."""
    from weko_index_tree.models import Index
    from .models import Community
    record = Record.get_record(item_id)
    index_id = record.get("path")
    index = Index.get_index_by_id(index_id[0])
    repository_id = "Root Index"
    while True:
        com = Community.query.filter_by(root_node_id=index.id).first()
        if com:
            repository_id = com.id
            break
        if not index.parent:
            break
        index = Index.get_index_by_id(index.parent)

    return repository_id

def delete_empty(data):
    if isinstance(data, dict):
        result = {}
        flg = False
        if len(data) == 0:
            return flg, result
        else:
            for k, v in data.items():
                not_empty, dd = delete_empty(v)
                if not_empty:
                    flg = True
                    result[k] = dd
            return flg, result
    elif isinstance(data, list):
        result = []
        flg = False
        if len(data) == 0:
            return flg, None
        else:
            for d in data:
                not_empty, dd = delete_empty(d)
                if not_empty:
                    flg = True
                    result.append(dd)
            return flg, result
    else:
        if data:
            return True, data
        else:
            return False, None
