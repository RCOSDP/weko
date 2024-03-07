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
from datetime import MINYEAR, datetime, timedelta

from flask import current_app, request, url_for
from flask_babelex import get_locale, to_user_timezone, to_utc
from invenio_communities import config as invenio_communities_config
from invenio_communities.models import Community
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PIDStatus
from invenio_records.models import RecordMetadata
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
from .resumption_token import serialize
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


def is_pubdate_in_future(record, isReserved=False):
    """Check pubdate of workflow is in future."""
    from weko_records_ui.utils import is_future
    adt = record.get('publish_date')

    # DOI RESERVATION FIX ------------ START
    if not is_future(adt):
        from invenio_pidstore.models import PersistentIdentifier
        record_keys = [
            key for key in record.keys()
        ]
        doi_text = ""

        for doi_item_key in record_keys:
            if isinstance(record.get(doi_item_key), dict):
                if record.get(doi_item_key).get("attribute_value_mlt") and \
                        isinstance(record.get(doi_item_key).get("attribute_value_mlt"), list) and \
                        record.get(doi_item_key).get("attribute_value_mlt") is not None:
                    if record.get(doi_item_key).get("attribute_value_mlt")[0].get("subitem_identifier_reg_text"):
                        doi_text = record.get(doi_item_key) \
                            .get("attribute_value_mlt")[0] \
                            .get("subitem_identifier_reg_text")
                            
        reserved_pid_doi = PersistentIdentifier.query.filter_by(
            pid_type="doi",
            pid_value=f"https://doi.org/" + doi_text,
            status=PIDStatus.REGISTERED
        ).order_by(
            db.desc(PersistentIdentifier.created)
        ).first()

        if (not isReserved and reserved_pid_doi is not None) or reserved_pid_doi is not None:
            from weko_workflow.models import ActionIdentifier, Activity, ActionStatusPolicy
            from weko_workflow.config import IDENTIFIER_GRANT_SELECT_DICT
            from weko_workflow.utils import prepare_edit_workflow, get_actionid, IdentifierHandle, \
                check_doi_validation_not_pass, convert_record_to_item_metadata, saving_doi_pidstore, \
                handle_finish_workflow
            from weko_workflow.api import WorkActivity
            from weko_workflow.views import previous_action
            from weko_items_ui.views import prepare_edit_item
            from weko_items_ui.utils import get_workflow_by_item_type_id
            from werkzeug.utils import import_string
            from invenio_pidstore.resolver import Resolver
            from weko_workflow.api import WorkActivity
            from invenio_pidrelations.contrib.versioning import PIDVersioning
            from weko_records.api import ItemTypes
            from weko_records_ui.utils import get_record_permalink
            from weko_workflow.schema.marshmallow import ResponseMessageSchema
            from flask import jsonify, has_request_context, abort
            from weko_deposit.signals import item_created

            identifier_grant = {
                'action_identifier_select': "",
                'action_identifier_jalc_doi': "",
                'action_identifier_jalc_cr_doi': "",
                'action_identifier_jalc_dc_doi': "",
                'action_identifier_ndl_jalc_doi': ""
            }

            doi_url = "https://doi.org/"

            post_json = {
                "identifier_grant_jalc_doi_link": "",
                "identifier_grant_jalc_cr_doi_link": "",
                "identifier_grant_jalc_dc_doi_link": "",
                "identifier_grant_ndl_jalc_doi_link": "",
            }
            
            record_title = record.get("title")[0]

            action_identifier = {}
            record_keys = [key for key in record.keys()]
            for key in record_keys:
                if isinstance(record[key], dict):
                    if "attribute_value_mlt" in record[key].keys():
                        if record[key].get("attribute_value_mlt") and \
                                isinstance(record[key].get("attribute_value_mlt"), list):
                            for identifier_reg_type in record[key].get("attribute_value_mlt"):
                                if isinstance(identifier_reg_type, dict):
                                    if identifier_reg_type.get("subitem_identifier_reg_text"):
                                        action_identifier['subitem_identifier_reg_text'] = identifier_reg_type.get("subitem_identifier_reg_text")
                                    if identifier_reg_type.get("subitem_identifier_reg_type"):
                                        action_identifier['subitem_identifier_reg_type'] = identifier_reg_type.get("subitem_identifier_reg_type")
                                        
                                        if identifier_reg_type.get("subitem_identifier_reg_type") == "JaLC":
                                            post_json["identifier_grant_jalc_doi_link"] = doi_url + identifier_reg_type.get("subitem_identifier_reg_text")
                                        elif identifier_reg_type.get("subitem_identifier_reg_type") == "Crossref":
                                            post_json["identifier_grant_jalc_doi_link"] = doi_url + identifier_reg_type.get("subitem_identifier_reg_text")
                                        elif identifier_reg_type.get("subitem_identifier_reg_type") == "DataCite":
                                            post_json["identifier_grant_jalc_doi_link"] = doi_url + identifier_reg_type.get("subitem_identifier_reg_text")
                                        elif identifier_reg_type.get("subitem_identifier_reg_type") == "NDL JaLC":
                                            post_json["identifier_grant_jalc_doi_link"] = doi_url + identifier_reg_type.get("subitem_identifier_reg_text")

            if action_identifier.get("subitem_identifier_reg_type") == "JaLC":
                identifier_grant["action_identifier_select"] = "1"
            elif action_identifier.get("subitem_identifier_reg_type") == "Crossref":
                identifier_grant["action_identifier_select"] = "2"
            elif action_identifier.get("subitem_identifier_reg_type") == "DataCite":
                identifier_grant["action_identifier_select"] = "3"
            elif action_identifier.get("subitem_identifier_reg_type") == "NDL JaLC":
                identifier_grant["action_identifier_select"] = "4"
            
            pid_value = record.get('_deposit', {}).get('pid', {}).get('value')
            record_class = import_string('weko_deposit.api:WekoDeposit')
            resolver = Resolver(
                pid_type='recid',
                object_type='rec',
                getter=record_class.get_record
            )
            recid, deposit = resolver.resolve(pid_value)

            draft_pid = PersistentIdentifier.query.filter_by(
                pid_type='recid',
                pid_value="{}.0".format(recid.pid_value)
            ).one_or_none()

            from sqlalchemy.exc import SQLAlchemyError
            from weko_deposit.api import WekoDeposit
            from invenio_files_rest.models import Bucket
            from invenio_records_files.models import RecordsBuckets

            if not draft_pid:
                draft_record = deposit.prepare_draft_item(recid)
                # create item link info of draft record from parent record
                weko_record = WekoRecord.get_record_by_pid(
                    draft_record.pid.pid_value)
                if weko_record:
                    weko_record.update_item_link(recid.pid_value)
            else:
                # Clone org bucket into draft record.
                try:
                    _parent = WekoDeposit.get_record(recid.object_uuid)
                    _deposit = WekoDeposit.get_record(draft_pid.object_uuid)
                    _deposit['path'] = _parent.get('path')
                    _deposit.merge_data_to_record_without_version(recid, True)
                    _deposit.publish()
                    _bucket = Bucket.get(_deposit.files.bucket.id)

                    if not _bucket:
                        _bucket = Bucket.create(
                            quota_size=current_app.config['WEKO_BUCKET_QUOTA_SIZE'],
                            max_file_size=current_app.config['WEKO_MAX_FILE_SIZE'],
                        )
                        RecordsBuckets.create(record=_deposit.model, bucket=_bucket)
                        _deposit.files.bucket.id = _bucket

                    bucket = deposit.files.bucket

                    sync_bucket = RecordsBuckets.query.filter_by(
                        bucket_id=_deposit.files.bucket.id
                    ).first()

                    snapshot = bucket.snapshot(lock=False)
                    snapshot.locked = False
                    _bucket.locked = False

                    sync_bucket.bucket_id = snapshot.id
                    _deposit['_buckets']['deposit'] = str(snapshot.id)

                    db.session.add(sync_bucket)
                    _bucket.remove()

                    _metadata = convert_record_to_item_metadata(deposit)
                    _metadata['deleted_items'] = {}
                    _cur_keys = [_key for _key in _metadata.keys()
                                if 'item_' in _key]
                    _drf_keys = [_key for _key in _deposit.item_metadata.keys()
                                if 'item_' in _key]
                    _metadata['deleted_items'] = list(set(_drf_keys) - set(_cur_keys))
                    
                    # _deposit.publish()

                    index = {'index': _deposit.get('path', []),
                            'actions': _deposit.get('publish_status')}
                    args = [index, _metadata]
                    _deposit.update(*args)
                    _deposit.commit()

                except SQLAlchemyError as ex:
                    raise ex
            
            post_activity = {}
            item_type_id = deposit.get('item_type_id')
            item_type = ItemTypes.get_by_id(item_type_id)
            activity = WorkActivity()
            latest_pid = PIDVersioning(child=recid).last_child
            item_uuid = latest_pid.object_uuid

            post_workflow = activity.get_workflow_activity_by_item_id(item_uuid)

            if not post_workflow:
                post_workflow = activity.get_workflow_activity_by_item_id(
                    recid.object_uuid
                )

            workflow = get_workflow_by_item_type_id(
                item_type.name_id,
                item_type_id
            )
            
            post_activity['workflow_id'] = workflow.id
            post_activity['flow_id'] = workflow.flow_id
            post_activity['itemtype_id'] = item_type_id
            post_activity['community'] = 'Root Index'
            post_activity['post_workflow'] = post_workflow

            doi_reservation_record_activity = post_workflow
            doi_reservation_record_activity_id = post_workflow.activity_id
            doi_reservation_record_action_identifier = ActionIdentifier.query.filter_by(activity_id=doi_reservation_record_activity_id).one_or_none()
            identifier_actionid = get_actionid('identifier_grant')
            work_activity = WorkActivity()
            activity_detail = work_activity.get_activity_detail(doi_reservation_record_activity_id)
            pid_id_hdn = IdentifierHandle(recid.object_uuid)
            pid_doi_ffxv = WekoRecord.get_record_by_pid(record.get("_deposit", {}).get("id"))

            work_activity.create_or_update_action_identifier(
                activity_id=doi_reservation_record_activity_id,
                action_id=identifier_actionid,
                identifier=identifier_grant,
            )

            saving_doi_pidstore(
                activity_detail.item_id,
                activity_detail.item_id,
                post_json,
                int(identifier_grant["action_identifier_select"]),
                False
            )

            pid_doi = IdentifierHandle(recid.object_uuid).get_pidstore()

            current_pid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                                object_type='rec',
                                                                object_uuid=activity_detail.item_id)

            try:
                if '.' not in pid_value and has_request_context():
                    user_id = activity_detail.activity_login_user if \
                        activity and activity_detail.activity_login_user else -1
                    item_created.send(
                        current_app._get_current_object(),
                        user_id=user_id,
                        item_id=current_pid,
                        item_title=record_title
                    )
                    
            except BaseException:
                abort(500, 'MAPPING_ERROR')

            flag = work_activity.upt_activity_action_status(
                activity_id=doi_reservation_record_activity_id, action_id=identifier_actionid,
                action_status=ActionStatusPolicy.ACTION_DONE,
                action_order='6'
            )
            if not flag:
                res = ResponseMessageSchema().load({"code":-2, "msg":""})
                return jsonify(res.data), 500
            work_activity.upt_activity_action_comment(
                activity_id=doi_reservation_record_activity_id,
                action_id=identifier_actionid,
                comment='',
                action_order='9'
            )
            doi_reserved_item_workflow = handle_finish_workflow(
                deposit,
                current_pid,
                recid
            )

        else:
            return is_future(adt)

    # DOI RESERVATION FIX ------------ END
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
