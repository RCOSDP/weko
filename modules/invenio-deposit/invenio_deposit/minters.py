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

"""Persistent identifier minters."""

from __future__ import absolute_import

import uuid

from .providers import DepositProvider


def deposit_minter(record_uuid, data):
    """Mint a deposit identifier.

    A PID with the following characteristics is created:

    .. code-block:: python

        {
            "object_type": "rec",
            "object_uuid": record_uuid,
            "pid_value": "<new-pid-value>",
            "pid_type": "depid",
        }

    The following deposit meta information are updated:

    .. code-block:: python

        deposit['_deposit'] = {
            "id": "<new-pid-value>",
            "status": "draft",
        }

    :param record_uuid: Record UUID.
    :param data: Record content.
    :returns: A :class:`invenio_pidstore.models.PersistentIdentifier` object.
    """
    provider = DepositProvider.create(
        object_type='rec',
        object_uuid=record_uuid,
        pid_value=uuid.uuid4().hex,
    )
    data['_deposit'] = {
        'id': provider.pid.pid_value,
        'status': 'draft',
    }
    return provider.pid
