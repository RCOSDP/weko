# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Deposit module receivers."""

from flask import current_app
from invenio_pidstore.models import PIDStatus
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records.models import RecordMetadata
from weko_records.api import RequestMailList
from weko_records.utils import json_loader
from sqlalchemy.orm.exc import NoResultFound

from .api import WekoDeposit
from .pidstore import get_record_without_version


def append_file_content(sender, json=None, record=None, index=None, **kwargs):
    """Append file content to ES record."""
    try:
        dep = WekoDeposit.get_record(record.id)
        pid = get_record_without_version(dep.pid)
        record_metadata = RecordMetadata.query.filter_by(id=record.id).first()
        record_metadata.version_id = record_metadata.version_id + 1
        im = dep.copy()
        im.pop('_deposit')
        im.pop('_buckets')
        im['control_number'] = im.get('recid')
        holds = ['_created', '_updated']
        pops = []
        for key in json:
            if key not in holds:
                pops.append(key)
        for key in pops:
            json.pop(key)
        metadata = dep.item_metadata
        _, jrc, _ = json_loader(metadata, pid, with_deleted=kwargs.get("with_deleted",False))
        dep.data = metadata
        dep.jrc = jrc

        # Update data based on data from DB
        dep.jrc['weko_shared_id'] = im.get('weko_shared_id')
        dep.jrc['weko_creator_id'] = im.get('owner')
        dep.jrc['_item_metadata'] = im
        dep.jrc['control_number'] = im.get('recid')
        dep.jrc['_oai'] = im.get('_oai')
        dep.jrc['relation_version_is_last'] = True \
            if pid == get_record_without_version(pid) else False
        dep._convert_jpcoar_data_to_es()
        im.pop('recid')
        if record_metadata.status != PIDStatus.DELETED:
            dep.get_content_files()

        # Updated metadata's path
        dep.jrc.update(dict(path=dep.get('path')))

        ps = dict(publish_status=dep.get('publish_status'))
        dep.jrc.update(ps)
        json.update(dep.jrc)

        request_mail_list = RequestMailList.get_mail_list_by_item_id(record.id)
        if request_mail_list:
            request_mail = {
                'request_mail_list': request_mail_list
            }
            json.update(request_mail)

        current_app.logger.info('FINISHED reindex record: {0}'.format(
            im['control_number']))
    except NoResultFound:
        current_app.logger.error('Indexing error: record does not exists: {0}'.format(
            record.id))
        raise
    except PIDDoesNotExistError:
        current_app.logger.error('Indexing error: pid does not exists: {0}'.format(
            record.id))
    except Exception:
        import traceback
        traceback.print_exc()
