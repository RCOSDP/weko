# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Files download/upload REST API similar to S3 for Invenio."""

from __future__ import absolute_import, print_function

import sys

from six import BytesIO

if sys.version_info.major == 2:
    PY2 = True
else:
    PY2 = False


def login_user(client, user):
    """Log in a specified user."""
    with client.session_transaction() as sess:
        sess['user_id'] = user.id if user else None
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
