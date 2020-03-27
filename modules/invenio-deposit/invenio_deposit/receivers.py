# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Deposit listeners."""

from __future__ import absolute_import, print_function

from invenio_indexer.tasks import index_record


def index_deposit_after_publish(sender, action=None, pid=None, deposit=None):
    """Index the record after publishing.

    .. note:: if the record is not published, it doesn't index.

    :param sender: Who send the signal.
    :param action: Action executed by the sender. (Default: ``None``)
    :param pid: PID object. (Default: ``None``)
    :param deposit: Deposit object. (Default: ``None``)
    """
    if action == 'publish':
        _, record = deposit.fetch_published()
        index_record.delay(str(record.id))
