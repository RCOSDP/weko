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
from invenio_pidstore.models import PersistentIdentifier, PIDAlreadyExists, \
    PIDDoesNotExistError, PIDStatus
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_handle.api import Handle
from weko_index_tree.models import Index
from weko_records.api import ItemsMetadata, ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping
from weko_admin.models import Identifier

from weko_workflow.config import IDENTIFIER_GRANT_LIST

from .api import WorkActivity
from .config import IDENTIFIER_GRANT_CAN_WITHDRAW, \
    IDENTIFIER_GRANT_SELECT_DICT, IDENTIFIER_ITEMSMETADATA_KEY


def get_identifier_setting(community_id):
    """
    Get Identifier Setting of current Community.

    :param community_id: Community Identifier
    :return: Dict or None
    """
    with db.session.no_autoflush:
        return Identifier.query.filter_by(
            repository=community_id).one_or_none()


def get_community_id_by_index(index_name):
    """
    Get community use indexName input is index_name_english.

    :param index_name: Index Tree's Name
    :return: None or Item Type's info
    """
    communities = Community.query.all()
    ret_community = []
    for community in communities:
        if community.index.index_name == index_name \
                or community.index.index_name_english == index_name:
            ret_community.append(community.id)

    if len(ret_community) > 0:
        return ret_community[0]
    return None


def saving_doi_pidstore(post_json, idf_grant=0, activity_id='0'):
    """
    Mapp doi pidstore data to ItemMetadata.

    :param post_json: request data
    :param idf_grant: identifier selected
    :param activity_id: activity id number
    """
    activity_obj = WorkActivity()
    activity_detail = activity_obj.get_activity_detail(activity_id)
    item = ItemsMetadata.get_record(id_=activity_detail.item_id)

    attrs = IDENTIFIER_ITEMSMETADATA_KEY
    temp_form = {attrs[0]: '',
                 attrs[1]: '',
                 attrs[2]: '',
                 attrs[3]: ''}
    tempdata = deepcopy(temp_form)
    flag_del_pidstore = False
    identifier_value = ''
    identifier_type = ''
    doi_register_val = ''
    doi_register_typ = ''

    if idf_grant == IDENTIFIER_GRANT_LIST[1][0] and post_json.get(
            'identifier_grant_jalc_doi_link'):
        jalcdoi_link = post_json.get('identifier_grant_jalc_doi_link')
        jalcdoi_tail = (jalcdoi_link.split('//')[1]).split('/')
        identifier_value = jalcdoi_link
        identifier_type = 'DOI'
        doi_register_val = '/'.join(jalcdoi_tail[1:])
        doi_register_typ = 'JaLC'
    elif idf_grant == IDENTIFIER_GRANT_LIST[2][0] and post_json.get(
            'identifier_grant_jalc_cr_doi_link'):
        jalcdoi_cr_link = post_json.get('identifier_grant_jalc_cr_doi_link')
        jalcdoi_cr_tail = (jalcdoi_cr_link.split('//')[1]).split('/')
        identifier_value = jalcdoi_cr_link
        identifier_type = 'DOI'
        doi_register_val = '/'.join(jalcdoi_cr_tail[1:])
        doi_register_typ = 'Crossref'
    elif idf_grant == IDENTIFIER_GRANT_LIST[3][0] and post_json.get(
            'identifier_grant_jalc_dc_doi_link'):
        jalcdoi_dc_link = post_json.get('identifier_grant_jalc_dc_doi_link')
        jalcdoi_dc_tail = (jalcdoi_dc_link.split('//')[1]).split('/')
        identifier_value = jalcdoi_dc_link
        identifier_type = 'DOI'
        doi_register_val = '/'.join(jalcdoi_dc_tail[1:])
        doi_register_typ = 'Datacite'
    # elif idf_grant == IDENTIFIER_GRANT_LIST[4][0] and post_json.get(
    # 'identifier_grant_crni_link'):
    #     jalcdoi_crni_link = post_json.get('identifier_grant_crni_link')
    #     identifier_value = jalcdoi_crni_link
    #     identifier_type = 'HDL'
    #     del tempdata[attrs[2]]
    #     del tempdata[attrs[3]]
    elif idf_grant == IDENTIFIER_GRANT_CAN_WITHDRAW:  # with draw
        # identifier_grant
        pidstore_identifier = item.get('pidstore_identifier')
        flag_del_pidstore = delete_doi_pidstore(
            pidstore_identifier['identifier_value'])
    else:
        current_app.logger.error(_('Identifier datas are empty!'))
        pidstore_identifier = item.get('pidstore_identifier')
        flag_del_pidstore = delete_doi_pidstore(
            pidstore_identifier['identifier_value'])

    try:
        tempdata[attrs[0]] = identifier_value
        tempdata[attrs[1]] = identifier_type
        if tempdata.get(attrs[2]) is not None \
                and tempdata.get(attrs[3]) is not None:
            tempdata[attrs[2]] = doi_register_val
            tempdata[attrs[3]] = doi_register_typ

        if not flag_del_pidstore:
            reg_invenio_pidstore(tempdata[attrs[0]], item.id)

        # Update metadata
        if tempdata != temp_form:
            # transfer to JPCOAR format
            record = WekoDeposit.get_record(activity_detail.item_id)
            item_type = ItemsMetadata.get_by_object_id(activity_detail.item_id)
            identifier_map = identifier_jpcoar_mapping(item_type.item_type_id,
                                                       attrs[0:2])
            _identifier_data = record.get(identifier_map['id']).\
                get('attribute_value_mlt')
            # data DOI generate
            _identifier_data.append({
                identifier_map['val']: tempdata[attrs[0]],
                identifier_map['type']: tempdata[attrs[1]]
            })
            res = {
                identifier_map['id']: _identifier_data,
                'pidstore_identifier': {}
            }

            res['pidstore_identifier']['identifier_value'] = tempdata[attrs[0]]
            if tempdata.get(attrs[2]) and tempdata.get(attrs[3]):
                doi_register_map = identifier_jpcoar_mapping(
                    item_type.item_type_id, attrs[2:4])
                res[doi_register_map['id']] = ({
                    doi_register_map['val']: tempdata[attrs[2]],
                    doi_register_map['type']: tempdata[attrs[3]]
                })
            with db.session.begin_nested():
                item.update(res)
                item.commit()
            db.session.commit()
    except Exception as ex:
        current_app.logger.exception(str(ex))
        db.session.rollback()


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


def delete_doi_pidstore(link_doi):
    """
    Change status of registed doi_pidstore.

    :param link_doi:
    :return: True/False
    """
    try:
        with db.session.no_autoflush:
            doi_pidstore = PersistentIdentifier.query.filter_by(
                pid_type='doi',
                object_type='rec',
                pid_value=link_doi,
                status=PIDStatus.REGISTERED).one_or_none()

        if doi_pidstore:
            doi_pidstore.delete()
            return doi_pidstore.status == PIDStatus.DELETED
        return False
    except PIDDoesNotExistError as pidNotEx:
        current_app.logger.error(pidNotEx)
        return False


def reg_invenio_pidstore(pid_value, item_id):
    """
    Register pids_tore.

    :param: pid_value, item_id
    """
    try:
        PersistentIdentifier.create('doi', pid_value, None,
                                    PIDStatus.REGISTERED, 'rec', item_id)
    except PIDAlreadyExists as pidArlEx:
        current_app.logger.error(pidArlEx)


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
        + '/record/' + str(deposit_id)

    weko_handle = Handle()
    handle = weko_handle.register_handle(location=record_url)

    if handle:
        try:
            prev_cnri = PersistentIdentifier.query.filter_by(
                pid_type='cnri',
                object_uuid=item_uuid).one_or_none()

            if prev_cnri:
                return

            cnri_pidstore = PersistentIdentifier.create(
                'cnri',
                str(handle),
                object_type='rec',
                object_uuid=item_uuid,
                status=PIDStatus.REGISTERED
            )
            return cnri_pidstore
        except PIDDoesNotExistError as pidNotEx:
            current_app.logger.error(pidNotEx)
    else:
        current_app.logger.error('Handle not found!')


def identifier_jpcoar_mapping(item_type_id, keys):
    """
    Mapping jpcoar for identifier.

    :param item_type_id: id of item_type
    :param keys: a list key of attribute mapping
    :return: res_dict
    """
    res_dict = {}
    if item_type_id:
        type_mapping = Mapping.get_record(item_type_id)
        item_map = get_mapping(type_mapping, "jpcoar_mapping")
        if keys[0] in item_map:
            _identifier_map = item_map[keys[0]].split('.')
            res_dict['id'] = _identifier_map[0]
            res_dict['val'] = _identifier_map[1]
        if keys[1] in item_map:
            res_dict['type'] = item_map[keys[1]].split('.')[1]
    return res_dict


def item_metadata_validation(item_id, identifier_type):
    """
    Validate item metadata.

    :param: item_id, identifier_type
    :return: error_list
    """
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
        return None

    journalarticle_nameid = 14
    journalarticle_type = 'other（プレプリント）'
    thesis_nameid = 12
    report_nameid = 16
    report_types = ['technical report', 'research report', 'report']
    elearning_type = 'learning material'
    dataset_nameid = 22
    dataset_type = 'software'
    datageneral_nameid = [13, 17, 18, 19, 20, 21]
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
    if not (item_type or resource_type) and type_check:
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
        if (item_type.name_id == journalarticle_nameid
            or resource_type == journalarticle_type) \
            or (item_type.name_id == thesis_nameid) \
            or (item_type.name_id == report_nameid
                or resource_type in report_types) \
            or (resource_type == elearning_type) \
            or (item_type.name_id in datageneral_nameid
                or resource_type in datageneral_types) \
                or item_type.name_id < 10:
            properties = ['title',
                          'identifier',
                          'identifierRegistration']
            error_list = validation_item_property(metadata_item,
                                                  identifier_type,
                                                  properties)
        # 別表2-5 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【研究データ】
        elif item_type.name_id == dataset_nameid or resource_type == \
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
        if item_type.name_id == journalarticle_nameid or resource_type == \
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
    empty_list = {'required': [], 'pattern': [], 'types': [], 'doi': ''}
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
        if requirements:
            error_list['required'] += requirements
        # half-with and special character check
        # else:
        #     for item in data:
        #         char_re = re.compile(r'[^a-zA-Z0-9\-\.\_\;\(\)\/.]')
        #         result = char_re.search(item)
        #         if bool(result):
        #             error_list['pattern'].append(key)
        if type_requirements:
            error_list['required'] += type_requirements
        else:
            for item in type_data:
                if (identifier_type == IDENTIFIER_GRANT_SELECT_DICT['JaLCDOI']
                        and not item == 'JaLC') or \
                    (identifier_type == IDENTIFIER_GRANT_SELECT_DICT[
                        'CrossRefDOI'] and not item == 'Crossref'):
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
            current_app.logger.debug(str(item_property) + ' jpcoar:mapping '
                                                          'is not correct')
            return None, None
        attribute = self.record.get(key.split('.')[0])
        if not attribute:
            return None, key
        else:
            for attr in attribute.get('attribute_value_mlt'):
                data.append(attr.get(key.split('.')[1]))
        return data, key
