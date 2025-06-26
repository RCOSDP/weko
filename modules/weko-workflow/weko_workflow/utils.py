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

"""Module of weko-workflow utils."""

import base64
import json
import os
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
import sys
from typing import List, NoReturn, Optional, Tuple, Union
import traceback

import pytz
import redis
from redis import sentinel
from celery.task.control import inspect
from flask import current_app, request, session
from flask_babelex import gettext as _
from flask_security import current_user
from invenio_accounts.models import Role, User, userrole
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_i18n.ext import current_i18n
from invenio_mail.admin import MailSettingView
from invenio_mail.models import MailConfig
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier, \
    PIDDoesNotExistError, PIDStatus
from invenio_pidstore.resolver import Resolver
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from passlib.handlers.oracle import oracle10
from simplekv.memory.redisstore import RedisStore
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from weko_admin.models import Identifier, SiteInfo, AdminSettings
from weko_admin.utils import get_restricted_access
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_handle.api import Handle
from weko_logging.activity_logger import UserActivityLogger
from weko_records.api import FeedbackMailList, RequestMailList, ItemsMetadata, ItemTypeNames, \
    ItemTypes, Mapping
from weko_records.models import ItemType, ItemReference
from weko_records.serializers.utils import get_full_mapping, get_item_type_name
from weko_records_ui.models import FilePermission
from weko_records_ui.external import call_external_system
from weko_redis import RedisConnection
from weko_user_profiles.config import \
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_POSITION_LIST
from weko_user_profiles.utils import get_user_profile_info
from werkzeug.utils import import_string
from weko_deposit.pidstore import get_record_without_version

from weko_workflow.config import IDENTIFIER_GRANT_LIST, \
    IDENTIFIER_GRANT_SUFFIX_METHOD, \
    WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TYPES_LIST, \
    WEKO_WORKFLOW_USAGE_REPORT_ITEM_TYPES_LIST


from .api import GetCommunity, UpdateItem, WorkActivity, WorkActivityHistory, \
    WorkFlow , Flow
from .config import DOI_VALIDATION_INFO, DOI_VALIDATION_INFO_CROSSREF, DOI_VALIDATION_INFO_DATACITE, IDENTIFIER_GRANT_SELECT_DICT, \
    WEKO_SERVER_CNRI_HOST_LINK, WEKO_STR_TRUE
from .models import Action as _Action, Activity
from .models import ActionStatusPolicy, ActivityStatusPolicy, GuestActivity,FlowAction
from .models import WorkFlow as _WorkFlow

def get_current_language():
    """Get current language.

    :return:
    """
    current_lang = current_i18n.language
    # In case current_lang is not English
    # neither Japanese set default to English
    languages = current_app.config[
        'WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_LANGUAGES']
    if current_lang not in languages:
        current_lang = 'en'
    return current_lang


def get_term_and_condition_content(item_type_name):
    """Read data of term and condition base on language and item_type_name.

    :param item_type_name:
    :return:
    """
    file_extension = current_app.config[
        'WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_EXTENSION']
    folder_path = current_app.config[
        'WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_LOCATION']
    current_lang = get_current_language()
    file_name = item_type_name + "_" + current_lang + file_extension
    data = ""
    try:
        with open(folder_path + file_name) as file:
            data = file.read().splitlines()
    except FileNotFoundError as ex:
        current_app.logger.error(str(ex))
    return data


def get_identifier_setting(community_id):
    """
    Get Identifier Setting of current Community.

    :param community_id: Community Identifier
    :return: Dict or None
    """
    with db.session.no_autoflush:
        return Identifier.query.filter_by(
            repository=community_id).one_or_none()


def saving_doi_pidstore(item_id,
                        record_without_version,
                        data=None,
                        doi_select=0,
                        temporal_saving=False):
    """
    Mapp doi pidstore data to ItemMetadata.

    :param data: request data
    :param doi_select: identifier selected
    :param item_id: object uuid
    :param record_without_version: object uuid
    """
    current_app.logger.debug('item_id: {0}'.format(item_id))
    current_app.logger.debug(
        'record_without_version: {0}'.format(record_without_version))
    current_app.logger.debug('data: {0}'.format(data))
    current_app.logger.debug('doi_select: {0}'.format(doi_select))
    current_app.logger.debug('temporal_saving: {0}'.format(temporal_saving))

    flag_del_pidstore = False
    identifier_val = ''
    doi_register_val = ''
    doi_register_typ = ''

    if doi_select == IDENTIFIER_GRANT_LIST[1][0] and data.get(
            'identifier_grant_jalc_doi_link'):
        jalcdoi_link = data.get('identifier_grant_jalc_doi_link')
        jalcdoi_tail = (jalcdoi_link.split('//')[1]).split('/')
        identifier_val = jalcdoi_link
        doi_register_val = '/'.join(jalcdoi_tail[1:])
        doi_register_typ = 'JaLC'
    elif doi_select == IDENTIFIER_GRANT_LIST[2][0] and data.get(
            'identifier_grant_jalc_cr_doi_link'):
        jalcdoi_cr_link = data.get('identifier_grant_jalc_cr_doi_link')
        jalcdoi_cr_tail = (jalcdoi_cr_link.split('//')[1]).split('/')
        identifier_val = jalcdoi_cr_link
        doi_register_val = '/'.join(jalcdoi_cr_tail[1:])
        doi_register_typ = 'Crossref'
    elif doi_select == IDENTIFIER_GRANT_LIST[3][0] and data.get(
            'identifier_grant_jalc_dc_doi_link'):
        jalcdoi_dc_link = data.get('identifier_grant_jalc_dc_doi_link')
        jalcdoi_dc_tail = (jalcdoi_dc_link.split('//')[1]).split('/')
        identifier_val = jalcdoi_dc_link
        doi_register_val = '/'.join(jalcdoi_dc_tail[1:])
        doi_register_typ = 'DataCite'
    elif doi_select == IDENTIFIER_GRANT_LIST[4][0] \
            and data.get('identifier_grant_ndl_jalc_doi_link'):
        ndljalcdoi_dc_link = data.get('identifier_grant_ndl_jalc_doi_link')
        ndljalcdoi_dc_tail = (ndljalcdoi_dc_link.split('//')[1]).split('/')
        identifier_val = ndljalcdoi_dc_link
        doi_register_val = '/'.join(ndljalcdoi_dc_tail[1:])
        doi_register_typ = 'NDL JaLC'
    else:
        current_app.logger.error(_('Identifier datas are empty!'))
        return False

    try:
        if not flag_del_pidstore and identifier_val and doi_register_val:
            if temporal_saving:
                identifier = IdentifierHandle(item_id)
                identifier.update_idt_registration_metadata(
                    doi_register_val,
                    doi_register_typ)
                current_app.logger.info(_('DOI temporary registered!'))
            else:
                identifier = IdentifierHandle(record_without_version)
                reg = identifier.register_pidstore('doi', identifier_val)
                UserActivityLogger.info(
                    operation="ITEM_ASSIGN_DOI",
                    target_key=str(item_id),
                )
                identifier.update_idt_registration_metadata(
                    doi_register_val,
                    doi_register_typ)
                if reg:
                    identifier = IdentifierHandle(item_id)
                    identifier.update_idt_registration_metadata(
                        doi_register_val,
                        doi_register_typ)
                current_app.logger.info(_('DOI successfully registered!'))
        return True
    except Exception as ex:
        current_app.logger.exception(str(ex))
        if not temporal_saving:
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            UserActivityLogger.error(
                operation="ITEM_ASSIGN_DOI",
                target_key=str(item_id),
                remarks=tb_info[0]
            )
        return False


def register_hdl(activity_id):
    """
    Register HDL into Persistent Identifiers.

    :param activity_id: Workflow Activity Identifier
    :return cnri_pidstore: HDL pidstore object or None
    """
    activity = WorkActivity().get_activity_detail(activity_id)
    # https://nii.backlog.jp/view/WEKO3_APP-84
    current_pid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                 object_type='rec',
                                                 object_uuid=activity.item_id)
    pid_without_ver = get_record_without_version(current_pid)
    item_uuid  = pid_without_ver.object_uuid
    # item_uuid = activity.item_id
    current_app.logger.debug(
        "register_hdl: {0} {1}".format(activity_id, item_uuid))
    record = WekoRecord.get_record(item_uuid)

    if record.pid_cnri:
        current_app.logger.info('This record was registered HDL!')
        return
    else:
        deposit_id = record.pid_parent.pid_value.split('parent:')[1]

    record_url = request.url.split('/workflow/')[0] \
        + '/records/' + str(deposit_id)

    weko_handle = Handle()
    handle = weko_handle.register_handle(location=record_url)
    if handle:
        handle = WEKO_SERVER_CNRI_HOST_LINK + str(handle)
        identifier = IdentifierHandle(item_uuid)
        identifier.register_pidstore('hdl', handle)
    else:
        current_app.logger.info('Cannot connect Handle server!')


def register_hdl_by_item_id(deposit_id, item_uuid, url_root):
    """
    Register HDL into Persistent Identifiers.

    :param deposit_id: id
    :param item_uuid: Item uuid
    :param url_root: url_root
    :return handle: HDL handle
    """
    current_app.logger.debug(
        "start register_hdl_by_item_id(deposit_id, item_uuid, url_root):")
    record_url = url_root \
        + 'records/' + str(deposit_id)

    weko_handle = Handle()
    handle = weko_handle.register_handle(location=record_url)

    if handle:
        handle = WEKO_SERVER_CNRI_HOST_LINK + str(handle)
        identifier = IdentifierHandle(item_uuid)
        identifier.register_pidstore('hdl', handle)
    else:
        current_app.logger.info('Cannot connect Handle server!')

    current_app.logger.debug(
        "end register_hdl_by_item_id(deposit_id, item_uuid, url_root):")
    return handle


def register_hdl_by_handle(hdl, item_uuid, item_uri):
    """
    Register HDL into Persistent Identifiers.

    :param hdl: HDL handle
    :param item_uuid: Item uuid
    """
    current_app.logger.debug(
        "start register_hdl_by_handle(handle, item_uuid):")
    current_app.logger.debug(
        "handle:{0} item_uuid:{1}".format(hdl, item_uuid))

    weko_handle = Handle()
    handle = weko_handle.register_handle(
        location=item_uri, hdl=hdl, overwrite=True)

    if handle:
        handle = WEKO_SERVER_CNRI_HOST_LINK + str(handle)
        identifier = IdentifierHandle(item_uuid)
        identifier.register_pidstore('hdl', handle)
    current_app.logger.debug("end register_hdl_by_handle(handle, item_uuid):")


def item_metadata_validation(item_id, identifier_type, record=None,
                             is_import=False, without_ver_id=None, file_path=None):
    """
    Validate item metadata.

    :param: item_id, identifier_type, record
    :return: error_list
    """

    ddi_item_type_name = 'DDI'
    journalarticle_type = ['conference paper',
                           'data paper', 'departmental bulletin paper',
                           'editorial', 'journal','journal article',
                           'review article', 'article','newspaper', 'software paper', 'periodical']
    thesis_types = ['thesis', 'bachelor thesis', 'master thesis',
                    'doctoral thesis']
    report_types = ['technical report', 'research report', 'report',
                    'book', 'book part']
    elearning_type = ['learning object', 'learning material']
    dataset_type = ['software', 'dataset', 'aggregated data',
                    'clinical trial data', 'compiled data',
                    'encoded data', 'experimental data', 'genomic data',
                    'geospatial data', 'laboratory notebook', 'measurement and test data',
                    'observational data', 'recorded data', 'simulation data',
                    'survey data', 'source code']
    datageneral_types = ['internal report', 'policy report', 'report part',
                         'working paper', 'interactive resource','lecture',
                         'musical notation', 'peer review','research proposal','research protocol',
                         'technical documentation', 'workflow',
                         'other', 'other periodical','sound', 'patent',
                         'cartographic material', 'map', 'commentary','lecture', 'image',
                         'utility model','transcription','trademark','still image', 'moving image', 'video',
                         'conference output', 'conference object','conference proceedings',
                         'conference poster','layout design','industrial design','design','design patent','PCT application','plant patent','plant variety protection','software patent',
                         'conference presentation','manuscript', 'data management plan', 'interview','other']

    def _check_resource_type(identifier_type, resource_type, old_resource_type):
        """
        Validate if the new resource type and the old resource type
        belong to the same mapping type
        """
        def _get_mapping_type(_resource_type):
            """
            get mapping_type from resource_type and identifier_type
            """
            mapping_type = ""
            if identifier_type == IDENTIFIER_GRANT_SELECT_DICT["JaLC"]:
                if _resource_type in journalarticle_type:
                    # 別表2-1 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
                    mapping_type = "journal_article"
                elif _resource_type in thesis_types:
                    # 別表2-2 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【学位論文】
                    mapping_type = "theis_type"
                elif _resource_type in report_types:
                    # 別表2-3 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【書籍】
                    mapping_type = "report_types"
                elif _resource_type in elearning_type:
                    # 別表2-4 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【e-learning】
                    mapping_type = "elearning_type"
                elif _resource_type in dataset_type:
                    # 別表2-5 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【研究データ】
                    mapping_type = "dataset_type"
                elif _resource_type in datageneral_types:
                    # 別表2-6 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【汎用データ】
                    mapping_type = "datageneral_types"
            elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT["Crossref"]:
                if _resource_type in journalarticle_type:
                    # 別表3-1 Crossref DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
                    mapping_type = "journal_article"
                elif _resource_type in thesis_types or _resource_type in report_types:
                    # 別表3-2 Crossref DOI登録メタデータのJPCOAR/JaLCマッピング【書籍】
                    mapping_type = "report_types"
            elif identifier_type in IDENTIFIER_GRANT_SELECT_DICT["DataCite"]:
                if _resource_type in dataset_type:
                    # 別表4-1 DataCite DOI登録メタデータのJPCOAR/JaLCマッピング【研究データ】
                    mapping_type = "dataset_type"
            return mapping_type
        old_type = _get_mapping_type(old_resource_type)
        new_type = _get_mapping_type(resource_type)
        if old_type == new_type:
            return True
        else:
            return False

    current_app.logger.debug("item_id: {}".format(item_id))
    current_app.logger.debug("identifier_type: {}".format(identifier_type))
    current_app.logger.debug("record: {}".format(record))
    current_app.logger.debug("is_import: {}".format(is_import))
    current_app.logger.debug("without_ver_id: {}".format(without_ver_id))
    current_app.logger.debug("file_path: {}".format(file_path))

    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
        return None

    metadata_item = MappingData(
        item_id) if item_id else MappingData(record=record)
    item_type = metadata_item.get_data_item_type()
    type_key, resource_type = metadata_item.get_first_data_by_mapping(
        'type.@value')

    error_list = {'required': [], 'required_key': [], 'pattern': [],
                  'either': [],  'either_key': [], 'mapping': [], 'other': ''}
    # check resource type request
    if not resource_type and not type_key:
        error_list['mapping'].append('dc:type')
        return error_list

    type_check = check_required_data(resource_type, type_key)
    if not item_type or not resource_type and type_check:
        error_list['required'].append(type_key)
        return error_list

    resource_type = resource_type.pop()
    if without_ver_id:
        _type_key, old_resource_type = MappingData(without_ver_id) \
            .get_first_data_by_mapping('type.@value')
        if old_resource_type and not _check_resource_type(identifier_type, resource_type, old_resource_type.pop()):
        #if old_resource_type and resource_type != old_resource_type.pop():
            error_list['other'] = 'You cannot change the resource type of ' \
                + 'items that have been grant a DOI.'
            return error_list

    # For NDL prefix, resource type is only doctoral thesis
    if identifier_type==IDENTIFIER_GRANT_SELECT_DICT['NDL JaLC'] and resource_type != "doctoral thesis":
        error_list['other'] = _("When assigning a JaLC DOI through NDL, the resource type must be 'doctor thesis'.")
        return error_list

    properties = {}
    # 必須
    required_properties = []
    # いずれか必須
    either_properties = []

    # JaLC DOI identifier registration
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['JaLC']:
        # 別表2-1 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
        if resource_type in journalarticle_type:
            required_properties = [
                'title',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                'pageStart',
                # 'fileURI',
            ]
            # remove 20220207
            # either_properties = ['version']
            # いずれか必須が動いていない
            # either_properties = ['publisher','date']

        # 別表2-2 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【学位論文】
        elif resource_type in thesis_types:
            required_properties = [
                'title',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                # 'degreeGrantor',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                # 'fileURI',
            ]
            # いずれか必須が動いていない
            # either_properties = ['date','degreeGrantor']
        # 別表2-3 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【書籍】
        elif resource_type in report_types:
            required_properties = [
                'title',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                # 'fileURI',
            ]
            # いずれか必須が動いていない
            # either_properties = ['date','publisher']
        # 別表2-4 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【e-learning】
        elif resource_type in elearning_type:
            required_properties = [
                'title',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                # 'fileURI',
            ]
            # いずれか必須が動いていない
            # either_properties = ['date','publisher']
        # 別表2-5 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【研究データ】
        elif resource_type in dataset_type:
            required_properties = [
                'title',
                # 'givenName',
                # 'creatorName',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                # 'fileURI',
            ]
            # いずれか必須が動いていない
            # either_properties = ['givenName','date','publisher']
            # remove 20220207
            # either_properties = ['geoLocation']

        # 別表2-6 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【汎用データ】
        elif resource_type in datageneral_types:
            required_properties = [
                'title',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                # 'fileURI',
            ]
            # いずれか必須が動いていない
            # either_properties = ['date','publisher']

    # CrossRef DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['Crossref']:
        # 別表3-1 Crossref DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
        if resource_type in journalarticle_type:
            required_properties = [
                'title',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                'sourceIdentifier',
                'sourceTitle',
                # 'fileURI',
            ]
            # いずれか必須が動いていない
            # either_properties = ['date','publisher']
        elif resource_type in report_types \
                or resource_type in thesis_types:
            required_properties = [
                'title',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                # 'fileURI',
            ]
            # いずれか必須が動いていない
            # either_properties = ['date','publisher']
    # DataCite DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['DataCite']:
        if resource_type in dataset_type:
            required_properties = [
                'title',
                # 'givenName',
                # 'creatorName',
                # 'publisher',
                # 'publisher_jpcoar',
                # 'date',
                # 'dateGranted',
                'type',
                # 'identifier',
                # 'identifierRegistration',
                # 'fileURI',
            ]
            # いずれか必須が動いていない
            # either_properties = ['givenName','date','publisher']
            # remove 20220207
            # either_properties = ['geoLocation']
    # NDL JaLC DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['NDL JaLC']:
        required_properties = [
            'title',
            'type'
        ]

    # 本文URL条件
    # DDIはスキップ
    # 新規登録(item_idなし、かつfile_pathがある場合は本文URL:があるとみなす
    # それ以外はfileURIが必須
    if item_type.item_type_name.name != ddi_item_type_name:
        if item_id is None:
            if file_path is None or len(file_path) == 0:
                required_properties.append('fileURI')
        else:
            required_properties.append('fileURI')

    if required_properties:
        properties['required'] = required_properties
    if either_properties:
        properties['either'] = either_properties

    current_app.logger.debug(item_type)
    current_app.logger.debug(resource_type)
    current_app.logger.debug(identifier_type)
    current_app.logger.debug(properties)
    current_app.logger.debug(metadata_item)

    # if properties and \
    #         ((identifier_type != IDENTIFIER_GRANT_SELECT_DICT['DataCite']
    #           and identifier_type != IDENTIFIER_GRANT_SELECT_DICT['NDL JaLC']
    #           ) or is_import):
    if properties:
        return validation_item_property(metadata_item, properties, identifier_type=identifier_type)
    else:
        error_list['other'] = _('Cannot register selected DOI for current Item Type of this '
                 'item.')
        return error_list


def merge_doi_error_list(current, new):
    """Merge DOI validation error list."""
    if new['required']:
        current['required'].extend(new['required'])
    if 'required_key' in new and new['required_key']:
        if 'required_key' in current:
            current['required_key'].extend(new['required_key'])
        else:
            current['required_key'] = new['required_key']
    if new['either']:
        current['either'].extend(new['either'])
    if 'either_key' in new and new['either_key']:
        if 'either_key' in current:
            current['either_key'].extend(new['either_key'])
        else:
            current['either_key'] = new['either_key']
    if new['pattern']:
        current['pattern'].extend(new['pattern'])
    if new['mapping']:
        current['mapping'].extend(new['mapping'])
        current['mapping'] = list(set(current['mapping']))


def validation_item_property(mapping_data, properties, identifier_type=None):
    """
    Validate item property.

    :param mapping_data: Mapping Data contain record and item_map
    :param properties: Property's keywords
    :return: error_list or None
    """
    error_list = {'required': [], 'required_key': [],
                  'pattern': [], 'either': [], 'either_key': [], 'mapping': []}
    empty_list = deepcopy(error_list)

    if properties.get('required'):
        error_list_required = validattion_item_property_required(
            mapping_data, properties['required'],identifier_type=identifier_type)
        if error_list_required:
            merge_doi_error_list(error_list, error_list_required)

    if properties.get('either'):
        error_list_either = validattion_item_property_either_required(
            mapping_data, properties['either'], identifier_type=identifier_type)
        if error_list_either:
            merge_doi_error_list(error_list, error_list_either)

    if error_list == empty_list:
        return None
    else:
        return error_list


def handle_check_required_data(mapping_data, mapping_key):
    """Check required and append to error_list if error."""
    keys = []
    values = []
    requirements = []
    current_app.logger.debug("mapping_data: {}".format(mapping_data))
    current_app.logger.debug("mapping_key: {}".format(mapping_key))

    data = mapping_data.get_data_by_mapping(mapping_key)
    for key, value in data.items():
        keys.append(key)
        values.append(value)
        _requirements = check_required_data(value, key, True)
        if _requirements:
            requirements.extend(_requirements)
        else:
            requirements = []
            break

    return requirements, keys, values


def handle_check_required_pattern_and_either(mapping_data, mapping_keys,
                                             error_list=None, is_either=False, identifier_type=None):
    """Check required, pattern and either required."""
    if not (mapping_data and mapping_keys):
        return
    if not error_list:
        error_list = {'required': [], 'required_key': [], 'pattern': [],
                      'either': [], 'either_key': [], 'mapping': []}
    empty_list = deepcopy(error_list)
    keys = []
    num_map = 0
    requirements = []
    doi_validation_information = deepcopy(DOI_VALIDATION_INFO)

    if identifier_type:
        if identifier_type == '2':
            doi_validation_information = DOI_VALIDATION_INFO_CROSSREF
        elif identifier_type == '3':
            doi_validation_information = DOI_VALIDATION_INFO_DATACITE

    for mapping_key in mapping_keys:
        for elem, pattern in doi_validation_information[mapping_key]:
            check_required_info = handle_check_required_data(
                mapping_data, elem)
            if not check_required_info[1]:
                error_list['mapping'].append(mapping_key)
                continue

            keys.extend(check_required_info[1])
            requirements.extend(check_required_info[0])
            if num_map == 0:
                num_map = len(check_required_info[1])
            if pattern and check_required_info[2]:
                _required_value_check = False
                for idx, values in enumerate(check_required_info[2]):
                    if values and pattern in values:
                        _required_value_check = True
                if not _required_value_check:
                    error_list['pattern'].append(mapping_key)

    if requirements:
        if num_map == 1 and not is_either:
            error_list['required'].extend(requirements)
            error_list['required_key'].append(mapping_key)
        else:
            error_list['either_key'].append(mapping_key)
            filter_root_keys = list(
                set([key.split('.')[0] for key in keys[:num_map]]))
            either_list = []
            for key in filter_root_keys:
                either_list.append([
                    k for k in keys if k.split('.')[0] == key])
            if is_either and not error_list['either']:
                error_list['either'] = either_list
            else:
                error_list['either'].append(either_list)

    current_app.logger.debug("mapping_data: {}".format(mapping_data))
    current_app.logger.debug("mapping_keys: {}".format(mapping_keys))
    current_app.logger.debug("error_list: {}".format(error_list))
    current_app.logger.debug("is_either: {}".format(is_either))
    if empty_list != error_list:
        return error_list


def validattion_item_property_required(
        mapping_data, properties, identifier_type=None):
    """
    Validate item property is required.

    :param mapping_data: Mapping Data contain record and item_map
    :param properties: Property's keywords
    :return: error_list or None
    """
    error_list = {'required': [], 'required_key': [],
                  'pattern': [], 'either': [], 'either_key': [], 'mapping': []}
    empty_list = deepcopy(error_list)

    # check file jpcoar:URI
    if 'fileURI' in properties:
        mapping_keys = ['jpcoar:URI']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check タイトル dc:title
    if 'title' in properties:
        mapping_keys = ['dc:title']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check 識別子 jpcoar:givenName
    if 'givenName' in properties:
        mapping_keys = ['jpcoar:givenName']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check 収録物識別子 jpcoar:sourceIdentifier
    if 'sourceIdentifier' in properties:
        mapping_keys = ['jpcoar:sourceIdentifier']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check 収録物名 jpcoar:sourceTitle
    if 'sourceTitle' in properties:
        mapping_keys = ['jpcoar:sourceTitle']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check 収録物名 dc:publisher
    if 'publisher' in properties:
        mapping_keys = ['dc:publisher']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check jpcoar:publisher
    if 'publisher_jpcoar' in properties:
        mapping_keys = ['jpcoar:publisher_jpcoar']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check datacite:date
    if 'date' in properties:
        mapping_keys = ['datacite:date']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check dcndl:dateGranted
    if 'dateGranted' in properties:
        mapping_keys = ['dcndl:dateGranted']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check dc:type
    if 'type' in properties:
        mapping_keys = ['dc:type']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check jpcoar:identifier
    # if 'identifier' in properties:
    #     mapping_keys = ['jpcoar:identifier']
    #     handle_check_required_pattern_and_either(
    #         mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check jpcoar:identifierRegistration
    # if 'identifierRegistration' in properties:
    #     mapping_keys = ['jpcoar:identifierRegistration']
    #     handle_check_required_pattern_and_either(
    #         mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check jpcoar:pageStart
    if 'pageStart' in properties:
        mapping_keys = ['jpcoar:pageStart']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check jpcoar:degreeGrantor
    if 'degreeGrantor' in properties:
        mapping_keys = ['jpcoar:degreeGrantor']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    # check jpcoar:creatorName
    if 'creatorName' in properties:
        mapping_keys = ['jpcoar:creatorName']
        handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, error_list, identifier_type=identifier_type)

    if error_list == empty_list:
        return None
    else:
        error_list['required'] = list(
            set(filter(None, error_list['required'])))
        error_list['pattern'] = list(set(filter(None, error_list['pattern'])))
        return error_list


def validattion_item_property_either_required(
        mapping_data, properties, identifier_type):
    """
    Validate item property is either required.

    :param mapping_data: Mapping Data contain record and item_map
    :param properties: Property's keywords
    :return: either_list
    """
    error_list = {'required': [], 'required_key': [],
                  'pattern': [], 'either': [], 'either_key': [], 'mapping': []}

    # For Dataset
    geo_location = None
    if 'geoLocation' in properties:
        # check 位置情報（点） datacite:geoLocationPoint
        mapping_keys = ['datacite:geoLocationPoint']
        geo_location = handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, identifier_type, None, True)

        # check 位置情報（空間） datacite:geoLocationBox
        if geo_location:
            mapping_keys = ['datacite:geoLocationBox']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys, identifier_type, None, True)
            if not errors:
                geo_location = None
            else:
                merge_doi_error_list(geo_location, errors)

        # check 位置情報（自由記述） datacite:geoLocationPlace
        if geo_location:
            mapping_keys = ['datacite:geoLocationPlace']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys, identifier_type, None, True)
            if not errors:
                geo_location = None
            else:
                merge_doi_error_list(geo_location, errors)

        if geo_location:
            if geo_location['either']:
                geo_location['either'] = [geo_location['either']]
            merge_doi_error_list(error_list, geo_location)

    # For other resource type
    version = None
    if 'version' in properties:
        # check フォーマット jpcoar:mimeType
        mapping_keys = ['jpcoar:mimeType']
        version = handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, identifier_type, None, True)

        if version:
            # check バージョン datacite:version
            mapping_keys = ['datacite:version']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys, identifier_type, None, True)
            if not errors:
                version = None
            else:
                merge_doi_error_list(version, errors)

        if version:
            # check 出版タイプ oaire:version
            mapping_keys = ['oaire:version']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys, identifier_type, None, True)
            if not errors:
                version = None
            else:
                merge_doi_error_list(version, errors)

        if version:
            if version['either']:
                version['either'] = [version['either']]
            merge_doi_error_list(error_list, version)

    publisher = None
    if 'publisher' in properties:
        mapping_keys = ['dc:publisher']
        publisher = handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, None, True,identifier_type)
        if publisher:
            mapping_keys = ['jpcoar:publisher_jpcoar']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys,  None, True,identifier_type)
            if not errors:
                publisher = None
            else:
                merge_doi_error_list(publisher, errors)

        if publisher:
            if publisher['either']:
                publisher['either'] = [publisher['either']]
            merge_doi_error_list(error_list, publisher)

    date = None
    if 'date' in properties:
        mapping_keys = ['datacite:date']
        date = handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, None, True,identifier_type)
        if date:
            mapping_keys = ['dcndl:dateGranted']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys,  None, True,identifier_type)
            if not errors:
                date = None
            else:
                merge_doi_error_list(date, errors)

        if date:
            if date['either']:
                date['either'] = [date['either']]
            merge_doi_error_list(error_list, date)


    # For other resource type
    degreeGrantor = None
    if 'degreeGrantor' in properties:
        mapping_keys = ['jpcoar:degreeGrantor']
        degreeGrantor = handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, identifier_type, None, True)

        if degreeGrantor:
            mapping_keys = ['dc:publisher']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys, identifier_type, None, True)
            if not errors:
                degreeGrantor = None
            else:
                merge_doi_error_list(degreeGrantor, errors)

        if degreeGrantor:
            # check 出版タイプ oaire:version
            mapping_keys = ['jpcoar:publisher_jpcoar']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys, identifier_type, None, True)
            if not errors:
                degreeGrantor = None
            else:
                merge_doi_error_list(degreeGrantor, errors)

        if degreeGrantor:
            if degreeGrantor['either']:
                degreeGrantor['either'] = [degreeGrantor['either']]
            merge_doi_error_list(error_list, degreeGrantor)

    givenName = None
    if 'givenName' in properties:
        mapping_keys = ['jpcoar:givenName']
        givenName = handle_check_required_pattern_and_either(
            mapping_data, mapping_keys, None, True,identifier_type)
        if givenName:
            mapping_keys = ['jpcoar:creatorName']
            errors = handle_check_required_pattern_and_either(
                mapping_data, mapping_keys,  None, True,identifier_type)
            if not errors:
                givenName = None
            else:
                merge_doi_error_list(givenName, errors)

        if givenName:
            if givenName['either']:
                givenName['either'] = [givenName['either']]
            merge_doi_error_list(error_list, givenName)

    return error_list


def check_required_data(data, key, repeatable=False):
    """
    Check whether data exist or not.

    :param data: request data
    :param key:  key of attribute contain data
    :param repeatable: whether allow input more than one data
    :return: error_list or None
    """
    error_list = []

    if not data or not repeatable and len(data) > 1:
        error_list.append(key)
    else:
        for item in data:
            if not item:
                error_list.append(key)

    if not error_list:
        return None
    else:
        return list(set(error_list))


def get_activity_id_of_record_without_version(pid_object=None):
    """
    Get activity ID of record without version.

    Arguments:
        pid_object  -- object pidstore

    Returns:
        deposit     -- string or None

    """
    if pid_object:
        # get workflow of first record attached version ID: x.1
        pid_value_first_ver = "{}.1".format(pid_object.pid_value)
        pid_object_first_ver = PersistentIdentifier.get(
            'recid',
            pid_value_first_ver
        )
        activity = WorkActivity()
        activity_first_ver = activity.get_workflow_activity_by_item_id(
            pid_object_first_ver.object_uuid)
        if activity_first_ver:
            return activity_first_ver.activity_id
        else:
            return None


def get_non_extract_files_by_recid(recid):
    """ Get extraction info from temp_data in activity.

    Args:
        recid (str): recid in deposit. "xxxxx" or "xxxxx.0"

    Returns:
        list[str]: list of non_extract filenames
    """
    pid = PersistentIdentifier.get('recid', recid)
    work_activity = WorkActivity()
    activity = work_activity.get_workflow_activity_by_item_id(pid.object_uuid)

    if activity is not None and isinstance(activity.temp_data, str):
        item_json = json.loads(activity.temp_data)
        # Load files from temp_data.
        files = item_json.get('files', [])
        return [
            file["filename"] for file in files if file.get("non_extract", False)
        ]

    return None


def check_suffix_identifier(idt_regis_value, idt_list, idt_type_list):
    """Check prefix/suffix in Identifier Registration contain in Identifier.

    Arguments:
        idt_regis_value -- {string array} Identifier Registration value
        idt_list        -- {string array} Identifier Data
        idt_type_list   -- {string array} Identifier Type List

    Returns:
        True/False   -- is prefix/suffix data exist

    """
    indices = [i for i, x in enumerate(idt_type_list or []) if x == "DOI"]
    list_value_error = []
    if idt_list and idt_regis_value:
        for pre in idt_regis_value:
            for index in indices:
                data = idt_list[index] or ''
                if (pre in data and (
                        len(data) - data.find(pre) - len(pre)) == 0):
                    return False
                else:
                    list_value_error.append(index)
        return list_value_error
    else:
        return list_value_error


class MappingData(object):
    """Mapping Data class."""

    record = None
    item_map = None

    def __init__(self, item_id=None, record=None):
        """Initilize pagination."""
        self.record = WekoRecord.get_record(item_id) if item_id else record
        item_type = self.get_data_item_type()
        item_type_mapping = Mapping.get_record(item_type.id)
        self.item_map = get_full_mapping(item_type_mapping, "jpcoar_mapping")

    def get_data_item_type(self):
        """Return item type data."""
        return ItemTypes.get_by_id(id_=self.record.get('item_type_id'))

    def get_data_by_mapping(self, mapping_key, ignore_empty=False,
                            hide_sub_keys=None, hide_parent_key=None):
        """
        Get data by mapping key.

        :param mapping_key: mapping key.
        :param ignore_empty: Is ignore empty value.
        :param ignore_prop_keys: Is ignore by keys.
        :return: properties key and data.
        """
        result = OrderedDict()

        property_keys = self.item_map.get(mapping_key)
        if not property_keys:
            current_app.logger.error(
                mapping_key + ' jpcoar:mapping is not correct')
        else:
            for key in property_keys:
                data = []
                split_key = key.split('.')
                if hide_parent_key and split_key[0] in hide_parent_key:
                    continue
                if hide_sub_keys and key.replace('[]', '') in hide_sub_keys:
                    continue
                attribute = self.record.get(split_key[0])
                if attribute and len(split_key) > 1:
                    data_result = get_item_value_in_deep(
                        attribute.get('attribute_value_mlt'),
                        split_key[1:]
                    )
                    if data_result:
                        for value in data_result:
                            data.append(value)
                if ignore_empty and not data:
                    continue
                result[key] = data

        return result

    def get_first_data_by_mapping(self, mapping_key):
        """
        Get the first data by mapping key.

        :param mapping_key: mapping key.
        :return: properties key and data.
        """
        data_info = self.get_data_by_mapping(mapping_key, True)
        return next(iter(data_info.items())) if data_info else (None, None)

    def get_first_property_by_mapping(self, mapping_key, ignore_empty=False):
        """
        Get the first key of property by mapping key.

        :param mapping_key: mapping key.
        :param ignore_empty: Is ignore empty value.
        :return: properties key and data.
        """
        data_info = self.get_data_by_mapping(mapping_key, ignore_empty)
        return next(iter(data_info.items()))[0] if data_info else None


def get_sub_item_value(atr_vm, key):
    """Get all data of input key.

    @param atr_vm:
    @param key:
    @return:
    """
    if isinstance(atr_vm, dict):
        for ke, va in atr_vm.items():
            if key == ke:
                yield va
            else:
                for z in get_sub_item_value(va, key):
                    yield z
    elif isinstance(atr_vm, list):
        for n in atr_vm:
            for k in get_sub_item_value(n, key):
                yield k


def get_item_value_in_deep(data, keys):
    """Get all data of input key.

    @param data: Metadata.
    @param keys: Split of mapping key.
    @return: A generator values.
    """
    if not (data and keys):
        return None

    if isinstance(data, dict):
        sub_data = data.get(keys[0], None)
        if not sub_data or len(keys) == 1:
            yield sub_data
        else:
            for val in get_item_value_in_deep(sub_data, keys[1:]):
                yield val
    elif isinstance(data, list):
        for sub_data in data:
            for val in get_item_value_in_deep(sub_data, keys):
                yield val


class IdentifierHandle(object):
    """Get Community Info."""

    item_uuid = ''
    item_type_id = None
    item_record = None
    item_metadata = None
    metadata_mapping = None

    def __init__(self, item_id):
        """Initialize IdentifierHandle."""
        self.item_uuid = item_id
        self.metadata_mapping = MappingData(item_id)
        self.item_type_id = self.metadata_mapping.get_data_item_type().id
        self.item_metadata = ItemsMetadata.get_record(item_id)
        self.item_record = self.metadata_mapping.record

    def get_pidstore(self, pid_type='doi', object_uuid=None):
        """Get Persistent Identifier Object by pid_value or item_uuid.

        Arguments:
            pid_type     -- {string} 'doi' (default) or 'hdl'
            object_uuid  -- {uuid} assigned object's uuid

        Returns:
            pid_object   -- PID object or None

        """
        if not object_uuid:
            object_uuid = self.item_uuid
        return get_parent_pid_with_type(pid_type, object_uuid)

    def check_pidstore_exist(self, pid_type, chk_value=None):
        """Get check whether PIDStore object exist.

        Arguments:
            pid_type     -- {string} 'doi' (default) or 'hdl'
            chk_value    -- {string} object_uuid or pid_value

        Returns:
            return       -- PID object if exist

        """
        try:
            with db.session.no_autoflush:
                if not chk_value:
                    return PersistentIdentifier.query.filter_by(
                        pid_type=pid_type,
                        object_uuid=self.item_uuid).all()
                return PersistentIdentifier.query.filter_by(
                    pid_type=pid_type,
                    pid_value=chk_value).one_or_none()
        except PIDDoesNotExistError as pid_not_exist:
            current_app.logger.error(pid_not_exist)
            return None

    def register_pidstore(self, pid_type, reg_value):
        """Register Persistent Identifier Object.

        Arguments:
            pid_type     -- {string} 'doi' (default) or 'hdl'
            reg_value    -- {string} pid_value

        Returns:
            return       -- PID object if exist

        """
        try:
            prev_pidstore = self.check_pidstore_exist(pid_type, reg_value)
            if not prev_pidstore:
                return PersistentIdentifier.create(
                    pid_type,
                    str(reg_value),
                    object_type='rec',
                    object_uuid=self.item_uuid,
                    status=PIDStatus.REGISTERED
                )
        except Exception as ex:
            current_app.logger.error(ex)
        return False

    def delete_pidstore_doi(self, pid_value=None):
        """Change Persistent Identifier Object status to DELETE.

        Arguments:
            pid_value -- {string} pid_value

        Returns:
            return    -- is pid object's status changed?

        """
        try:
            pids = []
            record = WekoRecord.get_record(self.item_uuid)
            with db.session.no_autoflush:
                pids = PersistentIdentifier.query.filter_by(
                    pid_type='doi',
                    status=PIDStatus.REGISTERED,
                    object_uuid=record.pid_parent.object_uuid).all()

            if pids:
                for _item in pids:
                    _item.delete()
                self.remove_idt_registration_metadata()
                return True
        except PIDDoesNotExistError as pidNotEx:
            current_app.logger.error(pidNotEx)
            return False
        except Exception as ex:
            current_app.logger.error(ex)
        return False

    def remove_idt_registration_metadata(self):
        """Remove Identifier Registration in Record Metadata.

        Returns:
            None

        """
        key_value = self.metadata_mapping.get_first_property_by_mapping(
            "identifierRegistration.@value")
        key_id = key_value.split('.')[0] if key_value else ''
        if self.item_metadata.get(key_id, []):
            del self.item_metadata[key_id]

            deleted_items = self.item_metadata.get('deleted_items', [])
            if deleted_items is not None:
                deleted_items.append(key_id)
            else:
                deleted_items = [key_id]
            self.item_metadata['deleted_items'] = deleted_items
        try:
            with db.session.begin_nested():
                rec = RecordMetadata.query.filter_by(id=self.item_uuid).first()
                deposit = WekoDeposit(rec.json, rec)
                index = {'index': deposit.get('path', []),
                         'actions': deposit.get('publish_status')}
                deposit.update(index, self.item_metadata)
                deposit.commit()
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()

    def update_idt_registration_metadata(self, input_value, input_type):
        """Update Identifier Registration in Record Metadata.

        Arguments:
            input_value -- {string} Identifier input
            input_type  -- {string} Identifier type

        Returns:
            None

        """
        key_value = self.metadata_mapping.get_first_property_by_mapping(
            "identifierRegistration.@value")
        key_type = self.metadata_mapping.get_first_property_by_mapping(
            "identifierRegistration.@attributes.identifierType")
        self.commit(key_id=key_value.split('.')[0],
                    key_val=key_value.split('.')[1],
                    key_typ=key_type.split('.')[1],
                    atr_nam='Identifier Registration',
                    atr_val=input_value,
                    atr_typ=input_type)

    def get_idt_registration_data(self):
        """Get Identifier Registration data.

        Returns:
            doi_value -- {string} Identifier
            doi_type  -- {string} Identifier type

        """
        _, doi_value = self.metadata_mapping.get_first_data_by_mapping(
            "identifierRegistration.@value")
        _, doi_type = self.metadata_mapping.get_first_data_by_mapping(
            "identifierRegistration.@attributes.identifierType")

        return doi_value, doi_type

    def commit(self, key_id, key_val, key_typ, atr_nam, atr_val, atr_typ):
        """Commit update.

        Arguments:
            key_id  -- {string} Identifier subitem's ID
            key_val -- {string} Identifier Value subitem's ID
            key_typ -- {string} Identifier Type subitem's ID
            atr_nam -- {string} attribute_name data
            atr_val -- {string} attribute_value_mlt value data
            atr_typ -- {string} attribute_value_mlt type data

        Returns:
            None

        """
        metadata_data = self.item_metadata.get(key_id, [])
        if atr_nam == 'Identifier Registration':
            metadata_data = {
                key_val: atr_val,
                key_typ: atr_typ
            }
        self.item_metadata[key_id] = metadata_data
        try:
            with db.session.begin_nested():
                rec = RecordMetadata.query.filter_by(id=self.item_uuid).first()
                deposit = WekoDeposit(rec.json, rec)
                index = {'index': deposit.get('path', []),
                         'actions': deposit.get('publish_status')}
                deposit.update(index, self.item_metadata)
                deposit.commit()
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()


def delete_bucket(bucket_id):
    """
    Delete a bucket and remove it size in location.

    Arguments:
        bucket_id       -- id of bucket have to be deleted.
    Returns:
        bucket_id       -- ...

    """
    bucket = Bucket.get(bucket_id)
    bucket.locked = False
    bucket.remove()


def merge_buckets_by_records(main_record_id,
                             sub_record_id,
                             sub_bucket_delete=False):
    """
    Change bucket_id of all sub bucket base on main bucket.

    Arguments:
        main_record_id  -- record uuid link with main bucket.
        sub_record_id   -- record uuid link with sub buckets.
        sub_bucket_delete -- Either delete subbucket after unlink?
    Returns:
        bucket_id       -- main bucket id.

    """
    try:
        with db.session.begin_nested():
            main_rec_bucket = RecordsBuckets.query.filter_by(
                record_id=main_record_id).one_or_none()
            sub_rec_buckets = RecordsBuckets.query.filter_by(
                record_id=sub_record_id).all()

            for sub_rec_bucket in sub_rec_buckets:
                if sub_rec_bucket.record_id == sub_record_id:
                    _sub_rec_bucket_id = sub_rec_bucket.bucket_id
                    sub_rec_bucket.bucket_id = main_rec_bucket.bucket_id
                    if sub_bucket_delete:
                        delete_bucket(_sub_rec_bucket_id)
                    db.session.add(sub_rec_bucket)
        return main_rec_bucket.bucket_id
    except Exception as ex:
        db.session.rollback()
        current_app.logger.exception(str(ex))
        return None


def delete_unregister_buckets(record_uuid):
    """
    Delete unregister bucket by pid.

    Find all bucket have same object version but link with unregister records.
    Arguments:
        record_uuid     -- record uuid link to checking bucket.
    Returns:
        None.

    """
    try:
        draft_record_bucket = RecordsBuckets.query.filter_by(
            record_id=record_uuid).one_or_none()
        with db.session.begin_nested():
            object_ver = ObjectVersion.query.filter_by(
                bucket_id=draft_record_bucket.bucket_id).first()
            if object_ver:
                draft_object_vers = ObjectVersion.query.filter_by(
                    file_id=object_ver.file_id).all()
                for draft_object in draft_object_vers:
                    if draft_object.bucket_id != draft_record_bucket.bucket_id:
                        delete_record_bucket = RecordsBuckets.query.filter_by(
                            bucket_id=draft_object.bucket_id).all()
                        if len(delete_record_bucket) == 1:
                            delete_pid_object = PersistentIdentifier.query. \
                                filter_by(pid_type='recid',
                                          object_type='rec',
                                          object_uuid=delete_record_bucket[
                                              0].record_id).one_or_none()
                            if not delete_pid_object:
                                bucket = Bucket.get(draft_object.bucket_id)
                                RecordsBuckets.query.filter_by(
                                    bucket_id=draft_object.bucket_id).delete()
                                bucket.locked = False
                                bucket.remove()
    except Exception as ex:
        db.session.rollback()
        current_app.logger.exception(str(ex))


def set_bucket_default_size(record_uuid):
    """
    Set Weko default size for draft bucket.

    Arguments:
        record_uuid     -- record uuid link to bucket.
    Returns:
        None.

    """
    draft_record_bucket = RecordsBuckets.query.filter_by(
        record_id=record_uuid).one_or_none()
    try:
        with db.session.begin_nested():
            draft_bucket = Bucket.get(draft_record_bucket.bucket_id)
            draft_bucket.quota_size = current_app.config[
                'WEKO_BUCKET_QUOTA_SIZE'],
            draft_bucket.max_file_size = current_app.config[
                'WEKO_MAX_FILE_SIZE'],
            db.session.add(draft_bucket)
    except Exception as ex:
        db.session.rollback()
        current_app.logger.exception(str(ex))


def is_show_autofill_metadata(item_type_name):
    """Check show auto fill metadata.

    @param item_type_name:
    @return:
    """
    result = True
    hidden_autofill_metadata_list = current_app.config.get(
        'WEKO_ITEMS_UI_HIDE_AUTO_FILL_METADATA')
    if item_type_name is not None and isinstance(hidden_autofill_metadata_list,
                                                 list):
        for item_type in hidden_autofill_metadata_list:
            if item_type_name == item_type:
                result = False
    return result


def is_hidden_pubdate(item_type_name):
    """Check hidden pubdate.

    @param item_type_name:
    @return:
    """
    hidden_pubdate_list = current_app.config.get(
        'WEKO_ITEMS_UI_HIDE_PUBLICATION_DATE')
    is_hidden = False
    if (item_type_name and isinstance(hidden_pubdate_list, list)
            and item_type_name in hidden_pubdate_list):
        is_hidden = True
    return is_hidden


def get_parent_pid_with_type(pid_type, object_uuid):
    """Get Persistent Identifier Object by pid_value or item_uuid.

    Arguments:
        pid_type     -- {string} 'doi' (default) or 'hdl'
        object_uuid  -- {uuid} assigned object's uuid

    Returns:
        pid_object   -- PID object or None

    """
    try:
        record = WekoRecord.get_record(object_uuid)
        with db.session.no_autoflush:
            pid_object = PersistentIdentifier.query.filter_by(
                pid_type=pid_type,
                object_uuid=record.pid_parent.object_uuid
            ).order_by(PersistentIdentifier.created.desc()).first()
            return pid_object
    except PIDDoesNotExistError as pid_not_exist:
        current_app.logger.error(pid_not_exist)
        return None


def filter_all_condition(all_args):
    """make a json data from request parameters that filtered by config['WEKO_WORKFLOW_FILTER_PARAMS'].

    Args:
        all_args (werkzeug.datastructures.ImmutableMultiDict): request paramaters

    Returns:
        dict: a json data of filtered request parameters.
    """
    conditions = {}
    list_key_condition = current_app.config.get('WEKO_WORKFLOW_FILTER_PARAMS',
                                                [])
    for args in all_args:
        for key in list_key_condition:
            if key in args:
                filter_condition(conditions, key, all_args.get(args))
    return conditions


def filter_condition(json, name, condition):
    """Add conditions to json object.

    Args:
        json (dict): _description_
        name (string): _description_
        condition (string): _description_
    """
    if json.get(name):
        json[name].append(condition)
    else:
        json[name] = [condition]


def get_actionid(endpoint):
    """
    Get action_id by action_endpoint.

    parameter:
    return: action_id
    """
    with db.session.no_autoflush:
        action = _Action.query.filter_by(
            action_endpoint=endpoint).one_or_none()
        if action:
            return action.id
        else:
            return None


def convert_record_to_item_metadata(record_metadata):
    """Convert record_metadata to item_metadata."""
    item_metadata = {
        'id': record_metadata['recid'],
        '$schema': record_metadata['item_type_id'],
        'pubdate': record_metadata['publish_date'],
        'title': record_metadata['item_title'],
        'weko_shared_id': record_metadata['weko_shared_id']
    }
    item_type = ItemTypes.get_by_id(record_metadata['item_type_id']).render

    for key, meta in item_type.get('meta_list', {}).items():
        if key in record_metadata:
            if meta.get('option', {}).get('multiple'):
                if 'attribute_value_mlt' in record_metadata[key]:
                    item_metadata[key] = \
                        record_metadata[key]['attribute_value_mlt']
            else:
                if 'attribute_value_mlt' in record_metadata[key]:
                    item_metadata[key] = \
                        record_metadata[key]['attribute_value_mlt'][0]

    return item_metadata


def prepare_edit_workflow(post_activity, recid, deposit):
    """
    Prepare Workflow Activity for draft record.

    Check and create draft record with id is "x.0".
    Create new workflow activity.
    Clone Identifier and Feedbackmail relation to last activity.

    parameter:
        post_activity: latest activity information.
        recid: current record id.
        deposit: current deposit data.
    return:
        rtn: new activity

    """
    # ! Check pid's version
    community = post_activity['community']
    activity = WorkActivity()

    draft_pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value="{}.0".format(recid.pid_value)
    ).one_or_none()

    if not draft_pid:
        draft_record = deposit.prepare_draft_item(recid)
        rtn = activity.init_activity(post_activity,
                                     community,
                                     draft_record.model.id)
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

            # update metadata
            _metadata = convert_record_to_item_metadata(deposit)
            _metadata['deleted_items'] = {}
            _cur_keys = [_key for _key in _metadata.keys()
                         if 'item_' in _key]
            _drf_keys = [_key for _key in _deposit.item_metadata.keys()
                         if 'item_' in _key]
            _metadata['deleted_items'] = list(set(_drf_keys) - set(_cur_keys))
            index = {'index': _deposit.get('path', []),
                     'actions': _deposit.get('publish_status')}
            args = [index, _metadata]
            _deposit.update(*args)
            _deposit.commit()
        except SQLAlchemyError as ex:
            raise ex

        rtn = activity.init_activity(post_activity,
                                     community,
                                     draft_pid.object_uuid)

    if rtn:
        # GOTO: TEMPORARY EDIT MODE FOR IDENTIFIER
        identifier_actionid = get_actionid('identifier_grant')
        identifier = {
            'action_identifier_jalc_doi': '',
            'action_identifier_jalc_cr_doi': '',
            'action_identifier_jalc_dc_doi': '',
            'action_identifier_ndl_jalc_doi': ''
        }
        pid_doi = IdentifierHandle(recid.object_uuid).get_pidstore()
        if pid_doi and pid_doi.status == PIDStatus.DELETED:
            identifier['action_identifier_select'] = current_app.config.get(
                "WEKO_WORKFLOW_IDENTIFIER_GRANT_WITHDRAWN", -3)
        elif pid_doi:
            identifier['action_identifier_select'] = current_app.config.get(
                "WEKO_WORKFLOW_IDENTIFIER_GRANT_CAN_WITHDRAW", -1)
        else:
            identifier['action_identifier_select'] = current_app.config.get(
                "WEKO_WORKFLOW_IDENTIFIER_GRANT_DOI", 0)

        activity.create_or_update_action_identifier(
            rtn.activity_id,
            identifier_actionid,
            identifier)

        mail_list = FeedbackMailList.get_mail_list_by_item_id(
            item_id=recid.object_uuid)
        if mail_list:
            action_id = current_app.config.get(
                "WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID", 3)
            activity.create_or_update_action_feedbackmail(
                activity_id=rtn.activity_id,
                action_id=action_id,
                feedback_maillist=mail_list
            )

        request_maillist = RequestMailList.get_mail_list_by_item_id(
            item_id=recid.object_uuid)
        if request_maillist:
            activity.create_or_update_activity_request_mail(
                activity_id=rtn.activity_id,
                request_maillist=request_maillist,
                is_display_request_button=True
            )

    return rtn


def prepare_delete_workflow(post_activity, recid, deposit):
    """
    Prepare Workflow Activity for draft record.

    Check and create draft record with id is "x.0".
    Create new workflow activity.
    Clone Identifier and Feedbackmail relation to last activity.

    Args:
        post_activity (dict): latest activity information.
        recid (PersistentIdentifier): current record id.
        deposit (WekoDeposit): current deposit data.

    Returns:
        Activity: new activity object.
    """
    # ! Check pid's version
    community = post_activity['community']
    activity = WorkActivity()

    pid_value = recid.pid_value.split('.')[0]
    del_value = (
        recid.pid_value
        if not '.' in recid.pid_value
        else "del_ver_{}".format(recid.pid_value)
    )

    draft_pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value="{}.0".format(pid_value)
    ).one_or_none()

    if del_value.startswith("del_ver_"):
        item_id = recid.object_uuid
    elif not draft_pid:
        draft_record = deposit.prepare_draft_item(recid)
        item_id = draft_record.model.id
    else:
        item_id = draft_pid.object_uuid

    rtn = activity.init_activity(
        post_activity, community, item_id
    )
    activity_detail = activity.get_activity_detail(rtn.activity_id)
    cur_action = activity_detail.action
    if rtn.action_id == 2:   # end_action
        from weko_records_ui.views import soft_delete
        soft_delete(del_value)
        activity.notify_about_activity(rtn.activity_id, "deleted")
        activity.upt_activity_action_status(
            activity_id=rtn.activity_id,
            action_id=rtn.action_id,
            action_status=ActionStatusPolicy.ACTION_DONE,
            action_order=rtn.action_order
            )
        act = {
            'activity_id': rtn.activity_id,
            'action_id': rtn.action_id,
            'action_version': cur_action.action_version,
            'action_status': ActionStatusPolicy.ACTION_DONE,
            'item_id': item_id,
            'action_order': rtn.action_order
        }
        activity.end_activity(act)

    if rtn.action_id == 4:   # approval
        activity.notify_about_activity(rtn.activity_id, "deletion_request")

    return rtn


def handle_finish_workflow(deposit, current_pid, recid):
    """
    Get user information by email.

    parameter:
        deposit:
        recid:
    return:
        acitivity_item_id
    """
    from weko_deposit.pidstore import get_record_without_version
    if not deposit:
        return None

    item_id = None
    old_record = None
    new_record = None
    record_pid = None
    old_item_reference_list = []
    new_item_reference_list = []
    is_newversion = False
    try:
        pid_without_ver = get_record_without_version(current_pid)
        if ".0" in current_pid.pid_value:
            deposit.commit()
        deposit.publish()
        updated_item = UpdateItem()
        non_extract = getattr(deposit, 'non_extract', None)
        # publish record without version ID when registering newly
        if recid:
            # new record attached version ID
            is_newversion = True
            new_deposit = deposit.newversion(current_pid)
            item_id = new_deposit.model.id
            ver_attaching_deposit = WekoDeposit(
                new_deposit,
                new_deposit.model)
            feedback_mail_list = FeedbackMailList.get_mail_list_by_item_id(
                pid_without_ver.object_uuid)
            if feedback_mail_list:
                FeedbackMailList.update(
                    item_id=item_id,
                    feedback_maillist=feedback_mail_list
                )
            request_mail_list = RequestMailList.get_mail_list_by_item_id(pid_without_ver.object_uuid)
            if request_mail_list:
                RequestMailList.update(
                    item_id=item_id,
                    request_maillist=request_mail_list
                )
            ver_attaching_deposit.publish()

            weko_record = WekoRecord.get_record_by_pid(new_deposit.pid.pid_value)
            if weko_record:
                weko_record.update_item_link(current_pid.pid_value)
            updated_item.publish(deposit)
            updated_item.publish(ver_attaching_deposit)
            record_pid = new_deposit.pid
        else:
            # update to record without version ID when editing
            if pid_without_ver:
                _record = WekoDeposit.get_record(
                    pid_without_ver.object_uuid)
                _deposit = WekoDeposit(_record, _record.model)
                _deposit['path'] = deposit.get('path', [])
                _deposit.non_extract = non_extract
                parent_record = _deposit. \
                    merge_data_to_record_without_version(current_pid)
                _deposit.publish()

                pv = PIDVersioning(child=pid_without_ver)
                last_ver = PIDVersioning(parent=pv.parent,child=pid_without_ver).get_children(
                    pid_status=PIDStatus.REGISTERED
                ).filter(PIDRelation.relation_type == 2).order_by(
                    PIDRelation.index.desc()).first()
                # Handle Edit workflow
                if ".0" in current_pid.pid_value:
                    maintain_record = WekoDeposit.get_record(
                        last_ver.object_uuid)
                    maintain_deposit = WekoDeposit(
                        maintain_record,
                        maintain_record.model)
                    maintain_deposit['path'] = deposit.get('path', [])
                    maintain_deposit.non_extract = non_extract
                    record_pid = maintain_record.pid
                    old_record = WekoRecord.get_record_by_pid(record_pid.pid_value)
                    old_item_reference_list = ItemReference.get_src_references(record_pid.pid_value).all()
                    old_item_reference_list = [deepcopy(item) for item in old_item_reference_list]
                    new_parent_record = maintain_deposit. \
                        merge_data_to_record_without_version(current_pid, True)
                    maintain_deposit.publish()
                    new_parent_record.commit()
                    updated_item.publish(new_parent_record)
                    # update item link info of main record
                    weko_record = WekoRecord.get_record_by_pid(
                        maintain_record.pid.pid_value)
                    if weko_record:
                        weko_record.update_item_link(current_pid.pid_value)
                else:  # Handle Upgrade workflow
                    draft_pid = PersistentIdentifier.get(
                        'recid',
                        '{}.0'.format(pid_without_ver.pid_value)
                    )
                    draft_deposit = WekoDeposit.get_record(
                        draft_pid.object_uuid)
                    draft_deposit['path'] = deposit.get('path', [])
                    record_pid = draft_pid
                    old_record = WekoRecord.get_record_by_pid(record_pid.pid_value)
                    old_item_reference_list = ItemReference.get_src_references(record_pid.pid_value).all()
                    old_item_reference_list = [deepcopy(item) for item in old_item_reference_list]
                    new_draft_record = draft_deposit. \
                        merge_data_to_record_without_version(current_pid)
                    draft_deposit.publish()
                    new_draft_record.commit()
                    updated_item.publish(new_draft_record)
                    # update item link info of draft record
                    weko_record = WekoRecord.get_record_by_pid(
                        draft_deposit.pid.pid_value)
                    if weko_record:
                        weko_record.update_item_link(current_pid.pid_value)

                # update item link info of parent record
                weko_record = WekoRecord.get_record_by_pid(
                    pid_without_ver.pid_value)
                if weko_record:
                    weko_record.update_item_link(current_pid.pid_value)
                parent_record.commit()
                updated_item.publish(parent_record)
                if ".0" in current_pid.pid_value and last_ver:
                    item_id = last_ver.object_uuid
                else:
                    item_id = current_pid.object_uuid
                db.session.commit()

        if record_pid:
            new_record = WekoRecord.get_record_by_pid(record_pid.pid_value)
            new_item_reference_list = \
                ItemReference.get_src_references(record_pid.pid_value).all()
            call_external_system(old_record=old_record,
                                 new_record=new_record,
                                 old_item_reference_list=old_item_reference_list,
                                 new_item_reference_list=new_item_reference_list)

        if pid_without_ver:
            from invenio_oaiserver.tasks import update_records_sets
            update_records_sets.delay([str(pid_without_ver.object_uuid)])
            opration = "ITEM_CREATE" if is_newversion else "ITEM_UPDATE"
            target_key = recid.recid if is_newversion else pid_without_ver.pid_value
            UserActivityLogger.info(
                operation=opration,
                target_key=target_key
            )
    except Exception as ex:
        db.session.rollback()
        current_app.logger.exception(str(ex))
        traceback.print_exc()
        exec_info = sys.exc_info()
        tb_info = traceback.format_tb(exec_info[2])
        opration = "ITEM_CREATE" if is_newversion else "ITEM_UPDATE"
        target_key = (
            recid.recid if is_newversion else pid_without_ver.pid_value
            if pid_without_ver else current_pid.pid_value
            )
        UserActivityLogger.error(
            operation=opration,
            target_key=target_key,
            remarks=tb_info[0]
        )
        return item_id
    return item_id


def delete_cache_data(key: str):
    """Delete cache data.

    :param key: Cache key.
    """
    current_value = current_cache.get(key) or str()
    if current_value:
        current_cache.delete(key)


def update_cache_data(key: str, value: str, timeout=None):
    """Create or Update cache data.

    :param key: Cache key.
    :param value: Cache value.
    :param timeout: Cache expired.
    """
    if timeout is not None:
        current_cache.set(key, value, timeout=timeout)
    else:
        current_cache.set(key, value)


def get_cache_data(key: str):
    """Get cache data.

    :param key: Cache key.

    :return: Cache value.
    """
    return current_cache.get(key) or str()


def check_an_item_is_locked(item_id=None):
    """Check if an item is locked.

    Args:
        item_id (str): The ID of the item to check.

    Returns:
        bool: If the item is locked, return True, else False.
    """
    def check(workers):
        for worker in workers:
            for task in workers[worker]:
                if task['name'] == 'weko_search_ui.tasks.import_item' \
                        and task['args'][0].get('id') == str(item_id):
                    return True
        return False

    _timeout = current_app.config.get("CELERY_GET_STATUS_TIMEOUT", 3.0)
    if not item_id or not inspect(timeout=_timeout).ping():
        return False

    return check(inspect(timeout=_timeout).active()) or \
        check(inspect(timeout=_timeout).reserved())


def get_account_info(user_id):
    """Get account's info: email, username.

    :param user_id: User id.

    :return: email, username.
    """
    data = get_user_profile_info(user_id)
    if data:
        return data.get('subitem_mail_address'), \
            data.get('subitem_displayname')
    else:
        return None, None


def check_existed_doi(doi_link):
    """Check a DOI is existed.

    :param doi_link: DOI link.

    :return:
    """
    respon = dict()
    respon['isExistDOI'] = False
    respon['isWithdrawnDoi'] = False
    respon['code'] = 1
    respon['msg'] = 'error'
    if doi_link:
        doi_pidstore = IdentifierHandle.check_pidstore_exist(
            None,
            'doi',
            doi_link)
        if doi_pidstore:
            respon['isExistDOI'] = True
            respon['msg'] = _('This DOI has been used already for another '
                              'item. Please input another DOI.')
            if doi_pidstore.status == PIDStatus.DELETED:
                respon['isWithdrawnDoi'] = True
                respon['msg'] = _(
                    'This DOI was withdrawn. Please input another DOI.')
        else:
            respon['msg'] = _('success')
        respon['code'] = 0
    return respon


def get_url_root():
    """Check a DOI is existed.

    :return: url root.
    """
    site_url = current_app.config['THEME_SITEURL']
    if not site_url.endswith('/'):
        site_url = site_url + '/'

    return request.host_url if request else site_url


def get_record_by_root_ver(pid_value):
    """Get record and files bu version.

    :return: record, files.
    """
    from weko_items_ui.utils import to_files_js
    files = []
    record = None
    if pid_value:
        pid_value = pid_value.split('.')[0]
        # Get Record by pid_value
        record = WekoRecord.get_record_by_pid(pid_value)
        # Get files by pid_value
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            pid_value=pid_value
        ).one_or_none()
        files = to_files_js(WekoDeposit.get_record(pid.object_uuid))
    else:
        return None, None
    return record, files


def get_disptype_and_ver_in_metainfo(metadata):
    """Get displaytype and licenseptype by vesion_id in metadata.

    :return: array.
    """
    ret = dict()
    for item in metadata:
        if isinstance(metadata.get(item), dict) \
            and metadata[item].get('attribute_type') \
            and metadata[item]['attribute_type'] == 'file' \
                and metadata[item].get('attribute_value_mlt'):
            for sub_item in metadata[item]['attribute_value_mlt']:
                if sub_item.get('version_id'):
                    ret[sub_item['version_id']] = {
                        'displaytype': sub_item.get('displaytype', None),
                        'licensetype': sub_item.get('licensetype', None),
                    }

    return ret


def set_files_display_type(record_metadata, files):
    """Get displayType in records and set into files.

    :return: Files.
    """
    data = get_disptype_and_ver_in_metainfo(record_metadata) or []
    if data:
        for file in files:
            if file.get('version_id') in data:
                file['displaytype'] = data[file.get(
                    'version_id')].get('displaytype', '')
                file['licensetype'] = data[file.get(
                    'version_id')].get('licensetype', '')

    return files


def get_thumbnails(files, allow_multi_thumbnail=True):
    """Get Thumbnail from file.

    :return: thumbnail.
    """
    thumbnails = []
    if files:
        thumbnails = [i for i in files
                      if 'is_thumbnail' in i.keys() and i['is_thumbnail']]
        if not allow_multi_thumbnail and thumbnails:
            thumbnails = [thumbnails.pop(0)]

    return thumbnails


def get_allow_multi_thumbnail(item_type_id, activity_id=None):
    """Get Multi Thumbnail from file."""
    if activity_id:
        from weko_items_ui.api import item_login
        _, _, _, _, _, _, _, _, _, _, _, allow_multi_thumbnail \
            = item_login(item_type_id=item_type_id)
        return allow_multi_thumbnail
    else:
        return None


def is_usage_application_item_type(activity_detail):
    """Check whether item type is in Usage Application item types.

    :param activity_detail:
    :return:
    """
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(
        activity_detail.workflow_id)
    item_type = get_item_type_name(workflow_detail.itemtype_id)
    item_type_list = current_app.config[
        'WEKO_ITEMS_UI_APPLICATION_ITEM_TYPES_LIST']
    if item_type in item_type_list:
        return True
    else:
        return False


def is_usage_application(activity_detail):
    """Check whether item type is in Usage Application item types.

    :param activity_detail:
    :return:
    """
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(
        activity_detail.workflow_id)

    item_type = get_item_type_name(workflow_detail.itemtype_id)
    item_type_list = current_app.config[
        'WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST']
    if item_type in item_type_list:
        return True
    else:
        return False


def send_mail_reminder(mail_info):
    """Send mail reminder.

    :mail_info: object
    """
    subject, body = get_mail_data(mail_info.get('template'))
    if not body:
        raise ValueError('Cannot get email template')
    body = replace_characters(mail_info, body)
    if not send_mail(subject, mail_info.get('mail_address'), body):
        raise ValueError('Cannot send mail')


def send_mail_approval_done(mail_info):
    """Send mail approval done.

    :mail_info: object
    """
    subject, body = email_pattern_approval_done(
        mail_info.get('item_type_name'))
    if body and subject:
        body = replace_characters(mail_info, body)
        send_mail(subject, mail_info.get('register_user_mail'), body)


def send_mail_registration_done(mail_info):
    """Send mail registration done.

    :mail_info: object
    """
    from weko_items_ui.utils import get_current_user_role
    role = get_current_user_role()
    item_type_name = mail_info.get('item_type_name')
    subject, body = email_pattern_registration_done(role, item_type_name)
    if body and subject:
        body = replace_characters(mail_info, body)
        send_mail(subject, mail_info.get('register_user_mail'), body)


def send_mail_request_approval(mail_info):
    """Send mail request approval.

    :mail_info: object
    """
    if mail_info:
        approver_mail = subject = body = None
        next_step = mail_info.get('next_step')
        if next_step == 'approval_advisor':
            approver_mail = mail_info.get('advisor_mail')
        elif next_step == 'approval_guarantor':
            approver_mail = mail_info.get('guarantor_mail')
        if approver_mail:
            subject, body = email_pattern_request_approval(
                mail_info.get('item_type_name'), next_step)
        if body and subject:
            subject = replace_characters(mail_info, subject)
            body = replace_characters(mail_info, body)
            send_mail(subject, approver_mail, body)


def send_mail(subject, recipient, body):
    """Send an email via the Flask-Mail extension.

    :subject: Email subject
    :recipient: Email recipient
    :body: content of email
    """
    if recipient:
        rf = {
            'subject': subject,
            'body': body,
            'recipient': recipient
        }
        return MailSettingView.send_statistic_mail(rf)


def email_pattern_registration_done(user_role, item_type_name):
    """Email pattern registration done.

    :user_role: object
    :item_type_name: object
    """
    current_config = current_app.config
    perfectures_item_type = current_config.get(
        "WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES")
    location_information_item_type = current_config.get(
        "WEKO_ITEMS_UI_APPLICATION_FOR_LOCATION_INFORMATION")
    output_registration_item_type = current_config.get(
        "WEKO_ITEMS_UI_OUTPUT_REPORT")
    usage_report_item_type = current_config.get(
        "WEKO_ITEMS_UI_USAGE_REPORT")
    item_type_list = current_config.get(
        "WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST")
    general_role = current_config.get("WEKO_USERPROFILES_GENERAL_ROLE")
    student_role = current_config.get("WEKO_USERPROFILES_STUDENT_ROLE")
    graduated_student_role = current_config.get(
        "WEKO_USERPROFILES_GRADUATED_STUDENT_ROLE")

    group = [perfectures_item_type, location_information_item_type]
    """Check itemtype name"""
    if item_type_name not in item_type_list:
        if item_type_name == output_registration_item_type:
            return get_mail_data(
                current_config.get("WEKO_WORKFLOW_RECEIVE_OUTPUT_REGISTRATION"))
        elif item_type_name == usage_report_item_type:
            return get_mail_data(
                current_config.get("WEKO_WORKFLOW_RECEIVE_USAGE_REPORT"))
        return None, None
    if user_role and user_role == general_role:
        if item_type_name not in group:
            return get_mail_data(
                current_config.get("WEKO_WORKFLOW_RECEIVE_USAGE_APP_BESIDE"
                                   "_PERFECTURE_AND_LOCATION_DATA_OF"
                                   "_GENERAL_USER"))
        elif item_type_name in group:
            return get_mail_data(
                current_config.get("WEKO_WORKFLOW_PERFECTURE_OR_LOCATION_DATA"
                                   "_OF_GENERAL_USER"))
    elif user_role and user_role in [graduated_student_role, student_role]:
        if item_type_name not in group:
            return get_mail_data(
                current_config.get("WEKO_WORKFLOW_RECEIVE_USAGE_APP_BESIDE"
                                   "_PERFECTURE_AND_LOCATION_DATA_OF_STUDENT_OR"
                                   "_GRADUATED_STUDENT"))
        elif item_type_name in group:
            return get_mail_data(
                current_config.get("WEKO_WORKFLOW_PERFECTURE_OR_LOCATION_DATA"
                                   "_OF_STUDENT_OR_GRADUATED_STUDENT"))
    return None, None


def email_pattern_request_approval(item_type_name, next_action):
    """Get mail pattern when request approval.

    :item_type_name: object
    :next_action: object
    """
    config = current_app.config
    if item_type_name not in config.get(
            'WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST'):
        return None, None
    if next_action == 'approval_guarantor':
        return get_mail_data(config.get(
            "WEKO_WORKFLOW_REQUEST_APPROVAL_TO_GUARANTOR_OF_USAGE_APP"))
    if next_action == 'approval_advisor':
        return get_mail_data(config.get(
            "WEKO_WORKFLOW_REQUEST_APPROVAL_TO_ADVISOR_OF_USAGE_APP"))


def email_pattern_approval_done(item_type_name):
    """Get mail pattern when approval done.

    :item_type_name: item type name
    """
    config = current_app.config
    if item_type_name not in config.get(
            'WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST'):
        if item_type_name == config.get("WEKO_ITEMS_UI_OUTPUT_REPORT"):
            return get_mail_data(
                config.get("WEKO_WORKFLOW_APPROVE_OUTPUT_REGISTRATION"))
        elif item_type_name == config.get("WEKO_ITEMS_UI_USAGE_REPORT"):
            return get_mail_data(
                config.get("WEKO_WORKFLOW_APPROVE_USAGE_REPORT"))
        return None, None
    if item_type_name != config.get(
            'WEKO_ITEMS_UI_APPLICATION_FOR_LOCATION_INFORMATION'):
        return get_mail_data(config.get(
            "WEKO_WORKFLOW_APPROVE_USAGE_APP_BESIDE_LOCATION_DATA"))
    else:
        return get_mail_data(config.get(
            "WEKO_WORKFLOW_APPROVE_LOCATION_DATA"))


def get_mail_data(file_name):
    """Get data of a email.

    :file_name: file name template
    """
    file_path = get_file_path(file_name)
    return get_subject_and_content(file_path)


def get_subject_and_content(file_path):
    """Get mail subject and content from template file.

    :file_path: this is a full path
    """
    import os
    if not os.path.exists(file_path):
        return None, None
    file = open(file_path, 'r')
    subject = body = ''
    index = 0
    """ Get subject and content body from template file """
    """ The first line is mail subject """
    """ Exclude the first line is mail content """
    for line in file:
        if index == 0:
            subject = line
        else:
            body += line
        index += 1
    """ Custom subject (remove 'Subject：' from subject) """
    subject = subject.replace('Subject：', '')
    subject = subject.replace('\n', '')
    return subject, body


def get_file_path(file_name):
    """Get file path from file name.

    :file_name: file name
    """
    config = current_app.config
    template_folder_path = \
        config.get("WEKO_WORKFLOW_MAIL_TEMPLATE_FOLDER_PATH")

    # Get file path (template path + file name)
    if template_folder_path is not None and file_name is not None:
        return os.path.join(template_folder_path, file_name)
    else:
        return ""


def replace_characters(data, content):
    """Replace character for content.

    :data:
    :content data:
    """
    replace_list = {
        '[1]': 'university_institution',
        '[2]': 'fullname',
        '[3]': 'activity_id',
        '[4]': 'mail_address',
        '[5]': 'research_title',
        '[6]': 'dataset_requested',
        '[7]': 'register_date',
        '[8]': 'advisor_name',
        '[9]': 'guarantor_name',
        '[10]': 'url',
        '[11]': 'advisor_affilication',
        '[12]': 'guarantor_affilication',
        '[13]': 'approval_date',
        '[14]': 'approval_date_after_7_days',
        '[15]': '31_march_corresponding_year',
        '[16]': 'report_number',
        '[17]': 'registration_number',
        '[18]': 'output_registration_title',
        '[19]': 'url_guest_user',
        '[restricted_fullname]': 'restricted_fullname',
        '[restricted_university_institution]':
            'restricted_university_institution',
        '[restricted_activity_id]': 'restricted_activity_id',
        '[restricted_research_title]': 'restricted_research_title',
        '[restricted_data_name]': 'restricted_data_name',
        '[restricted_application_date]': 'restricted_application_date',
        '[restricted_mail_address]': 'restricted_mail_address',
        '[restricted_download_link]': 'restricted_download_link',
        '[restricted_expiration_date]': 'restricted_expiration_date',
        '[restricted_expiration_date_ja]': 'restricted_expiration_date_ja',
        '[restricted_expiration_date_en]': 'restricted_expiration_date_en',
        '[restricted_approver_name]': 'restricted_approver_name',
        '[restricted_site_name_ja]': 'restricted_site_name_ja',
        '[restricted_site_name_en]': 'restricted_site_name_en',
        '[restricted_site_mail]': 'restricted_site_mail',
        '[restricted_site_url]': 'restricted_site_url',
        '[restricted_approver_affiliation]': 'restricted_approver_affiliation',
        '[restricted_supervisor]': '',
        '[restricted_reference]': '',
        '[data_download_date]': 'data_download_date',
        '[usage_report_url]': 'usage_report_url',
        '[restricted_usage_activity_id]': 'restricted_usage_activity_id',
        '[file_name]' : 'file_name',
        '[restricted_download_count]':'restricted_download_count',
        '[restricted_download_count_ja]':'restricted_download_count_ja',
        '[restricted_download_count_en]':'restricted_download_count_en',
    }
    for key in replace_list:
        value = replace_list.get(key)
        if data.get(value):
            content = content.replace(key, data.get(value))
        else:
            content = content.replace(key, '')
    return content


def get_register_info(activity_id):
    """Get register info.

    :activity_id: object
    """
    history = WorkActivityHistory()
    histories = history.get_activity_history_list(activity_id)
    date_format_str = current_app.config['WEKO_WORKFLOW_DATE_FORMAT']
    for activity_history in histories:
        if 'Item Registration' in activity_history.ActionName[0] and \
                activity_history.StatusDesc == 'action_done':
            return activity_history.user.email, \
                activity_history.action_date.strftime(date_format_str)

    return current_user.email, datetime.today().strftime(date_format_str)


def get_approval_dates(mail_info):
    """Get approval date.

    :mail_info: object
    """
    today = datetime.today()
    date_format_str = current_app.config['WEKO_WORKFLOW_DATE_FORMAT']
    mail_info['approval_date'] = today.strftime(date_format_str)
    mail_info['approval_date_after_7_days'] = \
        (today + timedelta(days=7)).strftime(date_format_str)
    year = today.year
    if today.month >= 1 and today.day >= 4:
        year = today.year + 1
    mail_info['31_march_corresponding_year'] = str(year) + '-03-31'


def get_item_info(item_id):
    """Get item info.

    :item_id: item id
    """
    if not item_id:
        return dict()
    try:
        item = ItemsMetadata.get_record(id_=item_id)
    except Exception as ex:
        current_app.logger.error('Cannot get item data: {}'.format(ex))
        temp = dict()
        return temp
    item_info = dict()
    for k, v in item.items():
        if isinstance(v, dict):
            item_info.update(v)
    return item_info


def get_site_info_name():
    """Get site name.

    @return:
    """
    site_name_en = site_name_ja = ''
    site_info = SiteInfo.get()
    if site_info:
        if len(site_info.site_name) == 1:
            site_name_en = site_name_ja = site_info.site_name[0]['name']
        elif len(site_info.site_name) == 2:
            for site in site_info.site_name:
                site_name_ja = site['name'] \
                    if site['language'] == 'ja' else site_name_ja
                site_name_en = site['name'] \
                    if site['language'] == 'en' else site_name_en
    return site_name_en, site_name_ja


def get_default_mail_sender():
    """Get default mail sender.

    :return:
    """
    mail_config = MailConfig.get_config()
    return mail_config.get('mail_default_sender', '')


def set_mail_info(item_info, activity_detail, guest_user=False):
    """Set main mail info.

    :item_info: object
    :activity_detail: object
    :guest_user: object
    """
    site_en, site_ja = get_site_info_name()
    site_mail = get_default_mail_sender()
    register_user = register_date = ''
    if not guest_user:
        register_user, register_date = get_register_info(
            activity_detail.activity_id)

    mail_info = dict(
        university_institution=item_info.get('subitem_university/institution'),
        fullname=item_info.get('subitem_fullname'),
        activity_id=activity_detail.activity_id,
        mail_address=item_info.get('subitem_mail_address'),
        research_title=item_info.get('subitem_research_title'),
        dataset_requested=item_info.get('subitem_dataset_usage'),
        register_date=register_date,
        advisor_name=item_info.get('subitem_advisor_fullname'),
        guarantor_name=item_info.get('subitem_guarantor_fullname'),
        url=request.url_root,
        advisor_affilication=item_info.get('subitem_advisor_affiliation'),
        guarantor_affilication=item_info.get('subitem_guarantor_affiliation'),
        advisor_mail=item_info.get('subitem_advisor_mail_address'),
        guarantor_mail=item_info.get('subitem_guarantor_mail_address'),
        register_user_mail=register_user,
        report_number=activity_detail.activity_id,
        registration_number=activity_detail.activity_id,
        output_registration_title=item_info.get('subitem_title'),
        # Restricted data newly supported
        restricted_fullname=item_info.get('subitem_restricted_access_name'),
        restricted_university_institution=item_info.get(
            'subitem_restricted_access_university/institution'),
        restricted_activity_id=activity_detail.activity_id,
        restricted_research_title=item_info.get(
            'subitem_restricted_access_research_title'),
        restricted_data_name=item_info.get(
            'subitem_restricted_access_dataset_usage'),
        restricted_application_date=item_info.get(
            'subitem_restricted_access_application_date'),
        restricted_mail_address=item_info.get(
            'subitem_restricted_access_mail_address'),
        restricted_download_link='',
        restricted_expiration_date='',
        restricted_approver_name='',
        restricted_approver_affiliation='',
        restricted_site_name_ja=site_ja,
        restricted_site_name_en=site_en,
        restricted_site_mail=site_mail,
        restricted_site_url=current_app.config['THEME_SITEURL'],
        mail_recipient=item_info.get('subitem_restricted_access_mail_address'),
        restricted_supervisor='',
        restricted_reference=''
    )
    return mail_info


def process_send_reminder_mail(activity_detail, mail_template):
    """Process send reminder mail.

    :activity_detail: object
    :mail_template: string
    """
    item_info = get_item_info(activity_detail.item_id)
    mail_info = set_mail_info(item_info, activity_detail)

    from weko_items_ui.utils import get_user_information
    update_user = get_user_information(activity_detail.activity_login_user)
    if update_user.get('email') != '':
        mail_info['mail_address'] = update_user.get('email')
    else:
        raise ValueError('Cannot get receiver mail address')

    if update_user.get('fullname') != '':
        mail_info['fullname'] = update_user.get('fullname')
    mail_info['template'] = mail_template
    try:
        send_mail_reminder(mail_info)
    except ValueError as val:
        raise ValueError(val)


def process_send_notification_mail(
        activity_detail, action_endpoint, next_action_endpoint):
    """Process send notification mail.

    :activity_detail: object
    :action_endpoint: object
    :next_action_endpoint: object
    """
    item_info = get_item_info(activity_detail.item_id)
    mail_info = set_mail_info(item_info, activity_detail)

    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(
        activity_detail.workflow_id)
    item_type_name = get_item_type_name(workflow_detail.itemtype_id)
    mail_info['item_type_name'] = item_type_name
    mail_info['next_step'] = next_action_endpoint
    """ Set registration date to 'mail_info' """
    get_approval_dates(mail_info)
    if 'item_login' in action_endpoint:
        """ Send mail for register to notify that registration is done"""
        send_mail_registration_done(mail_info)
    if 'approval_' in next_action_endpoint \
            and 'administrator' not in next_action_endpoint:
        """ Send mail for approver to request approval"""
        send_mail_request_approval(mail_info)
    if 'approval_administrator' in action_endpoint:
        """ Send mail to register to notify
            that registration is approved by admin """
        send_mail_approval_done(mail_info)


def get_application_and_approved_date(activities, columns):
    """Get application and approved date.

    @param activities:
    @param columns:
    """
    if 'application_date' in columns or 'approved_date' in columns:
        activities_id_list = []
        for activity_data in activities:
            activities_id_list.append(activity_data.activity_id)
        application_date_dc = {}
        approved_date_dc = {}
        if activities_id_list:
            activity_history = WorkActivityHistory()
            application_dates = activity_history.get_application_date(
                activities_id_list)
            for data in application_dates:
                application_date_dc[data.activity_id] = data.action_date

            approved_date_list = activity_history.get_approved_date(
                activities_id_list)
            for data in approved_date_list:
                approved_date_dc[data.get("activity_id")] = data.get(
                    "action_date")

        for item_activity in activities:
            application_date = application_date_dc.get(
                item_activity.activity_id)
            approved_date = approved_date_dc.get(item_activity.activity_id)
            item_activity.application_date = application_date
            item_activity.approved_date = approved_date


def get_workflow_item_type_names(activities: list):
    """Get workflow item type names.

    @param activities: Activity list.
    """
    workflow_id_lst = []
    for activity in activities:
        workflow_id_lst.append(activity.workflow_id)

    if workflow_id_lst:
        # Get Workflow list
        workflows = WorkFlow().get_workflow_by_ids(workflow_id_lst)
        item_type_id_lst = []
        temp_workflow_item_type_id = {}
        for data in workflows:
            item_type_id_lst.append(data.itemtype_id)
            temp_workflow_item_type_id[data.itemtype_id] = data.id

        # Get item type list
        item_type_name_list = ItemTypeNames.get_all_by_id(item_type_id_lst)
        workflow_item_type_names = {}
        for item_type_name in item_type_name_list:
            for data in workflows:
                if data.itemtype_id == item_type_name.id:
                    workflow_item_type_names[data.id] = item_type_name.name

        for activity in activities:
            item_type_name = workflow_item_type_names.get(activity.workflow_id)
            if item_type_name:
                activity.item_type_name = item_type_name


def create_usage_report(activity_id):
    """Auto create usage report.

    @param activity_id:
    @return:
    """
    # Get activity
    activity_detail = WorkActivity().get_activity_detail(activity_id)

    _workflow = WorkFlow()
    # Get usage report WF
    usage_report_workflow = _workflow.find_workflow_by_name(
        current_app.config['WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME'])
    if not usage_report_workflow:
        return None
    else:
        activity = dict(
            workflow_id=usage_report_workflow.id,
            flow_id=usage_report_workflow.flow_id
        )
        usage_report_activity_id = create_record_metadata(
            activity, activity_detail.item_id, activity_id,
            usage_report_workflow,
            activity_detail.extra_info.get("related_title")
        )
        return usage_report_activity_id


def create_record_metadata(
    activity,
    item_id,
    activity_id,
    usage_report_workflow,
    related_title
):
    """Create record metadata for usage report.

    @param activity:
    @param item_id:
    @param activity_id:
    @param usage_report_workflow:
    @param related_title:
    @return:
    """
    rec = RecordMetadata.query.filter_by(id=item_id).first()
    item_metadata = ItemsMetadata.get_record(id_=item_id).dumps()
    item_metadata.pop('id', None)
    record_metadata = rec.json
    attribute_value_key = 'attribute_value_mlt'

    # Usage reports approval by administrator only.
    # Remove other approver from metadata.
    item_metadata.pop('approval1', None)
    item_metadata.pop('approval2', None)

    data_dict = dict()
    for item in record_metadata:
        values = record_metadata.get(item)
        if isinstance(values, dict) and attribute_value_key in values:
            attribute = values.get(attribute_value_key)
            if isinstance(attribute, list):
                for data in attribute:
                    for key in data:
                        if key.startswith("subitem") and \
                                key not in ['subitem_advisor_mail_address',
                                            'subitem_guarantor_mail_address']:
                            data_dict[key] = data.get(key)

    item_type_id = usage_report_workflow.itemtype_id

    schema = ItemTypes.get_by_id(item_type_id).schema
    owner_id = current_user.get_id()
    new_usage_report_activity = WorkActivity().init_activity(activity)
    modify_item_metadata(
        item_metadata,
        item_type_id,
        new_usage_report_activity.activity_id,
        activity_id,
        data_dict,
        schema,
        owner_id,
        related_title
    )

    activity.update({'activity_id': new_usage_report_activity.activity_id})
    activity['activity_login_user'] = owner_id
    activity['activity_update_user'] = owner_id
    activity['title'] = item_metadata['title']

    WorkActivity().update_activity_action_handler(
        new_usage_report_activity.activity_id, owner_id)

    create_deposit(new_usage_report_activity.id)
    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value=str(new_usage_report_activity.id)
    ).first()

    record = WekoDeposit.get_record(pid.object_uuid)
    deposit = WekoDeposit(record, record.model)
    item_metadata['id'] = deposit['_deposit']['id']
    item_metadata['pid']['value'] = deposit['_deposit']['id']

    item_status = {
        'index': [usage_report_workflow.index_tree_id],
        'actions': 'publish',
    }

    deposit.update(item_status, item_metadata)

    deposit.commit()
    deposit.publish()

    activity['item_id'] = deposit.id

    first_ver = deposit.newversion(pid)
    if first_ver:
        first_ver.publish()

    update_activity_action(activity.get('activity_id'), owner_id)

    WorkActivity().update_activity(activity.get('activity_id'), activity)
    return new_usage_report_activity.activity_id


def modify_item_metadata(
    item,
    item_type_id,
    activity_id,
    usage_application_activity_id,
    data_dict,
    schema, owner_id,
    related_title
):
    """Mapping usage application data to usage report."""
    if not item:
        return None

    item['$schema'] = 'items/jsonschema/' + str(item_type_id)
    from weko_user_profiles.utils import get_user_profile_info
    user_profile = get_user_profile_info(int(owner_id))
    user_name = user_profile['subitem_displayname']
    record_title = {
        "en": '{} - {} - {} - {}'.format(
            related_title,
            current_app.config.get(
                'WEKO_ITEMS_UI_USAGE_REPORT_TITLE').get('en'),
            usage_application_activity_id, user_name
        ),
        "ja": '{} - {} - {} - {}'.format(
            related_title,
            current_app.config.get(
                'WEKO_ITEMS_UI_USAGE_REPORT_TITLE').get('ja'),
            usage_application_activity_id, user_name
        ),
    }

    # Set title to JP only
    item['title'] = record_title["ja"]
    properties = schema['properties']
    schema_dict = get_shema_dict(properties, data_dict)

    item_approval1 = ''
    item_approval2 = ''
    for data in item:
        cur_data = item[data]
        if isinstance(cur_data, dict) and \
                'subitem_advisor_mail_address' in cur_data:
            item_approval1 = data
        if isinstance(cur_data, dict) and \
                'subitem_guarantor_mail_address' in cur_data:
            item_approval2 = data
        for key in schema_dict:
            if isinstance(cur_data, dict) and key in cur_data:
                new_key = schema_dict[key]
                if new_key not in item:
                    item[new_key] = item.pop(data)

            if isinstance(cur_data, list):
                for item_data in cur_data:
                    if isinstance(item_data, dict) and key in item_data and \
                            schema_dict[key] not in item:
                        sub_data = item.get(data)
                        if isinstance(sub_data, list):
                            for title in sub_data:
                                if title.get('subitem_item_title') and \
                                    title.get(
                                        'subitem_item_title_language'):
                                    title['subitem_item_title'] = \
                                        record_title.get(
                                            title.get(
                                                'subitem_item_title_language'))
                        item[schema_dict[key]] = item.pop(data)
                        break
    item.pop(item_approval1, None)
    item.pop(item_approval2, None)

    return item


def replace_title_subitem(subitem_title, subitem_item_title_language):
    """Create deposit."""
    subitem_title = subitem_title.replace(
        current_app.config.get('WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE').
        get(subitem_item_title_language),
        current_app.config.get('WEKO_ITEMS_UI_USAGE_REPORT_TITLE').
        get(subitem_item_title_language)
    )
    return subitem_title


def get_shema_dict(properties, data_dict):
    """Get schemadict from properties and datadict.

    @param properties:
    @param data_dict:
    @return:
    """
    schema_dict = dict()
    if properties:
        for item_property in properties:
            schema_key = properties.get(item_property)
            if 'items' in schema_key:
                items = schema_key['items']
                if 'properties' in items:
                    for data_key in data_dict:
                        if data_key in items['properties']:
                            schema_dict[data_key] = item_property
            if 'properties' in schema_key:
                for data_key in data_dict:
                    if data_key in schema_key['properties']:
                        schema_dict[data_key] = item_property

    return schema_dict


def create_deposit(item_id):
    """Create deposit."""
    deposit = WekoDeposit.create({}, recid=int(item_id))
    return deposit


def update_activity_action(activity_id, owner_id):
    """Update activity action.

    @param activity_id:
    @param owner_id:
    """
    usage_application = current_app.config['WEKO_WORKFLOW_ACTION_ITEM_'
                                           'REGISTRATION_USAGE_APPLICATION']
    if usage_application:
        action = _Action.query.filter_by(
            action_name=usage_application).one_or_none()
        if action:
            activity = WorkActivity()
            activity_detail = activity.get_activity_by_id(activity_id)
            WorkActivity().upt_activity_action_status(
                activity_id=activity_id, action_id=action.id,
                action_status=ActionStatusPolicy.ACTION_DOING,
                action_order=activity_detail.action_order
            )
            WorkActivityHistory().upd_activity_history_detail(activity_id,
                                                              action.id)
            WorkActivityHistory().update_activity_history_owner(activity_id,
                                                                owner_id)


def check_continue(response, activity_id):
    """Check continue value.

    :param response:
    :param activity_id:
    :return:
    """
    if current_app.config.get('WEKO_WORKFLOW_CONTINUE_APPROVAL'):
        response['check_handle'] = 1
        activity = WorkActivity()
        item_id = activity.get_activity_detail(activity_id).item_id
        if item_id:
            record = RecordMetadata.query.filter_by(id=item_id).first()
            record = record.json
            attribute_value_key = 'attribute_value_mlt'
            data_type_key = 'subitem_stop/continue'
            for item in record:
                values = record.get(item)
                if isinstance(values,
                              dict) and attribute_value_key in values:
                    attribute = values.get(attribute_value_key)
                    if isinstance(attribute, list):
                        for data in attribute:
                            if data_type_key in data and data.get(
                                    data_type_key) == 'Continue':
                                response['check_continue'] = 1
                                return response
            response['check_continue'] = 0
            return response
    else:
        return response


def auto_fill_title(item_type_name):
    """Autofill title.

    @param item_type_name:
    @return:
    """
    def _get_title(title_key):
        title_value = ''
        if auto_fill_title_value.get(title_key):
            title_value = auto_fill_title_value.get(title_key)
        return title_value

    title = ""
    current_config = current_app.config
    autofill_title_setting = current_config.get(
        'WEKO_ITEMS_UI_AUTO_FILL_TITLE_SETTING')
    auto_fill_title_value = current_config.get(
        'WEKO_ITEMS_UI_AUTO_FILL_TITLE')
    if item_type_name is not None and isinstance(autofill_title_setting, dict):
        usage_application_key = current_config.get(
            'WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE_KEY')
        usage_report_key = current_config.get(
            'WEKO_ITEMS_UI_USAGE_REPORT_TITLE_KEY')
        output_registration_key = current_config.get(
            'WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE_KEY')

        usage_application_list = autofill_title_setting.get(
            usage_application_key, [])
        usage_report_list = autofill_title_setting.get(usage_report_key, [])
        output_registration_list = autofill_title_setting.get(
            output_registration_key, [])
        if item_type_name in usage_application_list:
            title = _get_title(usage_application_key)
        elif item_type_name in usage_report_list:
            title = _get_title(usage_report_key)
        elif item_type_name in output_registration_list:
            title = _get_title(output_registration_key)
    return title


def exclude_admin_workflow(workflow_list):
    """Exclude a list of workflow form workflow_list base on current user role.

    :param workflow_list:
    :return:
    """
    from weko_items_ui.utils import get_current_user_role
    if current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] and \
        not get_current_user_role() == \
            current_app.config['WEKO_USERPROFILES_ADMINISTRATOR_ROLE']:
        for workflow in workflow_list:
            for flow_action in workflow.flow_define.flow_actions:
                if flow_action.action.action_name == current_app.\
                        config['WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION']:
                    workflow_list.remove(workflow)
    return workflow_list


def is_enable_item_name_link(action_endpoint, item_type_name):
    """Check enable item name link.

    :param action_endpoint:
    :param item_type_name:
    :return:
    """
    if "item_login_application" == action_endpoint \
        and item_type_name == current_app.config.get(
            'WEKO_ITEMS_UI_USAGE_REPORT'):
        return False
    return True


def save_activity_data(data: dict) -> NoReturn:
    """Save activity data.

    @param data: activity data.
    """
    activity_id = data.get("activity_id")
    activity_data = {
        "title": data.get("title"),
        "shared_user_id": data.get("shared_user_id"),
        "approval1": data.get("approval1"),
        "approval2": data.get("approval2"),
    }
    if activity_id:
        WorkActivity().update_activity(activity_id, activity_data)

def send_mail_url_guest_user(mail_info: dict) -> bool:
    """Send mail url guest_user.

    :mail_info: object
    """
    subject, body = get_mail_data(mail_info.get('template'))
    if not body:
        return False
    body = replace_characters(mail_info, body)
    if not send_mail(subject, mail_info.get('mail_address'), body):
        return False
    else:
        return True


def generate_guest_activity_token_value(
    activity_id: str, file_name: str, activity_date: datetime, guest_mail: str
) -> str:
    """Generate guest activity token value.

    Args:
        activity_id (str):
        file_name (str):
        activity_date (datetime):
        guest_mail (str):

    Returns:
        [str]: token value string.

    """
    date_form_str = current_app.config['WEKO_WORKFLOW_DATE_FORMAT']
    token_pattern = current_app.config['WEKO_WORKFLOW_ACTIVITY_TOKEN_PATTERN']
    activity_date = activity_date.strftime(date_form_str)
    hash_value = token_pattern.format(activity_id, file_name, activity_date,
                                      guest_mail)
    secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
    token = oracle10.hash(secret_key, hash_value)
    token_value = "{} {} {} {}".format(activity_id, activity_date,
                                       guest_mail, token)
    token_value = base64.b64encode(token_value.encode()).decode()
    return token_value


def init_activity_for_guest_user(
    data: dict, is_usage_report: bool = False
) -> Tuple[Optional[object], str]:
    """Init activity for guest user.

    @param data:
    @param is_usage_report:
    @return:
    """
    def _get_guest_activity():
        _guest_activity = {
            "user_mail": guest_mail,
            "record_id": record_id,
            "file_name": file_name,
        }
        return GuestActivity.find(**_guest_activity)

    # Get data to generated key
    guest_mail = data.get("extra_info").get("guest_mail")
    file_name = data.get("extra_info").get("file_name")
    record_id = data.get("extra_info").get("record_id")

    guest_activity = _get_guest_activity()
    activity = None
    if not guest_activity:
        # Init activity for guest user.
        activity = WorkActivity().init_activity(data)
        activity_id = activity.activity_id

        # Generate token value
        token_value = generate_guest_activity_token_value(
            activity_id, file_name, activity.created, guest_mail
        )

        # Save create guest activity
        guest_activity = {
            "user_mail": guest_mail,
            "record_id": record_id,
            "file_name": file_name,
            "activity_id": activity_id,
            "token": token_value
        }

        # In case create usage report,
        # update expiration date from Admin settings
        if is_usage_report:
            guest_activity['is_usage_report'] = is_usage_report
            usage_report_access = get_restricted_access(
                'usage_report_workflow_access')
            guest_activity['expiration_date'] = int(usage_report_access.get(
                'expiration_date_access', 500))

        GuestActivity.create(**guest_activity)
    else:
        token_value = guest_activity[0].token

    # Generate URL
    url_pattern = "{}workflow/activity/guest-user/{}?token={}"
    tmp_url = url_pattern.format(request.url_root, file_name, token_value)

    return activity, tmp_url


def send_usage_application_mail_for_guest_user(guest_mail: str, temp_url: str):
    """Send usage application mail for guest user.

    @param guest_mail:
    @param temp_url:
    @return:
    """
    # Mail information
    site_name_en, site_name_ja = get_site_info_name()
    site_mail = get_default_mail_sender()
    site_url = current_app.config['THEME_SITEURL']
    mail_info = {
        'template': current_app.config.get("WEKO_WORKFLOW_ACCESS_ACTIVITY_URL"),
        'mail_address': guest_mail,
        'url_guest_user': temp_url,
        "restricted_site_name_ja": site_name_ja,
        "restricted_site_name_en": site_name_en,
        "restricted_site_mail": site_mail,
        "restricted_site_url": site_url,
    }
    return send_mail_url_guest_user(mail_info)


def validate_guest_activity_token(
    token: str, file_name: str
) -> Union[Tuple[bool, None, None], Tuple[bool, str, str]]:
    """Validate guest activity token.

    @param token:
    @param file_name:
    @return:
    """
    try:
        secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
        decode_param = base64.b64decode(token.encode()).decode()
        params = decode_param.split(" ")
        if len(params) != 4:
            return False, None, None
        pattern = "activity={} file_name={} date={} email={}"
        key_value = pattern.format(params[0], file_name, params[1], params[2])
        return oracle10.verify(
            secret_key, params[3], key_value), params[0], params[2]
    except Exception as err:
        current_app.logger.debug(err)
        return False, None, None


def validate_guest_activity_expired(activity_id: str) -> str:
    """Validate guest activity expired.

    @param activity_id:
    @return:
    """
    guest_activity = GuestActivity.find_by_activity_id(activity_id)
    if guest_activity:
        guest_activity = guest_activity[0]
    else:
        return ""
    if guest_activity.is_usage_report:
        try:
            expiration_date = timedelta(guest_activity.expiration_date)
            expiration_access_date = guest_activity.created.date() + \
                expiration_date
        except OverflowError:
            return ""
        current_date = datetime.utcnow().date()
        if current_date > expiration_access_date:
            return _("The specified link has expired.")
    return ""


def create_onetime_download_url_to_guest(activity_id: str,
                                         extra_info: dict):
    """Create onetime download URL to guest.

    @param activity_id:
    @param extra_info:
    @return:
    """
    file_name = extra_info.get('file_name')
    record_id = extra_info.get('record_id')
    user_mail = extra_info.get('user_mail')
    is_guest_user = False
    if not user_mail:
        user_mail = extra_info.get('guest_mail')
        is_guest_user = True
    if file_name and record_id and user_mail:
        from weko_records_ui.utils import generate_one_time_download_url
        onetime_file_url = generate_one_time_download_url(
            file_name, record_id, user_mail)

        # Delete guest activity.
        delete_guest_activity(activity_id)

        # Save onetime to Database.
        from weko_records_ui.utils import create_onetime_download_url
        one_time_obj = create_onetime_download_url(
            activity_id, file_name, record_id, user_mail, is_guest_user)
        expiration_tmp = {
            "expiration_date": "",
            "expiration_date_ja": "",
            "expiration_date_en": "",
        }
        if one_time_obj:
            try:
                expiration_date = timedelta(days=one_time_obj.expiration_date)
                expiration_date = datetime.today() + expiration_date
                expiration_date = expiration_date.strftime("%Y-%m-%d")
                expiration_tmp['expiration_date'] = expiration_date
            except OverflowError:
                expiration_tmp["expiration_date_ja"] = "無制限"
                expiration_tmp["expiration_date_en"] = "Unlimited"
            return {
                "file_url": onetime_file_url,
                **expiration_tmp,
            }
        else:
            current_app.logger.error("Can not create onetime download.")
            return False


def delete_guest_activity(activity_id: str) -> bool:
    """Delete guest activity for guest user.

    @param activity_id:
    @return:
    """
    guest_activity = GuestActivity.find_by_activity_id(activity_id)
    if guest_activity:
        return GuestActivity.delete(guest_activity[0])
    return False


def get_activity_display_info(activity_id: str):
    """_summary_

    Args:
        activity_id (str): _description_

    Returns:
        _type_: _description_
        action_endpoint
        int: action_id
        Activity: activity_detail
        Action: cur_action
        ActivityHistory: histories
        _type_: item {'lang': 'ja', 'owner': '1', 'title': 'ddd', '$schema': '/items/jsonschema/15', 'pubdate': '2022-08-21', 'shared_user_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'ddd', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_beb9', 'resourcetype': 'data paper'}}
        _type_: steps
        _type_: temporary_comment [{'ActivityId': 'A-20220821-00003', 'ActionId': 1, 'ActionName': 'Start', 'ActionVersion': '1.0.0', 'ActionEndpoint': 'begin_action', 'Author': 'wekosoftware@nii.ac.jp', 'Status': 'action_done', 'ActionOrder': 1}, {'ActivityId': 'A-20220821-00003', 'ActionId': 3, 'ActionName': 'Item Registration', 'ActionVersion': '1.0.1', 'ActionEndpoint': 'item_login', 'Author': '', 'Status': ' ', 'ActionOrder': 2}, {'ActivityId': 'A-20220821-00003', 'ActionId': 4, 'ActionName': 'Approval', 'ActionVersion': '2.0.0', 'ActionEndpoint': 'approval', 'Author': '', 'Status': ' ', 'ActionOrder': 3}, {'ActivityId': 'A-20220821-00003', 'ActionId': 5, 'ActionName': 'Item Link', 'ActionVersion': '1.0.1', 'ActionEndpoint': 'item_link', 'Author': '', 'Status': ' ', 'ActionOrder': 4}, {'ActivityId': 'A-20220821-00003', 'ActionId': 7, 'ActionName': 'Identifier Grant', 'ActionVersion': '1.0.0', 'ActionEndpoint': 'identifier_grant', 'Author': '', 'Status': ' ', 'ActionOrder': 5}, {'ActivityId': 'A-20220821-00003', 'ActionId': 2, 'ActionName': 'End', 'ActionVersion': '1.0.0', 'ActionEndpoint': 'end_action', 'Author': '', 'Status': ' ', 'ActionOrder': 6}]
        Workflow: workflow_detail
    """
    activity = WorkActivity()
    activity_detail = activity.get_activity_detail(activity_id)
    item = None
    if activity_detail and activity_detail.item_id:
        try:
            #obj = RecordMetadata.query.filter_by(id=activity_detail.item_id).one_or_none()
            #item = ItemsMetadata(obj.json, model=obj)
            item = ItemsMetadata.get_record(id_=activity_detail.item_id)
        except NoResultFound as ex:
            current_app.logger.exception(str(ex))
            item = None
    steps = activity.get_activity_steps(activity_id)
    history = WorkActivityHistory()
    histories = history.get_activity_history_list(activity_id)
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(
        activity_detail.workflow_id)
    if activity_detail.activity_status == \
            ActivityStatusPolicy.ACTIVITY_FINALLY \
            or activity_detail.activity_status == \
            ActivityStatusPolicy.ACTIVITY_CANCEL:
        activity_detail.activity_status_str = _('End')
    else:
        activity_detail.activity_status_str = \
            request.args.get('status', 'ToDo')
    cur_action = activity_detail.action
    action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
    temporary_comment = ""
    action_data = activity.get_activity_action_comment(
        activity_id=activity_id, action_id=action_id,
        action_order=activity_detail.action_order)
    if action_data:
        temporary_comment = action_data.action_comment

    current_app.logger.debug("action_endpoint:{}".format(action_endpoint))
    current_app.logger.debug("action_id:{}".format(action_id))
    current_app.logger.debug("activity_detail:{}".format(activity_detail))
    current_app.logger.debug("cur_action:{}".format(cur_action))
    current_app.logger.debug("histories:{}".format(histories))
    current_app.logger.debug("item:{}".format(item))
    current_app.logger.debug("steps:{}".format(steps))
    current_app.logger.debug("temporary_comment:{}".format(temporary_comment))
    current_app.logger.debug("workflow_detail:{}".format(workflow_detail))

    return action_endpoint, action_id, activity_detail, cur_action, histories, \
        item, steps, temporary_comment, workflow_detail


def __init_activity_detail_data_for_guest(activity_id: str, community_id: str):
    """Init activity data for guest user.

    @param activity_id:
    @param community_id:
    @return:
    """
    from weko_records_ui.utils import get_list_licence
    action_endpoint, action_id, activity_detail, cur_action, histories, item, \
        steps, temporary_comment, workflow_detail = \
        get_activity_display_info(activity_id)
    item_type_name = get_item_type_name(workflow_detail.itemtype_id)
    # Check auto set index
    is_auto_set_index_action = True

    # Get the design for widget rendering
    from weko_theme.utils import get_design_layout
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

    # Update session for steps get item_login
    session['activity_info'] = dict(
        activity_id=activity_id,
        action_id=activity_detail.action_id,
        action_version=cur_action.action_version,
        action_status=ActionStatusPolicy.ACTION_DOING,
        commond=''
    )
    session['itemlogin_id'] = activity_id
    session['itemlogin_activity'] = activity_detail
    # get item login info.
    from weko_items_ui.api import item_login
    step_item_login_url, need_file, need_billing_file, \
        record, json_schema, schema_form, \
        item_save_uri, files, endpoints, need_thumbnail, files_thumbnail, \
        allow_multi_thumbnail \
        = item_login(item_type_id=workflow_detail.itemtype_id)
    if not record and item:
        record = item

    # Get guest user profile
    guest_email = session['guest_email']
    user_name = guest_email.split('@')[0]
    profile = {
        'subitem_user_name': user_name,
        'subitem_fullname': user_name,
        'subitem_mail_address': guest_email,
        'subitem_displayname': user_name,
        'subitem_university/institution': '',
        'subitem_affiliated_division/department': '',
        'subitem_position': '',
        'subitem_phone_number': '',
        'subitem_position(other)': '',
        'subitem_affiliated_institution': [],
    }
    user_profile = {"results": profile}

    return dict(
        page=page,
        render_widgets=render_widgets,
        community_id=community_id,
        temporary_journal='',
        temporary_idf_grant='',
        temporary_idf_grant_suffix='',
        idf_grant_data='',
        idf_grant_input=IDENTIFIER_GRANT_LIST,
        idf_grant_method=current_app.config.get(
            'IDENTIFIER_GRANT_SUFFIX_METHOD', IDENTIFIER_GRANT_SUFFIX_METHOD),
        error_type='item_login_error',
        cur_step=action_endpoint,
        approval_record=[],
        recid=None,
        links=None,
        term_and_condition_content='',
        is_auto_set_index_action=is_auto_set_index_action,
        application_item_type=False,
        auto_fill_title=auto_fill_title(item_type_name),
        auto_fill_data_type=activity_detail.extra_info.get(
            "related_title") if activity_detail.extra_info else None,
        is_show_autofill_metadata=is_show_autofill_metadata(
            item_type_name),
        is_hidden_pubdate=is_hidden_pubdate(item_type_name),
        position_list=WEKO_USERPROFILES_POSITION_LIST,
        institute_position_list=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST,
        item_type_name=item_type_name,
        res_check=1,
        action_id=action_id,
        activity=activity_detail,
        histories=histories,
        item=item,
        steps=steps,
        temporary_comment=temporary_comment,
        workflow_detail=workflow_detail,
        user_profile=user_profile,
        list_license=get_list_licence(),
        cur_action=cur_action,
        activity_id=activity_detail.activity_id,
        is_enable_item_name_link=is_enable_item_name_link(
            action_endpoint, item_type_name),
        enable_feedback_maillist=current_app.config[
            'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
        enable_contributor=current_app.config[
            'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
        out_put_report_title=current_app.config[
            "WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE"],
        action_endpoint_key=current_app.config.get(
            'WEKO_ITEMS_UI_ACTION_ENDPOINT_KEY'),
        approval_email_key=get_approval_keys(),
        step_item_login_url=step_item_login_url,
        need_file=need_file,
        need_billing_file=need_billing_file,
        records=record,
        record=[],
        jsonschema=json_schema,
        schemaform=schema_form,
        item_save_uri=item_save_uri,
        files=files,
        endpoints=endpoints,
        need_thumbnail=need_thumbnail,
        files_thumbnail=files_thumbnail,
        allow_multi_thumbnail=allow_multi_thumbnail,
        id=workflow_detail.itemtype_id,
    )


def prepare_data_for_guest_activity(activity_id: str) -> dict:
    """Prepare for guest activity.

    @param activity_id:
    @return:
    """
    ctx = {'community': None}
    getargs = request.args
    community_id = ""
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(getargs.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

    init_data = __init_activity_detail_data_for_guest(
        activity_id, community_id)
    ctx.update(init_data)
    action_endpoint = ctx['cur_step']
    activity_detail = ctx['activity']
    cur_action = ctx['cur_action']

    if 'item_login' == action_endpoint or \
        'item_login_application' == action_endpoint or \
            'file_upload' == action_endpoint:
        ctx['res_check'] = 0
        if request.method == 'POST':
            is_user_agreed = request.form.get('checked')
            if is_user_agreed == "on":
                # update user agreement when user check the checkbox
                WorkActivity().upt_activity_agreement_step(
                    activity_id=activity_id, is_agree=True)

        ctx['application_item_type'] = is_usage_application_item_type(
            activity_detail)
        item_type_name = ctx['item_type_name']

        if current_app.config['WEKO_WORKFLOW_ENABLE_SHOWING_TERM_OF_USE'] and \
                cur_action.action_is_need_agree:
            # if this is Item Registration step and the user have not agreed
            # term and condition yet, set to that page
            from weko_items_ui.utils import is_need_to_show_agreement_page
            if is_need_to_show_agreement_page(item_type_name) and \
                    not activity_detail.activity_confirm_term_of_use:
                ctx['step_item_login_url'] = 'weko_workflow/' \
                                             'term_and_condition.html'
                ctx['term_and_condition_content'] = \
                    get_term_and_condition_content(item_type_name)
        # Get approval record
        item = get_items_metadata_by_activity_detail(activity_detail)
        approval_record = []
        if item:
            _, approval_record = get_pid_and_record(item.id)
        # be use for index tree and comment page.
        session['itemlogin_item'] = ctx['item']
        session['itemlogin_steps'] = ctx['steps']
        session['itemlogin_action_id'] = ctx['action_id']
        session['itemlogin_cur_step'] = ctx['cur_step']
        session['itemlogin_record'] = approval_record
        session['itemlogin_histories'] = ctx['histories']
        session['itemlogin_res_check'] = ctx['res_check']
        session['itemlogin_pid'] = ctx['recid']
        session['itemlogin_community_id'] = community_id

    return ctx


def recursive_get_specified_properties(properties):
    """Recursive get specified properties.

    :param properties:
    :return:
    """
    if not properties:
        return None
    if "items" in properties:
        for item in properties["items"]:
            if item.get("approval"):
                return item.get("key")
            else:
                result = recursive_get_specified_properties(item)
                if result:
                    return result


def get_approval_keys():
    """Get approval keys.

    :return:
    """
    from weko_records.models import ItemTypeProperty
    result = ItemTypeProperty.query.filter_by(delflg=False).all()
    approval_keys = []
    for value in result:
        properties = value.form
        if properties:
            result = recursive_get_specified_properties(properties)
            if result:
                approval_keys.append(result)
    return approval_keys


def process_send_mail(mail_info, mail_pattern_name):
    """Send mail approval rejected.

    :mail_info: object
    """
    if not mail_info.get("mail_recipient"):
        current_app.logger.error('Mail address is not defined')
        return

    subject, body = get_mail_data(mail_pattern_name)
    if body and subject:
        body = replace_characters(mail_info, body)
        return send_mail(subject, mail_info['mail_recipient'], body)


def cancel_expired_usage_reports():
    """Cancel expired usage reports."""
    expired_activities = GuestActivity.get_expired_activities()
    if expired_activities:
        WorkActivity().cancel_usage_report_activities(expired_activities)


def process_send_approval_mails(activity_detail, actions_mail_setting,
                                next_step_appover_id, file_data):
    """Process send mail for approval steps.

    :param activity_detail:
    :param actions_mail_setting:
    :param next_step_appover_id:
    :param file_data:
    :return:
    """
    is_guest_user = True if activity_detail.extra_info.get(
        'guest_mail') else False
    item_info = get_item_info(activity_detail.item_id)
    mail_info = set_mail_info(item_info, activity_detail, is_guest_user)
    mail_info['restricted_download_link'] = file_data.get("file_url", '')
    mail_info['restricted_expiration_date'] = file_data.get(
        "expiration_date", '')
    mail_info['restricted_expiration_date_ja'] = file_data.get(
        "expiration_date_ja", '')
    mail_info['restricted_expiration_date_en'] = file_data.get(
        "expiration_date_en", '')

    # Override guest mail if any
    if is_guest_user:
        mail_info['mail_recipient'] = activity_detail.extra_info.get(
            'guest_mail')

    if actions_mail_setting["approval"]:
        if actions_mail_setting.get("previous", {}).get(
                "inform_approval", False):
            process_send_mail(
                mail_info,
                current_app.config["WEKO_WORKFLOW_APPROVE_DONE"])

        if actions_mail_setting.get('next', {}).get("request_approval", False):
            approval_user = None
            if next_step_appover_id :
                approval_user = db.session.query(User).filter_by(
                    id=int(next_step_appover_id)).first()
            if not approval_user:
                current_app.logger.error("Does not have approval data")
            else:
                mail_info['mail_recipient'] = approval_user.email
            process_send_mail(
                mail_info,
                current_app.config["WEKO_WORKFLOW_REQUEST_APPROVAL"])

    if actions_mail_setting["reject"]:
        if actions_mail_setting.get(
                "previous", {}).get("inform_reject", False):
            process_send_mail(
                mail_info,
                current_app.config["WEKO_WORKFLOW_APPROVE_REJECTED"])


def get_usage_data(item_type_id, activity_detail, user_profile=None):
    """Get usage data.

    @param item_type_id: Item Type identifier.
    @param activity_detail: Activity detail
    @param user_profile: User profile.
    @return:
    """
    def __build_metadata_for_usage_report(record_data: Union[dict, list],
                                          usage_report_data: dict):
        if isinstance(record_data, dict):
            for k, v in record_data.items():
                if k in usage_report_data_key:
                    usage_report_data[usage_report_data_key[k]] = v
                else:
                    __build_metadata_for_usage_report(v, usage_report_data)
        elif isinstance(record_data, list):
            for data in record_data:
                __build_metadata_for_usage_report(data, usage_report_data)
    result = {}
    extra_info = activity_detail.extra_info
    if not extra_info:
        return result

    cfg = current_app.config
    wf_issued_date = activity_detail.created.strftime("%Y-%m-%d")

    if item_type_id in cfg.get(
            'WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TYPES_LIST'):
        if isinstance(user_profile, dict):
            mail_address = user_profile.get(
                'results').get('subitem_mail_address')
        else:
            mail_address = extra_info.get('guest_mail', '')

        related_title = str(extra_info.get('related_title', ''))
        item_title = cfg.get('WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TITLE') \
            + activity_detail.created.strftime("%Y%m%d") \
            + str(related_title) + '_'

        result = dict(
            usage_type='Application',
            dataset_usage=related_title,
            usage_data_name='',
            mail_address=mail_address,
            university_institution='',
            affiliated_division_department='',
            position='',
            position_other='',
            phone_number='',
            usage_report_id='',
            wf_issued_date=wf_issued_date,
            item_title=item_title
        )
    elif item_type_id in cfg.get('WEKO_WORKFLOW_USAGE_REPORT_ITEM_TYPES_LIST'):
        usage_record_id = extra_info.get('usage_record_id')
        usage_report_data_key = {
            "subitem_restricted_access_name": "usage_data_name",
            "subitem_restricted_access_mail_address": "mail_address",
            "subitem_restricted_access_university/institution":
                "university_institution",
            "subitem_restricted_access_affiliated_division/department":
                "affiliated_division_department",
            "subitem_restricted_access_position": "position",
            "subitem_restricted_access_position(others)": "position_other",
            "subitem_restricted_access_phone_number": "phone_number",
        }
        result = dict(
            usage_type='Report',
            dataset_usage='',
            usage_data_name='',
            mail_address='',
            university_institution='',
            affiliated_division_department='',
            position='',
            position_other='',
            phone_number='',
            usage_report_id=activity_detail.activity_id,
            wf_issued_date=wf_issued_date,
            item_title=''
        )
        related_activity_id = extra_info.get('usage_activity_id')
        if not related_activity_id:
            return result

        rm = RecordMetadata.query.filter_by(id=usage_record_id).first()
        if not rm:
            return result
        __build_metadata_for_usage_report(rm.json, result)
        result['dataset_usage'] = rm.json.get('item_title')
        result['item_title'] = related_activity_id + cfg.get(
            'WEKO_WORKFLOW_USAGE_REPORT_ITEM_TITLE') + result['usage_data_name']

    return result


def update_approval_date(activity):
    """Update approval date.

    @param activity:
    @return:
    """
    item_id = activity.item_id
    record = WekoRecord.get_record(item_id)
    deposit = WekoDeposit(record, record.model)
    if deposit.get("item_type_id") not in \
        WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TYPES_LIST \
            + WEKO_WORKFLOW_USAGE_REPORT_ITEM_TYPES_LIST:
        return
    approval_date_key = current_app.config[
        'WEKO_WORKFLOW_RESTRICTED_ACCESS_APPROVAL_DATE']
    sub_approval_date_key, attribute_name = \
        get_sub_key_by_system_property_key(approval_date_key,
                                           deposit.get("item_type_id"))
    if sub_approval_date_key:
        current_date = get_current_date()
        dict_approval_date = {
            approval_date_key: current_date,
            'subitem_restricted_access_approval_date_type': "Accepted"
        }
        update_approval_date_for_deposit(deposit, sub_approval_date_key,
                                         dict_approval_date,
                                         attribute_name)
        update_system_data_for_item_metadata(item_id,
                                             sub_approval_date_key,
                                             dict_approval_date)
        update_system_data_for_activity(activity,
                                        sub_approval_date_key,
                                        dict_approval_date)


def create_record_metadata_for_user(usage_application_activity, usage_report):
    """Update metadata usage application for usage report.

    @param usage_report:
    @param usage_application_activity:
    @return:
    """
    item_id = usage_application_activity.item_id
    if item_id and usage_report:
        record = WekoRecord.get_record(item_id)
        deposit = WekoDeposit(record, record.model)
        usage_report_id_key = current_app.config[
            'WEKO_WORKFLOW_RESTRICTED_ACCESS_USAGE_REPORT_ID']
        sub_system_data_key, attribute_name = \
            get_sub_key_by_system_property_key(usage_report_id_key,
                                               deposit.get("item_type_id"))
        if sub_system_data_key:
            dict_system_data = {usage_report_id_key: usage_report.activity_id}
            deposit_without_ver, item_id_without_ver = get_record_first_version(
                deposit)
            if item_id_without_ver:
                update_system_data_for_item_metadata(
                    item_id_without_ver,
                    sub_system_data_key,
                    dict_system_data)
                update_approval_date_for_deposit(deposit_without_ver,
                                                 sub_system_data_key,
                                                 dict_system_data,
                                                 attribute_name)
            update_system_data_for_item_metadata(item_id,
                                                 sub_system_data_key,
                                                 dict_system_data)
            update_approval_date_for_deposit(deposit,
                                             sub_system_data_key,
                                             dict_system_data,
                                             attribute_name)
            update_system_data_for_activity(usage_application_activity,
                                            sub_system_data_key,
                                            dict_system_data)


def get_current_date():
    """Get current date.

    @return:
    """
    return datetime.today().strftime('%Y-%m-%d')


def get_sub_key_by_system_property_key(system_property_key, item_type_id):
    """Get sub key by system property key.

    @param system_property_key:
    @param item_type_id:
    @return:
    """
    if not item_type_id:
        return None, None
    item_type = ItemType.query.filter_by(id=item_type_id).one_or_none()
    sub_key = ''
    attribute_name = ''
    if not item_type:
        return sub_key, attribute_name
    for k, v in item_type.schema['properties'].items():
        if isinstance(v, dict) and 'properties' in v and system_property_key \
                in v['properties']:
            sub_key = k
            if 'title' in v:
                attribute_name = v['title']
            break
    return sub_key, attribute_name


def update_system_data_for_item_metadata(item_id, sub_system_data_key,
                                         dict_system_data):
    """Update approval date for item metadata.

    @param item_id:
    @param sub_system_data_key:
    @param dict_system_data:
    @return:
    """
    item_meta = ItemsMetadata.get_record(id_=item_id)
    item_meta[sub_system_data_key] = dict_system_data
    item_meta.commit()
    db.session.commit()


def update_approval_date_for_deposit(deposit, sub_approval_date_key,
                                     dict_approval_date, attribute_name):
    """Update approval date for deposit.

    @param deposit:
    @param sub_approval_date_key:
    @param dict_approval_date:
    @param attribute_name:
    @return:
    """
    approval_date_data = {'attribute_name': attribute_name,
                          "attribute_value_mlt": [dict_approval_date]}
    deposit[sub_approval_date_key] = approval_date_data
    deposit.item_metadata[sub_approval_date_key] = dict_approval_date
    deposit.commit()
    db.session.commit()


def update_system_data_for_activity(activity, sub_system_data_key,
                                    dict_system_data):
    """Update approval date for activity.

    @param activity:
    @param sub_system_data_key:
    @param dict_system_data:
    @return:
    """
    if activity:
        if activity.temp_data:
            temp = json.loads(activity.temp_data)
        else:
            temp = {'metainfo': {}}
        temp['metainfo'][sub_system_data_key] = dict_system_data
        activity.temp_data = json.dumps(temp)
        db.session.merge(activity)
        db.session.commit()


def check_authority_by_admin(activity, user=None):
    """Check authority by admin.

    :param activity:
    :return:
    """
    # If user has admin role
    user = user or current_user
    supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
    for role in list(user.roles or []):
        if role.name in supers:
            return True
    # If user has community role
    # and the user who created activity is member of community
    # role -> has permission:
    community_role_names = current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY']
    for community_role_name in community_role_names:
        # Get the list of users who has the community role
        community_users = User.query.outerjoin(userrole).outerjoin(Role) \
            .filter(community_role_name == Role.name) \
            .filter(userrole.c.role_id == Role.id) \
            .filter(User.id == userrole.c.user_id) \
            .all()
        community_user_ids = [
            community_user.id for community_user in community_users]
        for role in list(user.roles or []):
            if role.name in community_role_name:
                # User has community role
                if activity.activity_login_user in community_user_ids:
                    return True
                break
    return False


def get_record_first_version(deposit):
    """Get PID of record first version ID."""
    pid_value = str(int(float(deposit['_deposit']['id'])))
    pid = PersistentIdentifier.query.filter_by(
        pid_value=pid_value, pid_type='recid').first()
    record = WekoRecord.get_record(pid.object_uuid)
    deposit = WekoDeposit(record, record.model)
    return deposit, pid.object_uuid


def get_files_and_thumbnail(activity_id, item_id):
    """Get files and thumbnail from activity id.

    Args:
        activity_id: The activity identifier.
        item_id:  Item uuid.
    """
    from weko_items_ui.utils import to_files_js
    files, files_thumbnail = [], []
    deposit = WekoDeposit.get_record(item_id)
    activity = WorkActivity()
    metadata = activity.get_activity_metadata(activity_id)
    # Load files from metadata.
    if metadata:
        item_json = json.loads(metadata)
        files = item_json.get('files') if item_json.get('files') else []
    # Load files from deposit.
    if deposit and not files:
        files = to_files_js(deposit)
    # Load files thumbnail from files.
    if files and not files_thumbnail:
        files_thumbnail = [i for i in files
                           if 'is_thumbnail' in i.keys()
                           and i['is_thumbnail']]
    return files, files_thumbnail


def get_pid_and_record(item_id):
    """
    get_pid_and_record Get record data for the first time access to editing item screen.

    Args:
        item_id (_type_): id of Item metadata.

    Returns:
        _type_: A tuple containing (pid, object).

    Raises:
        invenio_pidstore.errors.PIDDoesNotExistError: if no PID is found.
        invenio_pidstore.errors.PIDDeletedError: if PID is deleted.
    """
    recid = PersistentIdentifier.get_by_object(
        pid_type='recid', object_type='rec', object_uuid=item_id)
    record_class = import_string('weko_deposit.api:WekoRecord')
    resolver = Resolver(pid_type='recid', object_type='rec',
                        getter=record_class.get_record)
    return resolver.resolve(recid.pid_value)


def get_items_metadata_by_activity_detail(activity_detail):
    """Get item metadata from activity id.

    Args:
        activity_detail:Activity detail.
    """
    item = None
    if activity_detail and activity_detail.item_id:
        try:
            item = ItemsMetadata.get_record(id_=activity_detail.item_id)
        except NoResultFound as ex:
            current_app.logger.exception(str(ex))
            item = None
    return item


def get_main_record_detail(activity_id,
                           activity_detail,
                           action_endpoint=None,
                           item=None,
                           approval_record=None,
                           files=None,
                           files_thumbnail=None):
    """Get item link record, files, thumbnail.

    Args:
        activity_id: Activity identifier.
        activity_detail: Activity detail.
        action_endpoint: Action endpoint.
        item: Item metadata.
        approval_record: Approval record.
        files: File content
        files_thumbnail: Thumbnail file.
    """
    def check_record(record):
        return record and len(record) > 0 and isinstance(record, (list, dict))

    recid = None
    action_endpoint = action_endpoint or activity_detail.action.action_endpoint
    if not item:
        if not isinstance(approval_record, dict) \
                or not approval_record.get('item_type_id'):
            return dict(
                record=list(),
                files=list(),
                files_thumbnail=list())
        else:
            item = get_items_metadata_by_activity_detail(activity_detail)
    if item and not approval_record:
        recid, approval_record = get_pid_and_record(item.id)
    if item and not files:
        files, files_thumbnail = get_files_and_thumbnail(activity_id, item.id)

    record_metadata = []
    item_type_id = approval_record.get('item_type_id')
    new_files = []
    new_thumbnail = []
    pid = item.get('pid')

    # case create item
    if item and item.get('pid', {}).get('value') and action_endpoint:
        # case when edit item and step is item_login
        if action_endpoint == 'item_login':
            pid_value = item['pid']['value']
            record_metadata, new_files = get_record_by_root_ver(pid_value)
            allow_multi_thumbnails = get_allow_multi_thumbnail(
                item_type_id,
                activity_id)
            new_thumbnail = get_thumbnails(new_files, allow_multi_thumbnails)
        else:
            # case when edit item and step # item_login
            if activity_detail.item_id:
                new_files = deepcopy(files)
                record_metadata, new_files = get_record_by_root_ver(
                    item['pid']['value'])
                item['title'] = record_metadata['title'][0]
                multi_thumbnail = get_allow_multi_thumbnail(item_type_id,
                                                            activity_id)
                new_thumbnail = get_thumbnails(new_files, multi_thumbnail)
                if check_record(approval_record) and new_files:
                    new_files = set_files_display_type(
                        record_metadata,
                        new_files)
    else:
        record_metadata = approval_record
        new_files = deepcopy(files)

        allow_multi_thumbnails = \
            get_allow_multi_thumbnail(item_type_id, activity_id)
        new_thumbnail = get_thumbnails(new_files, allow_multi_thumbnails)

        if not new_thumbnail:
            new_thumbnail = files_thumbnail
        pid = recid

    if check_record(record_metadata) and new_files:
        set_files_display_type(record_metadata, new_files)

    return dict(
        record=record_metadata,
        files=new_files,
        files_thumbnail=new_thumbnail,
        pid=pid)


def prepare_doi_link_workflow(item_id, doi_input):
    """Parsing DOI link from storing data.

    Args:
        item_id: Record identifier number.
        doi_input: DOI input from last Identifier Setting.
    """
    data = request.get_json() or {}
    community_id = data['community'] if data.get('community') else 'Root Index'
    identifier_setting = get_identifier_setting(community_id)
    ret = {}

    current_app.logger.debug('item_id: {0}'.format(item_id))
    current_app.logger.debug('doi_input: {0}'.format(doi_input))
    current_app.logger.debug('data: {0}'.format(data))
    current_app.logger.debug('community_id: {0}'.format(community_id))
    current_app.logger.debug(
        'identifier_setting: {0}'.format(identifier_setting))

    # valid date pidstore_identifier data
    if identifier_setting:
        text_empty = '<Empty>'
        if not identifier_setting.jalc_doi:
            identifier_setting.jalc_doi = text_empty
        if not identifier_setting.jalc_crossref_doi:
            identifier_setting.jalc_crossref_doi = text_empty
        if not identifier_setting.jalc_datacite_doi:
            identifier_setting.jalc_datacite_doi = text_empty
        if not identifier_setting.ndl_jalc_doi:
            identifier_setting.ndl_jalc_doi = text_empty
        # Semi-automatic suffix
        suffix_method = current_app.config.get(
            'IDENTIFIER_GRANT_SUFFIX_METHOD', IDENTIFIER_GRANT_SUFFIX_METHOD)
        if not identifier_setting.suffix:
            identifier_setting.suffix = ''

        current_app.logger.debug(
            'suffix_method: {0}'.format(suffix_method))

        if suffix_method == 0:
            url_format = '{}/{}/{}'
            _item_id = '%010d' % int(item_id)
            _jalc_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[1][2],
                identifier_setting.jalc_doi,
                _item_id)
            _jalc_cr_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[2][2],
                identifier_setting.jalc_crossref_doi,
                _item_id)
            _jalc_dc_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[3][2],
                identifier_setting.jalc_datacite_doi,
                _item_id)
        elif suffix_method == 1:
            url_format = '{}/{}/{}{}'
            _jalc_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[1][2],
                identifier_setting.jalc_doi,
                identifier_setting.suffix,
                doi_input.get('action_identifier_jalc_doi'))
            _jalc_cr_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[2][2],
                identifier_setting.jalc_crossref_doi,
                identifier_setting.suffix,
                doi_input.get('action_identifier_jalc_cr_doi'))
            _jalc_dc_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[3][2],
                identifier_setting.jalc_datacite_doi,
                identifier_setting.suffix,
                doi_input.get('action_identifier_jalc_dc_doi'))
        elif suffix_method == 2:
            url_format = '{}/{}/{}'
            _jalc_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[1][2],
                identifier_setting.jalc_doi,
                doi_input.get('action_identifier_jalc_doi'))
            _jalc_cr_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[2][2],
                identifier_setting.jalc_crossref_doi,
                doi_input.get('action_identifier_jalc_cr_doi'))
            _jalc_dc_doi_link = url_format.format(
                IDENTIFIER_GRANT_LIST[3][2],
                identifier_setting.jalc_datacite_doi,
                doi_input.get('action_identifier_jalc_dc_doi'))
        _ndl_jalc_doi_link = '{}/{}/{}'.format(
            IDENTIFIER_GRANT_LIST[4][2],
            identifier_setting.ndl_jalc_doi,
            doi_input.get('action_identifier_ndl_jalc_doi'))

        ret = {
            'identifier_grant_jalc_doi_link': _jalc_doi_link,
            'identifier_grant_jalc_cr_doi_link': _jalc_cr_doi_link,
            'identifier_grant_jalc_dc_doi_link': _jalc_dc_doi_link,
            'identifier_grant_ndl_jalc_doi_link': _ndl_jalc_doi_link
        }

    return ret


def get_pid_value_by_activity_detail(activity_detail):
    """Get pid_value by activity detail.

    Args:
        activity_detail: Activity detail.
    """
    if activity_detail.temp_data:
        temp_data = json.loads(activity_detail.temp_data)
        if temp_data.get('endpoints', {}).get('self', ''):
            self_list = temp_data.get('endpoints').get('self', '').split('/')

            if len(self_list) > 0:
                return self_list[-1]
            else:
                return ''


def check_doi_validation_not_pass(item_id, activity_id,
                                  identifier_select, without_ver_id=None):
    """Call DOI validation and save error cache."""
    error_list = item_metadata_validation(item_id, identifier_select,
                                          without_ver_id=without_ver_id)
    if isinstance(error_list, str):
        return error_list

    redis_connection = RedisConnection()
    sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)

    if error_list:
        sessionstore.put(
            'updated_json_schema_{}'.format(activity_id),
            json.dumps(error_list).encode('utf-8'),
            ttl_secs=300)
        return True
    else:
        if sessionstore.redis.exists(
                'updated_json_schema_{}'.format(activity_id)):
            sessionstore.delete(
                'updated_json_schema_{}'.format(activity_id))
        return False

def make_activitylog_tsv(activities):
    """make tsv for activitiy_log

    Args:
        activities: activities for download as tsv.
    """
    import csv
    from io import StringIO
    file_output = StringIO()

    keys = current_app.config.get("WEKO_WORKFLOW_ACTIVITYLOG_XLS_COLUMNS")

    writer = csv.writer(file_output, delimiter="\t", lineterminator="\n")
    writer.writerow(keys)
    for item in activities:
        term = []
        for name in keys:
            term.append(getattr(item,name))
        writer.writerow(term)

    return file_output.getvalue()


def make_activitylog_tsv(activities):
    """make tsv for activitiy_log

    Args:
        activities: activities for download as tsv.
    """
    import csv
    from io import StringIO
    file_output = StringIO()

    keys = current_app.config.get("WEKO_WORKFLOW_ACTIVITYLOG_XLS_COLUMNS")

    writer = csv.writer(file_output, delimiter="\t", lineterminator="\n")
    writer.writerow(keys)
    for item in activities:
        term = []
        for name in keys:
            term.append(getattr(item,name))
        writer.writerow(term)

    return file_output.getvalue()


def is_terms_of_use_only(workflow_id :int) -> bool:
    """
    return true if the workflow is [terms_of_use_only(利用規約のみ)]

    note:
        [terms of use only] workflow is open_restricted flag is "true".
        and
        [terms of use only] workflow is structed "Begin Action" and "End Action" only.

    Args
        int :workflow_id
    Return
        bool :is the workflow [terms of use only]
    """

    current_app.logger.info(workflow_id)
    ids = [workflow_id]

    wf:_WorkFlow = WorkFlow().get_workflow_by_ids(ids)
    current_app.logger.info(wf)
    if wf[0].open_restricted :
        fa :list[FlowAction] =Flow().get_flow_action_list(wf[0].flow_id)
        if len(fa) == 2 :
            #begin action and end action
            return True
    return False

def grant_access_rights_to_all_open_restricted_files(activity_id :str ,permission:Union[FilePermission,GuestActivity] , activity_detail :Activity) -> dict:
    """
    Target all of open_restricted files in the item , grant access rights for login user.
    or
    Target a open_restricted file that is applyed by the guest user  in the item , grant access rights for guest user.

    Args:
        str :activity_id
        FilePermission :permission
        Activity :activity_detail
    Returns
        dict :one time url and expired_date
    """
    url_and_expired_date:dict = {}
    if isinstance(permission ,FilePermission): #contributer
        files = WekoRecord.get_record_by_pid(permission.record_id).get_file_data()
        for file in files:
            #{'url': {'url': 'https://weko3.example.org/record/1/files/aaa (1).txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2023-02-03'}], 'terms': 'term_free', 'format': 'text/plain', 'provide': [{'role': 'none_loggin', 'workflow': '2'}, {'role': '3', 'workflow': '1'}], 'version': '1', 'dataType': 'perfectures', 'filename': 'aaa (1).txt', 'filesize': [{'value': '5 B'}], 'mimetype': 'text/plain', 'accessrole': 'open_restricted', 'version_id': '2a0aa15b-d3e2-4846-9e3a-e1e734a1a620', 'displaytype': 'simple', 'licensefree': 'licence text', 'licensetype': 'license_free', 'termsDescription': '利用規約のフリーインプット本文です'}
            if file['accessrole'] in 'open_restricted':

                if file['filename'] != permission.file_name:
                    # create all open_restricted content records in unapplyed
                    FilePermission.init_file_permission(permission.user_id, permission.record_id, file['filename'], activity_id)

                #insert file_onetime_download
                extra_info:dict = deepcopy(activity_detail.extra_info)
                extra_info.update({'file_name' : file['filename']})
                tmp:dict = create_onetime_download_url_to_guest(activity_detail.activity_id,extra_info)

                if file['filename'] == permission.file_name:
                    # a applyed content.
                    url_and_expired_date = tmp

        # approve all open_restricted contents.
        permissions = FilePermission.find_by_activity(activity_id)
        for permi in permissions:
            FilePermission.update_status(permi,1) #1:Approval

    elif isinstance(permission,GuestActivity): #guest user

        #insert file_onetime_download
        extra_info:dict = deepcopy(activity_detail.extra_info)
        # extra_info.update({'file_name' : permission.file_name})
        tmp:dict = create_onetime_download_url_to_guest(activity_detail.activity_id,extra_info)

        url_and_expired_date = tmp

    #url_and_expired_date of a applyed content.
    return url_and_expired_date

def delete_lock_activity_cache(activity_id, data):
    """Delete lock activity cache.

    Args:
        activity_id (str): The activity identifier.
        data (dict): Data containing the locked value.

    Returns:
        str: Message indicating the result of the unlock operation.
    """
    cache_key = 'workflow_locked_activity_{}'.format(activity_id)
    locked_value = str(data.get('locked_value'))
    msg = None
    cur_locked_val = str(get_cache_data(cache_key)) or str()
    if cur_locked_val and cur_locked_val == locked_value:
        delete_cache_data(cache_key)
        msg = _('Unlock success')
    return msg

def delete_user_lock_activity_cache(activity_id, data):
    cache_key = "workflow_userlock_activity_{}".format(str(current_user.get_id()))
    cur_locked_val = str(get_cache_data(cache_key)) or str()
    msg = _("Not unlock")

    if cur_locked_val and not data["is_opened"] or (cur_locked_val == activity_id and data['is_force']):
        delete_cache_data(cache_key)
        msg = "User Unlock Success"
    return msg

def check_pretty(pretty):
    """
    Check request parameter pretty.

    :param pretty: boolean of string type.
    """
    if pretty.lower() in WEKO_STR_TRUE:
        current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    else:
        current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False


def convert_to_timezone(dt, user_timezone=None):
    """
    Convert a datetime object to the specified timezone.

    Args:
        dt (datetime): The datetime object to convert.
        user_timezone (str): The timezone string (e.g., 'Asia/Tokyo').

    Returns:
        datetime: The converted datetime object.
    """
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    if user_timezone:
        timezone = pytz.timezone(user_timezone)
        dt = dt.astimezone(timezone)
    return dt


def load_template(template_name, language=None):
    """Load the specified email template.

    Args:
        template_name (str): The name of the template file.
        language (str, optional): The language code for the template (e.g., 'en', 'ja').

    Returns:
        dict: A dictionary containing the email template with the following keys:
            - 'subject' (str): The subject line of the email template.
            - 'body' (str): The body content of the email template.

    Raises:
        FileNotFoundError: If the template file does not exist in the specified directory.
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(
                    current_path,
                    'templates',
                    'weko_workflow',
                    'email_templates')
    if language is None:
        language = "en"
    template_path = os.path.join(folder_path, template_name.format(language=language))
    if not os.path.exists(template_path):
        template_path = os.path.join(folder_path, template_name.format(language="en"))
    with open(template_path, "r") as file:
        lines = file.readlines()
    # The first line is the subject, and the rest is the body.
    subject = lines[0].strip() if lines else ""
    body = "".join(lines[1:]).strip() if len(lines) > 1 else ""
    return {"subject": subject, "body": body}


def fill_template(template, data):
    """
    Embed data into the template.

    Args:
        template (dict): email template with the following keys:
            - 'subject' (str): The subject template of the email.
            - 'body' (str): The body template of the email.
        data (dict): data to replace placeholders in the template.

    Returns:
        dict: generated email content with the following keys:
            - 'subject' (str): The subject of the email after embedding the data.
            - 'body' (str): The body of the email after embedding the data.
    """
    subject = template["subject"]
    body = template["body"]

    for key, value in data.items():
        subject = subject.replace(f"{{{{ {key} }}}}", str(value))
        body = body.replace(f"{{{{ {key} }}}}", str(value))

    return {"subject": subject, "body": body}


def check_activity_settings(settings=None):
    """Check activity setting."""
    if settings is None:
        settings = AdminSettings.get('activity_display_settings',dict_to_object=False)
    if settings is not None:
        if isinstance(settings,dict):
            if 'activity_display_flg' in settings:
                current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] = settings['activity_display_flg']
        else:
            if hasattr(settings,'activity_display_flg'):
                current_app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] = settings.activity_display_flg
