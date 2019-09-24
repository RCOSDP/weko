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
from invenio_communities.models import Community
from invenio_db import db
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier, PIDAlreadyExists, \
    PIDDoesNotExistError, PIDStatus
from invenio_records.api import Record
from weko_admin.models import Identifier
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_handle.api import Handle
from weko_records.api import ItemsMetadata, ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping

from weko_workflow.config import IDENTIFIER_GRANT_LIST

from .api import WorkActivity
from .config import IDENTIFIER_GRANT_CAN_WITHDRAW, \
    IDENTIFIER_GRANT_SELECT_DICT, IDENTIFIER_ITEMSMETADATA_KEY, \
    WEKO_SERVER_CNRI_HOST_LINK


def get_identifier_setting(community_id):
    """
    Get Identifier Setting of current Community.

    :param community_id: Community Identifier
    :return: Dict or None
    """
    with db.session.no_autoflush:
        return Identifier.query.filter_by(
            repository=community_id).one_or_none()


def saving_doi_pidstore(data=None, doi_select=0, activity_id='0'):
    """
    Mapp doi pidstore data to ItemMetadata.

    :param data: request data
    :param doi_select: identifier selected
    :param activity_id: activity id number
    """
    activity_obj = WorkActivity()
    activity_detail = activity_obj.get_activity_detail(activity_id)
    identifier = IdentifierHandle(activity_detail.item_id)

    flag_del_pidstore = False
    identifier_val = ''
    identifier_typ = ''
    doi_register_val = ''
    doi_register_typ = ''

    if doi_select == IDENTIFIER_GRANT_LIST[1][0] and data.get(
            'identifier_grant_jalc_doi_link'):
        jalcdoi_link = data.get('identifier_grant_jalc_doi_link')
        jalcdoi_tail = (jalcdoi_link.split('//')[1]).split('/')
        identifier_val = jalcdoi_link
        identifier_typ = 'DOI'
        doi_register_val = '/'.join(jalcdoi_tail[1:])
        doi_register_typ = 'JaLC'
    elif doi_select == IDENTIFIER_GRANT_LIST[2][0] and data.get(
            'identifier_grant_jalc_cr_doi_link'):
        jalcdoi_cr_link = data.get('identifier_grant_jalc_cr_doi_link')
        jalcdoi_cr_tail = (jalcdoi_cr_link.split('//')[1]).split('/')
        identifier_val = jalcdoi_cr_link
        identifier_typ = 'DOI'
        doi_register_val = '/'.join(jalcdoi_cr_tail[1:])
        doi_register_typ = 'Crossref'
    elif doi_select == IDENTIFIER_GRANT_LIST[3][0] and data.get(
            'identifier_grant_jalc_dc_doi_link'):
        jalcdoi_dc_link = data.get('identifier_grant_jalc_dc_doi_link')
        jalcdoi_dc_tail = (jalcdoi_dc_link.split('//')[1]).split('/')
        identifier_val = jalcdoi_dc_link
        identifier_typ = 'DOI'
        doi_register_val = '/'.join(jalcdoi_dc_tail[1:])
        doi_register_typ = 'DataCite'
    else:
        current_app.logger.error(_('Identifier datas are empty!'))

    try:
        if not flag_del_pidstore and identifier_val and doi_register_val:
            reg = identifier.register_pidstore('doi', identifier_val)

            if reg:
                identifier.update_identifier_data(identifier_val,
                                                  identifier_typ)
                identifier.update_identifier_regist_data(doi_register_val,
                                                         doi_register_typ)
    except Exception as ex:
        current_app.logger.exception(str(ex))


def is_withdrawn_doi(doi_link):
    """
    Get doi was withdrawn.

    :param: doi_link
    :return: True/False
    """
    try:
        link_doi = doi_link['doi_link']
        query = PersistentIdentifier.query.filter_by(
            pid_value=link_doi, status=PIDStatus.DELETED)
        return query.count() > 0
    except PIDDoesNotExistError as pidNotEx:
        current_app.logger.error(pidNotEx)
        return False


def find_doi(doi_link):
    """
    Get doi has been register by another item.

    :param: doi_link
    :return: True/False
    """
    is_existed = False
    try:
        link_doi = doi_link['doi_link']
        pid_identifiers = PersistentIdentifier.query.filter_by(
            pid_type='doi', object_type='rec',
            pid_value=link_doi, status=PIDStatus.REGISTERED).all()
        for pid_identifier in pid_identifiers:
            if pid_identifier.pid_value == link_doi:
                is_existed = True
        return is_existed
    except PIDDoesNotExistError as pidNotEx:
        current_app.logger.error(pidNotEx)
        return is_existed


def register_cnri(activity_id):
    """
    Register CNRI with Persistent Identifiers.

    :param activity_id: Workflow Activity Identifier
    :return cnri_pidstore: CNRI pidstore object or None
    """
    activity = WorkActivity().get_activity_detail(activity_id)
    item_uuid = activity.item_id
    record = WekoRecord.get_record(item_uuid)

    deposit_id = record.get('_deposit')['id']
    record_url = request.url.split('/workflow/')[0] \
        + '/records/' + str(deposit_id)

    weko_handle = Handle()
    handle = weko_handle.register_handle(location=record_url)

    if handle:
        handle = WEKO_SERVER_CNRI_HOST_LINK + str(handle)
        identifier = IdentifierHandle(item_uuid)
        reg = identifier.register_pidstore('cnri', handle)

        if reg:
            identifier.update_identifier_data(handle, 'HDL')
    else:
        current_app.logger.error('Cannot connect Handle server!')


def item_metadata_validation(item_id, identifier_type):
    """
    Validate item metadata.

    :param: item_id, identifier_type
    :return: error_list
    """
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
        return None

    journalarticle_nameid = [14, 3, 5, 9]
    journalarticle_type = 'other（プレプリント）'
    thesis_nameid = 12
    report_nameid = 16
    report_types = ['technical report', 'research report', 'report']
    elearning_type = 'learning material'
    dataset_nameid = [22, 4]
    dataset_type = 'software'
    datageneral_nameid = [13, 17, 18, 19, 20, 21, 1, 10]
    datageneral_types = ['internal report', 'policy report', 'report part',
                         'working paper', 'interactive resource',
                         'musical notation', 'research proposal',
                         'technical documentation',
                         'workflow', 'その他（その他）']

    metadata_item = MappingData(item_id)
    item_type = metadata_item.get_data_item_type()
    resource_type, type_key = metadata_item.get_data_by_property("type.@value")
    type_check = check_required_data(resource_type, type_key)

    # check resource type request
    if not resource_type and not type_key:
        return 'Resource Type Property either missing ' \
            'or jpcoar mapping not correct!'
    if not item_type or not resource_type and type_check:
        error_list = {'required': [], 'pattern': [], 'types': [], 'doi': ''}
        error_list['required'].append(type_key)
        return error_list
    resource_type = resource_type.pop()

    # JaLC DOI identifier registration
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['JaLCDOI']:
        # 別表2-1 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
        # 別表2-2 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【学位論文】
        # 別表2-3 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【書籍】
        # 別表2-4 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【e-learning】
        # 別表2-6 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【汎用データ】
        if (item_type.name_id in journalarticle_nameid
            or resource_type == journalarticle_type) \
            or (item_type.name_id == thesis_nameid) \
            or (item_type.name_id == report_nameid
                or resource_type in report_types) \
            or (resource_type == elearning_type) \
            or (item_type.name_id in datageneral_nameid
                or resource_type in datageneral_types):
            properties = ['title',
                          'identifier',
                          'identifierRegistration']
            error_list = validation_item_property(metadata_item,
                                                  identifier_type,
                                                  properties)
        # 別表2-5 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【研究データ】
        elif item_type.name_id in dataset_nameid or resource_type == \
                dataset_type:
            properties = ['title',
                          'givenName',
                          'identifier',
                          'identifierRegistration']
            error_list = validation_item_property(metadata_item,
                                                  identifier_type,
                                                  properties)
        else:
            error_list = 'false'
    # CrossRef DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['CrossRefDOI']:
        if item_type.name_id in journalarticle_nameid or resource_type == \
                journalarticle_type:
            properties = ['title',
                          'identifier',
                          'publisher',
                          'identifierRegistration',
                          'sourceIdentifier',
                          'sourceTitle']
            error_list = validation_item_property(metadata_item,
                                                  identifier_type,
                                                  properties)
        elif item_type.name_id in [thesis_nameid, report_nameid] or \
                resource_type in report_types:
            properties = ['title',
                          'identifier',
                          'identifierRegistration']
            error_list = validation_item_property(metadata_item,
                                                  identifier_type,
                                                  properties)
        else:
            error_list = 'false'
    else:
        error_list = 'false'

    if error_list == 'false':
        return _('Cannot register selected DOI for current Item Type of this '
                 'item.')

    return error_list


def validation_item_property(mapping_data, identifier_type, properties):
    """
    Validate item property.

    :param mapping_data: Mapping Data contain record and item_map
    :param identifier_type: Selected identifier
    :param properties: Property's keywords
    :return: error_list or None
    """
    error_list = {'required': [], 'pattern': [], 'types': [], 'doi': ''}
    empty_list = deepcopy(error_list)
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
        creators = mapping_data.record.get(key.split('.')[0])
        for creator in creators.get("attribute_value_mlt"):
            for subitem in creator:
                for item in creator[subitem]:
                    if item.get(key.split('.')[1]):
                        data.append(item.get(key.split('.')[1]))

        repeatable = True
        requirements = check_required_data(data, key, repeatable)
        if requirements:
            error_list['pattern'] += requirements

    # check 識別子 jpcoar:identifier
    if 'identifier' in properties:
        data, key = mapping_data.get_data_by_property("identifier.@value")
        type_data, type_key = mapping_data.get_data_by_property(
            "identifier.@attributes.identifierType")

        repeatable = True
        requirements = check_required_data(data, key, repeatable)
        type_requirements = check_required_data(type_data,
                                                type_key,
                                                repeatable)
        if requirements:
            error_list['required'] += requirements
        if type_requirements:
            error_list['required'] += type_requirements
        else:
            for item in type_data:
                if item not in ['HDL', 'URI', 'DOI']:
                    error_list['required'].append(type_key)

    # check ID登録 jpcoar:identifierRegistration
    if 'identifierRegistration' in properties:
        data, key = mapping_data.get_data_by_property(
            "identifierRegistration.@value")
        type_data, type_key = mapping_data.get_data_by_property(
            "identifierRegistration.@attributes.identifierType")

        requirements = check_required_data(data, key)
        type_requirements = check_required_data(type_data, type_key)
        if requirements and not requirements == [None]:
            error_list['required'] += requirements
        # half-with and special character check
        # else:
        #     for item in data:
        #         char_re = re.compile(r'[^a-zA-Z0-9\-\.\_\;\(\)\/.]')
        #         result = char_re.search(item)
        #         if bool(result):
        #             error_list['pattern'].append(key)
        if type_requirements and not type_requirements == [None]:
            error_list['required'] += type_requirements
        else:
            if type_data:
                for item in type_data:
                    if (identifier_type
                            == IDENTIFIER_GRANT_SELECT_DICT['JaLCDOI']
                            and not item == 'JaLC') or \
                            (identifier_type
                             == IDENTIFIER_GRANT_SELECT_DICT['CrossRefDOI']
                             and not item == 'Crossref'):
                        error_list['required'].append(type_key)

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
            for attr in attribute.get('attribute_value_mlt'):
                data.append(attr.get(key.split('.')[1]))
        return data, key


class IdentifierHandle(object):
    """Get Community Info."""

    item_uuid = ''
    item_type_id = None
    item_record = None
    item_metadata = None
    metadata_mapping = None

    def __init__(self, item_id):
        """Initilize pagination."""
        self.item_uuid = item_id
        self.metadata_mapping = MappingData(item_id)
        self.item_type_id = self.metadata_mapping.get_data_item_type().id
        self.item_metadata = ItemsMetadata.get_record(item_id)
        self.item_record = self.metadata_mapping.record

    def get_pistore(self, pid_type='doi', object_uuid=None):
        """Get Persistent Identifier Object by pid_value or item_uuid.

        Arguments:
            pid_type     -- {string} data list

        Returns:
            dict -- error message

        """
        if not object_uuid:
            object_uuid = self.item_uuid
        with db.session.no_autoflush:
            doi_pidstore = PersistentIdentifier.query.filter_by(
                        pid_type=pid_type,
                        object_uuid=object_uuid).all()
            if not doi_pidstore:
                current_pid = PersistentIdentifier.get_by_object(
                    pid_type='recid',
                    object_type='rec',
                    object_uuid=object_uuid
                )
                child = PIDRelation.query.filter_by(
                    child_id=current_pid.id).one_or_none()
                if child and child.parent:
                    parent = PersistentIdentifier.get(
                        'recid',
                        child.parent.pid_value.split('/')[1])
                    doi_pidstore = self.get_pistore(pid_type, parent.object_uuid)

            if pid_type == 'doi' and isinstance(doi_pidstore, array):
                doi_pidstore = doi_pidstore[0]
            return doi_pidstore

    def check_pidstore_exist(self, pid_type, chk_value=None):
        """Get Persistent Identifier Object by pid_value or item_uuid.

        Arguments:
            pid_type     -- {string} data list
            search_value -- {string} is sending feedback

        Returns:
            dict -- error message

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
        """Get Persistent Identifier Object by pid_value or item_uuid.

        Arguments:
            pid_type     -- {string} data list
            search_value -- {string} is sending feedback

        Returns:
            dict -- error message

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
            else:
                return False
        except Exception as ex:
            current_app.logger.error(ex)
            return False

    def delete_doi_pidstore_status(self, pid_value=None):
        """Get Persistent Identifier Object by pid_value or item_uuid.

        Arguments:
            pid_value -- {string} data list

        Returns:
            dict -- error message

        """
        try:
            if not pid_value:
                pid_value = self.get_pistore().pid_value
            doi_pidstore = self.check_pidstore_exist('doi', pid_value)

            if doi_pidstore and doi_pidstore.status == PIDStatus.REGISTERED:
                doi_pidstore.delete()

                permalink_uri = ''
                cnri_datas = self.get_pistore('cnri')
                if cnri_datas:
                    permalink_uri = cnri_datas[-1]
                metadata_data = {
                    'permalink': permalink_uri
                }
                with db.session.begin_nested():
                    self.item_metadata.update(metadata_data)
                    self.item_metadata.commit()
                db.session.commit()
                return doi_pidstore.status == PIDStatus.DELETED
            return False
        except PIDDoesNotExistError as pidNotEx:
            current_app.logger.error(pidNotEx)
            return False
        except Exception as ex:
            current_app.logger.error(ex)
            return False

    def update_identifier_data(self, input_value, input_type):
        """Get Persistent Identifier Object by pid_value or item_uuid.

        Arguments:
            pid_value -- {string} data list

        Returns:
            dict -- error message

        """
        _, key_value = self.metadata_mapping.get_data_by_property(
            "identifier.@value")
        _, key_type = self.metadata_mapping.get_data_by_property(
            "identifier.@attributes.identifierType")

        try:
            self.commit(key_id=key_value.split('.')[0],
                        key_val=key_value.split('.')[1],
                        key_typ=key_type.split('.')[1],
                        atr_nam='Identifier',
                        atr_val=input_value,
                        atr_typ=input_type
                        )
        except Exception as pidNotEx:
            current_app.logger.error(pidNotEx)
            db.session.rollback()

    def update_identifier_regist_data(self, input_value, input_type):
        """Get Persistent Identifier Object by pid_value or item_uuid.

        Arguments:
            pid_value -- {string} data list

        Returns:
            dict -- error message

        """
        _, key_value = self.metadata_mapping.get_data_by_property(
            "identifierRegistration.@value")
        _, key_type = self.metadata_mapping.get_data_by_property(
            "identifierRegistration.@attributes.identifierType")

        try:
            self.commit(key_id=key_value.split('.')[0],
                        key_val=key_value.split('.')[1],
                        key_typ=key_type.split('.')[1],
                        atr_nam='Identifier Registration',
                        atr_val=input_value,
                        atr_typ=input_type
                        )
        except Exception as pidNotEx:
            current_app.logger.error(pidNotEx)
            db.session.rollback()

    def commit(self, key_id, key_val, key_typ, atr_nam, atr_val, atr_typ):
        """Get Persistent Identifier Object by pid_value or item_uuid.

        Arguments:
            pid_value -- {string} data list

        Returns:
            dict -- error message

        """
        item_type_obj = ItemTypes.get_by_id(self.item_type_id)
        option = item_type_obj.render.get('meta_list', {})\
            .get(key_id, {}).get('option')

        multi_option = None
        if option:
            multi_option = option.get('multiple')

        data = self.item_record.get(key_id)

        if not data:
            record_data = {
                key_id: {
                    "attribute_name": atr_nam,
                    "attribute_value_mlt": [
                        {
                            key_val: atr_val,
                            key_typ: atr_typ
                        }
                    ]
                }
            }
        else:
            if multi_option:
                data['attribute_value_mlt'].append({
                    key_val: atr_val,
                    key_typ: atr_typ
                })
            else:
                data['attribute_value_mlt'] = [{
                    key_val: atr_val,
                    key_typ: atr_typ
                }]
            record_data = {
                key_id: data
            }

        metadata_data = self.item_metadata.get(key_id, [])
        if atr_nam == 'Identifier':
            metadata_data.append({
                key_val: atr_val,
                key_typ: atr_typ
            })
            metadata_data = {
                key_id: metadata_data,
                'permalink': atr_val
            }
        elif atr_nam == 'Identifier Registration':
            metadata_data = {
                key_id: {
                    key_val: atr_val,
                    key_typ: atr_typ
                }
            }

        with db.session.begin_nested():
            self.item_metadata.update(metadata_data)
            self.item_metadata.commit()
            self.item_record.update(record_data)
            self.item_record.commit()
        db.session.commit()
