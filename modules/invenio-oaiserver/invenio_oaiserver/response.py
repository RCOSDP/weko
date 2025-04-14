# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAI-PMH 2.0 response generator."""
import copy
import pickle
import traceback
import json
from datetime import MINYEAR, datetime, timedelta

from flask import current_app, request, url_for
from flask_babelex import get_locale, to_user_timezone, to_utc
from invenio_communities import config as invenio_communities_config
from invenio_communities.models import Community
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PIDStatus
from invenio_records.models import RecordMetadata
from invenio_files_rest.models import Bucket, FileInstance, Location, ObjectVersion
from lxml import etree
from lxml.etree import Element, ElementTree, SubElement
from sqlalchemy.orm.exc import NoResultFound
from weko_deposit.api import WekoRecord
from weko_index_tree.api import Indexes
from weko_schema_ui.schema import get_oai_metadata_formats
from weko_schema_ui.models import PublishStatus

from .api import OaiIdentify
from .fetchers import oaiid_fetcher
from .models import OAISet
from .provider import OAIIDProvider
from .query import get_records
from .resumption_token import serialize, serialize_file_response
from .utils import HARVEST_PRIVATE, OUTPUT_HARVEST, PRIVATE_INDEX, \
    datetime_to_datestamp, get_index_state, handle_license_free, \
    is_output_harvest, serializer

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
OAIPMH_FOLDER_NAME = 'OAI_SERVER_FILE_CREATE'


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
    if "url" in kwargs.keys():
        e_request.text = kwargs['url']
    else:
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
    # current_app.logger.debug("kwargs:{0}".format(kwargs))
    # kwargs:{'metadataPrefix': 'jpcoar_1.0', 'identifier': 'oai:weko3.example.org:00000003', 'verb': 'GetRecord'}

    e_tree, e_oaipmh = envelope(**kwargs)
    e_element = SubElement(e_oaipmh, etree.QName(NS_OAIPMH, kwargs['verb']))
    return e_tree, e_element


def identify(**kwargs):
    """Create OAI-PMH response for verb Identify."""
    cfg = current_app.config

    # add by Mr ryuu. at 2018/06/06 start
    # Get The Set Of Identify
    identify = OaiIdentify.get_all()
    # add by Mr ryuu. at 2018/06/06 end

    e_tree, e_identify = verb(**kwargs)

    e_repositoryName = SubElement(
        e_identify, etree.QName(NS_OAIPMH, 'repositoryName'))

    # add by Mr ryuu. at 2018/06/06 start
    if identify:
        cfg['OAISERVER_REPOSITORY_NAME'] = identify.repositoryName
    # add by Mr ryuu. at 2018/06/06 end
        e_email = SubElement(e_identify, etree.QName(NS_OAIPMH, 'adminEmail'))
        e_email.text = identify.emails

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
    if not identify:
        e_earliestDatestamp.text = datetime_to_datestamp(
            db.session.query(db.func.min(RecordMetadata.created)
                             ).scalar() or datetime(MINYEAR, 1, 1)
        )
    else:
        e_earliestDatestamp.text = datetime_to_datestamp(
            identify.earliestDatastamp)
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
        if Indexes.is_index(str(oai_set.spec)) is True:
            index_path = [oai_set.spec.replace(':', '/')]
            if Indexes.is_public_state([str(oai_set.id)]) is not None \
                    and (not Indexes.is_public_state(index_path.copy())
                         or not Indexes.get_harvest_public_state(
                        index_path.copy())):
                continue

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


def header(parent, identifier, datestamp, sets=[], deleted=False):
    """Attach ``<header/>`` element to a parent."""
    e_header = SubElement(parent, etree.QName(NS_OAIPMH, 'header'))
    if deleted:
        e_header.set('status', 'deleted')
    e_identifier = SubElement(e_header, etree.QName(NS_OAIPMH, 'identifier'))
    e_identifier.text = identifier
    e_datestamp = SubElement(e_header, etree.QName(NS_OAIPMH, 'datestamp'))
    e_datestamp.text = datetime_to_datestamp(datestamp)
    if sets:
        _paths, _sets = extract_paths_from_sets(sets)

        paths = Indexes.get_path_name(_paths)
        for path in paths:
            if path.public_state and path.harvest_public_state:
                e = SubElement(e_header, etree.QName(NS_OAIPMH, 'setSpec'))
                e.text = path.path.replace('/', ':')

        for set in _sets:
            e = SubElement(e_header, etree.QName(NS_OAIPMH, 'setSpec'))
            e.text = set

    return e_header


def extract_paths_from_sets(sets):
    """Extract the paths in the set

    Args:
        sets (list): list of sets

    Returns:
        list,list: list of paths and list of sets
    """
    _paths = []
    _sets = []
    for set in sets:
        if Indexes.is_index(set):
            _paths.append(set)
        else:
            _sets.append(set)

    return _paths, _sets


def is_new_workflow(record):
    """Check workflow is new activity."""
    return str(record.get("publish_status")) == PublishStatus.NEW.value


def is_deleted_workflow(pid, record):
    """Check workflow is deleted."""
    return pid.status == PIDStatus.DELETED or \
        str(record.get("publish_status")) == PublishStatus.DELETE.value


def is_private_workflow(record):
    """Check publish status of workflow is private."""
    return str(record.get("publish_status")) == PublishStatus.PRIVATE.value


def is_pubdate_in_future(record):
    """Check pubdate of workflow is in future."""
    from weko_records_ui.utils import is_future
    adt = record.get('publish_date')
    return is_future(adt)


def is_private_index(record):
    """Check index of workflow is private."""
    paths = pickle.loads(pickle.dumps(record.get('path'), -1))
    return not Indexes.is_public_state_and_not_in_future(paths)


def is_private_index_by_public_list(item_path, public_index_ids):
    """Check index of workflow is private."""
    for path in item_path:
        if path in public_index_ids:
            return False
    return True


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
    """Create OAI-PMH response for verb GetRecord."""
    # current_app.logger.debug("kwargs:{0}".format(kwargs))
    # kwargs:{'metadataPrefix': 'jpcoar_1.0', 'identifier': 'oai:weko3.example.org:00000003', 'verb': 'GetRecord'}

    identify = OaiIdentify.get_all()
    if not identify or not identify.outPutSetting:
        return error([('idDoesNotExist', 'No matching identifier')])

    record_dumper = serializer(kwargs['metadataPrefix'])
    pid_object = OAIIDProvider.get(pid_value=kwargs['identifier']).pid
    record = WekoRecord.get_record_by_uuid(pid_object.object_uuid)
    set_identifier(record, record)

    e_tree, e_getrecord = verb(**kwargs)
    e_record = SubElement(e_getrecord, etree.QName(NS_OAIPMH, 'record'))

    index_state = get_index_state()
    path_list = record.get('path') if 'path' in record else []
    _is_output = is_output_harvest(path_list, index_state)
    current_app.logger.debug("_is_output:{}".format(_is_output))
    current_app.logger.debug("path_list:{}".format(path_list))
    current_app.logger.debug(
        "is_exists_doi(record):{}".format(is_exists_doi(record)))
    current_app.logger.debug(
        "is_pubdate_in_future(record):{}".format(is_pubdate_in_future(record)))
    current_app.logger.debug("is_deleted_workflow(pid_object, record):{}".format(
        is_deleted_workflow(pid_object, record)))
    current_app.logger.debug(
        "is_private_workflow(pid_object):{}".format(is_private_workflow(record)))

    # Harvest is private
    # or New activity
    if path_list and (_is_output == HARVEST_PRIVATE or
                      (is_exists_doi(record) and
                       (_is_output == PRIVATE_INDEX or is_pubdate_in_future(record))) or
                      is_new_workflow(record)):
        return error([('idDoesNotExist', 'No matching identifier')])
    # Item is deleted
    # or Harvest is public & Item is private
    # or Harvest is public & Index is private
    # or Harvest is public & There is no guest role in the index Browsing Privilege
    elif _is_output == PRIVATE_INDEX or \
            not path_list or \
            is_deleted_workflow(pid_object, record) or \
            is_private_workflow(record) or \
            is_pubdate_in_future(record):
        header(
            e_record,
            identifier=pid_object.pid_value,
            datestamp=record.updated,
            deleted=True
        )
        return e_tree

    _sets = list(set(record.get('path', [])+record['_oai'].get('sets', [])))
    header(
        e_record,
        identifier=pid_object.pid_value,
        datestamp=record.updated,
        sets=_sets
    )
    e_metadata = SubElement(e_record,
                            etree.QName(NS_OAIPMH, 'metadata'))

    etree_record = pickle.loads(pickle.dumps(record, -1))

    if not etree_record.get('system_identifier_doi', None):
        etree_record['system_identifier_doi'] = get_identifier(record)

    # Merge licensetype and licensefree
    etree_record = handle_license_free(etree_record)

    root = record_dumper(pid_object, {'_source': etree_record})

    e_metadata.append(root)
    return e_tree


def listidentifiers(**kwargs):
    """Create OAI-PMH response for verb ListIdentifiers."""
    e_tree, e_listidentifiers = verb(**kwargs)
    identify = OaiIdentify.get_all()
    if not identify or not identify.outPutSetting:
        return error(get_error_code_msg(), **kwargs)

    index_state = get_index_state()
    set_is_output = 0
    if 'set' in kwargs:
        set_obj = OAISet.get_set_by_spec(kwargs['set'])
        if not set_obj:
            return error(get_error_code_msg(), **kwargs)
        path = kwargs['set'].replace(':', '/')
        set_is_output = is_output_harvest([path], index_state)
        if set_is_output == HARVEST_PRIVATE:
            return error(get_error_code_msg(), **kwargs)

    result = get_records(**kwargs)
    if not result.total:
        return error(get_error_code_msg(), **kwargs)

    for r in result.items:
        try:
            pid = oaiid_fetcher(r['id'], r['json']['_source'])
            pid_object = OAIIDProvider.get(pid_value=pid.pid_value).pid
            record = WekoRecord.get_record_by_uuid(pid_object.object_uuid)
            set_identifier(record, record)

            path_list = record.get('path') if 'path' in record else []
            _is_output = is_output_harvest(path_list, index_state) \
                if 'set' not in kwargs else set_is_output
            current_app.logger.debug("pid:{}".format(pid))
            current_app.logger.debug("_is_output:{}".format(_is_output))
            current_app.logger.debug("path_list:{}".format(path_list))
            current_app.logger.debug(
                "is_exists_doi(record):{}".format(is_exists_doi(record)))
            current_app.logger.debug(
                "is_pubdate_in_future(record):{}".format(is_pubdate_in_future(record)))
            current_app.logger.debug("is_deleted_workflow(pid_object, record):{}".format(
                is_deleted_workflow(pid_object, record)))
            current_app.logger.debug(
                "is_private_workflow(pid_object):{}".format(is_private_workflow(record)))
            # Harvest is private
            if path_list and (_is_output == HARVEST_PRIVATE or
                              (is_exists_doi(record) and
                               (_is_output == PRIVATE_INDEX or is_pubdate_in_future(record))) or
                              is_new_workflow(record)):
                continue
            # Item is deleted
            # or Harvest is public & Item is private
            # or Harvest is public & Index is private
            # or Harvest is public & There is no guest role in the index Browsing Privilege
            elif _is_output == PRIVATE_INDEX or \
                    not path_list or \
                    is_deleted_workflow(pid_object, record) or \
                    is_private_workflow(record) or \
                    is_pubdate_in_future(record):
                header(
                    e_listidentifiers,
                    identifier=pid.pid_value,
                    #datestamp=r['updated'],
                    datestamp=record.updated,
                    deleted=True
                )
            else:
                _sets = list(set(record.get('path', []) +
                                 record['_oai'].get('sets', [])))
                header(
                    e_listidentifiers,
                    identifier=pid.pid_value,
                    # datestamp=r['updated'],
                    datestamp=record.updated,
                    sets=_sets
                )
        except PIDDoesNotExistError:
            current_app.logger.error(
                "PIDDoesNotExistError: pid_value: {}".format(pid.pid_value))
            current_app.logger.error(
                "PIDDoesNotExistError: recid: {}".format(r['id']))
        except NoResultFound:
            current_app.logger.error(
                "NoResultFound: object_uuid: {}".format(pid_object.object_uuid))

    if len(e_listidentifiers) == 0:
        return error(get_error_code_msg(), **kwargs)

    current_app.logger.debug(
        "number of identifiers :{}".format(len(e_listidentifiers)))
    resumption_token(e_listidentifiers, result, **kwargs)
    return e_tree


def listrecords(**kwargs):
    """Create OAI-PMH response for verb ListRecords."""
    if _use_file_data(**kwargs):
        return _create_response_from_file(**kwargs)

    record_dumper = serializer(kwargs['metadataPrefix'])
    e_tree, e_listrecords = verb(**kwargs)

    identify = OaiIdentify.get_all()
    if not identify or not identify.outPutSetting:
        current_app.logger.debug(
            "No identify.outPutSetting")
        return error(get_error_code_msg(), **kwargs)

    index_state = get_index_state()
    set_is_output = 0
    if 'set' in kwargs:
        set_obj = OAISet.get_set_by_spec(kwargs['set'])
        if not set_obj:
            return error(get_error_code_msg(), **kwargs)
        current_app.logger.debug("set: {}".format(set_obj.spec))
        path = kwargs['set'].replace(':', '/')
        set_is_output = is_output_harvest([path], index_state)
        current_app.logger.debug("set_is_output: {}".format(set_is_output))
        if set_is_output == HARVEST_PRIVATE:
            return error(get_error_code_msg(), **kwargs)

    result = get_records(**kwargs)
    if not result.total:
        return error(get_error_code_msg(), **kwargs)

    for r in result.items:
        try:
            pid = oaiid_fetcher(r['id'], r['json']['_source'])
            pid_object = OAIIDProvider.get(pid_value=pid.pid_value).pid
            record = WekoRecord.get_record_by_uuid(pid_object.object_uuid)
            set_identifier(record, record)
            path_list = record.get('path') if 'path' in record else []
            _is_output = is_output_harvest(path_list, index_state) \
                if 'set' not in kwargs else set_is_output

            current_app.logger.debug("pid:{}".format(pid))
            current_app.logger.debug("_is_output:{}".format(_is_output))
            current_app.logger.debug("path_list:{}".format(path_list))
            current_app.logger.debug(
                "is_exists_doi(record):{}".format(is_exists_doi(record)))
            current_app.logger.debug(
                "is_pubdate_in_future(record):{}".format(is_pubdate_in_future(record)))
            current_app.logger.debug("is_deleted_workflow(pid_object, record):{}".format(
                is_deleted_workflow(pid_object, record)))
            current_app.logger.debug(
                "is_private_workflow(pid_object):{}".format(is_private_workflow(record)))
            # Harvest is private
            if path_list and (_is_output == HARVEST_PRIVATE or
                              (is_exists_doi(record) and
                               (_is_output == PRIVATE_INDEX or is_pubdate_in_future(record))) or
                              is_new_workflow(record)):
                continue
            # Item is deleted
            # or Harvest is public & Item is private
            # or Harvest is public & Index is private
            # or Harvest is public & There is no guest role in the index Browsing Privilege
            elif _is_output == PRIVATE_INDEX or \
                    not path_list or \
                    is_deleted_workflow(pid_object, record) or \
                    is_private_workflow(record) or \
                    is_pubdate_in_future(record):
                e_record = SubElement(
                    e_listrecords, etree.QName(NS_OAIPMH, 'record'))

                # When called from a batch of file creation for ListRecords,
                # the set information is embedded at delete.
                if kwargs.get('url') == 'batch':
                    _sets = list(set(r['json']['_source'].get('path', []) +
                                 r['json']['_source']['_oai'].get('sets', [])))
                    header(
                        e_record,
                        identifier=pid.pid_value,
                        datestamp=record.updated,
                        sets=_sets,
                        deleted=True
                    )
                else:
                    header(
                        e_record,
                        identifier=pid.pid_value,
                        #datestamp=r['updated'],
                        datestamp=record.updated,
                        deleted=True
                    )
            else:
                e_record = SubElement(
                    e_listrecords, etree.QName(NS_OAIPMH, 'record'))
                _sets = list(set(record.get('path', []) +
                                 record['_oai'].get('sets', [])))
                header(
                    e_record,
                    identifier=pid.pid_value,
                    datestamp=record.updated,
                    sets=_sets
                )
                e_metadata = SubElement(e_record, etree.QName(NS_OAIPMH,
                                                              'metadata'))
                etree_record = pickle.loads(pickle.dumps(record, -1))
                if not etree_record.get('system_identifier_doi', None):
                    etree_record['system_identifier_doi'] = get_identifier(
                        record)

                # Merge licensetype and licensefree
                etree_record = handle_license_free(etree_record)
                e_metadata.append(record_dumper(
                    pid, {'_source': etree_record}))

        except PIDDoesNotExistError:
            current_app.logger.error(
                "PIDDoesNotExistError: pid_value: {}".format(pid.pid_value))
            current_app.logger.error(
                "PIDDoesNotExistError: recid: {}".format(r['id']))
        except NoResultFound:
            current_app.logger.error(
                "NoResultFound: object_uuid: {}".format(pid_object.object_uuid))

    # Check <record> tag not exist.
    if len(e_listrecords) == 0:
        return error(get_error_code_msg(), **kwargs)

    current_app.logger.debug(
        "number of records :{}".format(len(e_listrecords)))
    resumption_token(e_listrecords, result, **kwargs)
    return e_tree


def get_error_code_msg(code=''):
    """Return list error message."""
    msg = ""
    if code == '':
        code = current_app.config.get('OAISERVER_CODE_NO_RECORDS_MATCH')
        msg = current_app.config.get('OAISERVER_MESSAGE_NO_RECORDS_MATCH')

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
    from weko_records.api import ItemsMetadata
    from weko_records.serializers.utils import get_mapping

    item_type = ItemsMetadata.get_by_object_id(object_uuid)
    item_map = get_mapping(item_type.item_type_id, "jpcoar_mapping")

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
    from weko_records.api import ItemsMetadata
    from weko_records.serializers.utils import get_mapping
    from weko_schema_ui.schema import get_oai_metadata_formats

    metadata_formats = get_oai_metadata_formats(current_app)
    item_type = ItemsMetadata.get_by_object_id(object_uuid)
    mapping_type = metadata_formats[meta_prefix]['serializer'][1]['schema_type']
    item_map = get_mapping(item_type.item_type_id,
                           "{}_mapping".format(mapping_type))
    file_keys_str = None
    if item_map:
        file_props = current_app.config["OAISERVER_FILE_PROPS_MAPPING"]
        if mapping_type in file_props:
            file_keys_str = item_map.get(file_props[mapping_type])
        else:
            file_keys_str = None

    if not file_keys_str:
        return record
    else:
        file_keys = file_keys_str.split(',')

    for file_key in file_keys:
        key = file_key.split('.')
        if len(key) == 3 and record.get(key[0]):
            attr_mlt = record[key[0]]["attribute_value_mlt"]
            if isinstance(attr_mlt, list):
                for attr in attr_mlt:
                    if attr.get('filename'):
                        if not attr.get(key[1]):
                            attr[key[1]] = {}
                        attr[key[1]][key[2]] = create_files_url(
                            request.url_root,
                            record.get('recid'),
                            attr.get('filename'))
            elif isinstance(attr_mlt, dict) and \
                    attr_mlt.get('filename'):
                if not attr_mlt.get(key[1]):
                    attr_mlt[key[1]] = {}
                attr_mlt[key[1]][key[2]] = create_files_url(
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


def _create_response_from_file(**kwargs):
    """ Create the ListRecords response from a pre-created file.

        Args:
            kwargs: Parameters
        Returns:
            XML ListRecords response.
    """
    e_tree, e_listrecords = verb(**kwargs)
    location = get_location()
    if location is None:
        current_app.logger.error(
            'ERR_IOS-001: Location is not set up correctly.')
        return error([('ERR_IOS-001', 'InternalError')], **kwargs)

    param = None
    if 'resumptionToken' not in kwargs:
        data_json = get_data_json(location)
        if data_json is None:
            current_app.logger.error('ERR_IOS-002: IO error occurred.\
                                      Could not retrieve data_json.')
            return error([('ERR_IOS-002', 'InternalError')], **kwargs)

        param = _get_parameter(data_json, **kwargs)
    else:
        param = _get_parameter(None, **kwargs)

    current_app.logger.debug('param : {0}'.format(param))

    file_objs, data_count, index_obj = get_target_files(param)

    if index_obj is None:
        current_app.logger.error('ERR_IOS-002: IO error occurred.\
                                  Could not retrieve index_json.')
        return error([('ERR_IOS-002', 'InternalError')], **kwargs)

    if data_count == 0:
        return error(get_error_code_msg(), **kwargs)

    data_index = param['index']
    for file_obj in file_objs:
        with file_obj.file.storage().open() as f:
            record = etree.fromstring(f.read().decode(encoding='utf-8'))
            e_listrecords.append(record)
            data_index += 1

    _resumption_token_file_response(
        e_listrecords, data_index, data_count, **param)

    return e_tree


def _resumption_token_file_response(parent, data_index, data_count, **param):
    """Attach resumption token element to a parent."""

    if data_count < current_app.config['OAISERVER_PAGE_SIZE']:
        return

    token = serialize_file_response(data_index, data_count, **param)
    e_resumptionToken = SubElement(parent, etree.QName(NS_OAIPMH,
                                                       'resumptionToken'))
    e_resumptionToken.set('expirationDate', param['expirationDate'])
    e_resumptionToken.set('cursor', str(param['index']))
    e_resumptionToken.set('completeListSize', str(data_count))

    if token:
        e_resumptionToken.text = token


def get_target_files(param):
    """ Returns the file information to be returned by ListRecords.

        Args:
            param: Parameters containing search criteria
        Returns:
            File information to be returned for ListRecords.
    """
    current_app.logger.debug('param : {0}'.format(param))
    folder_path = '{0}/{1}/{2}'.format(
        OAIPMH_FOLDER_NAME, param['data_id'], param['metadataPrefix'])
    current_app.logger.debug(
        'index.json search key : {0}/index.json'.format(folder_path))
    index_obj = ObjectVersion.query.filter_by(
        key='{0}/index.json'.format(folder_path)).first()

    if index_obj is None:
        return None, None, None

    index = param['index']
    target_count = 0
    response_count = 0
    page_size = current_app.config['OAISERVER_PAGE_SIZE']
    file_obj_key = []
    with index_obj.file.storage().open() as f:
        index_json = json.loads(f.read().decode(encoding='utf-8'))
        for item_json in index_json.get('items'):
            if is_target_file(item_json, param):
                target_count += 1
                if index < target_count and response_count < page_size:
                    response_count += 1
                    file_obj_key.append('{0}/{1}'.format(
                        folder_path, item_json.get('file_name')))

    file_objs = ObjectVersion.query.filter(
        ObjectVersion.key.in_(file_obj_key)).order_by(ObjectVersion.key)

    return file_objs, target_count, index_obj


def is_target_file(item_json, param):
    """ Determine whether the item in question is eligible for return.

        Args:
            item_json: Information on items
            param: Parameters containing search criteria
        Returns:
            Returns True if the target item is eligible for return.
    """
    item_time = datetime.strptime(
        item_json.get('datestamp'), '%Y-%m-%dT%H:%M:%SZ')
    if param.get('from_time') is not None and \
       param.get('from_time').replace(tzinfo=None) > item_time:
        return False
    if param.get('until_time') is not None and \
       param.get('until_time').replace(tzinfo=None) < item_time:
        return False
    if param.get('set_spec') is not None:
        if len(item_json.get('setSpec')) == 0:
            return False

        for setspec in item_json.get('setSpec'):
            if param.get('set_spec') != setspec:
                return False

    return True


def get_location():
    """ Returns the Location where the file for acceleration is stored."""

    location_name = current_app.config['OAISERVER_FILE_BATCH_STORAGE_LOACTION']
    if location_name is None:
        return None

    return Location.query.filter_by(name=location_name).first()


def get_data_json(location):
    """ Get definition information on files for acceleration.

        Args:
            location: Location where the file is stored.
        Returns:
            Definition information on files for acceleration.
    """

    data_json = None
    data_folder = None

    for obj_version in ObjectVersion.query.filter_by(key=OAIPMH_FOLDER_NAME):
        if obj_version.bucket.default_location == location.id:
            data_folder = obj_version
            break

    current_app.logger.debug('data_folder : {0}'.format(str(data_folder)))

    if data_folder:
        data_json_obj = ObjectVersion.get(
            data_folder.bucket_id, "{0}/data.json".format(OAIPMH_FOLDER_NAME))
        current_app.logger.debug('file_id : {0}'.format(data_json_obj.file_id))
        if data_json_obj is not None:
            try:
                with data_json_obj.file.storage().open() as f:
                    data_json = json.loads(f.read().decode(encoding='utf-8'))
                    current_app.logger.debug(
                        'data.json : {0}'.format(data_json))
            except Exception as e:
                current_app.logger.error(e)
                current_app.logger.error(traceback.format_exc())
                raise e
    return data_json


def _get_parameter(data_json, **kwargs):
    """ Get the parameters required to create a
        ListRecords response from a file.

        Args:
            data_json: Definition information on files for acceleration.
            kwargs: request parameter.
        Returns:
            True if created from a file.
    """
    result = {}
    from_time_obj = None
    until_time_obj = None
    current_app.logger.debug('kwargs : {0}'.format(kwargs))
    if 'resumptionToken' in kwargs:
        if kwargs['resumptionToken'].get('from') is not None:
            from_time_obj = datetime.strptime(
                kwargs['resumptionToken'].get('from'), '%Y-%m-%dT%H:%M:%SZ')
        if kwargs['resumptionToken'].get('until') is not None:
            until_time_obj = datetime.strptime(
                kwargs['resumptionToken'].get('until'), '%Y-%m-%dT%H:%M:%SZ')

        result.update(
            verb=kwargs['verb'],
            data_id=kwargs['resumptionToken'].get('data_id'),
            metadataPrefix=kwargs['resumptionToken'].get('metadataPrefix'),
            from_time=from_time_obj,
            from_time_str=kwargs['resumptionToken'].get('from'),
            until_time=until_time_obj,
            until_time_str=kwargs['resumptionToken'].get('until'),
            set_spec=kwargs['resumptionToken'].get('set'),
            index=kwargs['resumptionToken'].get('index'),
            expirationDate=kwargs['resumptionToken'].get('expirationDate')
        )
    else:
        if 'set' in kwargs:
            set_obj = OAISet.get_set_by_spec(kwargs['set'])
            if not set_obj:
                return error(get_error_code_msg(), **kwargs)
            path = kwargs['set'].replace(':', '/')
            index_state = get_index_state()
            set_is_output = is_output_harvest([path], index_state)
            if set_is_output == HARVEST_PRIVATE:
                return error(get_error_code_msg(), **kwargs)

        expirationDate = None
        for data in data_json.get('datas'):
            if data.get('id') == data_json.get('current_data'):
                expirationDate = data.get('expired_time')

        from_time_str = None
        if kwargs.get('from_') is not None:
            from_time_str = datetime_to_datestamp(kwargs.get('from_'))

        until_time_str = None
        if kwargs.get('until') is not None:
            until_time_str = datetime_to_datestamp(kwargs.get('until'))

        result.update(
            verb=kwargs.get('verb'),
            data_id=data_json.get('current_data'),
            metadataPrefix=kwargs.get('metadataPrefix'),
            from_time=kwargs.get('from_'),
            from_time_str=from_time_str,
            until_time=kwargs.get('until'),
            until_time_str=until_time_str,
            set_spec=kwargs.get('set'),
            index=0,
            expirationDate=expirationDate
        )
    return result


def _use_file_data(**kwargs):
    """ Determines whether a response is created from a file.

        Args:
            kwargs: Parameters
        Returns:
            True if created from a file.
    """
    if kwargs.get('url') == 'batch':
        return False
    if 'resumptionToken' in kwargs:
        if kwargs['resumptionToken'].get('data_id') is not None:
            return True
        return False

    try:
        file_batch_enable = current_app.config['OAISERVER_FILE_BATCH_ENABLE']
        if not file_batch_enable:
            return False

        location = get_location()
        if location is None:
            return False

        if not kwargs.get('metadataPrefix') in \
           current_app.config['OAISERVER_FILE_BATCH_FORMATS']:
            return False

        data_json = get_data_json(location)
        if data_json is None:
            return False

        if data_json.get('current_data') is None:
            return False

        folder_path = '{0}/{1}/{2}'.format(OAIPMH_FOLDER_NAME,
                                           data_json.get('current_data'),
                                           kwargs.get('metadataPrefix'))
        index_obj = ObjectVersion.query.filter_by(
            key='{0}/index.json'.format(folder_path)).first()
        if index_obj is None:
            return False

        return True
    except Exception as e:
        current_app.logger.warn(e)
        current_app.logger.warn(traceback.format_exc())
        current_app.logger.warn('ERR_IOS-002: IO error occurred.')

        return False
