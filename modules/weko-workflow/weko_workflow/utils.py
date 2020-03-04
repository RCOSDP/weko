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
from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier, \
    PIDDoesNotExistError, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from sqlalchemy.exc import SQLAlchemyError
from weko_admin.models import Identifier
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_handle.api import Handle
from weko_records.api import ItemsMetadata, ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping

from weko_workflow.config import IDENTIFIER_GRANT_LIST

from .api import WorkActivity
from .config import IDENTIFIER_GRANT_SELECT_DICT, WEKO_SERVER_CNRI_HOST_LINK


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
                        doi_select=0):
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
    else:
        current_app.logger.error(_('Identifier datas are empty!'))

    try:
        if not flag_del_pidstore and identifier_val and doi_register_val:
            identifier = IdentifierHandle(record_without_version)
            reg = identifier.register_pidstore('doi', identifier_val)

            if reg:
                identifier = IdentifierHandle(item_id)
                identifier.update_idt_registration_metadata(doi_register_val,
                                                            doi_register_typ)
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


def item_metadata_validation(item_id, identifier_type):
    """
    Validate item metadata.

    :param: item_id, identifier_type
    :return: error_list
    """
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
        return None

    journalarticle_nameid = [3, 5, 9]
    journalarticle_type = ['other（プレプリント）', 'conference paper',
                           'data paper', 'departmental bulletin paper',
                           'editorial', 'journal article', 'periodical',
                           'review article', 'article']
    thesis_types = ['thesis', 'bachelor thesis', 'master thesis',
                    'doctoral thesis']
    report_types = ['technical report', 'research report', 'report',
                    'book', 'book part']
    elearning_type = ['learning material']
    dataset_nameid = [4]
    dataset_type = ['software', 'dataset']
    datageneral_nameid = [1, 10]
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
            'pmid': '',
            'doi': '',
            'url': '',
            "msg": 'Resource Type Property either missing '
            'or jpcoar mapping not correct!',
            'error_type': 'no_resource_type'
        }

    if not item_type or not resource_type and type_check:
        error_list = {'required': [], 'pattern': [], 'pmid': '',
                      'doi': '', 'url': ''}
        error_list['required'].append(type_key)
        return error_list
    resource_type = resource_type.pop()
    properties = []

    # JaLC DOI identifier registration
    if identifier_type == IDENTIFIER_GRANT_SELECT_DICT['JaLCDOI']:
        # 別表2-1 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【ジャーナルアーティクル】
        # 別表2-3 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【書籍】
        # 別表2-4 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【e-learning】
        # 別表2-6 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【汎用データ】
        if item_type.name_id in journalarticle_nameid \
            or resource_type in journalarticle_type \
            or resource_type in report_types \
            or (resource_type in elearning_type) \
            or (item_type.name_id in datageneral_nameid
                or resource_type in datageneral_types):
            properties = ['title']
        # 別表2-2 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【学位論文】
        elif resource_type in thesis_types:
            properties = ['title',
                          'creator']
        # 別表2-5 JaLC DOI登録メタデータのJPCOAR/JaLCマッピング【研究データ】
        elif item_type.name_id in dataset_nameid \
                or resource_type in dataset_type:
            properties = ['title',
                          'givenName']
    # CrossRef DOI identifier registration
    elif identifier_type == IDENTIFIER_GRANT_SELECT_DICT['CrossRefDOI']:
        if item_type.name_id in journalarticle_nameid or resource_type in \
                journalarticle_type:
            properties = ['title'
                          'publisher',
                          'sourceIdentifier',
                          'sourceTitle']
        elif resource_type in report_types:
            properties = ['title']
        elif resource_type in thesis_types:
            properties = ['title',
                          'creator']

    if properties:
        return validation_item_property(metadata_item,
                                        identifier_type,
                                        properties)
    else:
        return _('Cannot register selected DOI for current Item Type of this '
                 'item.')


def validation_item_property(mapping_data, identifier_type, properties):
    """
    Validate item property.

    :param mapping_data: Mapping Data contain record and item_map
    :param identifier_type: Selected identifier
    :param properties: Property's keywords
    :return: error_list or None
    """
    error_list = {'required': [], 'pattern': [], 'pmid': '',
                  'doi': '', 'url': ''}
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

    # check 識別子 jpcoar:givenName and jpcoar:nameIdentifier
    if 'creator' in properties:
        _, key = mapping_data.get_data_by_property(
            "creator.givenName.@value")
        _, idt_key = mapping_data.get_data_by_property(
            "creator.nameIdentifier.@value")

        data = []
        idt_data = []
        creators = mapping_data.record.get(key.split('.')[0])
        for creator in creators.get("attribute_value_mlt"):
            for subitem in creator:
                for item in creator[subitem]:
                    if item.get(key.split('.')[1]):
                        data.append(item.get(key.split('.')[1]))
                    if item.get(idt_key.split('.')[1]):
                        idt_data.append(item.get(idt_key.split('.')[1]))

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
        error_list['required'] = list(set(error_list['required']))
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
                return doi_pidstore.status == PIDStatus.DELETED
        except PIDDoesNotExistError as pidNotEx:
            current_app.logger.error(pidNotEx)
            return False
        except Exception as ex:
            current_app.logger.error(ex)
        return False

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
                            delete_pid_object = PersistentIdentifier.query.\
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
