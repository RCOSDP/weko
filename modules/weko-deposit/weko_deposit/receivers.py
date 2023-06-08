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
from invenio_records.models import RecordMetadata
from weko_records.api import FeedbackMailList
from weko_records.utils import json_loader

from .api import WekoDeposit
from .pidstore import get_record_without_version


def append_file_content(sender, json=None, record=None, index=None, **kwargs):
    """Append file content to ES record."""
    try:
        dep = WekoDeposit.get_record(record.id)
        pid = get_record_without_version(dep.pid)
        record_metadata = RecordMetadata.query.filter_by(id=record.id).first()
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
        _, jrc, _ = json_loader(metadata, pid)
        dep.data = metadata
        dep.jrc = jrc

        # Update data based on data from DB
        dep.jrc['weko_shared_ids'] = im.get('weko_shared_ids')
        dep.jrc['weko_creator_id'] = im.get('owner')
        dep.jrc['_item_metadata'] = im
        dep.jrc['control_number'] = im.get('recid')
        dep.jrc['_oai'] = im.get('_oai')
        dep.jrc['relation_version_is_last'] = True \
            if pid == get_record_without_version(pid) else False
        dep._convert_jpcoar_data_to_es()
        im.pop('recid')
        dep.get_content_files()

        # Updated metadata's path
        if record_metadata.status == PIDStatus.REGISTERED:
            dep.jrc.update(dict(path=dep.get('path')))
        else:
            dep.jrc.update(dict(path=[]))

        ps = dict(publish_status=dep.get('publish_status'))
        dep.jrc.update(ps)
        if dep.jrc.get('content', None):
            kwargs['arguments']['pipeline'] = 'item-file-pipeline'
        json.update(dep.jrc)

        # Updated FeedbackMail List
        mail_list = FeedbackMailList.get_mail_list_by_item_id(record.id)
        if mail_list:
            feedback_mail = {
                'feedback_mail_list': mail_list
            }
            json.update(feedback_mail)

        current_app.logger.info('FINISHED reindex record: {0}'.format(
            im['control_number']))
    except Exception:
        import traceback
        current_app.logger.error(traceback.print_exc())
