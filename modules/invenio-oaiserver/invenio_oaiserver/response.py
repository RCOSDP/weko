# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAI-PMH 2.0 response generator."""
import copy
import traceback
from datetime import MINYEAR, datetime, timedelta

from flask import current_app, request, url_for
from invenio_db import db
from invenio_records.models import RecordMetadata
from lxml import etree
from lxml.etree import Element, ElementTree, SubElement
from weko_deposit.api import WekoRecord
from weko_index_tree.api import Indexes
from weko_schema_ui.schema import get_oai_metadata_formats

from .api import OaiIdentify
from .fetchers import oaiid_fetcher
from .models import OAISet
from .provider import OAIIDProvider
from .query import get_records
from .resumption_token import serialize
from .utils import datetime_to_datestamp, handle_license_free, serializer

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
    e_deletedRecord.text = 'transient'

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


def is_deleted_workflow(pid):
    """Check workflow is deleted."""
    deleted_status = "D"
    return pid.status == deleted_status


def is_private_workflow(record):
    """Check publish status of workflow is private."""
    private_status = 1
    return int(record.get("publish_status")) == private_status


def is_private_index(record):
    """Check index of workflow is private."""
    return not Indexes.is_public_state(copy.deepcopy(record.get("path")))


def set_identifier(param_record, param_rec):
    """Set identifier (doi, cnri, url) for this record."""
    # Set default value for system_identifier_doi.
    if not param_record.get('json') or \
            not param_record['json']['_source'] or \
            not param_record['json']['_source']['_item_metadata']:
        param_record['json'] = \
            {'_source': {'_item_metadata': {'system_identifier_doi': None}}}
    # Set default identifier for system_identifier_doi.
    if not param_record['json']['_source']['_item_metadata']\
            .get('system_identifier_doi'):
        param_record['json']['_source']['_item_metadata'][
            'system_identifier_doi'] = get_identifier(param_rec)


def is_exists_doi(param_record):
    """Check identifier doi exists in this record."""
    item_metadata = param_record['json']['_source']['_item_metadata']
    system_identifier_doi = item_metadata.get('system_identifier_doi', {})
    attribute_value_mlt = system_identifier_doi.get('attribute_value_mlt', {})
    for mlt in attribute_value_mlt:
        identifier_type = mlt.get('subitem_systemidt_identifier_type')
        if identifier_type == 'DOI':
            return True
    return False


def getrecord(**kwargs):
    """Create OAI-PMH response for verb Identify."""
    def get_error_code_msg():
        """Get error by type."""
        code = current_app.config.get('OAISERVER_CODE_NO_RECORDS_MATCH')
        msg = current_app.config.get('OAISERVER_MESSAGE_NO_RECORDS_MATCH')
        return [(code, msg)]

    record_dumper = serializer(kwargs['metadataPrefix'])
    pid = OAIIDProvider.get(pid_value=kwargs['identifier']).pid

    identify = OaiIdentify.get_all()
    harvest_public_state, record = WekoRecord.get_record_with_hps(
        pid.object_uuid)

    e_tree, e_getrecord = verb(**kwargs)
    e_record = SubElement(e_getrecord, etree.QName(NS_OAIPMH, 'record'))
    set_identifier(record, record)
    # Harvest is private
    _is_private_index = is_private_index(record)
    if not harvest_public_state or\
            (identify and not identify.outPutSetting) or \
            (_is_private_index
                and harvest_public_state and is_exists_doi(record)):
        return error(get_error_code_msg(), **kwargs)
    # Item is deleted
    # or Harvest is public & Item is private
    # or Harvest is public & Index is private
    elif is_deleted_workflow(pid) or (
        harvest_public_state and is_private_workflow(record)) or (
            harvest_public_state and _is_private_index):
        header(
            e_record,
            identifier=pid.pid_value,
            datestamp=record.updated,
            sets=record.get('_oai', {}).get('sets', []),
            deleted=True
        )
        return e_tree

    header(
        e_record,
        identifier=pid.pid_value,
        datestamp=record.updated,
        sets=record.get('_oai', {}).get('sets', []),
    )
    e_metadata = SubElement(e_record,
                            etree.QName(NS_OAIPMH, 'metadata'))

    etree_record = copy.deepcopy(record)

    if not etree_record.get('system_identifier_doi', None):
        etree_record['system_identifier_doi'] = get_identifier(record)

    # Merge licensetype and licensefree
    etree_record = handle_license_free(etree_record)

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
    def get_error_code_msg():
        """Get error by type."""
        code = current_app.config.get('OAISERVER_CODE_NO_RECORDS_MATCH')
        msg = current_app.config.get('OAISERVER_MESSAGE_NO_RECORDS_MATCH')
        return [(code, msg)]

    def append_deleted_record(e_listrecords, pid_object, rec):
        """Append attribute [status="deleted] for 'header' tag."""
        e_record = SubElement(e_listrecords, etree.QName(NS_OAIPMH, 'record'))
        header(
            e_record,
            identifier=pid_object.pid_value,
            datestamp=rec.updated,
            sets=rec.get('_oai', {}).get('sets', []),
            deleted=True
        )

    record_dumper = serializer(kwargs['metadataPrefix'])
    e_tree, e_listrecords = verb(**kwargs)
    result = get_records(**kwargs)
    identify = OaiIdentify.get_all()
    if not result.total or not identify or \
            (identify and not identify.outPutSetting):
        return error(get_error_code_msg(), **kwargs)
    for record in result.items:
        try:
            pid = oaiid_fetcher(record['id'], record['json']['_source'])
            pid_object = OAIIDProvider.get(pid_value=pid.pid_value).pid
            rec = WekoRecord.get_record(record['id'])
            set_identifier(record, rec)
            # Check output delete, noRecordsMatch
            if not is_private_index(rec):
                if is_deleted_workflow(pid_object) or \
                        is_private_workflow(rec):
                    append_deleted_record(e_listrecords, pid_object, rec)
                    continue
            else:
                append_deleted_record(e_listrecords, pid_object, rec)
                continue
            e_record = SubElement(
                e_listrecords, etree.QName(NS_OAIPMH, 'record'))
            header(
                e_record,
                identifier=pid.pid_value,
                datestamp=record['updated'],
                sets=record['json']['_source'].get('_oai', {}).get('sets', []),
            )
            e_metadata = SubElement(e_record, etree.QName(NS_OAIPMH,
                                                          'metadata'))
            etree_record = copy.deepcopy(record['json'])
            # Merge licensetype and licensefree
            handle_license_free(etree_record['_source']['_item_metadata'])
            e_metadata.append(record_dumper(pid, etree_record))
        except Exception:
            current_app.logger.error(traceback.print_exc())
            current_app.logger.error('Error when exporting item id '
                                     + str(record['id']))
    # Check <record> tag not exist.
    if len(e_listrecords) == 0:
        return error(get_error_code_msg(), **kwargs)
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


def combine_record_file_urls(record, object_uuid, meta_prefix):
    """Add file urls to record metadata.

    Get file property information by item_mapping and put to metadata.
    """
    from weko_records.api import ItemsMetadata, Mapping
    from weko_records.serializers.utils import get_mapping
    from weko_schema_ui.schema import get_oai_metadata_formats

    metadata_formats = get_oai_metadata_formats(current_app)
    item_type = ItemsMetadata.get_by_object_id(object_uuid)
    item_type_id = item_type.item_type_id
    type_mapping = Mapping.get_record(item_type_id)
    mapping_type = metadata_formats[meta_prefix]['serializer'][1]['schema_type']
    item_map = get_mapping(type_mapping,
                           "{}_mapping".format(mapping_type))

    if item_map:
        file_props = current_app.config["OAISERVER_FILE_PROPS_MAPPING"]
        if mapping_type in file_props:
            file_keys = item_map.get(file_props[mapping_type])
        else:
            file_keys = None

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


def get_identifier(record):
    """Get Identifier of record(DOI or HDL), if not set URL as default.

    @param record:
    @return:
    """
    result = {
        "attribute_name": "Identifier",
        "attribute_value_mlt": [
        ]
    }

    if record.pid_doi:
        result["attribute_value_mlt"].append(dict(
            subitem_systemidt_identifier=record.pid_doi.pid_value,
            subitem_systemidt_identifier_type=record.pid_doi.pid_type.upper(),
        ))
    if record.pid_cnri:
        result["attribute_value_mlt"].append(dict(
            subitem_systemidt_identifier=record.pid_cnri.pid_value,
            subitem_systemidt_identifier_type=record.pid_cnri.pid_type.upper(),
        ))
    if current_app.config.get('WEKO_SCHEMA_RECORD_URL'):
        result["attribute_value_mlt"].append(dict(
            subitem_systemidt_identifier=current_app.config[
                'WEKO_SCHEMA_RECORD_URL'].format(
                request.url_root, record['_deposit']['id'].split('.')[0]),
            subitem_systemidt_identifier_type='URI',
        ))
    return result
