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

from flask import current_app
from flask_babelex import gettext as _
from invenio_communities.models import Community
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDAlreadyExists, \
    PIDDoesNotExistError, PIDStatus
from weko_records.api import ItemsMetadata
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_records.api import FilesMetadata, ItemTypes
from weko_records.api import Mapping
from weko_records.serializers.utils import get_mapping
import re

from .api import WorkActivity
from .config import IDENTIFIER_ITEMSMETADATA_FORM, IDENTIFIER_GRANT_SELECT_DICT


def get_community_id_by_index(index_name):
    """
    Get community use indexName input is index_name_english.

    :param: index_name_english
    :return: dict of item type info
    """
    communities = Community.query.all()
    ret_community = []
    for community in communities:
        if community.index.index_name_english == index_name:
            ret_community.append(community.id)

    if len(ret_community) > 0:
        return ret_community[0]
    return None


def pidstore_identifier_mapping(post_json, idf_grant=0, activity_id='0'):
    """
    Mapp pidstore identifier data to ItemMetadata.

    :param post_json: request data
    :param idf_grant: identifier selected
    :param activity_id: activity id number
    """
    activity_obj = WorkActivity()
    activity_detail = activity_obj.get_activity_detail(activity_id)
    item = ItemsMetadata.get_record(id_=activity_detail.item_id)

    # transfer to JPCOAR format
    res = {'pidstore_identifier': {}}
    tempdata = IDENTIFIER_ITEMSMETADATA_FORM
    flag_del_pidstore = False

    if idf_grant == 0:
        res['pidstore_identifier'] = tempdata
    elif idf_grant == 1:  # identifier_grant_jalc_doi
        jalcdoi_link = post_json.get('identifier_grant_jalc_doi_link')
        if jalcdoi_link:
            jalcdoi_tail = (jalcdoi_link.split('//')[1]).split('/')
            tempdata['identifier']['value'] = jalcdoi_link
            tempdata['identifier']['properties']['identifierType'] = 'DOI'
            tempdata['identifierRegistration']['value'] = \
                jalcdoi_tail[1:]
            tempdata['identifierRegistration']['properties'][
                'identifierType'] = 'JaLC'
            res['pidstore_identifier'] = tempdata
    elif idf_grant == 2:  # identifier_grant_jalc_cr
        jalcdoi_cr_link = post_json.get('identifier_grant_jalc_cr_doi_link')
        if jalcdoi_cr_link:
            jalcdoi_cr_tail = (jalcdoi_cr_link.split('//')[1]).split('/')
            tempdata['identifier']['value'] = jalcdoi_cr_link
            tempdata['identifier']['properties']['identifierType'] = 'DOI'
            tempdata['identifierRegistration']['value'] = \
                jalcdoi_cr_tail[1:]
            tempdata['identifierRegistration']['properties'][
                'identifierType'] = 'Crossref'
            res['pidstore_identifier'] = tempdata
    elif idf_grant == 3:  # identifier_grant_jalc_dc_doi
        jalcdoi_dc_link = post_json.get('identifier_grant_jalc_dc_doi_link')
        if jalcdoi_dc_link:
            jalcdoi_dc_tail = (jalcdoi_dc_link.split('//')[1]).split('/')
            tempdata['identifier']['value'] = jalcdoi_dc_link
            tempdata['identifier']['properties']['identifierType'] = 'DOI'
            tempdata['identifierRegistration']['value'] = \
                jalcdoi_dc_tail[1:]
            tempdata['identifierRegistration']['properties'][
                'identifierType'] = 'Datacite'
            res['pidstore_identifier'] = tempdata
    elif idf_grant == 4:  # identifier_grant_crni
        jalcdoi_crni_link = post_json.get('identifier_grant_crni_link')
        if jalcdoi_crni_link:
            tempdata['identifier']['value'] = jalcdoi_crni_link
            tempdata['identifier']['properties']['identifierType'] = 'HDL'
            del tempdata['identifierRegistration']
            res['pidstore_identifier'] = tempdata
    elif idf_grant == -1:  # with draw identifier_grant
        pidstore_identifier = item.get('pidstore_identifier')
        res['pidstore_identifier'] = tempdata
        flag_del_pidstore = del_invenio_pidstore(
            pidstore_identifier['identifier']['value'])
    else:
        current_app.logger.error(_('Identifier datas are empty!'))
        pidstore_identifier = item.get('pidstore_identifier')
        res['pidstore_identifier'] = tempdata
        flag_del_pidstore = del_invenio_pidstore(
            pidstore_identifier['identifier']['value'])
    try:
        if not flag_del_pidstore:
            reg_invenio_pidstore(tempdata['identifier']['value'], item.id)

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
    isExistDoi = False
    try:
        link_doi = doi_link['doi_link']
        pid_identifiers = PersistentIdentifier.query.filter_by(
            pid_type='doi', object_type='rec',
            pid_value=link_doi, status=PIDStatus.REGISTERED).all()
        for pid_identifier in pid_identifiers:
            if pid_identifier.pid_value == link_doi:
                isExistDoi = True
        return isExistDoi
    except PIDDoesNotExistError as pidNotEx:
        current_app.logger.error(pidNotEx)
        return isExistDoi


def del_invenio_pidstore(link_doi):
    """
    Change status of pids_tore has been registed.

    :param: link_doi
    :return: True/False
    """
    try:
        pid_identifier = PersistentIdentifier.query.\
            filter_by(pid_type='doi', object_type='rec', pid_value=link_doi,
                      status=PIDStatus.REGISTERED).one()
        if pid_identifier:
            pid_identifier.delete()
            return pid_identifier.status == PIDStatus.DELETED
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


def item_metadata_validation(item_id, identifier_type):
    """
    Register pids_tore.

    :param: pid_value, item_id
    """
    if identifier_type == 0:
        return None

    error_list = []
    journalarticle_nameid = 14
    journalarticle_type = 'other（プレプリント）'
    thesis_nameid = 12
    report_nameid = 16
    report_types = ['technical report','research report','report']
    elearning_type = 'learning material'
    dataset_nameid = 22
    dataset_type = 'software'
    datageneral_nameid = [13, 17, 18, 19, 20, 21]
    datageneral_types = ['internal report', 'policy report', 'report part',
                'working paper', 'interactive resource','research proposal', 'technical documentation', 'workflow', 'その他（その他）']

    metadata_item = MappingData(item_id)
    item_type = metadata_item.get_data_item_type()
    resource_type, type_key = metadata_item.get_data_by_property("type.@value")

    # check resource type request
    if not (item_type or resource_type):
        error_list.append(type_key.split('.')[0])
        return error_list
    resource_type = resource_type.pop()

    # JaLC DOI identifier registration
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['JaLCDOI']:
        # 別表2-1 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
        if item_type.name_id == journalarticle_nameid or resource_type == journalarticle_type:
            properties = ['title', 'identifier', 'identifierRegistration']
            error_list = validation_item_property(metadata_item, identifier_type, properties)
        # 別表2-2 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【学位論文】
        elif item_type.name_id == thesis_nameid:
            properties = ['title', 'identifier', 'identifierRegistration']
            error_list = validation_item_property(metadata_item, identifier_type, properties)
        # 別表2-3 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【書籍】
        elif item_type.name_id == report_nameid or resource_type in report_types:
            properties = ['title', 'identifier', 'identifierRegistration']
            error_list = validation_item_property(metadata_item, identifier_type, properties)
        # 別表2-4 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【e-learning】
        elif resource_type == elearning_type:
            properties = ['title', 'identifier', 'identifierRegistration']
            error_list = validation_item_property(metadata_item, identifier_type, properties)
        # 別表2-5 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【研究データ】
        elif item_type.name_id == dataset_nameid or resource_type == dataset_type:
            properties = ['title', 'givenName', 'identifier', 'identifierRegistration']
            error_list = validation_item_property(metadata_item, identifier_type, properties)
        # 別表2-6 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【汎用データ】
        elif item_type.name_id in datageneral_nameid or resource_type in datageneral_types:
            properties = ['title', 'identifier', 'identifierRegistration']
            error_list = validation_item_property(metadata_item, identifier_type, properties)
        else:
            error_list = 'false'
    # CrossRef DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['CrossRefDOI']:
        if item_type.name_id == journalarticle_nameid or resource_type == journalarticle_type:
            properties = ['title', 'identifier', 'identifierRegistration', 'sourceIdentifier', 'sourceTitle']
            error_list = validation_item_property(metadata_item, identifier_type, properties)
        if item_type.name_id in [thesis_nameid, report_nameid] or resource_type in report_types:
            properties = ['title', 'identifier', 'identifierRegistration']
            error_list = validation_item_property(metadata_item, identifier_type, properties)
        else:
            error_list = 'false'
    else:
        error_list = 'false'

    if error_list == 'false':
        return 'Selected Identifier Grant NOT support for current ItemType'

    return error_list

def validation_item_property(mapping_data, identifier_type, properties):
    error_list = []
    # check タイトル dc:title
    if 'title' in properties:
        title_data, title_key = mapping_data.get_data_by_property("title.@value")

        if not title_data:
            error_list.append(title_key)

    # check 識別子 jpcoar:givenName
    if 'givenName' in properties:
        datas, key = mapping_data.get_data_by_property("creator.givenName.@value")
        
        if not datas:
            error_list.append(key)
        else:
            idx = 0
            for data in datas:
                if not data:
                    error_list.append(key + '.' + str(idx))
                idx += 1

    # check 識別子 jpcoar:identifier
    if 'identifier' in properties:
        datas, key = mapping_data.get_data_by_property("identifier.@value")
        type_datas, type_key = mapping_data.get_data_by_property("identifier.@attributes.identifierType")
        
        if not (datas or type_datas):
            error_list.append(key)
            error_list.append(type_key)
        else:
            idx = 0
            for data in datas:
                if not data:
                    error_list.append(key + '.' + str(idx))
                idx += 1
            idx = 0
            for type_data in type_datas:
                if not type_data in ['HDL', 'URI']:
                    error_list.append(type_key + '.' + str(idx))
                idx += 1

    # check ID登録 jpcoar:identifierRegistration
    if 'identifierRegistration' in properties:
        datas, key = mapping_data.get_data_by_property("identifierRegistration.@value")
        type_datas, type_key = mapping_data.get_data_by_property("identifierRegistration.@attributes.identifierType")
        
        if not (datas or type_datas):
            error_list.append(key)
            error_list.append(type_key)
        else:
            idx = 0
            for data in datas:
                if not data:
                    error_list.append(key + '.' + str(idx))
                else:
                    char_re = re.compile(r'[^a-zA-Z0-9\-\.\_\;\(\)\/.]')
                    result = char_re.search(data)
                    if bool(result):
                        error_list.append(key + '.' + str(idx))
                idx += 1
            idx = 0
            for type_data in type_datas:
                if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['JaLCDOI'] and not type_data == 'JaLC':
                    error_list.append(type_key + '.' + str(idx))
                if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['CrossRefDOI'] and not type_data == 'Crossref':
                    error_list.append(type_key + '.' + str(idx))
                idx += 1

    # check 収録物識別子 jpcoar:sourceIdentifier
    if 'sourceIdentifier' in properties:
        datas, key = mapping_data.get_data_by_property("sourceIdentifier.@value")
        type_datas, type_key = mapping_data.get_data_by_property("sourceIdentifier.@attributes.identifierType")
        
        if not (datas or type_datas):
            error_list.append(key)
            error_list.append(type_key)
        else:
            idx = 0
            for data in datas:
                if not data:
                    error_list.append(key + '.' + str(idx))
                idx += 1
            idx = 0
            for type_data in type_datas:
                if not type_data:
                    error_list.append(type_key + '.' + str(idx))
                idx += 1

    # check 収録物名 jpcoar:sourceTitle
    if 'sourceTitle' in properties:
        datas, key = mapping_data.get_data_by_property("sourceTitle.@value")
        lang_datas, lang_key = mapping_data.get_data_by_property("sourceTitle.@attributes.xml:lang")
        
        if not (datas or lang_datas):
            error_list.append(key)
            error_list.append(lang_key)
        else:
            idx = 0
            for data in datas:
                if not data:
                    error_list.append(key + '.' + str(idx))
                idx += 1
            if not 'en' in lang_datas:
                error_list.append(lang_key + '.' + str(idx))

    return error_list


class MappingData(object):
    """Dummy pagination class."""

    record = None
    item_map = None

    def __init__(self, item_id):
        """Initilize pagination."""
        self.record = WekoRecord.get_record(item_id)
        item_type = self.get_data_item_type()
        item_type_mapping = Mapping.get_record(item_type.id)
        self.item_map = get_mapping(item_type_mapping, "jpcoar_mapping")

    def get_data_by_property(self, property):
        key = self.item_map.get(property)
        data = []
        if not key:
            current_app.logger.debug(str(property) + ' jpcoar:mapping is not correct')
            return None, None
        attribute = self.record.get(key.split('.')[0])
        if not attribute:
            return None, key
        else:
            for attr in attribute.get('attribute_value_mlt'):
                data.append(attr.get(key.split('.')[1]))
        return data, key

    def get_data_item_type(self):
        item_type = ItemTypes.get_by_id(id_=self.record.get('item_type_id'))
        return item_type