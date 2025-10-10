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

"""WEKO3 module docstring."""
import json
import os
import signal
import ssl
import traceback
from datetime import datetime
from urllib.parse import urlparse

import pytz
import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from flask import current_app
from invenio_db import db
from invenio_oaiharvester.harvester import DCMapper, DDIMapper, JPCOARMapper
from invenio_oaiharvester.tasks import event_counter
from lxml import etree

from .api import ResyncHandler
from .config import INVENIO_RESYNC_INDEXES_MODE, \
    INVENIO_RESYNC_INDEXES_STATUS, INVENIO_RESYNC_LOGS_STATUS, \
    INVENIO_RESYNC_MODE, INVENIO_RESYNC_SAVE_PATH
from .models import ResyncIndexes, ResyncLogs
from .utils import get_list_records, process_item, process_sync

RESYNC_SAVING_FORMAT_BIOPROJECT = 'BIOPROJECT-JSON-LD'
RESYNC_SAVING_FORMAT_BIOSAMPLE = 'BIOSAMPLE-JSON-LD'

ssl._create_default_https_context = ssl._create_unverified_context


logger = get_task_logger(__name__)


def is_running_task(id):
    """Check harvest running."""
    resync = ResyncHandler.get_resync(id)
    if resync and resync.task_id:
        return True
    else:
        return False


@shared_task
def run_sync_import(id):
    current_app.logger.debug('{0} {1} {2}: {3}'.format(
        __file__, 'start run_sync_import()', 'id', id))

    if is_running_task(id):
        current_app.logger.debug('{0} {1} {2}: {3}'.format(
            __file__, 'end run_sync_import()', 'id', id))
        return (
            {
                'task_state': 'SUCCESS',
                'task_id': run_sync_import.request.id
            }
        )
    start_time = datetime.now()
    resync = db.session.query(ResyncIndexes).filter_by(id=id).first()
    counter = init_counter()
    resync_index = ResyncHandler.get_resync(id)

    resync_log = prepare_log(
        resync,
        id,
        counter,
        task_id=run_sync_import.request.id,
        log_type='import'
    )
    try:
        DCMapper.update_itemtype_map()
        pause = False

        def sigterm_handler(*args):
            nonlocal pause
            pause = True

        signal.signal(signal.SIGTERM, sigterm_handler)
        base = get_list_records(resync.id)
        while True:
            current_app.logger.info('[{0}] [{1}]'.format(
                0, 'Processing records'))
            try:
                hostname = urlparse(resync.base_url)
                records = get_list_records(resync.id)
                current_app.logger.debug(
                    "len(records):{0}".format(len(records)))
                successful = []
                for i in records:
                    try:
                        current_app.logger.debug('{0} {1} {2}: {3}'.format(
                            __file__, 'run_sync_import()', 'resource', i))
                        if INVENIO_RESYNC_MODE:
                            if (resync.saving_format ==
                                    RESYNC_SAVING_FORMAT_BIOSAMPLE) or \
                                (resync.saving_format ==
                                    RESYNC_SAVING_FORMAT_BIOPROJECT):
                                record = get_record_from_json_file(i)
                            else:
                                record = get_record_from_file(i)

                        else:
                            record = get_record(
                                url='{}://{}/oai'.format(
                                    hostname.scheme,
                                    hostname.netloc
                                ),
                                record_id=i,
                                metadata_prefix='jpcoar_1.0',
                            )

                        if len(record) == 1:
                            process_item(record[0], resync, counter)
                            db.session.commit()
                            successful.append(i)
                    except Exception as ex:
                        db.session.rollback()
                        current_app.logger.exception(
                            'Error occurred while importing item')
                        current_app.logger.error(ex)
                        event_counter('error_items', counter)
                        continue

                for item in successful:
                    records.remove(item)

                resync_index.update({
                    'result': json.dumps(records)
                })

            except Exception as ex:
                current_app.logger.error(traceback.format_exc())
                current_app.logger.error(
                    'Error occurred while processing harvesting item\n' + str(
                        ex))

            resync_log.status = current_app.config.get(
                "INVENIO_RESYNC_LOGS_STATUS",
                INVENIO_RESYNC_LOGS_STATUS
            ).get('successful')

            break

        current_app.logger.debug('{0} {1} {2}: {3}'.format(
            __file__, 'end run_sync_import()', 'id', id))
    except Exception as ex:
        current_app.logger.error(traceback.format_exc())
        resync_log.status = current_app.config.get(
            "INVENIO_RESYNC_LOGS_STATUS",
            INVENIO_RESYNC_LOGS_STATUS
        ).get('failed')
        current_app.logger.error(str(ex))
        resync_log.errmsg = str(ex)[:255]
    finally:
        try:
            res = finish(
                resync,
                resync_log,
                counter,
                start_time,
                run_sync_import.request.id,
                log_type='import'
            )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            end_time = datetime.now()
            res = (
                {
                    'task_state': 'FAILED',
                    'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'execution_time': str(end_time - start_time),
                    'task_name': 'import',
                    'task_type': 'import',
                    'repository_name': 'weko',
                    'task_id': resync_sync.request.id
                },
            )
    return res


def get_record_from_file(rc):
    """Get records """
    record = etree.Element('record')
    header = etree.SubElement(record, 'header')
    identifier = etree.SubElement(header, 'identifier')
    identifier.text = rc['uri']
    datestamp = etree.SubElement(header, 'datestamp')
    datestamp.text = (datetime.fromtimestamp(
        rc['timestamp'], tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")
    metadata = etree.SubElement(record, 'metadata')
    filename = ''
    for l in rc['ln']:
        if (l['rel'] == 'file'):
            filename = l['href']
    try:
        et = etree.parse(filename)
        metadata.extend(et.findall('.'))
        records = [record]
    except Exception as e:
        current_app.logger.error(e)
        records = []

    return records


def get_record_from_json_file(rc):
    """ Creates and returns record information from a JSON-LD format file.

        Create and return record information based on the following
          information contained in <url> of ResourceList.
            ['timestamp']: Time the resource was updated.
            ['ln']['href']: Path where the resource file retrieved
                            by ResouceSync is stored.
       If creation of record information fails, empty information is returned.

        Args:
            rc: Information equivalent to <url> in ResourceList.

        Returns:
            record: record information created from a file in JSON-LD
                    format. If creation fails, empty information is returned.
    """
    filename = ''
    for l in rc['ln']:
        if (l['rel'] == 'file'):
            filename = l['href']
    record = {'record': {'header': {}}}
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
            record['record']['metadata'] = json_data

        record['record']['header']['identifier'] = json_data['identifier']
        record['record']['header']['datestamp'] = (datetime.fromtimestamp(
            rc['timestamp'], tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")
        records = [record]
    except Exception as e:
        current_app.logger.error(e)
        records = []

    return records


def get_record(
        url,
        record_id=None,
        metadata_prefix=None,
        encoding='utf-8'):
    """Get records by record_id."""
    # Avoid SSLError - dh key too small
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
    payload = {
        'verb': 'GetRecord',
        'metadataPrefix': metadata_prefix,
        'identifier': 'oai:weko3.example.org:{}'.format('%08d' % int(record_id))
        # 'identifier': 'oai:invenio:{}'.format('%08d' % int(record_id))

    }
    records = None
    payload_str = "&".join("%s=%s" % (k, v) for k, v in payload.items())
    current_app.logger.debug('{0} {1} {2}: {3}'.format(
        __file__, 'get_record()', 'url', url))
    current_app.logger.debug('{0} {1} {2}: {3}'.format(
        __file__, 'get_record()', 'payload_str', payload_str))

    response = requests.get(url, params=payload_str, verify=False)
    et = etree.XML(response.text.encode(encoding))
    current_app.logger.debug('{0} {1} {2}: {3}'.format(
        __file__, 'get_record()', 'et', response.text.encode(encoding)))
    records = et.findall('./GetRecord/record', namespaces=et.nsmap)
    current_app.logger.debug('{0} {1} {2}: {3}'.format(
        __file__, 'get_record()', 'et', records))

    return records


@shared_task()
def resync_sync(id):
    """Run resource sync."""
    if is_running_task(id):
        return ({
            'task_state': 'SUCCESS',
            'task_id': resync_sync.request.id
        })
    start_time = datetime.now()
    resync = ResyncIndexes.query.filter_by(id=id).first()
    counter = init_counter()
    resync_log = prepare_log(
        resync,
        id,
        counter,
        task_id=resync_sync.request.id,
        log_type='sync'
    )
    resync_log_id = resync_log.id

    try:
        pause = False

        def sigterm_handler(*args):
            nonlocal pause
            pause = True

        signal.signal(signal.SIGTERM, sigterm_handler)
        current_app.logger.info('[{0}] [{1}]'.format(
            0, 'Processing records'))
        process_sync(id, counter)
        resync_log = ResyncLogs.query.filter_by(id=resync_log_id).first()
        resync_log.status = current_app.config.get(
            "INVENIO_RESYNC_LOGS_STATUS",
            INVENIO_RESYNC_LOGS_STATUS
        ).get('successful')

    except Exception as ex:
        resync_log = ResyncLogs.query.filter_by(id=resync_log_id).first()
        resync_log.status = current_app.config.get(
            "INVENIO_RESYNC_LOGS_STATUS",
            INVENIO_RESYNC_LOGS_STATUS
        ).get('failed')
        current_app.logger.error(str(ex))
        resync_log.errmsg = str(ex)[:255]
    finally:
        try:
            resync = ResyncIndexes.query.filter_by(id=id).first()
            res = finish(
                resync,
                resync_log,
                counter,
                start_time,
                resync_sync.request.id,
                log_type='sync'
            )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            end_time = datetime.now()
            res = (
                {
                    'task_state': 'FAILED',
                    'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'execution_time': str(end_time - start_time),
                    'task_name': 'sync',
                    'task_type': 'sync',
                    'repository_name': 'weko',
                    'task_id': resync_sync.request.id
                },
            )
        return res


def prepare_log(resync, id, counter, task_id, log_type):
    """Prepare log for resource sync."""
    current_app.logger.info(
        '[{0}] [{1}] START'.format(0, 'Resync ' + log_type))
    # For registering runtime stats

    resync.task_id = task_id
    try:
        resync_log = ResyncLogs(
            resync_indexes_id=id,
            status=current_app.config.get(
                "INVENIO_RESYNC_LOGS_STATUS",
                INVENIO_RESYNC_LOGS_STATUS
            ).get('running'),
            log_type=log_type,
            start_time=datetime.utcnow(),
            counter=counter,
            task_id=task_id
        )
        db.session.add(resync_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
    return resync_log


def finish(resync, resync_log, counter, start_time, request_id, log_type):
    """Finish resource sync by logging and save to db."""
    resync.task_id = None
    end_time = datetime.now()
    resync_log.end_time = end_time
    resync_log.counter = counter
    current_app.logger.info('[{0}] [{1}] END'.format(0, 'Resync ' + log_type))
    if resync.status == current_app.config.get(
        "INVENIO_RESYNC_INDEXES_STATUS",
        INVENIO_RESYNC_INDEXES_STATUS
    ).get("automatic") and resync_log.log_type == 'sync' and  \
        resync.resync_mode != current_app.config.get(
            "INVENIO_RESYNC_INDEXES_MODE",
            INVENIO_RESYNC_INDEXES_MODE
    ).get("audit"):
        run_sync_import.apply_async(
            args=(
                resync.id,
            )
        )

    return (
        {
            'task_state': 'SUCCESS',
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'execution_time': str(end_time - start_time),
            'task_name': log_type,
            'task_type': log_type,
            'repository_name': 'weko',  # TODO: Set and Grab from config
            'task_id': request_id
        },
    )


def init_counter():
    """Create Init Counter."""
    return {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }


@shared_task
def run_sync_auto():
    """Run sync auto."""
    current_app.logger.debug("[0] START RUN SYNC AUTO")
    list_resync = ResyncHandler.get_list_resync()
    for resync in list_resync:
        if resync.status == current_app.config.get(
            "INVENIO_RESYNC_INDEXES_STATUS",
            INVENIO_RESYNC_INDEXES_STATUS
        ).get("automatic") and resync.is_running:
            delta_time = datetime.now() - resync.updated
            if not delta_time.days % resync.interval_by_day:
                current_app.logger.debug(
                    "[0] START RUN SYNC {}".format(resync.id))
                resync_sync.apply_async(
                    args=(
                        resync.id,
                    )
                )
    current_app.logger.debug("[0] END RUN SYNC AUTO")
    return (
        {
            'task_state': 'SUCCESS',
            'repository_name': 'weko',  # TODO: Set and Grab from config
            'task_id': run_sync_auto.request.id
        },
    )
