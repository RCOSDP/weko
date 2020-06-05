# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAI-PMH 2.0 response generator."""
import copy
from datetime import MINYEAR, datetime, timedelta

from flask import current_app, request, url_for
from invenio_db import db
from invenio_records.models import RecordMetadata
from lxml import etree
from lxml.etree import Element, ElementTree, SubElement
from weko_deposit.api import WekoRecord
from weko_schema_ui.schema import get_oai_metadata_formats

from .api import OaiIdentify
from .fetchers import oaiid_fetcher
from .models import OAISet
from .provider import OAIIDProvider
from .query import get_records
from .resumption_token import serialize
from .utils import datetime_to_datestamp, serializer

NS_OAIPMH = 'http://www.openarchives.org/OAI/2.0/'
NS_OAIPMH_XSD = 'http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd'
NS_XSI = 'http://www.w3.org/2001/XMLSchema-instance'
NS_OAIDC = 'http://www.openarchives.org/OAI/2.0/oai_dc/'
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_JPCOAR = "https://irdb.nii.ac.jp/schema/jpcoar/1.0/"

NSMAP = {
    None: NS_OAIPMH,
}

NSMAP_DESCRIPTION = {
    'oai_dc': NS_OAIDC,
    'dc': NS_DC,
    'xsi': NS_XSI,
}

DATETIME_FORMATS = {
    'YYYY-MM-DDThh:mm:ssZ': '%Y-%m-%dT%H:%M:%SZ',
    'YYYY-MM-DD': '%Y-%m-%d',
}


def envelope(**kwargs):
    """Create OAI-PMH envelope for response."""
    e_oaipmh = Element(etree.QName(NS_OAIPMH, 'OAI-PMH'), nsmap=NSMAP)
    e_oaipmh.set(etree.QName(NS_XSI, 'schemaLocation'),
                 '{0} {1}'.format(NS_OAIPMH, NS_OAIPMH_XSD))
    e_tree = ElementTree(element=e_oaipmh)

    if current_app.config['OAISERVER_XSL_URL']:
        e_oaipmh.addprevious(etree.ProcessingInstruction(
            'xml-stylesheet', 'type="text/xsl" href="{0}"'
                .format(current_app.config['OAISERVER_XSL_URL'])))

    e_responseDate = SubElement(
        e_oaipmh, etree.QName(
            NS_OAIPMH, 'responseDate'))
    # date should be first possible moment
    e_responseDate.text = datetime_to_datestamp(datetime.utcnow())
    e_request = SubElement(e_oaipmh, etree.QName(NS_OAIPMH, 'request'))
    for key, value in kwargs.items():
        if key == 'from_' or key == 'until':
            value = datetime_to_datestamp(value)
        elif key == 'resumptionToken':
            value = value['token']
        e_request.set(key, value)
    e_request.text = url_for('invenio_oaiserver.response', _external=True)
    return e_tree, e_oaipmh


def error(errors, **kwargs):
    """Create error element."""
    e_tree, e_oaipmh = envelope(**kwargs)
    for code, message in errors:
        e_error = SubElement(e_oaipmh, etree.QName(NS_OAIPMH, 'error'))
        e_error.set('code', code)
        e_error.text = message
    return e_tree


def verb(**kwargs):
    """Create OAI-PMH envelope for response with verb."""
    e_tree, e_oaipmh = envelope(**kwargs)
    e_element = SubElement(e_oaipmh, etree.QName(NS_OAIPMH, kwargs['verb']))
    return e_tree, e_element


def identify(**kwargs):
    """Create OAI-PMH response for verb Identify."""
    cfg = current_app.config

    # add by Mr ryuu. at 2018/06/06 start
    # Get The Set Of Identify
    oaiObj = OaiIdentify.get_all()
    # add by Mr ryuu. at 2018/06/06 end

    e_tree, e_identify = verb(**kwargs)

    e_repositoryName = SubElement(
        e_identify, etree.QName(NS_OAIPMH, 'repositoryName'))

    # add by Mr ryuu. at 2018/06/06 start
    if oaiObj is not None:
        cfg['OAISERVER_REPOSITORY_NAME'] = oaiObj.repositoryName
    # add by Mr ryuu. at 2018/06/06 end

    e_repositoryName.text = cfg['OAISERVER_REPOSITORY_NAME']

    e_baseURL = SubElement(e_identify, etree.QName(NS_OAIPMH, 'baseURL'))

    e_baseURL.text = url_for('invenio_oaiserver.response', _external=True)

    e_protocolVersion = SubElement(e_identify,
                                   etree.QName(NS_OAIPMH, 'protocolVersion'))
    e_protocolVersion.text = cfg['OAISERVER_PROTOCOL_VERSION']

    # add by Mr ryuu. at 2018/06/06 start
    if oaiObj is not None:
        cfg['OAISERVER_ADMIN_EMAILS'][0] = oaiObj.emails
    # add by Mr ryuu. at 2018/06/06 end

    for adminEmail in cfg['OAISERVER_ADMIN_EMAILS']:
        e = SubElement(e_identify, etree.QName(NS_OAIPMH, 'adminEmail'))
        e.text = adminEmail

    e_earliestDatestamp = SubElement(
        e_identify, etree.QName(
            NS_OAIPMH, 'earliestDatestamp'))

    # update by Mr ryuu. at 2018/06/06 start
    if not oaiObj:
        e_earliestDatestamp.text = datetime_to_datestamp(
            db.session.query(db.func.min(RecordMetadata.created)
                             ).scalar() or datetime(MINYEAR, 1, 1)
        )
    else:
        e_earliestDatestamp.text = datetime_to_datestamp(
            oaiObj.earliestDatastamp)
    # update by Mr ryuu. at 2018/06/06 end

    e_deletedRecord = SubElement(e_identify,
                                 etree.QName(NS_OAIPMH, 'deletedRecord'))
    e_deletedRecord.text = 'no'

    e_granularity = SubElement(e_identify,
                               etree.QName(NS_OAIPMH, 'granularity'))
    assert cfg['OAISERVER_GRANULARITY'] in DATETIME_FORMATS
    e_granularity.text = cfg['OAISERVER_GRANULARITY']

    compressions = cfg['OAISERVER_COMPRESSIONS']
    if compressions != ['identity']:
        for compression in compressions:
            e_compression = SubElement(e_identify,
                                       etree.QName(NS_OAIPMH, 'compression'))
            e_compression.text = compression

    for description in cfg.get('OAISERVER_DESCRIPTIONS', []):
        e_description = SubElement(e_identify,
                                   etree.QName(NS_OAIPMH, 'description'))
        e_description.append(etree.fromstring(description))

    return e_tree


def resumption_token(parent, pagination, **kwargs):
    """Attach resumption token element to a parent."""
    # Do not add resumptionToken if all results fit to the first page.
    if pagination.page == 1 and not pagination.has_next:
        return

    token = serialize(pagination, **kwargs)
    e_resumptionToken = SubElement(parent, etree.QName(NS_OAIPMH,
                                                       'resumptionToken'))
    if pagination.total:
        expiration_date = datetime.utcnow() + timedelta(
            seconds=current_app.config[
                'OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME'
            ]
        )
        e_resumptionToken.set('expirationDate', datetime_to_datestamp(
            expiration_date
        ))
        e_resumptionToken.set('cursor', str(
            (pagination.page - 1) * pagination.per_page
        ))
        e_resumptionToken.set('completeListSize', str(pagination.total))

    if token:
        e_resumptionToken.text = token


def listsets(**kwargs):
    """Create OAI-PMH response for ListSets verb."""
    e_tree, e_listsets = verb(**kwargs)

    page = kwargs.get('resumptionToken', {}).get('page', 1)
    size = current_app.config['OAISERVER_PAGE_SIZE']
    oai_sets = OAISet.query.paginate(page=page, per_page=size, error_out=False)

    for oai_set in oai_sets.items:
        e_set = SubElement(e_listsets, etree.QName(NS_OAIPMH, 'set'))
        e_setSpec = SubElement(e_set, etree.QName(NS_OAIPMH, 'setSpec'))
        e_setSpec.text = oai_set.spec
        e_setName = SubElement(e_set, etree.QName(NS_OAIPMH, 'setName'))
        e_setName.text = oai_set.name
        if oai_set.description:
            e_setDescription = SubElement(e_set, etree.QName(NS_OAIPMH,
                                                             'setDescription'))
            e_dc = SubElement(
                e_setDescription, etree.QName(NS_OAIDC, 'dc'),
                nsmap=NSMAP_DESCRIPTION
            )
            e_dc.set(etree.QName(NS_XSI, 'schemaLocation'), NS_OAIDC)
            e_description = SubElement(e_dc, etree.QName(NS_DC, 'description'))
            e_description.text = oai_set.description

    resumption_token(e_listsets, oai_sets, **kwargs)
    return e_tree


def listmetadataformats(**kwargs):
    """Create OAI-PMH response for ListMetadataFormats verb."""
    oad = get_oai_metadata_formats(current_app)
    e_tree, e_listmetadataformats = verb(**kwargs)

    if 'identifier' in kwargs:
        # test if record exists
        OAIIDProvider.get(pid_value=kwargs['identifier'])

    if not len(oad):
        return error(get_error_code_msg('noMetadataFormats'), **kwargs)

    for prefix, metadata in oad.items():
        e_metadataformat = SubElement(
            e_listmetadataformats, etree.QName(NS_OAIPMH, 'metadataFormat')
        )
        e_metadataprefix = SubElement(
            e_metadataformat, etree.QName(NS_OAIPMH, 'metadataPrefix')
        )
        e_metadataprefix.text = prefix
        e_schema = SubElement(
            e_metadataformat, etree.QName(NS_OAIPMH, 'schema')
        )
        e_schema.text = metadata['schema']
        e_metadataNamespace = SubElement(
            e_metadataformat, etree.QName(NS_OAIPMH, 'metadataNamespace')
        )
        e_metadataNamespace.text = metadata['namespace']

    return e_tree


def header(parent, identifier, datestamp, sets=None, deleted=False):
    """Attach ``<header/>`` element to a parent."""
    e_header = SubElement(parent, etree.QName(NS_OAIPMH, 'header'))
    if deleted:
        e_header.set('status', 'deleted')
    e_identifier = SubElement(e_header, etree.QName(NS_OAIPMH, 'identifier'))
    e_identifier.text = identifier
    e_datestamp = SubElement(e_header, etree.QName(NS_OAIPMH, 'datestamp'))
    e_datestamp.text = datetime_to_datestamp(datestamp)
    for spec in sets or []:
        e = SubElement(e_header, etree.QName(NS_OAIPMH, 'setSpec'))
        e.text = spec
    return e_header


def getrecord(**kwargs):
    """Create OAI-PMH response for verb Identify."""
    def get_error_code_msg():
        code = 'noRecordsMatch'
        msg = 'The combination of the values of the from, until, ' \
              'set and metadataPrefix arguments results in an empty list.'
        return [(code, msg)]

    record_dumper = serializer(kwargs['metadataPrefix'])
    pid = OAIIDProvider.get(pid_value=kwargs['identifier']).pid
    # record = Record.get_record(pid.object_uuid)

    identify = OaiIdentify.get_all()
    harvest_public_state, record = WekoRecord.get_record_with_hps(
        pid.object_uuid)
    if (identify and not identify.outPutSetting) or not harvest_public_state:
        return error(get_error_code_msg(), **kwargs)

    e_tree, e_getrecord = verb(**kwargs)
    e_record = SubElement(e_getrecord, etree.QName(NS_OAIPMH, 'record'))

    header(
        e_record,
        identifier=pid.pid_value,
        datestamp=record.updated,
        sets=record.get('_oai', {}).get('sets', []),
    )
    e_metadata = SubElement(e_record,
                            etree.QName(NS_OAIPMH, 'metadata'))

    etree_record = copy.deepcopy(record)
    if check_correct_system_props_mapping(
            pid.object_uuid,
            current_app.config.get('OAISERVER_SYSTEM_FILE_MAPPING')):
        etree_record = combine_record_file_urls(etree_record, pid.object_uuid)

    root = record_dumper(pid, {'_source': etree_record})

    e_metadata.append(root)
    return e_tree


def listidentifiers(**kwargs):
    """Create OAI-PMH response for verb ListIdentifiers."""
    e_tree, e_listidentifiers = verb(**kwargs)
    result = get_records(**kwargs)

    if not result.total:
        return error(get_error_code_msg(), **kwargs)

    for record in result.items:
        pid = oaiid_fetcher(record['id'], record['json']['_source'])
        header(
            e_listidentifiers,
            identifier=pid.pid_value,
            datestamp=record['updated'],
            sets=record['json']['_source'].get('_oai', {}).get('sets', []),
        )

    resumption_token(e_listidentifiers, result, **kwargs)
    return e_tree


def listrecords(**kwargs):
    """Create OAI-PMH response for verb ListRecords."""
    record_dumper = serializer(kwargs['metadataPrefix'])

    e_tree, e_listrecords = verb(**kwargs)
    result = get_records(**kwargs)

    if not result.total:
        return error(get_error_code_msg(), **kwargs)

    for record in result.items:
        pid = oaiid_fetcher(record['id'], record['json']['_source'])
        e_record = SubElement(e_listrecords,
                              etree.QName(NS_OAIPMH, 'record'))
        header(
            e_record,
            identifier=pid.pid_value,
            datestamp=record['updated'],
            sets=record['json']['_source'].get('_oai', {}).get('sets', []),
        )
        e_metadata = SubElement(e_record, etree.QName(NS_OAIPMH, 'metadata'))
        e_metadata.append(record_dumper(pid, record['json']))

    resumption_token(e_listrecords, result, **kwargs)
    return e_tree


def get_error_code_msg(code='noRecordsMatch'):
    """Return list error message."""
    msg = 'The combination of the values of the from, until, ' \
          'set and metadataPrefix arguments results in an empty list.'

    if code == 'noMetadataFormats':
        msg = 'There is no metadata format available.'

    return [(code, msg)]


def create_identifier_index(root, **kwargs):
    """Create indentifier index in xml tree."""
    try:
        e_jpcoar = Element(etree.QName(NS_OAIPMH, 'metadata'))
        e_identifier = SubElement(e_jpcoar,
                                  etree.QName(NS_JPCOAR, 'identifier'),
                                  attrib={
                                      'identifierType':
                                      kwargs['pid_type'].upper()})
        e_identifier.text = kwargs['pid_value']
        e_identifier_registration = root.find(
            'jpcoar:identifierRegistration',
            namespaces=root.nsmap)
        if e_identifier_registration is not None:
            e_identifier_registration.addprevious(e_identifier)
        else:
            root.append(e_identifier)

    except Exception as e:
        current_app.logger.error(str(e))
    return root


def check_correct_system_props_mapping(object_uuid, system_mapping_config):
    """Validate and return if selection mapping is correct.

    Correct mapping mean item map have the 2 field same with config
    """
    from weko_records.api import ItemsMetadata, Mapping
    from weko_records.serializers.utils import get_mapping

    item_type = ItemsMetadata.get_by_object_id(object_uuid)
    item_type_id = item_type.item_type_id
    type_mapping = Mapping.get_record(item_type_id)
    item_map = get_mapping(type_mapping, "jpcoar_mapping")

    if system_mapping_config:
        for key in system_mapping_config:
            if key not in item_map or key in item_map and \
                    system_mapping_config[key] not in item_map[key]:
                return False
    else:
        return False
    return True


def combine_record_file_urls(record, object_uuid):
    """Add file urls to record metadata.

    Get file property information by item_mapping and put to metadata.
    """
    from weko_records.api import ItemsMetadata, Mapping
    from weko_records.serializers.utils import get_mapping

    item_type = ItemsMetadata.get_by_object_id(object_uuid)
    item_type_id = item_type.item_type_id
    type_mapping = Mapping.get_record(item_type_id)
    item_map = get_mapping(type_mapping, "jpcoar_mapping")
    item_map_ddi = get_mapping(type_mapping, "ddi_mapping")

    if item_map_ddi:
        file_keys = item_map_ddi.get(
            "stdyDscr.dataAccs.setAvail.accsPlac.@value")
    else:
        file_keys = item_map.get(current_app.config[
            "OAISERVER_FILE_PROPS_MAPPING"])

    if not file_keys:
        return record
    else:
        file_keys = file_keys.split('.')

    if len(file_keys) == 3 and record.get(file_keys[0]):
        attr_mlt = record[file_keys[0]]["attribute_value_mlt"]
        if isinstance(attr_mlt, list):
            for attr in attr_mlt:
                if attr.get('filename'):
                    if not attr.get(file_keys[1]):
                        attr[file_keys[1]] = {}
                    attr[file_keys[1]][file_keys[2]] = \
                        create_files_url(
                            request.url_root,
                            record.get('recid'),
                            attr.get('filename'))
        elif isinstance(attr_mlt, dict) and \
                attr_mlt.get('filename'):
            if not attr_mlt.get(file_keys[1]):
                attr_mlt[file_keys[1]] = {}
            attr_mlt[file_keys[1]][file_keys[2]] = \
                create_files_url(
                    request.url_root,
                    record.get('recid'),
                    attr_mlt.get('filename'))

    return record


def create_files_url(root_url, record_id, filename):
    """Generation of downloading file url."""
    return "{}record/{}/files/{}".format(
        root_url,
        record_id,
        filename)
