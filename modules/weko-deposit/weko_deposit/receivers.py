# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Deposit module receivers."""

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from invenio_pidstore.models import PIDStatus
from invenio_records.models import RecordMetadata
from weko_records.api import FeedbackMailList
from weko_records.errors import WekoRecordsError
from weko_records.utils import json_loader

from .api import WekoDeposit
from .errors import WekoDepositError
from .logger import weko_logger
from .pidstore import get_record_without_version

def append_file_content(sender, json=None, record=None, index=None, **kwargs):
    """Append file content to record for ES.

    Append file content to record before reindexing Elasticsearch.

    Args:
        sender (object): The current Flask application. Not used.
        json (dict , Optional): \
            The dumped record dictionary which can be modified.\
            Default to `None`.
        record (object, Optional): The record being indexed. Default to `None`.
        index (Optional): The index in which the record will be indexed.\
            Default to `None`. Not used.
        **kwargs: Keyword arguments. Need to include `with_deleted`.
    """
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

        weko_logger(key='WEKO_COMMON_FOR_STRT')
        for i, key in enumerate(json):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=key)
            if key not in holds:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f'key:{key} not in holds')
                pops.append(key)
        weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_FOR_STRT')
        for i, key in enumerate(pops):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=key)
            json.pop(key)
        weko_logger(key='WEKO_COMMON_FOR_END')

        metadata = dep.item_metadata
        _, jrc, _ = json_loader(metadata, pid,
                                with_deleted=kwargs.get("with_deleted",False))
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
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="record_metadata.status != PIDStatus.DELETED")
            dep.get_content_files()

        # Updated metadata's path
        dep.jrc.update(dict(path=dep.get('path')))

        ps = dict(publish_status=dep.get('publish_status'))
        dep.jrc.update(ps)
        json.update(dep.jrc)

        # Updated FeedbackMail List
        mail_list = FeedbackMailList.get_mail_list_by_item_id(record.id)
        if mail_list:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='mail_list is not empty')

            feedback_mail = {'feedback_mail_list': mail_list}
            json.update(feedback_mail)

        weko_logger(key='WEKO_DEPOSIT_APPEND_FILE_CONTENT',
                    recid=im['control_number'])

    except SQLAlchemyError as ex:
        weko_logger(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
        # raise WekoDepositError(ex=ex)
    except WekoRecordsError as ex:
        raise
    except Exception:
        weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
        # raise WekoDepositError(ex=ex)
