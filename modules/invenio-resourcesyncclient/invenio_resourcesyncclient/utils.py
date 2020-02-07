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
from resync.client import Client
from resync.client_utils import url_or_file_open, init_logging
from resync.mapper import MapperError
from resync.resource_list_builder import ResourceListBuilder
from resync.sitemap import Sitemap
from flask import current_app
import requests
from invenio_oaiharvester.utils import ItemEvents
from invenio_oaiharvester.harvester import DCMapper, DDIMapper, JPCOARMapper
from invenio_oaiharvester.tasks import map_indexes, event_counter
import dateutil
from invenio_db import db

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from lxml import etree
from weko_deposit.api import WekoDeposit
from weko_records_ui.utils import soft_delete

def read_capability(url):
    """Read capability of an url"""
    s = Sitemap()
    capability = None
    try:
        document = s.parse_xml(url_or_file_open(url))
    except IOError as e:
        raise e
    if 'capability' in document.md:
        capability = document.md['capability']
    return capability


def sync_baseline(map, base_url, dryrun=False):
    """Run resync baseline"""
    client = Client()
    init_logging(verbose=True)
    try:
        # set sitemap_name to specify the only url to sync
        # set mappings to specify the url will
        # be used to validate subitem in resync library
        client.sitemap_name = base_url
        client.dryrun = dryrun
        client.set_mappings(map)
        client.baseline_or_audit()
        return True
    except MapperError:
        # if mapper error then remove one element in url and retry
        paths = map[0].rsplit('/', 1)
        map[0] = paths[0]
        return False
    except Exception as e:
        raise e


def sync_audit(map):
    """Run resync audit"""
    client = Client()
    client.set_mappings(map)
    init_logging(verbose=True)
    src_resource_list = client.find_resource_list()
    rlb = ResourceListBuilder(mapper=client.mapper)
    dst_resource_list = rlb.from_disk()
    # Compare these resource lists respecting any comparison options
    (same, updated, deleted, created) = dst_resource_list.compare(
        src_resource_list)
    return dict(
        same=len(same),updated=len(updated),deleted=len(deleted),created=len(created)
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
    records = []
    response = requests.get(url, params=payload)
    et = etree.XML(response.text.encode(encoding))
    records = records + et.findall('./GetRecord/record', namespaces=et.nsmap)
    return records


def get_list_records():
    return ['1', '2', '3.1', '3.2']


def process_item(record, resync, counter):
    """Process item."""
    event_counter('processed_items', counter)
    event = ItemEvents.INIT
    xml = etree.tostring(record, encoding='utf-8').decode()
    mapper = JPCOARMapper(xml)
    resyncid = PersistentIdentifier.query.filter_by(
        pid_type='resyncid', pid_value=mapper.identifier()).first()
    if resyncid:
        r = RecordMetadata.query.filter_by(id=resyncid.object_uuid).first()
        recid = PersistentIdentifier.query.filter_by(
            pid_type='recid', object_uuid=resyncid.object_uuid).first()
        recid.status = PIDStatus.REGISTERED
        pubdate = dateutil.parser.parse(
            r.json['pubdate']['attribute_value']).date()
        dep = WekoDeposit(r.json, r)
        indexes = dep['path'].copy()
        event = ItemEvents.UPDATE
    elif mapper.is_deleted():
        return
    else:
        dep = WekoDeposit.create({})
        PersistentIdentifier.create(pid_type='resyncid',
                                    pid_value=mapper.identifier(),
                                    object_type=dep.pid.object_type,
                                    object_uuid=dep.pid.object_uuid)
        indexes = []
        event = ItemEvents.CREATE
    indexes.append(str(resync.index_id)) if str(
        resync.index_id) not in indexes else None

    if mapper.is_deleted():
        soft_delete(recid.pid_value)
        event = ItemEvents.DELETE
    else:
        json = mapper.map()
        json['$schema'] = '/items/jsonschema/' + str(mapper.itemtype.id)
        dep['_deposit']['status'] = 'draft'
        dep.update({'actions': 'publish', 'index': indexes}, json)
        dep.commit()
        dep.publish()
        # add item versioning
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=dep.pid.pid_value).first()
        with current_app.test_request_context() as ctx:
            first_ver = dep.newversion(pid)
            first_ver.publish()
    db.session.commit()
    if event == ItemEvents.CREATE:
        event_counter('created_items', counter)
    elif event == ItemEvents.UPDATE:
        event_counter('updated_items', counter)
    elif event == ItemEvents.DELETE:
        event_counter('deleted_items', counter)

