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

from copy import deepcopy

from flask import current_app, request
from flask_babelex import gettext as _
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier, \
    PIDDoesNotExistError, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from sqlalchemy.exc import SQLAlchemyError
from weko_admin.models import Identifier
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_handle.api import Handle
from weko_index_tree.models import Index
from weko_records.api import FeedbackMailList, ItemsMetadata, ItemTypes, \
    Mapping
from weko_records.serializers.utils import get_mapping
from weko_search_ui.config import WEKO_IMPORT_DOI_TYPE
from weko_user_profiles.utils import get_user_profile_info

from weko_workflow.config import IDENTIFIER_GRANT_LIST

from .api import UpdateItem, WorkActivity
from .config import IDENTIFIER_GRANT_SELECT_DICT, WEKO_SERVER_CNRI_HOST_LINK
from .models import Action as _Action


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
    """Check prefix/suffiex in Identifier Registration contain in Identifier.

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
        """Initilize pagination."""
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
        """Initilize IdentifierHandle."""
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

        Arguments:

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
