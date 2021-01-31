# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Utils for weko-accounts."""
import random
import string

from flask import current_app, request
from invenio_db import db

from .models import ShibbolethUser


def get_remote_addr():
    """
    Get remote ip address.

    # An 'X-Forwarded-For' header includes a comma separated list of the
    # addresses, the first address being the actual remote address.
    """
    if not request:
        return None

    address = request.headers.get('X-Real-IP', None)

    if address is None:
        address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if address is not None:
            address = address.encode('utf-8').split(b',')[0].strip().decode()

    return address


def generate_random_str(length=128):
    """Generate secret key."""
    rng = random.SystemRandom()

    return ''.join(
        rng.choice(string.ascii_letters + string.digits)
        for _ in range(0, length)
    )


def parse_attributes():
    """Parse arguments from environment variables."""
    attrs = {}
    error = False

    for header, attr in current_app.config[
            'WEKO_ACCOUNTS_SSO_ATTRIBUTE_MAP'].items():
        required, name = attr
        value = request.form.get(header, '') if request.method == 'POST' \
            else request.args.get(header, '')
        attrs[name] = value

        if required and not value:
            error = True

    return attrs, error


def get_shib_roles(user):
    """Parse arguments from environment variables."""
    if not user or not user.get_id():
        return []

    with db.session.no_autoflush:
        shib_user = ShibbolethUser.query.filter_by(
            shib_mail=user.email).one_or_none()

        if shib_user:
            return shib_user.shib_roles
        else:
            return []
