# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Celery tasks used by Invenio-OAIHarvester."""

from __future__ import absolute_import, print_function

import json
import signal
import traceback
from ast import literal_eval as make_tuple
from collections import OrderedDict
from datetime import datetime

import dateutil
from celery import current_task, shared_task
from celery.task.control import inspect
from celery.utils.log import get_task_logger
from flask import current_app
from flask_babelex import gettext as _
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from lxml import etree
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_index_tree.models import Index
from weko_records.models import ItemMetadata
from weko_records_ui.utils import restore, soft_delete

from .api import get_records, list_records, send_run_status_mail
from .config import OAIHARVESTER_ENABLE_ITEM_VERSIONING
from .harvester import DCMapper, DDIMapper, JPCOARMapper
from .harvester import list_records as harvester_list_records
from .harvester import list_sets, map_sets
from .models import HarvestLogs, HarvestSettings
from .signals import oaiharvest_finished
from .utils import ItemEvents, get_identifier_names

logger = get_task_logger(__name__)


@shared_task
def get_specific_records(identifiers, metadata_prefix=None, url=None,
                         name=None, signals=True, encoding=None,
                         **kwargs):
    """Harvest specific records from an OAI repo via OAI-PMH identifiers.

    :param metadata_prefix: The prefix for the metadata return (e.g. 'oai_dc')
    :param identifiers: list of unique identifiers for records to be harvested.
    :param url: The The url to be used to create the endpoint.
    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param signals: If signals should be emitted about results.
    :param encoding: Override the encoding returned by the server. ISO-8859-1
                     if it is not provided by the server.
    """
    identifiers = get_identifier_names(identifiers)
    request, records = get_records(identifiers, metadata_prefix, url, name,
                                   encoding)
    if signals:
        oaiharvest_finished.send(request, records=records, name=name, **kwargs)


@shared_task
def list_records_from_dates(metadata_prefix=None, from_date=None,
                            until_date=None, url=None,
                            name=None, setspecs=None, signals=True,
                            encoding=None, **kwargs):
    """Harvest multiple records from an OAI repo.

    :param metadata_prefix: The prefix for the metadata return (e.g. 'oai_dc')
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    :param url: The The url to be used to create the endpoint.
    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param setspecs: The 'set' criteria for the harvesting (optional).
    :param signals: If signals should be emitted about results.
    :param encoding: Override the encoding returned by the server. ISO-8859-1
                     if it is not provided by the server.
    """
    try:
        request, records = list_records(
            metadata_prefix,
            from_date,
            until_date,
            url,
            name,
            setspecs,
            encoding
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
    if signals:
        oaiharvest_finished.send(request, records=records, name=name, **kwargs)


def create_indexes(parent_id, sets):
    """Create indexes."""
    existed_leaves = Index.query.filter_by(parent=parent_id).all()
    if existed_leaves:
        pos = max([idx.position for idx in existed_leaves]) + 1
    else:
        pos = 0
    specs = [leaf.harvest_spec for leaf in existed_leaves]
    parent_idx = Index.query.filter_by(id=parent_id).first()
    for s in sets:
        if s not in specs:
            idx = Index()
            idx.parent = parent_id
            idx.browsing_role = parent_idx.browsing_role
            idx.contribute_role = parent_idx.contribute_role
            idx.index_name = sets[s]
            idx.index_name_english = sets[s]
            idx.harvest_spec = s
            idx.public_state = True
            idx.recursive_public_state = True
            idx.position = pos
            pos = pos + 1
            db.session.add(idx)


def map_indexes(index_specs, parent_id):
    """Get indexes map."""
    res = []
    for spec in index_specs:
        idx = Index.query.filter_by(
            harvest_spec=spec, parent=parent_id, is_deleted=False).first()
        res.append(idx.id) if idx else None
    return res


def event_counter(event_name, counter):
    """Event counter."""
    if event_name in counter:
        counter[event_name] = counter[event_name] + 1
    else:
        counter[event_name] = 1


def process_item(record, harvesting, counter, request_info):
    """Process item."""
    event_counter('processed_items', counter)
    event = ItemEvents.INIT

    xml = etree.tostring(record, encoding='utf-8').decode()
    # current_app.logger.debug('[{0}] [{1}] Processing xml: {2}'.format(
    #    0, 'Harvesting', xml))
    if harvesting.metadata_prefix == 'oai_dc':
        mapper = DCMapper(xml)
    elif harvesting.metadata_prefix == 'jpcoar' or \
            harvesting.metadata_prefix == 'jpcoar_1.0':
        mapper = JPCOARMapper(xml)
    elif harvesting.metadata_prefix == 'jpcoar_2.0':
        mapper = JPCOARMapper(xml)
    elif harvesting.metadata_prefix == 'oai_ddi25' or \
            harvesting.metadata_prefix == 'ddi':
        mapper = DDIMapper(xml)
    else:
        return

    current_app.logger.debug('[{0}] [{1}] Processing identifier: {2} prefix: {3}'.format(
        0, 'Harvesting', mapper.identifier(), harvesting.metadata_prefix))
    hvstid = PersistentIdentifier.query.filter_by(
        pid_type='hvstid', pid_value=mapper.identifier()).first()
    if hvstid:
        r = RecordMetadata.query.filter_by(id=hvstid.object_uuid).first()
        recid = PersistentIdentifier.query.filter_by(
            pid_type='recid', object_uuid=hvstid.object_uuid).first()
        recid.status = PIDStatus.REGISTERED
        pubdate = dateutil.parser.parse(
            r.json['pubdate']['attribute_value']).date()
        # dep = WekoDeposit(r.json, r)
        dep = WekoDeposit.get_record(hvstid.object_uuid)
        indexes = dep.get("path", []).copy()
        event = ItemEvents.UPDATE
    elif mapper.is_deleted():    # skip deleted item if item is not registered
        return
    else:
        dep = WekoDeposit.create({})
        PersistentIdentifier.create(pid_type='hvstid',
                                    pid_value=mapper.identifier(),
                                    object_type=dep.pid.object_type,
                                    object_uuid=dep.pid.object_uuid)
        indexes = []
        event = ItemEvents.CREATE

    if int(harvesting.auto_distribution):
        for i in map_indexes(mapper.specs(), harvesting.index_id):
            indexes.append(str(i)) if i not in indexes else None
    if not indexes or len(indexes) == 0:
        indexes.append(str(harvesting.index_id)) if str(
            harvesting.index_id) not in indexes else None

    if hvstid and pubdate >= mapper.datestamp() and indexes == dep['path'] and harvesting.update_style == '1':
        return

    if mapper.is_deleted():    # delete item if item is already registered
        soft_delete(recid.pid_value)
        event = ItemEvents.DELETE
    else:
        if dep.pid.status == PIDStatus.DELETED:
            recid.status = PIDStatus.DELETED
            restore(recid.pid_value)
        json_data = mapper.map()
        if not json_data:
            return

        # START: temporary fix for JDCat
        # merge creatorNames
        current_app.logger.debug('[{0}] [{1}] Processing json: {2}'.format(
            0, 'Harvesting', mapper.identifier()))
        if harvesting.metadata_prefix == 'oai_ddi25' or harvesting.metadata_prefix == 'ddi':
            if 'item_1593074267803' in json_data:
                n2 = len(json_data['item_1593074267803'])
                n = int(n2/2)
                if 'creatorNames' in json_data['item_1593074267803'][0] and 'creatorNames' in json_data['item_1593074267803'][n]:
                    if 'creatorNameLang' in json_data['item_1593074267803'][0]['creatorNames'][0] and 'creatorNameLang' in json_data['item_1593074267803'][n]['creatorNames'][0]:
                        if json_data['item_1593074267803'][0]['creatorNames'][0]['creatorNameLang'] != json_data['item_1593074267803'][n]['creatorNames'][0]['creatorNameLang']:
                            for i in range(n):
                                json_data['item_1593074267803'][i]['creatorNames'].append(
                                    json_data['item_1593074267803'][i+n]['creatorNames'][0])
                                if json_data['item_1593074267803'][i]['creatorNames'][0]['creatorNameLang'] == 'en':
                                    tmp = json_data['item_1593074267803'][i]['creatorNames'][0]
                                    json_data['item_1593074267803'][i]['creatorNames'][0] = json_data['item_1593074267803'][i]['creatorNames'][1]
                                    json_data['item_1593074267803'][i]['creatorNames'][1] = tmp
                                if 'nameIdentifiers' in json_data['item_1593074267803'][i]:
                                    del json_data['item_1593074267803'][i]['nameIdentifiers']
                            del json_data['item_1593074267803'][n:]

        # for e in json_data:
        #    current_app.logger.debug('[{0}] [{1}] Processing json_data[e]: {2}'.format(
        #        0, 'Harvesting', json_data[e]))
        #    current_app.logger.debug('[{0}] [{1}] Processing json_data[e] type: {2}'.format(
        #        0, 'Harvesting', type(json_data[e])))
        #    if isinstance(json_data[e], list):
        #        tmp = list(
        #            map(json.loads, set(map(json.dumps, json_data[e]))))
        #        json_data[e] = tmp
        #        current_app.logger.debug('[{0}] [{1}] Processing json_data[e]: {2}'.format(
        #            0, 'Harvesting', json_data[e]))

        # current_app.logger.debug('[{0}] [{1}] Processing json_data: {2}'.format(
        #    0, 'Harvesting', json_data))
        # END: temporary fix for JDCat

        json_data['$schema'] = '/items/jsonschema/' + str(mapper.itemtype.id)
        dep['_deposit']['status'] = 'draft'
        dep.clear()

        # START: temporary fix for JDCat
        # if json['$schema'] == '/items/jsonschema/14' and 'item_1588260046718' in json:
        if harvesting.metadata_prefix == 'oai_ddi25' or harvesting.metadata_prefix == 'ddi':
            # if json['$schema'] == '/items/jsonschema/14' and 'item_1588260046718' in json:
            if 'item_1588260046718' in json_data:
                for i in json_data['item_1588260046718']:
                    i['subitem_1592380784883'] = 'Other'

            # if json['$schema'] == '/items/jsonschema/14' and 'item_1592405734122' in json:
            if 'item_1592405734122' in json_data:
                # current_app.logger.debug('json: %s' % json['item_1551264917614'])
                for i in json_data['item_1592405734122']:
                    i['subitem_1591320918354'] = 'Distributor'

            if 'item_1600078832557' in json_data:
                for i in json_data['item_1600078832557']:
                    i['accessrole'] = 'open_access'
            
            json_data['resourcetype']=[]
            json_data['resourcetype'].append({
                "resourcetype": "dataset", "resourceuri": "http://purl.org/coar/resource_type/c_ddb1"})        
        # END: temporary fix for JDCat

        # current_app.logger.debug('[{0}] [{1}] Processing {2}'.format(
        #     0, 'Harvesting', json))
        dep.update({'actions': 'publish', 'index': indexes}, json_data)
        dep.commit()
        dep.publish()

        # add item versioning
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=dep.pid.pid_value).first()

        current_app.logger.debug('[{0}] [{1}] Processing {2}'.format(
            0, 'Harvesting', pid))

        idt_list = mapper.identifiers
        from weko_workflow.utils import IdentifierHandle

        idt = IdentifierHandle(pid.object_uuid)
        current_app.logger.debug('[{0}] [{1}] Processing {2}'.format(
            0, 'Harvesting', idt_list))
        current_app.logger.debug('[{0}] [{1}] Processing {2}'.format(
            0, 'Harvesting', idt))
        for it in idt_list:
            pid_type = it['type'].lower()
            pid_obj = idt.get_pidstore(pid_type)
            if not pid_obj:
                idt.register_pidstore(pid_type, it['identifier'])

        if OAIHARVESTER_ENABLE_ITEM_VERSIONING or (event == ItemEvents.CREATE):
            with current_app.test_request_context() as ctx:
                first_ver = dep.newversion(pid)
                first_ver.publish()

    harvesting.item_processed = harvesting.item_processed + 1

    current_app.logger.debug('[{0}] [{1}] Finish {2} {3}'.format(
        0, 'Harvesting', mapper.identifier(), event))

    if event == ItemEvents.CREATE:
        event_counter('created_items', counter)
        from weko_search_ui.utils import send_item_created_event_to_es
        send_item_created_event_to_es({"pid": dep.pid}, request_info)
    elif event == ItemEvents.UPDATE:
        event_counter('updated_items', counter)
    else: #event == ItemEvents.DELETE:
        event_counter('deleted_items', counter)


@ shared_task
def link_success_handler(retval):
    """Register task stats into invenio-stats."""
    current_app.logger.info(
        '[{0}] [{1} {2}] SUCCESS'.format(
            0, 'Harvest Task', retval[0]['task_id']))
    oaiharvest_finished.send(current_app._get_current_object(),
                             exec_data=retval[0], user_data=retval[1])


@ shared_task
def link_error_handler(request, exc, traceback):
    """Register task stats into invenio-stats for failure."""
    args = make_tuple(request.argsrepr)  # Cannot access original args
    start_time = datetime.strptime(args[1], '%Y-%m-%dT%H:%M:%S')
    end_time = datetime.now()
    oaiharvest_finished.send(current_app._get_current_object(),
                             exec_data={
                                 'task_state': 'FAILURE',
                                 'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                                 'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                                 'total_records': 0,
                                 'execution_time': str(end_time - start_time),
                                 'task_name': 'harvest',
                                 'repository_name': 'weko',  # TODO: Grab from config
                                 'task_id': request.id
    },
        user_data=args[2])


def is_harvest_running(id, task_id):
    """Check harvest running."""
    actives = inspect(timeout=current_app.config.get("CELERY_GET_STATUS_TIMEOUT", 3.0)).active()
    for worker in actives:
        for task in actives[worker]:
            if task['name'] == 'invenio_oaiharvester.tasks.run_harvesting':
                if task['args'][0] == str(id) and task['id'] != task_id:
                    return True
    return False


@ shared_task
def run_harvesting(id, start_time, user_data, request_info): 
    """Run harvest."""
    def dump(setting):
        setting_json = {}
        setting_json['repository_name'] = setting.repository_name
        setting_json['base_url'] = setting.base_url
        setting_json['from_date'] = setting.from_date.strftime(
            '%Y-%m-%d') if setting.from_date else ''
        setting_json['until_date'] = setting.until_date.strftime(
            '%Y-%m-%d') if setting.until_date else ''
        setting_json['set_spec'] = setting.set_spec
        setting_json['metadata_prefix'] = setting.metadata_prefix
        setting_json['target_index'] = setting.target_index.index_name
        setting_json['update_style'] = setting.update_style
        setting_json['auto_distribution'] = setting.auto_distribution
        return setting_json

    if is_harvest_running(id, run_harvesting.request.id):
        return ({'task_state': 'SUCCESS',
                 'task_id': run_harvesting.request.id},
                user_data)

    current_app.logger.info('[{0}] [{1}] START'.format(0, 'Harvesting'))
    # For registering runtime stats
    start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')

    try:
        harvesting = HarvestSettings.query.filter_by(id=id).first()
        harvesting.task_id = current_task.request.id
        rtoken = harvesting.resumption_token
        counter = {}
        try:
            if not rtoken:
                harvesting.item_processed = 0
                counter['processed_items'] = 0
                counter['created_items'] = 0
                counter['updated_items'] = 0
                counter['deleted_items'] = 0
                counter['error_items'] = 0
                harvest_log = HarvestLogs(harvest_setting_id=id, status='Running',
                                        start_time=datetime.utcnow(), counter=counter)
                db.session.add(harvest_log)
            else:
                harvest_log = HarvestLogs.query.filter_by(
                    harvest_setting_id=id).order_by(
                    HarvestLogs.id.desc()).first()
                harvest_log.end_time = None
                harvest_log.status = 'Running'
                counter = harvest_log.counter
            harvest_log.setting = dump(harvesting)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
    
        if int(harvesting.auto_distribution):
            sets = list_sets(harvesting.base_url)
            sets_map = map_sets(sets)
            create_indexes(harvesting.index_id, sets_map)
            db.session.commit()
        DCMapper.update_itemtype_map()
        pause = False

        def sigterm_handler(*args):
            nonlocal pause
            pause = True
        signal.signal(signal.SIGTERM, sigterm_handler)
        while True:
            records, rtoken = harvester_list_records(
                harvesting.base_url,
                harvesting.from_date.__str__() if harvesting.from_date and not rtoken else None,
                harvesting.until_date.__str__() if harvesting.until_date and not rtoken else None,
                harvesting.metadata_prefix,
                harvesting.set_spec,
                rtoken)
            current_app.logger.info('[{0}] [{1}]'.format(
                                    0, 'Processing records'))
            for record in records:
                try:
                    process_item(record, harvesting, counter, request_info)
                    db.session.commit()
                except Exception as ex:
                    current_app.logger.debug(traceback.format_exc())
                    current_app.logger.error(
                        'Error occurred while processing harvesting item\n' + str(ex))
                    db.session.rollback()
                    event_counter('error_items', counter)
            harvesting.resumption_token = rtoken
            db.session.commit()
            if not rtoken:
                harvest_log.status = 'Successful'
                break
            elif pause is True:
                harvest_log.status = 'Suspended'
                break
    except Exception as ex:
        db.session.rollback()
        harvest_log.status = 'Failed'
        current_app.logger.error(str(ex))
        harvest_log.errmsg = str(ex)[:255]
        harvest_log.requrl = harvesting.base_url
        harvesting.resumption_token = None
    finally:
        try:
            harvesting.task_id = None
            end_time = datetime.utcnow()
            harvest_log.end_time = end_time
            harvest_log.counter = counter
            current_app.logger.info('[{0}] [{1}] END'.format(0, 'Harvesting'))
            send_run_status_mail(harvesting, harvest_log)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(ex)
        return ({'task_state': 'SUCCESS',
                 'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                 'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                 'total_records': harvesting.item_processed,
                 'execution_time': str(end_time - start_time),
                 'task_name': 'harvest',
                 'repository_name': 'weko',  # TODO: Set and Grab from config
                 'task_id': run_harvesting.request.id},
                user_data)


@ shared_task(ignore_results=True)
def check_schedules_and_run():
    """Check schedules and run."""
    settings = HarvestSettings.query.all()
    now = datetime.utcnow()
    user_data = {
            'ip_address': "",
            'user_agent': "",
            'user_id': -1,
            'session_id': ""
    }
    request_info = {
            "remote_addr": "",
            "referrer": "",
            "hostname": "",
            "user_id": -1,
            "action": "HARVEST"
    }
    for h in settings:
        if h.schedule_enable is True:
            if (h.schedule_frequency == 'daily') or \
               (h.schedule_frequency == 'weekly' and h.schedule_details == now.weekday()) or \
               (h.schedule_frequency == 'monthly' and h.schedule_details == now.day):
                run_harvesting.delay(
                    h.id, now.strftime('%Y-%m-%dT%H:%M:%S%z'), user_data,request_info)
