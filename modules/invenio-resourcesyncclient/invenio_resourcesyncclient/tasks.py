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
from datetime import datetime
import signal
import requests
from lxml import etree
from urllib.parse import urlparse
from celery import current_task, shared_task
from celery.task.control import inspect
from celery.utils.log import get_task_logger
from invenio_db import db
from invenio_oaiharvester.harvester import DCMapper, DDIMapper, JPCOARMapper
from invenio_oaiharvester.tasks import event_counter

from flask import current_app

from .models import ResyncIndexes, ResyncLogs
from .utils import get_list_records, process_item
logger = get_task_logger(__name__)


def is_harvest_running(id, task_id):
    """Check harvest running."""
    actives = inspect().active()
    for worker in actives:
        for task in actives[worker]:
            if task['name'] == 'invenio_resourcesyncclient.tasks.' \
                               'run_harvesting':
                if eval(task['args'])[0] == str(id) and task['id'] != task_id:
                    return True
    return False


@shared_task
def run_sync_import(id, start_time):
    """Run harvest."""
    if is_harvest_running(id, run_sync_import.request.id):
        return ({'task_state': 'SUCCESS',
                 'task_id': run_sync_import.request.id})

    current_app.logger.info('[{0}] [{1}] START'.format(0, 'Resync Import'))
    # For registering runtime stats
    start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')

    resync = ResyncIndexes.query.filter_by(id=id).first()
    resync.task_id = current_task.request.id
    counter = {}
    counter['processed_items'] = 0
    counter['created_items'] = 0
    counter['updated_items'] = 0
    counter['deleted_items'] = 0
    counter['error_items'] = 0
    resync_log = ResyncLogs(
        resync_indexes_id=id,
        status='Running',
        log_type='Import',
        start_time=datetime.utcnow(),
        counter=counter
    )
    db.session.add(resync_log)
    db.session.commit()
    try:
        DCMapper.update_itemtype_map()
        pause = False

        def sigterm_handler(*args):
            nonlocal pause
            pause = True
        signal.signal(signal.SIGTERM, sigterm_handler)
        while True:
            current_app.logger.info('[{0}] [{1}]'.format(
                                    0, 'Processing records'))
            # for record_id in records:
            try:
                hostname = urlparse(resync.base_url)
                records_id = get_list_records(resync.resync_save_dir)
                for i in records_id:
                    record = get_record(
                        url='{}://{}/oai2d'.format(
                            hostname.scheme,
                            hostname.netloc
                        ),
                        record_id=i,
                        metadata_prefix='jpcoar',
                    )
                    process_item(record[0], resync, counter)
            except Exception as ex:
                current_app.logger.error(
                    'Error occurred while processing harvesting item\n' + str(ex))
                db.session.rollback()
                event_counter('error_items', counter)
            db.session.commit()
            resync_log.status = 'Successful'
            break
    except Exception as ex:
        resync_log.status = 'Failed'
        current_app.logger.error(str(ex))
        resync_log.errmsg = str(ex)[:255]
    finally:
        resync.task_id = None
        end_time = datetime.utcnow()
        resync_log.end_time = end_time
        resync_log.counter = counter
        current_app.logger.info('[{0}] [{1}] END'.format(0, 'Resync Import'))
        db.session.commit()
        return ({'task_state': 'SUCCESS',
                 'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                 'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                 'execution_time': str(end_time - start_time),
                 'task_name': 'import',
                 'task_type': 'import',
                 'repository_name': 'weko',  # TODO: Set and Grab from config
                 'task_id': run_sync_import.request.id
                 },
                )


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
        'identifier': 'oai:invenio:recid/{}'.format(record_id)
    }
    records = None
    response = requests.get(url, params=payload)
    et = etree.XML(response.text.encode(encoding))
    current_app.logger.debug(et)
    records = et.findall('./GetRecord/record', namespaces=et.nsmap)
    return records
