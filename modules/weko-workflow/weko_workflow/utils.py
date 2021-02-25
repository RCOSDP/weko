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
import os
from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import NoReturn, Tuple, Union

from flask import current_app, request, session
from flask_babelex import gettext as _
from flask_security import current_user
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_i18n.ext import current_i18n
from invenio_mail.admin import MailSettingView
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier, \
    PIDDoesNotExistError, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from passlib.handlers.oracle import oracle10
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from weko_admin.models import Identifier
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_handle.api import Handle
from weko_index_tree.models import Index
from weko_records.api import FeedbackMailList, ItemsMetadata, ItemTypeNames, \
    ItemTypes, Mapping
from weko_records.serializers.utils import get_item_type_name, get_mapping
from weko_records_ui.utils import get_list_licence
from weko_search_ui.config import WEKO_IMPORT_DOI_TYPE
from weko_user_profiles.config import WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_POSITION_LIST
from weko_user_profiles.utils import get_user_profile_info

from weko_workflow.config import IDENTIFIER_GRANT_LIST, \
    IDENTIFIER_GRANT_SUFFIX_METHOD

from .api import GetCommunity, UpdateItem, WorkActivity, WorkActivityHistory, \
    WorkFlow
from .config import IDENTIFIER_GRANT_SELECT_DICT, WEKO_SERVER_CNRI_HOST_LINK
from .models import Action as _Action
from .models import ActionStatusPolicy, ActivityStatusPolicy, GuestActivity


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


def saving_doi_pidstore(item_id, record_without_version, data=None,
                        doi_select=0, is_feature_import=False):
    """
    Mapp doi pidstore data to ItemMetadata.

    :param data: request data
    :param doi_select: identifier selected
    :param item_id: object uuid
    :param record_without_version: object uuid
    """
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
    elif is_feature_import and doi_select == IDENTIFIER_GRANT_LIST[4][0] \
            and data.get('identifier_grant_ndl_jalc_doi_link'):
        ndljalcdoi_dc_link = data.get('identifier_grant_ndl_jalc_doi_link')
        ndljalcdoi_dc_tail = (ndljalcdoi_dc_link.split('//')[1]).split('/')
        identifier_val = ndljalcdoi_dc_link
        doi_register_val = '/'.join(ndljalcdoi_dc_tail[1:])
        doi_register_typ = 'NDL JaLC'
    else:
        current_app.logger.error(_('Identifier datas are empty!'))

    try:
        if not flag_del_pidstore and identifier_val and doi_register_val:
            identifier = IdentifierHandle(record_without_version)
            reg = identifier.register_pidstore('doi', identifier_val)
            identifier.update_idt_registration_metadata(doi_register_val,
                                                        doi_register_typ)

            if reg:
                identifier = IdentifierHandle(item_id)
                identifier.update_idt_registration_metadata(doi_register_val,
                                                            doi_register_typ)
            update_indexes_public_state(item_id)
            current_app.logger.info(_('DOI successfully registered!'))
    except Exception as ex:
        current_app.logger.exception(str(ex))


def register_hdl(activity_id):
    """
    Register HDL into Persistent Identifiers.

    :param activity_id: Workflow Activity Identifier
    :return cnri_pidstore: HDL pidstore object or None
    """
    activity = WorkActivity().get_activity_detail(activity_id)
    item_uuid = activity.item_id
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

    return handle


def register_hdl_by_handle(handle, item_uuid):
    """
    Register HDL into Persistent Identifiers.

    :param handle: HDL handle
    :param item_uuid: Item uuid
    """
    if handle:
        handle = WEKO_SERVER_CNRI_HOST_LINK + str(handle)
        identifier = IdentifierHandle(item_uuid)
        identifier.register_pidstore('hdl', handle)


def item_metadata_validation(item_id, identifier_type):
    """
    Validate item metadata.

    :param: item_id, identifier_type
    :return: error_list
    """
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
        return None

    ddi_item_type_name = 'DDI'
    journalarticle_type = ['other（プレプリント）', 'conference paper',
                           'data paper', 'departmental bulletin paper',
                           'editorial', 'journal article', 'periodical',
                           'review article', 'article']
    thesis_types = ['thesis', 'bachelor thesis', 'master thesis',
                    'doctoral thesis']
    report_types = ['technical report', 'research report', 'report',
                    'book', 'book part']
    elearning_type = ['learning material']
    dataset_type = ['software', 'dataset']
    datageneral_types = ['internal report', 'policy report', 'report part',
                         'working paper', 'interactive resource',
                         'musical notation', 'research proposal',
                         'technical documentation', 'workflow',
                         'その他（その他）', 'sound', 'patent',
                         'cartographic material', 'map', 'lecture', 'image',
                         'still image', 'moving image', 'video',
                         'conference object', 'conference proceedings',
                         'conference poster']

    metadata_item = MappingData(item_id)
    item_type = metadata_item.get_data_item_type()
    resource_type, type_key = metadata_item.get_data_by_property("type.@value")
    type_check = check_required_data(resource_type, type_key)

    # check resource type request
    if not resource_type and not type_key:
        return {
            'required': [],
            'pattern': [],
            'either': [],
            'pmid': '',
            'doi': '',
            'url': '',
            "msg": 'Resource Type Property either missing '
                   'or jpcoar mapping not correct!',
            'error_type': 'no_resource_type'
        }

    if not item_type or not resource_type and type_check:
        error_list = {'required': [], 'pattern': [], 'pmid': '',
                      'doi': '', 'url': '', 'either': []}
        error_list['required'].append(type_key)
        return error_list
    resource_type = resource_type.pop()
    properties = {}
    # 必須
    required_properties = []
    # いずれか必須
    either_properties = []

    # JaLC DOI identifier registration
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['JaLCDOI']:
        # 別表2-1 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
        # 別表2-3 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【書籍】
        # 別表2-4 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【e-learning】
        # 別表2-6 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【汎用データ】
        if resource_type in journalarticle_type \
                or resource_type in report_types \
                or (resource_type in elearning_type) \
                or resource_type in datageneral_types:
            required_properties = ['title']
            if item_type.item_type_name.name != ddi_item_type_name:
                required_properties.append('fileURI')
        # 別表2-2 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【学位論文】
        elif resource_type in thesis_types:
            required_properties = ['title',
                                   'creator']
            if item_type.item_type_name.name != ddi_item_type_name:
                required_properties.append('fileURI')
        # 別表2-5 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【研究データ】
        elif resource_type in dataset_type:
            required_properties = ['title',
                                   'givenName']
            if item_type.item_type_name.name != ddi_item_type_name:
                required_properties.append('fileURI')
            either_properties = ['geoLocationPoint',
                                 'geoLocationBox',
                                 'geoLocationPlace']
    # CrossRef DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['CrossRefDOI']:
        if resource_type in journalarticle_type:
            required_properties = ['title',
                                   'publisher',
                                   'sourceIdentifier',
                                   'sourceTitle']
            if item_type.item_type_name.name != ddi_item_type_name:
                required_properties.append('fileURI')
        elif resource_type in report_types:
            required_properties = ['title']
            if item_type.item_type_name.name != ddi_item_type_name:
                required_properties.append('fileURI')
        elif resource_type in thesis_types:
            required_properties = ['title',
                                   'creator']
            if item_type.item_type_name.name != ddi_item_type_name:
                required_properties.append('fileURI')
    # DataCite DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['DataCiteDOI'] \
            and item_type.item_type_name.name != ddi_item_type_name:
        required_properties = ['fileURI']
    # NDL JaLC DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['NDLJaLCDOI'] \
            and item_type.item_type_name.name != ddi_item_type_name:
        required_properties = ['fileURI']

    if required_properties:
        properties['required'] = required_properties
    if either_properties:
        properties['either'] = either_properties

    if properties and \
            identifier_type != IDENTIFIER_GRANT_SELECT_DICT['DataCiteDOI'] \
            and identifier_type != IDENTIFIER_GRANT_SELECT_DICT['NDLJaLCDOI']:
        return validation_item_property(metadata_item, properties)
    else:
        return _('Cannot register selected DOI for current Item Type of this '
                 'item.')


def validation_item_property(mapping_data, properties):
    """
    Validate item property.

    :param mapping_data: Mapping Data contain record and item_map
    :param properties: Property's keywords
    :return: error_list or None
    """
    error_list = {'required': [], 'pattern': [], 'pmid': '',
                  'doi': '', 'url': '', 'either': []}
    empty_list = deepcopy(error_list)

    if properties.get('required'):
        error_list_required = validattion_item_property_required(
            mapping_data, properties['required'])
        if error_list_required:
            error_list['required'] = error_list_required['required']
            error_list['pattern'] = error_list_required['pattern']

    if properties.get('either'):
        error_list_either = validattion_item_property_either_required(
            mapping_data, properties['either'])
        if error_list_either:
            error_list['either'] = error_list_either

    if error_list == empty_list:
        return None
    else:
        return error_list


def validattion_item_property_required(
        mapping_data, properties):
    """
    Validate item property is required.

    :param mapping_data: Mapping Data contain record and item_map
    :param properties: Property's keywords
    :return: error_list or None
    """
    error_list = {'required': [], 'pattern': []}
    empty_list = deepcopy(error_list)
    # check jpcoar:URI
    if 'fileURI' in properties:
        _, key = mapping_data.get_data_by_property(
            "file.URI.@value")
        data = []
        if key:
            key = key.split('.')[0]
            item_file = mapping_data.record.get(key)
            if item_file:
                file_name_data = get_sub_item_value(
                    item_file.get("attribute_value_mlt"), 'filename')
                if file_name_data:
                    for value in file_name_data:
                        data.append(value)
                data.append(file_name_data)

            repeatable = True
            requirements = check_required_data(
                data, key + '.filename', repeatable)
            if requirements:
                error_list['required'] += requirements
    # check タイトル dc:title
    if 'title' in properties:
        title_data, title_key = mapping_data.get_data_by_property(
            "title.@value")
        lang_data, lang_key = mapping_data.get_data_by_property(
            "title.@attributes.xml:lang")

        repeatable = True
        requirements = check_required_data(title_data, title_key, repeatable)
        lang_requirements = check_required_data(lang_data,
                                                lang_key,
                                                repeatable)
        if requirements:
            error_list['required'] += requirements
        if lang_requirements:
            error_list['required'] += lang_requirements

    # check 識別子 jpcoar:givenName
    if 'givenName' in properties:
        _, key = mapping_data.get_data_by_property(
            "creator.givenName.@value")
        data = []
        if key:
            creators = mapping_data.record.get(key.split('.')[0])
            if creators:
                given_name_data = get_sub_item_value(
                    creators.get("attribute_value_mlt"), key.split('.')[-1])
                if given_name_data:
                    for value in given_name_data:
                        data.append(value)
                data.append(given_name_data)

        repeatable = True
        requirements = check_required_data(data, key, repeatable)
        if requirements:
            error_list['pattern'] += requirements

    # check 識別子 jpcoar:givenName and jpcoar:nameIdentifier
    if 'creator' in properties:
        _, key = mapping_data.get_data_by_property(
            "creator.givenName.@value")
        _, idt_key = mapping_data.get_data_by_property(
            "creator.nameIdentifier.@value")

        data = []
        idt_data = []
        creators = mapping_data.record.get(key.split('.')[0])
        if key:
            creator_data = get_sub_item_value(
                creators.get("attribute_value_mlt"),
                key.split('.')[-1])
            if creator_data:
                for value in creator_data:
                    data.append(value)
        if idt_key:
            creator_name_identifier = get_sub_item_value(
                creators.get("attribute_value_mlt"), idt_key.split('.')[-1])
            if creator_name_identifier:
                for value in creator_name_identifier:
                    idt_data.append(value)

        repeatable = True
        requirements = check_required_data(data, key, repeatable)
        repeatable = True
        idt_requirements = check_required_data(idt_data, idt_key, repeatable)
        if requirements and idt_requirements:
            error_list['pattern'] += requirements
            error_list['pattern'] += idt_requirements

    # check 収録物識別子 jpcoar:sourceIdentifier
    if 'sourceIdentifier' in properties:
        data, key = mapping_data.get_data_by_property(
            "sourceIdentifier.@value")
        type_data, type_key = mapping_data.get_data_by_property(
            "sourceIdentifier.@attributes.identifierType")

        requirements = check_required_data(data, key)
        type_requirements = check_required_data(type_data, type_key)
        if requirements:
            error_list['required'] += requirements
        if type_requirements:
            error_list['required'] += type_requirements

    # check 収録物名 jpcoar:sourceTitle
    if 'sourceTitle' in properties:
        data, key = mapping_data.get_data_by_property("sourceTitle.@value")
        lang_data, lang_key = mapping_data.get_data_by_property(
            "sourceTitle.@attributes.xml:lang")

        requirements = check_required_data(data, key)
        lang_requirements = check_required_data(lang_data, lang_key)
        if requirements:
            error_list['required'] += requirements
        if lang_requirements:
            error_list['required'] += lang_requirements
        else:
            if 'en' not in lang_data:
                error_list['required'].append(lang_key)

    # check 収録物名 dc:publisher
    if 'publisher' in properties:
        data, key = mapping_data.get_data_by_property("publisher.@value")
        lang_data, lang_key = mapping_data.get_data_by_property(
            "publisher.@attributes.xml:lang")

        repeatable = True
        requirements = check_required_data(data, key, repeatable)
        lang_requirements = check_required_data(lang_data,
                                                lang_key,
                                                repeatable)
        if requirements:
            error_list['required'] += requirements
        if lang_requirements:
            error_list['required'] += lang_requirements
        else:
            if 'en' not in lang_data:
                error_list['required'].append(lang_key)

    if error_list == empty_list:
        return None
    else:
        error_list['required'] = list(
            set(filter(None, error_list['required']))
        )
        error_list['pattern'] = list(set(filter(None, error_list['pattern'])))
        return error_list


def validattion_item_property_either_required(
        mapping_data, properties):
    """
    Validate item property is either required.

    :param mapping_data: Mapping Data contain record and item_map
    :param properties: Property's keywords
    :return: error_list or None
    """
    error_list = []
    # check 位置情報（点） detacite:geoLocationPoint
    if 'geoLocationPoint' in properties:
        latitude_data, latitude_key = mapping_data.get_data_by_property(
            "geoLocation.geoLocationPoint.pointLatitude.@value")
        longitude_data, longitude_key = mapping_data.get_data_by_property(
            "geoLocation.geoLocationPoint.pointLongitude.@value")

        repeatable = True
        requirements = []
        latitude_requirement = check_required_data(
            latitude_data, latitude_key, repeatable)
        if latitude_requirement:
            requirements += latitude_requirement

        longitude_requirement = check_required_data(
            longitude_data, longitude_key, repeatable)
        if longitude_requirement:
            requirements += longitude_requirement

        if not requirements:
            return None
        else:
            requirements = list(filter(None, requirements))
            error_list.append(requirements)

    # check 位置情報（空間） datacite:geoLocationBox
    if 'geoLocationBox' in properties:
        east_data, east_key = mapping_data.get_data_by_property(
            "geoLocation.geoLocationBox.eastBoundLongitude.@value")
        north_data, north_key = mapping_data.get_data_by_property(
            "geoLocation.geoLocationBox.northBoundLatitude.@value")
        south_data, south_key = mapping_data.get_data_by_property(
            "geoLocation.geoLocationBox.southBoundLatitude.@value")
        west_data, west_key = mapping_data.get_data_by_property(
            "geoLocation.geoLocationBox.westBoundLongitude.@value")

        repeatable = True
        requirements = []
        east_requirement = check_required_data(
            east_data, east_key, repeatable)
        if east_requirement:
            requirements += east_requirement

        north_requirement = check_required_data(
            north_data, north_key, repeatable)
        if north_requirement:
            requirements += north_requirement

        south_requirement = check_required_data(
            south_data, south_key, repeatable)
        if south_requirement:
            requirements += south_requirement

        west_requirement = check_required_data(
            west_data, west_key, repeatable)
        if west_requirement:
            requirements += west_requirement

        if not requirements:
            return None
        else:
            requirements = list(filter(None, requirements))
            error_list.append(requirements)

    # check 位置情報（自由記述） datacite:geoLocationPlace
    if 'geoLocationPlace' in properties:
        data, key = mapping_data.get_data_by_property(
            "geoLocation.geoLocationPlace.@value")

        repeatable = True
        requirements = check_required_data(data, key, repeatable)
        if not requirements:
            return None
        else:
            error_list += requirements

    error_list = list(filter(None, error_list))
    if error_list:
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
        return error_list


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

    def __init__(self, item_id):
        """Initialize pagination."""
        self.record = WekoRecord.get_record(item_id)
        item_type = self.get_data_item_type()
        item_type_mapping = Mapping.get_record(item_type.id)
        self.item_map = get_mapping(item_type_mapping, "jpcoar_mapping")

    def get_data_item_type(self):
        """Return item type data."""
        return ItemTypes.get_by_id(id_=self.record.get('item_type_id'))

    def get_data_by_property(self, item_property):
        """
        Get data by property text.

        :param item_property: property value in item_map
        :return: error_list or None
        """
        key = self.item_map.get(item_property)
        data = []
        if not key:
            current_app.logger.error(str(item_property) + ' jpcoar:mapping '
                                                          'is not correct')
            return None, None
        attribute = self.record.get(key.split('.')[0])
        if not attribute:
            return None, key
        else:
            data_result = get_sub_item_value(
                attribute.get('attribute_value_mlt'), key.split('.')[-1])
            if data_result:
                for value in data_result:
                    data.append(value)
        return data, key


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
            if not pid_value:
                pid_value = self.get_pidstore().pid_value
            doi_pidstore = self.check_pidstore_exist('doi', pid_value)

            if doi_pidstore and doi_pidstore.status == PIDStatus.REGISTERED:
                doi_pidstore.delete()
                self.remove_idt_registration_metadata()
                return doi_pidstore.status == PIDStatus.DELETED
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
        _, key_value = self.metadata_mapping.get_data_by_property(
            "identifierRegistration.@value")
        key_id = key_value.split('.')[0]
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
        _, key_value = self.metadata_mapping.get_data_by_property(
            "identifierRegistration.@value")
        _, key_type = self.metadata_mapping.get_data_by_property(
            "identifierRegistration.@attributes.identifierType")

        self.commit(key_id=key_value.split('.')[0],
                    key_val=key_value.split('.')[1],
                    key_typ=key_type.split('.')[1],
                    atr_nam='Identifier Registration',
                    atr_val=input_value,
                    atr_typ=input_type
                    )

    def get_idt_registration_data(self):
        """Get Identifier Registration data.

        Returns:
            doi_value -- {string} Identifier
            doi_type  -- {string} Identifier type

        """
        doi_value, _ = self.metadata_mapping.get_data_by_property(
            "identifierRegistration.@value")
        doi_type, _ = self.metadata_mapping.get_data_by_property(
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
            ).one_or_none()
            return pid_object
    except PIDDoesNotExistError as pid_not_exist:
        current_app.logger.error(pid_not_exist)
        return None


def filter_all_condition(all_args):
    """
    Filter conditions.

    :param all_args:
    :return:
    """
    conditions = {}
    list_key_condition = current_app.config.get('WEKO_WORKFLOW_FILTER_PARAMS',
                                                [])
    for args in all_args:
        for key in list_key_condition:
            if key in args:
                filter_condition(conditions, key, request.args.get(args))
    return conditions


def filter_condition(json, name, condition):
    """
    Add conditions to json object.

    :param json:
    :param name:
    :param condition:
    :return:
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
    post_workflow = post_activity['post_workflow']
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
    else:
        # Clone org bucket into draft record.
        with db.session.begin_nested():
            drf_deposit = WekoDeposit.get_record(draft_pid.object_uuid)
            cur_deposit = WekoDeposit.get_record(recid.object_uuid)
            cur_bucket = cur_deposit.files.bucket
            bucket = Bucket.get(drf_deposit.files.bucket.id)

            sync_bucket = RecordsBuckets.query.filter_by(
                bucket_id=drf_deposit.files.bucket.id
            ).first()
            snapshot = cur_bucket.snapshot(lock=False)
            snapshot.locked = False
            bucket.locked = False

            sync_bucket.bucket_id = snapshot.id
            drf_deposit['_buckets']['deposit'] = str(snapshot.id)
            bucket.remove()
            drf_deposit.commit()
            db.session.add(sync_bucket)
        db.session.commit()
        rtn = activity.init_activity(post_activity,
                                     community,
                                     draft_pid.object_uuid)

    if rtn:
        # GOTO: TEMPORARY EDIT MODE FOR IDENTIFIER
        identifier_actionid = get_actionid('identifier_grant')
        if post_workflow:
            identifier = activity.get_action_identifier_grant(
                post_workflow.activity_id, identifier_actionid)
        else:
            identifier = activity.get_action_identifier_grant(
                '', identifier_actionid)

        if not identifier:
            identifier_handle = IdentifierHandle(recid.object_uuid)
            doi_value, doi_type = identifier_handle.get_idt_registration_data()
            if doi_value and doi_type:
                identifier = {
                    'action_identifier_select':
                        WEKO_IMPORT_DOI_TYPE.index(doi_type[0]) + 1,
                    'action_identifier_jalc_doi': '',
                    'action_identifier_jalc_cr_doi': '',
                    'action_identifier_jalc_dc_doi': '',
                    'action_identifier_ndl_jalc_doi': ''
                }

        if identifier:
            if identifier.get('action_identifier_select') > \
                current_app.config.get(
                    "WEKO_WORKFLOW_IDENTIFIER_GRANT_DOI", 0):
                identifier['action_identifier_select'] = \
                    current_app.config.get(
                        "WEKO_WORKFLOW_IDENTIFIER_GRANT_CAN_WITHDRAW", -1)
            elif identifier.get('action_identifier_select') == \
                current_app.config.get(
                    "WEKO_WORKFLOW_IDENTIFIER_GRANT_IS_WITHDRAWING", -2):
                identifier['action_identifier_select'] = \
                    current_app.config.get(
                        "WEKO_WORKFLOW_IDENTIFIER_GRANT_WITHDRAWN", -3)
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
    try:
        combine_record_file_urls(deposit)
        pid_without_ver = get_record_without_version(current_pid)
        if ".0" in current_pid.pid_value:
            deposit.commit()
        deposit.publish()
        updated_item = UpdateItem()
        # publish record without version ID when registering newly
        if recid:
            # new record attached version ID
            new_deposit = deposit.newversion(current_pid)
            item_id = new_deposit.model.id
            ver_attaching_deposit = WekoDeposit(
                new_deposit,
                new_deposit.model)
            combine_record_file_urls(ver_attaching_deposit)
            feedback_mail_list = FeedbackMailList.get_mail_list_by_item_id(
                pid_without_ver.object_uuid)
            if feedback_mail_list:
                FeedbackMailList.update(
                    item_id=item_id,
                    feedback_maillist=feedback_mail_list
                )
                ver_attaching_deposit.update_feedback_mail()
            ver_attaching_deposit.publish()

            weko_record = WekoRecord.get_record_by_pid(current_pid.pid_value)
            if weko_record:
                weko_record.update_item_link(current_pid.pid_value)
            updated_item.publish(deposit)
            updated_item.publish(ver_attaching_deposit)
        else:
            # update to record without version ID when editing
            if pid_without_ver:
                _record = WekoDeposit.get_record(
                    pid_without_ver.object_uuid)
                _deposit = WekoDeposit(_record, _record.model)
                _deposit['path'] = deposit.get('path', [])

                parent_record = _deposit. \
                    merge_data_to_record_without_version(current_pid)
                _deposit.publish()

                pv = PIDVersioning(child=pid_without_ver)
                last_ver = PIDVersioning(parent=pv.parent).get_children(
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
                    new_parent_record = maintain_deposit. \
                        merge_data_to_record_without_version(current_pid)
                    maintain_deposit.publish()
                    combine_record_file_urls(new_parent_record)
                    new_parent_record.update_feedback_mail()
                    new_parent_record.commit()
                    updated_item.publish(new_parent_record)
                else:  # Handle Upgrade workflow
                    draft_pid = PersistentIdentifier.get(
                        'recid',
                        '{}.0'.format(pid_without_ver.pid_value)
                    )
                    draft_deposit = WekoDeposit.get_record(
                        draft_pid.object_uuid)
                    draft_deposit['path'] = deposit.get('path', [])
                    new_draft_record = draft_deposit. \
                        merge_data_to_record_without_version(current_pid)
                    draft_deposit.publish()
                    combine_record_file_urls(new_draft_record)
                    new_draft_record.update_feedback_mail()
                    new_draft_record.commit()
                    updated_item.publish(new_draft_record)

                weko_record = WekoRecord.get_record_by_pid(
                    pid_without_ver.pid_value)
                if weko_record:
                    weko_record.update_item_link(current_pid.pid_value)
                combine_record_file_urls(parent_record)
                parent_record.update_feedback_mail()
                db.session.commit()
                updated_item.publish(parent_record)
                if ".0" in current_pid.pid_value and last_ver:
                    item_id = last_ver.object_uuid
                else:
                    item_id = current_pid.object_uuid
    except Exception as ex:
        db.session.rollback()
        current_app.logger.exception(str(ex))
        return item_id
    return item_id


def delete_cache_data(key: str):
    """Delete cache data.

    :param key: Cache key.
    """
    current_value = current_cache.get(key) or str()
    if current_value:
        current_cache.delete(key)


def update_cache_data(key: str, value: str, timeout=0):
    """Update cache data.

    :param key: Cache key.
    :param value: Cache value.
    """
    if timeout:
        current_cache.set(key, value, timeout=timeout)
    else:
        current_cache.set(key, value)


def get_cache_data(key: str):
    """Get cache data.

    :param key: Cache key.

    :return: Cache value.
    """
    return current_cache.get(key) or str()


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


def combine_record_file_urls(record, meta_prefix='jpcoar'):
    """Add file urls to record metadata.

    Get file property information by item_mapping and put to metadata.
    """
    def check_url_is_manual(version_id):
        for file in record.files.dumps():
            if file.get('version_id') == version_id:
                return False
        return True

    from weko_records.api import Mapping
    from weko_records.serializers.utils import get_mapping

    item_type_id = record.get('item_type_id')
    type_mapping = Mapping.get_record(item_type_id)
    item_map = get_mapping(type_mapping, "{}_mapping".format(meta_prefix))

    file_keys = None
    if item_map:
        file_props = current_app.config["OAISERVER_FILE_PROPS_MAPPING"]
        if meta_prefix in file_props:
            file_keys = item_map.get(file_props[meta_prefix])
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
                    if not (attr[file_keys[1]].get(file_keys[2])
                            and check_url_is_manual(attr.get('version_id'))):
                        attr[file_keys[1]][file_keys[2]] = \
                            create_files_url(
                                request.url_root,
                                record.get('recid'),
                                attr.get('filename'))
        elif isinstance(attr_mlt, dict) and \
                attr_mlt.get('filename'):
            if not attr_mlt.get(file_keys[1]):
                attr_mlt[file_keys[1]] = {}
            if not (attr_mlt[file_keys[1]].get(file_keys[2])
                    and check_url_is_manual(attr_mlt.get('version_id'))):
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


def update_indexes_public_state(item_id):
    """Update indexes public state.

    :param item_id: Item id.

    :return:
    """
    rm = RecordMetadata.query.filter_by(id=item_id).first()
    index_id_list = rm.json['path']
    updated_index_ids = []
    update_db = False
    for index_ids in index_id_list:
        for index_id in index_ids.split('/'):
            if index_id not in updated_index_ids:
                updated_index_ids.append(index_id)
                update_db = True
                index = Index.query.filter_by(id=index_id).first()
                index.public_state = True
    if update_db:
        db.session.commit()


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
        '[19]': 'url_guest_user'
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
    try:
        item = ItemsMetadata.get_record(id_=item_id)
    except Exception as ex:
        current_app.logger.exception('Cannot get item data:', ex)
        temp = dict()
        return temp
    item_info = dict()
    for k, v in item.items():
        if isinstance(v, dict):
            item_info.update(v)
    return item_info


def set_mail_info(item_info, activity_detail):
    """Set main mail info.

    :item_info: object
    :activity_detail: object
    """
    register_user, register_date = \
        get_register_info(activity_detail.activity_id)
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
        output_registration_title=item_info.get('subitem_title')
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
    # Get WF detail
    _workflow_detail = _workflow.get_workflow_by_id(activity_detail.workflow_id)
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
    db.session.commit()
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
    try:
        deposit = WekoDeposit.create({}, recid=int(item_id))
        db.session.commit()
        return deposit
    except Exception:
        db.session.rollback()


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
            WorkActivity().upt_activity_action_status(
                activity_id=activity_id, action_id=action.id,
                action_status=ActionStatusPolicy.ACTION_DOING
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


def init_activity_for_guest_user(data: dict) -> bool:
    """Init activity for guest user.

    @param data:
    @return:
    """
    def _get_guest_activity():
        _guest_activity = {
            "user_mail": guest_mail,
            "record_id": record_id,
            "file_name": file_name,
        }
        return GuestActivity.find(**_guest_activity)

    def _generate_token_value():
        token_pattern = "activity={} file_name={} date={} email={}"
        hash_value = token_pattern.format(activity_id, file_name, activity_date,
                                          guest_mail)
        secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
        token = oracle10.hash(secret_key, hash_value)
        _token_value = "{} {} {} {}".format(activity_id, activity_date,
                                            guest_mail, token)
        _token_value = base64.b64encode(_token_value.encode()).decode()
        return _token_value

    # Get data to generated key
    activity_date = date.today().strftime("%y-%m-%d")
    guest_mail = data.get("extra_info").get("guest_mail")
    file_name = data.get("extra_info").get("file_name")
    record_id = data.get("extra_info").get("record_id")

    guest_activity = _get_guest_activity()
    if not guest_activity:
        # Init activity for guest user.
        activity = WorkActivity().init_activity(data)
        activity_id = activity.activity_id

        # Generate token value
        token_value = _generate_token_value()

        # Save create guest activity
        guest_activity = {
            "user_mail": guest_mail,
            "record_id": record_id,
            "file_name": file_name,
            "activity_id": activity_id,
            "token": token_value
        }
        GuestActivity.create(**guest_activity)
    else:
        token_value = guest_activity[0].token
        activity_id = guest_activity[0].activity_id

    # Generate URL
    url_pattern = "{}workflow/activity/guest-user/{}?token={}"
    url = url_pattern.format(request.url_root, file_name, token_value)

    # Mail information
    mail_info = {
        'template': current_app.config.get("WEKO_WORKFLOW_ACCESS_ACTIVITY_URL"),
        'mail_address': guest_mail,
        'url_guest_user': url
    }
    return send_mail_url_guest_user(mail_info)


def validate_guest_activity(
    token: str, file_name: str
) -> Union[Tuple[bool, None, None], Tuple[bool, str, str]]:
    """Validate guest activity.

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


def send_onetime_download_url_to_guest(activity_id: str,
                                       extra_info: dict) -> bool:
    """Send onetime download URL to guest.

    @param activity_id:
    @param extra_info:
    @return:
    """
    file_name = extra_info.get('file_name')
    record_id = extra_info.get('record_id')
    guest_mail = extra_info.get('guest_mail')
    if file_name and record_id and guest_mail:
        from weko_records_ui.utils import generate_one_time_download_url
        onetime_file_url = generate_one_time_download_url(
            file_name, record_id, guest_mail)

        # Delete guest activity.
        delete_guest_activity(activity_id)

        # Mail information
        mail_info = {
            'template': current_app.config.get(
                "WEKO_WORKFLOW_ACCESS_DOWNLOAD_URL"),
            'mail_address': guest_mail,
            'url_guest_user': onetime_file_url
        }
        return send_mail_url_guest_user(mail_info)


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
    """Get activity.

    @param activity_id:
    @return:
    """
    activity = WorkActivity()
    activity_detail = activity.get_activity_detail(activity_id)
    item = None
    if activity_detail and activity_detail.item_id:
        try:
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
    temporary_comment = activity.get_activity_action_comment(
        activity_id=activity_id, action_id=action_id)
    return action_endpoint, action_id, activity_detail, cur_action, histories, \
        item, steps, temporary_comment, workflow_detail


def __init_activity_detail_data_for_guest(activity_id: str, community_id: str):
    """Init activity data for guest user.

    @param activity_id:
    @param community_id:
    @return:
    """
    action_endpoint, action_id, activity_detail, cur_action, histories, item, \
        steps, temporary_comment, workflow_detail = \
        get_activity_display_info(activity_id)
    item_type_name = get_item_type_name(workflow_detail.itemtype_id)
    # Check auto set index
    is_auto_set_index_action = False
    for step in steps:
        if step.get('ActionEndpoint') == 'item_login_application' \
            and current_app.config[
                'WEKO_WORKFLOW_ENABLE_AUTO_SET_INDEX_FOR_ITEM_TYPE']:
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
        idf_grant_method=IDENTIFIER_GRANT_SUFFIX_METHOD,
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
        approval_email_key=current_app.config.get(
            'WEKO_ITEMS_UI_APPROVAL_MAIL_SUBITEM_KEY'),
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

    init_data = __init_activity_detail_data_for_guest(activity_id, community_id)
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

        # be use for index tree and comment page.
        session['itemlogin_item'] = ctx['item']
        session['itemlogin_steps'] = ctx['steps']
        session['itemlogin_action_id'] = ctx['action_id']
        session['itemlogin_cur_step'] = ctx['cur_step']
        session['itemlogin_record'] = ctx['approval_record']
        session['itemlogin_histories'] = ctx['histories']
        session['itemlogin_res_check'] = ctx['res_check']
        session['itemlogin_pid'] = ctx['recid']
        session['itemlogin_community_id'] = community_id

    return ctx
