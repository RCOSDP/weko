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

"""Weko Deposit Pid Store."""

from sqlalchemy.exc import SQLAlchemyError

from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.fetchers import FetchedPID
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, \
    RecordIdentifier

from .errors import WekoDepositError
from .logger import weko_logger


def weko_deposit_minter(record_uuid, data, recid=None):
    """Mint a record identifier.

    Generate a new recid and depid for the record.

    Args:
        record_uuid (str): UUID of record.
        data (dict): Record data to fill the deposit.
        recid (str): Record ID.

    Returns:
        :obj:`PersistentIdentifier`: depid; PID object.
    """
    if recid is None:
        weko_logger(key='WEKO_COMMON_IF_ENTER', branch='recid is None')

        id_ = RecordIdentifier.next()
    else:
        weko_logger(key='WEKO_COMMON_IF_ENTER', branch='recid is not None')
        if isinstance(recid, int):
            weko_logger(key='WEKO_COMMON_IF_ENTER', branch='recid is int')
            RecordIdentifier.insert(recid)

        id_ = recid

    recid = PersistentIdentifier.create(
        'recid',
        str(id_),
        object_type='rec',
        object_uuid=record_uuid,
        status=PIDStatus.RESERVED
    )
    data['recid'] = str(recid.pid_value)

    # Create depid with same pid_value of the recid
    depid = PersistentIdentifier.create(
        'depid',
        str(recid.pid_value),
        object_type='rec',
        object_uuid=record_uuid,
        status=PIDStatus.RESERVED
    )
    data.update({
        '_deposit': {
            'id': depid.pid_value,
            'status': 'draft',
        },
    })

    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=depid)
    return depid


def weko_deposit_fetcher(record_uuid, data):
    """Fetch a deposit identifier.

    Get the pid of records from the record data.

    Args:
        record_uuid (str): Record UUID.
        data (dict): Record data.

    Returns:
        :obj:`FetchedPID`: PID object that contains pid_value.
    """
    pid_value = data.get('_deposit', {}).get('id')

    result =FetchedPID(
        provider=None,
        pid_type='depid',
        pid_value=pid_value,
    ) if pid_value else None
    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
    return result


def get_latest_version_id(recid):
    """Get latest version ID.

    Get latest version ID to store item of before updating.

    Args:
        recid (str): Record ID.

    Returns:
        int: Version ID.
    """
    version_id = 1
    pid_value = "{}.%".format(recid)
    pid = PersistentIdentifier.query.filter_by(pid_type='recid')\
        .filter(PersistentIdentifier.pid_value.like(pid_value)).all()
    if pid:
        weko_logger(key='WEKO_COMMON_IF_ENTER', branch='pid is not empty')

        version_id = max([int(idx.pid_value.split('.')[-1]) for idx in pid])
        version_id += 1

    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=version_id)
    return version_id


def get_record_identifier(recid):
    """Get record identifier.

    Args:
        recid (str): Record ID.

    Returns:
        RecordIdentifier: Record ID without version ID.\
            If not found, return None.
    """
    record_id = None
    try:
        record_id = RecordIdentifier.query.filter_by(recid=int(recid))\
            .one_or_none()
    except SQLAlchemyError as ex:
        weko_logger(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
        # raise WekoDepositError(ex=ex)
    except Exception as ex:
        weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
        # raise WekoDepositError(ex=ex)

    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=record_id)
    return record_id


def get_record_without_version(pid):
    """Get PID of record without version ID.

    Args:
        pid (:obj:`PersistentIdentifier`): PID of record.

    Returns:
        str: PID of record without version ID.
    """
    recid_without_ver = None
    parent_relations = PIDRelation.get_child_relations(pid).one_or_none()
    if parent_relations is not None:
        weko_logger(key='WEKO_COMMON_IF_ENTER',
                    branch='parent_relations is not None')

        parent_pid = PersistentIdentifier.query. \
            filter_by(id=parent_relations.parent_id).one_or_none()
        if parent_pid is not None:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='parent_pid is not None')

            parent_pid_value = parent_pid.pid_value.split(':')[-1]
            recid_without_ver = PersistentIdentifier.get(
                pid_type='recid',
                pid_value=parent_pid_value)

    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=recid_without_ver)
    return recid_without_ver
