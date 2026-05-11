# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Files download/upload REST API similar to S3 for Invenio."""

from __future__ import absolute_import, print_function

import sys

from six import BytesIO
from sqlalchemy import inspect

if sys.version_info.major == 2:
    PY2 = True
else:
    PY2 = False


def login_user(client, user):
    """Log in a specified user."""
    user_id = None
    if user:
        identity = inspect(user).identity
        user_id = identity[0] if identity else user.id
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['_fresh'] = True


class BadBytesIO(BytesIO):
    """Class for closing the stream for further reading abruptly."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        self.called = False
        if PY2:
            return BytesIO.__init__(self, *args, **kwargs)
        else:
            return super(BadBytesIO, self).__init__(*args, **kwargs)

    def read(self, *args, **kwargs):
        """Fail on second read."""
        if self.called:
            self.close()
        self.called = True
        if PY2:
            return BytesIO.read(self, *args, **kwargs)
        else:
            return super(BadBytesIO, self).read(*args, **kwargs)
