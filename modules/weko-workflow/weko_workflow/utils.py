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
from weko_records.serializers.utils import get_mapping, get_metadata_from_map

from .api import WorkActivity
from .config import IDENTIFIER_ITEMSMETADATA_FORM


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
    flagDelPidstore = False

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
        flagDelPidstore = del_invenio_pidstore(pidstore_identifier['identifier']['value'])
    else:
        current_app.logger.error(_('Identifier datas are empty!'))
        pidstore_identifier = item.get('pidstore_identifier')
        res['pidstore_identifier'] = tempdata
        flagDelPidstore = del_invenio_pidstore(pidstore_identifier['identifier']['value'])
    try:
        if not flagDelPidstore:
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


def item_metadata_validation(item_id, idf_select):
    """
    Register pids_tore.

    :param: pid_value, item_id
    """
    if idf_select == 0:
        return None

    error_list = []
    record = WekoRecord.get_record(item_id)
    item_type = ItemTypes.get_by_id(id_=record.get('item_type_id'))
    item_type_mapping = Mapping.get_record(item_type.id)
    item_map = get_mapping(item_type_mapping, "jpcoar_mapping")

    # get record's resource type
    type_key = item_map.get("type.@value").split('.')[0]
    resource_json = record.get(type_key)
    resource_type = None
    # check resource type request
    if not type_key or not resource_json:
        return error_list.append(type_key)

    if resource_json.get("attribute_value_mlt"):
        resource_type = resource_json.get("attribute_value_mlt")[0].get("resourcetype")
    elif resource_json.get("attribute_value"):
        resource_type = resource_json.get("attribute_value").get("resourcetype")

    # current_app.logger.debug(type_key)
    # current_app.logger.debug(resource_json)
    # current_app.logger.debug(idf_select)
    # current_app.logger.debug(item_type.name_id)

    # JaLC DOI identifier registration
    if idf_select == '1':
        # 別表2-1 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
        if item_type.name_id == 14 or resource_type == 'other（プレプリント）':
            # check タイトル dc:title
            title_key = item_map.get("title.@value")
            title_data = None
            title_attribute = record.get(title_key.split('.')[0])
            if title_attribute.get('attribute_value_mlt'):
                title_data = title_attribute['attribute_value_mlt'][0].get(title_key.split('.')[1])
            elif title_attribute.get('attribute_value'):
                title_data = title_attribute['attribute_value'].get(title_key.split('.')[1])

            if not title_data:
                error_list.append(title_key)

            # check 識別子 jpcoar:identifier


    # CrossRef DOI identifier registration
    elif idf_select == '2':
        if item_type and ( item_type.name_id == 14 or item_type.name_id == 16 or item_type.name_id == 12 or item_type.name_id == 15):
            pass
        else:
            return None # Error

    current_app.logger.debug(error_list)
    return error_list
