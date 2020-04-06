# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Weko Deposit Pid Store."""

from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.fetchers import FetchedPID
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, \
    RecordIdentifier


def weko_deposit_minter(record_uuid, data, recid=None):
    """Weko deposit."""
    if not recid:
        id_ = RecordIdentifier.next()
    else:
        if isinstance(recid, int):
            RecordIdentifier.insert(recid)
        id_ = recid
    recid = PersistentIdentifier.create(
        'recid',
        str(id_),
        object_type='rec',
        object_uuid=record_uuid,
        status=PIDStatus.REGISTERED
    )
    data['recid'] = str(recid.pid_value)

    # Create depid with same pid_value of the recid
    depid = PersistentIdentifier.create(
        'depid',
        str(recid.pid_value),
        object_type='rec',
        object_uuid=record_uuid,
        status=PIDStatus.REGISTERED,
    )

    data.update({
        '_deposit': {
            'id': depid.pid_value,
            'status': 'draft',
        },
    })
    return depid


def weko_deposit_fetcher(record_uuid, data):
    """Fetch a deposit identifier."""
    pid_value = data.get('_deposit', {}).get('id')
    return FetchedPID(
        provider=None,
        pid_type='depid',
        pid_value=pid_value,
    ) if pid_value else None


def get_latest_version_id(recid):
    """Get latest version ID to store item of before updating."""
    version_id = 1
    pid_value = "{}.%".format(recid)
    pid = PersistentIdentifier.query.filter_by(pid_type='recid')\
        .filter(PersistentIdentifier.pid_value.like(pid_value)).all()
    if pid:
        version_id = int(max([idx.pid_value.split('.')[-1] for idx in pid])) + 1

    return version_id


def get_record_identifier(recid):
    """Get record identifier."""
    record_id = None
    try:
        record_id = RecordIdentifier.query.filter_by(recid=int(recid))\
            .one_or_none()
    except ValueError:
        pass
    return record_id


def get_record_without_version(pid):
    """Get PID of record without version ID."""
    recid_without_ver = None
    parent_relations = PIDRelation.get_child_relations(pid).one_or_none()
    if parent_relations:
        parent_pid = PersistentIdentifier.query. \
            filter_by(id=parent_relations.parent_id).one_or_none()
        if parent_pid:
            parent_pid_value = parent_pid.pid_value.split(':')[-1]
            recid_without_ver = PersistentIdentifier.get(
                pid_type='recid',
                pid_value=parent_pid_value)

    return recid_without_ver
