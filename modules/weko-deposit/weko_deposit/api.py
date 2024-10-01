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

"""Weko Deposit API."""
import copy
import uuid
from collections import OrderedDict
from datetime import datetime, timezone,date
from typing import NoReturn, Union
from tika import parser

from redis import RedisError
from dictdiffer import dot_lookup
from dictdiffer.merge import Merger, UnresolvedConflictsException
from invenio_search.engine import search
from flask import abort, current_app, json, request, session
from flask_security import current_user
from invenio_db import db
from invenio_deposit.api import Deposit, index, preserve
from invenio_files_rest.models import (
    Bucket, Location, MultipartObject, ObjectVersion, Part)
from invenio_i18n.ext import current_i18n
from invenio_indexer.api import RecordIndexer
from invenio_pidrelations.contrib.draft import PIDNodeDraft
from invenio_pidrelations.contrib.versioning import PIDNodeVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.serializers.utils import serialize_relations
from invenio_pidstore.errors import PIDDoesNotExistError, PIDInvalidAction
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_files.api import FileObject, Record
from invenio_records_files.models import RecordsBuckets
from invenio_records_rest.errors import PIDResolveRESTError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified

from weko_admin.models import AdminSettings
from weko_index_tree.api import Indexes
from weko_records.api import (
    FeedbackMailList, ItemLink, ItemsMetadata, ItemTypes
)
from weko_records.models import ItemMetadata, ItemReference
from weko_records.utils import (
    get_all_items, get_attribute_value_all_items,
    get_options_and_order_list, json_loader,
    remove_weko2_special_character, set_timestamp,set_file_date
)
from weko_redis.errors import WekoRedisError
from weko_redis.redis import RedisConnection
from weko_schema_ui.models import PublishStatus
from weko_user_profiles.models import UserProfile

from .config import WEKO_DEPOSIT_SYS_CREATOR_KEY
from .errors import WekoDepositError
from .logger import weko_logger
from .pidstore import (
    get_latest_version_id, get_record_without_version,
    weko_deposit_fetcher, weko_deposit_minter
)

PRESERVE_FIELDS = (
    '_deposit',
    '_buckets',
    '_files',
    '_internal',
    '_oai',
    'relations',
    'owners',
    'recid',
    'conceptrecid',
    'conceptdoi',
)

# WEKO_DEPOSIT_SYS_CREATOR_KEY = (
#     current_app.config.get('WEKO_DEPOSIT_SYS_CREATOR_KEY')
# )

class WekoFileObject(FileObject):
    """Extend FileObject for detail page.

    This class extends the FileObject class to provide additional
    functionality for handling file objects in the detail page of the WEKO
    system.<br>
    It includes methods for updating file information and checking whether a
    file can be previewed.

    Attributes:
        obj (Record): Record object.
        data (dict): Record data.
        preview_able (bool): File preview able or not.
    """

    def __init__(self, obj, data):
        """Bind to current bucket.

        This method initializes the object and binds it to the current bucket.

        Args:
            obj (Record):
                Record object.
            data (dict):
                Record data.
        """
        weko_logger(key='WEKO_COMMON_CALLED_ARGUMENT', arg=(obj, data))
        self.obj = obj
        self.data = data
        self.info()
        self.preview_able = self.file_preview_able()

    def info(self):
        """Update file information.

        This method updates own file information.
        Attribute `filename` is not present if the record is not set in the
        index. Therefore, nothing is done.

        Returns:
            dict:
                Updated file information.
        """
        super(WekoFileObject, self).dumps()
        self.data.update(self.obj.file.json)
        if hasattr(self, 'filename'):
            weko_logger(key='WEKO_COMMON_IF_ENTER', branch='filename exsisted')

            index = self['filename'].rfind('.')
            self['filename'] = self['filename'][:index]
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=self.data)

        return self.data

    def file_preview_able(self):
        """Check whether file can be previewed or not.

        This method checks whether the file can be previewed based on its type
        and size.

        Returns:
            bool:
                True if the file can be previewed, False otherwise.
        """
        file_type = ''
        file_size = self.data['size']

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, (k, v) in \
            enumerate(current_app.config['WEKO_ITEMS_UI_MS_MIME_TYPE'].items()):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=k)

            if self.data.get('format') in v:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='format exsisted in value')
                file_type = k
                break
        weko_logger(key='WEKO_COMMON_FOR_END')

        if file_type in current_app.config[
                'WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT'].keys():
            weko_logger(key='WEKO_COMMON_IF_ENTER', branch='')
            # Convert MB to Bytes in decimal
            file_size_limit = current_app.config[
                'WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT'][
                file_type] * 1000000
            if file_size > file_size_limit:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='file_size is large than file_size_limit')
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=False)
                return False

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=True)
        return True


class WekoIndexer(RecordIndexer):
    """Provide an interface for indexing records in Elasticsearch.

    This class extends the RecordIndexer class to index records and manipulate
    data in Elasticsearch. It includes methods for uploading metadata, deleting
    file indexes, updating relation versions, and updating Elasticsearch data.

    Attributes:
        es_index (str):
            Search index in Elasticsearch.
        es_doc_type (str):
            Default document type in Elasticsearch.
        file_doc_type (str):
            File document type in Elasticsearch.
    """

    def get_es_index(self):
        """Assign Elastic search settings.

        Retrieves the search index, default document type, and file document
        type from the application's configuration and assigns them to instance
        variables.

        Returns:
            None
        """
        self.es_index = current_app.config['SEARCH_UI_SEARCH_INDEX']

    def upload_metadata(self, jrc, item_id, revision_id, skip_files=False):
        """Upload the item metadata to ElasticSearch.

        Prepares and indexes the metadata of an item to Elasticsearch, using
        its ID, revision number, and content (`jrc`).

        Args:
            jrc (dict):
                JSON representation of the item's metadata.
            item_id (:obj:`PersistentIdentifier`):
                PID of the item.
            revision_id (int):
                Revision number of the item.
            skip_files (bool, optional):
                Whether to skip indexing of associated files.
                Defaults to False. Not used.
        """
        es_info = {
            "id": str(item_id),
            "index": self.es_index,
        }
        body = {
            "version": revision_id + 1,
            "version_type": self._version_type,
            "body": jrc
        }

        if self.client.exists(**es_info):
            weko_logger(key='WEKO_COMMON_IF_ENTER', branch='')
            del body['version']
            del body['version_type']

        self.client.index(**{**es_info, **body})

    def delete_file_index(self, body, parent_id):
        """Delete file index in Elasticsearch.

        Attempts to delete file index specified in `body` from Elasticsearch.

        Args:
            body (list):
                List of file IDs to be deleted.
            parent_id (int):
                Parent item ID used for routing the delete operation.


        Raises:
            WekoDepositIndexerError:
                If an error occurs while deleting a file index.
        """
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, lst in enumerate(body):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=i,
                        element=lst)
            try:
                self.client.delete(id=str(lst),
                                    index=self.es_index,
                                    routing=parent_id)
            except ElasticsearchException as ex:
                weko_logger(key='WEKO_DEPOSIT_FAILED_DELETE_FILE_INDEX',
                            record_id=str(lst), ex=ex)
                # raise WekoDepositIndexerError(ex=ex,
                #                     msg="Delete file index error.") from ex
            except Exception as ex:
                weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
                # raise WekoDepositIndexerError(ex=ex) from ex
        weko_logger(key='WEKO_COMMON_FOR_END')

    def update_relation_version_is_last(self, version):
        """Updates relation version 'is_last' in Elasticsearch.

        This method updates the `is_last` record of a relation on elasticsearch
        based on the data in `Wekodeposit`.<br>
        Note: ignore error information if the update fails with certain
            status codes (400, 404).

        Args:
            version (dict):
                It containes the relation version data, including the 'id'
                (str) of the relation version and the 'is_last' (bool) status.

        Returns:
            dict:
                The response from Elasticsearch after attempting the update.

        Raises:
            ElasticsearchException:
                If an error occurs during the update process (excluding errors
                with status codes 400 and 404, which are ignored).
        """
        self.get_es_index()
        pst = 'relation_version_is_last'
        id = str(version.get('id'))
        body = {'doc': {pst: version.get('is_last')}}

        result = self.client.update(
            index=self.es_index,
            id=str(version.get('id')),
            body=body, ignore=[400, 404]
        )
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result


    def update_es_data(self, record, update_revision=True,
                    update_oai=False, is_deleted=False,
                    field='path'):
        """Update es data.

        This method updates `oai` and `version` in Elasticsearch based on the
        data in `record`.

        Args:
            record (:obj:WekoDeposit): Record instance to update.
            update_revision (bool, optional): True: Update `version` in ES.
                False: Update without `version`. Defaults to True.
            update_oai (bool, optional): True: Update `oai` in ES.
                False: Update nothing in ES. Defaults to False.
            is_deleted (bool, optional): True: Get `field` in ES.
                False: Get empty list in ES.Defaults to False.
            field (str, optional): This is a key. Defaults to 'path'.

        Returns:
            dict:
                The response from Elasticsearch after attempting the update.

        """
        self.get_es_index()
        _oai = '_oai'
        sets = 'sets'
        body = {}
        if not update_oai:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='update_oai is False')
            body = {
                'doc': {
                    '_item_metadata': {
                        field: record.get(field)
                    },
                    field: record.get(field),
                    '_updated': datetime.now(timezone.utc).isoformat()
                }
            }
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='update_oai is True')
            body = {
                'doc': {
                    _oai: {
                        sets: record.get(_oai, {}).get(sets, []),
                    } if record.get(_oai) else {},
                    '_item_metadata': {
                        _oai: {
                            sets: record.get(_oai, {}).get(sets, []),
                        } if record.get(_oai) else {},
                        field: record.get(field)
                    },
                    field: record.get(field) if not is_deleted else [],
                    '_updated': datetime.now(timezone.utc).isoformat()
                }
            }

        if update_revision:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='update_revision is True')
            result = self.client.update(
                index=self.es_index,
                id=str(record.id),
                version=record.revision_id,
                body=body
            )

            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
            return result
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='update_revision is False')
            result = self.client.update(
                index=self.es_index,
                id=str(record.id),
                body=body
            )

            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
            return result

    def index(self, record):
        """Index a record(fake function).

        This method indexes a record in Elasticsearch.

        Args:
            record(:obj:WekoDeposit): Record instance. Not used.

        """
        self.get_es_index()

    def delete(self, record):
        """Delete a record.

        This method deletes a record in Elasticsearch.
        Not utilized.

        Args:
            record(:obj:WekoDeposit): Record instance.
        """
        self.get_es_index()

        self.client.delete(id=str(record.id), index=self.es_index)

    def delete_by_id(self, uuid):
        """Delete a record by id.

        This method deletes a record in Elasticsearch by its ID.

        Args:
            uuid(:obj:`UUID`): Record ID.
        """
        try:
            self.get_es_index()
            self.client.delete(id=str(uuid),
                                index=self.es_index,
                                doc_type=self.es_doc_type)
        except search.OpenSearchException as ex:
            weko_logger(key='WEKO_DEPOSIT_FAILED_DELETE_RECORD_BY_ID',
                        uuid=str(uuid), ex=ex)
            # raise WekoDepositIndexerError(ex=ex,
            #                     msg="Delete record by id error.") from ex
        except Exception as ex:
            weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            # raise WekoDepositIndexerError(ex=ex) from ex

    def get_count_by_index_id(self, tree_path):
        """Get count by index id.

        This method get count of records in Elasticsearch by tree path.

        Args:
            tree_path(int): Tree path instance. Index ID.
        """
        search_query = {
            'query': {
                'term': {
                    'path.tree': tree_path
                }
            }
        }
        self.get_es_index()
        search_result = self.client.count(index=self.es_index,
                                            body=search_query)
        result = search_result.get('count')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def get_pid_by_es_scroll(self, path):
        """Get pid by Elasticsearch scroll.

        Args:
            path(int): Path instance. Index ID.

        Returns:
            list: Result from Elasticsearch.
        """
        search_query = {
            "query": {
                "match": {
                    "path.tree": path
                }
            },
            "_source": "_id",
            "size": 3000
        }
        def get_result(result):
            """Get result.

            Get result from Elasticsearch.

            Args:
                result(dict): Result from Elasticsearch.

            Returns:
                list: Result from Elasticsearch.
            """
            # if result:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='result is True')
            hit = result['hits']['hits']
            if hit:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='hit is True')
                weko_logger(key='WEKO_COMMON_RETURN_VALUE',
                            value=[h.get('_id') for h in hit])
                return [h.get('_id') for h in hit]
            else:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='hit is False')
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
                return None

            # else:
            #     weko_logger(key='WEKO_COMMON_IF_ENTER',
            #                 branch='result is False')
            #     weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
            #     return None
        ind = self.record_to_index({})

        search_result = self.client.search(index=ind,
                                            body=search_query, scroll='1m')
        if search_result:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='search_result is True')
            res = get_result(search_result)
            scroll_id = search_result['_scroll_id']

            if res:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='res is not none')
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=res)
                yield res

                weko_logger(key='WEKO_COMMON_WHILE_START')
                while res:
                    weko_logger(key='WEKO_COMMON_WHILE_LOOP_ITERATION',
                                count=None, element=scroll_id)
                    res = self.client.scroll(scroll_id=scroll_id, scroll='1m')
                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=res)
                    yield res
                weko_logger(key='WEKO_COMMON_WHILE_END')

            self.client.clear_scroll(scroll_id=scroll_id)

    def get_metadata_by_item_id(self, item_id):
        """Get metadata of item by id from Elasticsearch.

        This method retrieves the metadata of an item from Elasticsearch by
        its ID.

        Args:
            item_id: Item ID (UUID).

        Return:
            str: The response from Elasticsearch after attempting the get.
        """
        self.get_es_index()
        result = self.client.get(index=self.es_index,
                                id=str(item_id))
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def update_feedback_mail_list(self, feedback_mail):
        """Update feedback mail info.

        This method updates the feedback mail list in Elasticsearch.

        Args:
            feedback_mail (dict):
                feedback_mail: mail list in json format.

            {'id': UUID('05fd7cbd-6aad-4c76-a62e-7947868cccf6'), \
            'mail_list': [{'email': 'wekosoftware@nii.ac.jp', \
            'author_id': ''}]}

        Returns:
            str: _feedback_mail_id
        """
        self.get_es_index()
        pst = 'feedback_mail_list'
        body = {'doc': {pst: feedback_mail.get('mail_list')}}

        result = self.client.update(
            index=self.es_index,
            id=str(feedback_mail.get('id')),
            body=body
        )
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def update_author_link(self, author_link):
        """Update author_link info.

        This method updates the author link in Elasticsearch.

        Args:
            author_link (dict):
                author_link: author link in json format.

        Returns:
            str: _author_link_id
        """
        self.get_es_index()
        pst = 'author_link'
        body = {'doc': {pst: author_link.get('author_link')}}

        result = self.client.update(
            index=self.es_index,
            id=str(author_link.get('id')),
            body=body
        )
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def update_jpcoar_identifier(self, dc, item_id):
        """Update JPCOAR meta data item.

        This method updates the JPCOAR identifier in Elasticsearch.

        Args:
            dc (dict):
                dc: Item meta data in json format that use for update index
                    in Elasticsearch.
            item_id (str):
                item_id: item id.
        """
        self.get_es_index()
        body = {'doc': {'_item_metadata': dc}}
        result = self.client.update(
            index=self.es_index,
            id=str(item_id),
            body=body
        )
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def __build_bulk_es_data(self, updated_data):
        """Build search engine data.

        This method builds the data to be used in the bulk update operation.

        Args:
            updated_data(dict): Records data to update.
        """
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, record in enumerate(updated_data):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=record)

            es_data = {
                "_id": str(record.get('_id')),
                "_index": self.es_index,
                "_source": record.get('_source'),
            }
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=es_data)
            yield es_data
        weko_logger(key='WEKO_COMMON_FOR_END')

    def bulk_update(self, updated_data):
        """Bulk update.

        This method updates multiple records in Elasticsearch.

        Args:
            updated_data(dict): Updated data.
        """
        self.get_es_index()
        es_data = self.__build_bulk_es_data(updated_data)
        if es_data:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='es_data is not None')
            success, failed = search.helpers.bulk(self.client, es_data)
            if len(failed) > 0:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='failed is not None')
                weko_logger(key='WEKO_COMMON_FOR_START')
                for i, error in enumerate(failed):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=i, element=error)
                    current_app.logger.error(error)
                weko_logger(key='WEKO_COMMON_FOR_END')


class WekoDeposit(Deposit):
    """Define API for changing deposit state."""

    indexer = WekoIndexer()

    deposit_fetcher = staticmethod(weko_deposit_fetcher)

    deposit_minter = staticmethod(weko_deposit_minter)

    data = None
    jrc = None
    is_edit = False

    @property
    def item_metadata(self):
        """Return the Item metadata.

        This method returns the item metadata.


        Args:
            None

        Returns:
            dict: item_metadata from item_id in instance
            "ex :OrderedDict([('pubdate', {'attribute_name': 'PubDate',
            'attribute_value': '2022-06-03'}), ('item_1617186331708',
            {'attribute_name': 'Title',
            'attribute_value_mlt': [{'subitem_1551255647225': 'test1',
            'subitem_1551255648112': 'ja'}]}), ('item_1617258105262',
            {'attribute_name': 'Resource Type',
            'attribute_value_mlt': [
            {'resourceuri': 'http://purl.org/coar/resource_type/c_5794',
            'resourcetype': 'conference paper'}]}), ('item_title', 'test1'),
            ('item_type_id', '15'), ('control_number', '1.1'),
            ('author_link', []), ('weko_shared_id', -1), ('owner', '1'),
            ('publish_date', '2022-06-03'), ('title', ['test1']),
            ('relation_version_is_last', True), ('path', ['1557820086539']),
            ('publish_status', '0')])"

        Raises:
            sqlalchemy.orm.exc.NoResultFound
        """
        result = ItemsMetadata.get_record(self.id).dumps()
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def is_published(self):
        """Check if deposit is published.


        This method checks if the deposit is published.

        Args:
            None

        Returns:
            dict: published deposit id if  deposit ispubilshed.
            {'type': 'depid', 'value': '34', 'revision_id': 0}
        """
        result = self['_deposit'].get('pid') is not None
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @preserve(fields=('_deposit', '$schema'))
    def merge_with_published(self):
        """Merge changes with latest published version.


        This method merges changes with the latest published version and then
        unify the paches. (not use)

        Args:
            None

        Returns:
            dict: destination

        Raises:
            MergeConflict(): throw when catch UnresolvedConflictsException.
        """
        pid, first = self.fetch_published()
        lca = first.revisions[self['_deposit']['pid']['revision_id']]
        # ignore _deposit and $schema field
        args = [lca.dumps(), first.dumps(), self.dumps()]
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, arg in enumerate(args):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=i,
                        element=arg)
            if '$schema' in arg:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='$schema is in arg')
                del arg['$schema']
            if '_deposit' in arg:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='_deposit is in arg')
                del arg['_deposit']
            if 'control_number' in arg:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='control_number is in arg')
                del arg['control_number']
        weko_logger(key='WEKO_COMMON_FOR_END')
        args.append({})
        m = Merger(*args)
        try:
            m.run()
        except UnresolvedConflictsException as ex:
            weko_logger(key='WEKO_DEPOSIT_FAILED_MERGE_CHANGE', pid=pid, ex=ex)
            raise WekoDepositError(ex=ex, msg="Merge conflict error.") from ex
        except Exception as ex:
            weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            raise WekoDepositError(ex=ex) from ex
        result = self._patch(m.unified_patches, lca)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @staticmethod
    def _patch(diff_result, destination, in_place=False):
        """Patch the diff result to the destination dictionary.

        This method patches the diff result to the destination dictionary.
        (not use)

        Args:
            diff_result (dict): Changes returned by ``diff``.
            destination (dict): Structure to apply the changes to.
            in_place (boolean): By default, destination dictionary is deep
            copied before applying the patch, and the copy is returned.
            Setting ``in_place=True`` means that patch will apply the changes
            directly to and return the destination structure.
            Defaults to False.

        Returns:
            dict: destination
        """
        (ADD, REMOVE, CHANGE) = (
            'add', 'remove', 'change')
        if not in_place:
            weko_logger(key='WEKO_COMMON_IF_ENTER', branch='in_place is True')
            destination = copy.deepcopy(destination)

        def add(node, changes):
            """Add changes to the destination.

            This method adds changes to the destination by three cases.

            Args:
                node (list): Node to apply the changes to.
                changes (dict): Changes to apply.
            """
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (key, value) in enumerate(changes):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=key)
                dest = dot_lookup(destination, node)
                if isinstance(dest, list):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='dest is list')
                    dest.insert(key, value)
                elif isinstance(dest, set):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='dest is set')
                    dest |= value
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='dest is not list and set')
                    dest[key] = value
            weko_logger(key='WEKO_COMMON_FOR_END')

        def change(node, changes):
            """Apply changes to the specified node.

            This method changes the node in the destination by three cases.

            Args:
                node (list): Node to apply the changes to.
                changes (dict): Changes to apply.
            """
            dest = dot_lookup(destination, node, parent=True)
            if isinstance(node, str):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='node is str')
                last_node = node.split('.')[-1]
            else:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='node is not str')
                last_node = node[-1]
            if isinstance(dest, list):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='dest is list')
                last_node = int(last_node)
            _, value = changes
            dest[last_node] = value

        def remove(node, changes):
            """Remove changes from the destination.

            This method removes changes from the destination by three cases.

            Args:
                node (list): Node to apply the changes to.
                changes (dict): Changes to apply.
            """
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (key, value) in enumerate(changes):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=key)
                dest = dot_lookup(destination, node)
                if isinstance(dest, set):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='dest is set')
                    dest -= value
                else:
                    if isinstance(dest, list) and isinstance(key, int) and len(
                            dest) > key:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='dest is list and key is int and '
                                            'length of dest is larger than key')
                        del dest[key]
                    elif isinstance(dest, dict) and dest.get(key):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='dest is dict and key is in dest')
                        del dest[key]
            weko_logger(key='WEKO_COMMON_FOR_END')

        patchers = {
            REMOVE: remove,
            ADD: add,
            CHANGE: change
        }

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, (action, node, changes) in enumerate(diff_result):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=action)
            patchers[action](node, changes)
        weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=destination)
        return destination

    def _publish_new(self, id_=None):
        """Override the publish new to avoid creating multiple pids.

        This method reuses existing PIDs in order to prevent multiple PIDs
        being created.

        Args:
            id_ (str): uuid for publish new to avoid creating multiple pids.
                        Defaults to None.

        Returns:
            dict: new created record
        """
        id_ = id_ or uuid.uuid4()
        record_pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', object_uuid=self.id).first()

        self['_deposit']['pid'] = {
            'type': record_pid.pid_type,
            'value': record_pid.pid_value,
            'revision_id': 0,
        }

        data = dict(self.dumps())
        data['$schema'] = self.record_schema

        with self._process_files(id_, data):
            record = self.published_record_class.create(data, id_=id_)

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=record)
        return record

    def _update_version_id(self, metas, bucket_id):
        """Update 'version_id' of file_metadatas.

        This method get version id and updates the 'version_id' of
        file_metadatas based on the data in 'metas'.

        Args:
            metas (dict): Record Metadata to update version_id
            bucket_id (str): Bucket UUID for search ObjectVersion

        Returns:
            bool: "True: file_version is updated.
                False: fail file_version update"

        """
        _filename_prop = 'filename'
        files_versions = ObjectVersion.get_by_bucket(bucket=bucket_id,
                                                    with_deleted=True).all()
        files_versions = {x.key: x.version_id for x in files_versions}
        file_meta = []

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, item in enumerate(metas):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=item)
            if (not isinstance(metas[item], dict)
                    or not metas[item].get('attribute_value_mlt')):
                weko_logger(key='WEKO_COMMON_CONTINUE',
                            branch='metadata is not dict or attribute_value_mlt'
                                    ' does not exsist')
                continue
            itemmeta = metas[item]['attribute_value_mlt']
            if (itemmeta and isinstance(itemmeta, list)
                    and isinstance(itemmeta[0], dict)
                    and itemmeta[0].get(_filename_prop)):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='itemmeta is list and first element is dict '
                                    'and filename is in first element')
                file_meta.extend(itemmeta)
            elif (isinstance(itemmeta, dict)
                    and itemmeta.get(_filename_prop)):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='itemmeta is dict and '
                                    'filename is in itemmeta')
                file_meta.extend([itemmeta])
        weko_logger(key='WEKO_COMMON_FOR_END')

        if not file_meta:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='file_meta is empty')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=False)
            return False

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, item in enumerate(file_meta):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=item)
            item['version_id'] = str(files_versions.get(
                item.get(_filename_prop), ''))
        weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=True)
        return True

    def publish(self, pid=None, id_=None):
        """Publish the deposit.

        This method publishes the deposit.

        Args:
            pid (int): Force the new pid value. (Default: ``None``)
            id_ (str): Force the new uuid value as deposit id.
                        (Default: ``None``)

        Returns:
            dict: pubilshed deposit dict
        """
        deposit = None
        deposit = self.publish_without_commit(pid, id_)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=deposit)
        return deposit

    def publish_without_commit(self, pid=None, id_=None):
        """Publish the deposit without commit.

        This method publishes the deposit without commit and updates the
        relation version current to Elasticsearch.

        Args:
            pid (int): Force the new pid value. (Default: ``None``)
            id_ (str): Force the new uuid value as deposit id.
                        (Default: ``None``)

        Returns:
            dict: pubilshed deposit dict
        """
        if not self.data:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='data is None')
            self.data = self.get('_deposit', {})
        if 'control_number' in self:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='control_number is in self')
            self.pop('control_number')
        if '$schema' not in self:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='$schema is not in self')
            self['$schema'] = (
                current_app.extensions['invenio-jsonschemas']
                .path_to_url(current_app.config['DEPOSIT_DEFAULT_JSONSCHEMA'])
            )
        self.is_edit = True

        deposit = super(WekoDeposit, self).publish(pid, id_)
        # update relation version current to ES
        recid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            object_uuid=self.id
        ).one_or_none()
        relations = serialize_relations(recid)
        if relations and 'version' in relations:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="relations is not empty and "
                                "`version` is in relations")
            relations_ver = relations['version'][0]
            relations_ver['id'] = recid.object_uuid
            relations_ver['is_last'] = relations_ver.get('index') == 0
            self.indexer.update_relation_version_is_last(relations_ver)

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=deposit)
        return deposit

    @classmethod
    def create(cls, data, id_=None, recid=None):
        """Create a deposit.

        This method adds the creation of the bucket immediately upon creation
        of the deposit and associates it.

        Args:
            data (dict): new create record data "ex: {'recid': '34',
                        '_deposit': {'id': '34', 'status': 'draft'}}"
            id_ (str): Force the new uuid value as deposit id.
                        (Default: ``None``)
            recid (str): new recid value

        Returns:
            dict: pubilshed deposit dict
        """
        if '$schema' in data:
            data.pop('$schema')

        # Get workflow storage location
        location_name = None
        if session and 'activity_info' in session:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='activity_info is in session')
            activity_info = session['activity_info']

            # Need to import here to avoid circular import
            from weko_workflow.api import WorkActivity
            activity = WorkActivity.get_activity_by_id(
                activity_info['activity_id'])

            if activity and activity.workflow and activity.workflow.location:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='activity.workflow.location is in activity')
                location_name = activity.workflow.location.name

        bucket = Bucket.create(
            location=location_name,
            quota_size=current_app.config['WEKO_BUCKET_QUOTA_SIZE'],
            max_file_size=current_app.config['WEKO_MAX_FILE_SIZE'],
        )
        data['_buckets'] = {'deposit': str(bucket.id)}

        # save user_name & display name.
        if current_user and current_user.is_authenticated:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='current_user is authenticated')
            user = UserProfile.get_by_userid(current_user.get_id())
            if '_deposit' in data:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='_deposit is in data')
                data['_deposit']['owners_ext'] = {
                    'username': user._username if user else '',
                    'displayname': user._displayname if user else '',
                    'email': current_user.email
                }

        if recid:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='recid is not None')
            deposit = super(WekoDeposit, cls).create(
                data,
                id_=id_,
                recid=recid
            )
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='recid is None')
            deposit = super(WekoDeposit, cls).create(data, id_=id_)

        record_id = 0
        if data.get('_deposit'):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='_deposit is in data')
            record_id = str(data['_deposit']['id'])
        parent_pid = PersistentIdentifier.create(
            'parent',
            'parent:{0}'.format(record_id),
            object_type='rec',
            object_uuid=deposit.id,
            status=PIDStatus.REGISTERED
        )

        RecordsBuckets.create(record=deposit.model, bucket=bucket)

        recid = PersistentIdentifier.get('recid', record_id)
        depid = PersistentIdentifier.get('depid', record_id)
        PIDNodeVersioning(pid=parent_pid).insert_draft_child(child_pid=recid)
        PIDNodeDraft(pid=recid).insert_child(depid)
        # Update this object_uuid for item_id of activity.
        if session and 'activity_info' in session:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='activity_info is in session')
            activity = session['activity_info']

            # Need to import here to avoid circular import
            from weko_workflow.api import WorkActivity
            workactivity = WorkActivity()
            workactivity.upt_activity_item(activity, str(recid.object_uuid))

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=deposit)
        return deposit

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def update(self, *args, **kwargs):
        """Update only drafts.

        Update the item information using the item metadata of arg1 and arg2.

        Args:
            *args:
                arg1: index information.<br>
                    example:
        ```
        {'pid': {
            'type': 'depid',
            'value': '34',
            'revision_id': 0},
            'lang': 'ja',
            'owner': '1',
            'title': 'test deposit',
            'owners': [1],
            'status': 'published',
            '$schema': '/items/jsonschema/15',
            'pubdate': '2022-06-07',
            'created_by': 1,
            'owners_ext': {
                'email': 'wekosoftware@nii.ac.jp',
                'username': '',
                'displayname': ''},
            'shared_user_id': -1,
            'item_1617186331708': [{
                'subitem_1551255647225': 'test deposit',
                'subitem_1551255648112': 'ja'}],
            'item_1617258105262': {
                'resourceuri': 'http://purl.org/coar/resource_type/c_5794',
                'resourcetype': 'conference paper'},
            'item_1617605131499': [{'url': {
                'url':
            'https://weko3.example.org/record/34/files/tagmanifest-sha256.txt'},
                'date': [{
                    'dateType': 'Available', 'dateValue': '2022-06-07'}],
                'format': 'text/plain',
                'filename': 'tagmanifest-sha256.txt',
                'filesize': [{'value': '323 B'}],
                'accessrole': 'open_access',
                'version_id': 'b27b05d9-e19f-47fb-b6f5-7f031b1ef8fe'}]}
        ```
            **kwargs:
                unused: (Default: ``empty``)
        """
        self['_deposit']['status'] = 'draft'
        if len(args) > 1:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='args is more than 1')
            dc, deleted_items = self.convert_item_metadata(args[0], args[1])
            super(WekoDeposit, self).update(dc)
        elif len(args)==1:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='args is 1')
            dc, deleted_items = self.convert_item_metadata(args[0])
            super(WekoDeposit, self).update(dc)
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='args is empty')
            super(WekoDeposit, self).update()

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def clear(self, *args, **kwargs):
        """Clear only drafts.

        This method clears the draft status of the deposit.

        Args:
            *args: usable within weko but is not being used.
                (Default: ``empty``)
            **kwargs: usable within weko but is not being used.
                (Default: ``empty``)

        Returns:
            None
        """
        if self['_deposit']['status'] != 'draft':
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='status is not draft')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
            return
        super(WekoDeposit, self).clear(*args, **kwargs)

    @index(delete=True)
    def delete(self, force=True, pid=None):
        """Delete deposit.

        This method deletes the deposit and removes bucket.
        Status required: ``'draft'``.

        Args:
            force(bool): Force deposit delete. (Default: ``True``)
            pid(dict): Force pid object. (Default: ``None``)

        Returns:
            deposit: A new Deposit object

        """
        # Delete the recid
        recid = PersistentIdentifier.get(
            pid_type='recid', pid_value=self.pid.pid_value)

        if recid.status == PIDStatus.RESERVED:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='recid status is reserved')
            db.session.delete(recid)

        # if this item has been deleted
        self.delete_es_index_attempt(recid)

        # Completely remove bucket
        bucket = self.files.bucket
        with db.session.begin_nested():
            # Remove Record-Bucket link
            RecordsBuckets.query.filter_by(record_id=self.id).delete()
            mp_q = MultipartObject.query_by_bucket(bucket)
            # Remove multipart objects
            Part.query.filter(
                Part.upload_id.in_(mp_q.with_entities(
                    MultipartObject.upload_id).subquery())
            ).delete(synchronize_session='fetch')
            mp_q.delete(synchronize_session='fetch')
        bucket.locked = False
        bucket.remove()

        result = super(Deposit, self).delete()
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def commit(self, *args, **kwargs):
        """Store changes on current instance in database and index it.

        1. Get deposit's bucket then set the workflow's storage location to\
            the bucket's default location.
        2. Update the item metadata in the database.
        3. Register the item metadata in search engine.
        4. Update the version_id of records_metadata in the database.

        Args:
            *args: usable within weko but is not being used.
                (Default: ``empty``)
            **kwargs: usable within weko but is not being used.
                (Default: ``empty``)

        Raises:
            WekoDepositError: fail upload metadata to elasticsearch.
        """
        super(WekoDeposit, self).commit(*args, **kwargs)
        record = RecordMetadata.query.get(self.pid.object_uuid)
        if self.data and len(self.data):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='data is not empty')
            # Get deposit bucket
            deposit_bucket = Bucket.query.get(self['_buckets']['deposit'])
            if deposit_bucket and deposit_bucket.location:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='location is in deposit_bucket')
                # Get workflow storage location
                workflow_storage_location = None

                if session and 'activity_info' in session:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='activity_info is in session')
                    activity_info = session['activity_info']

                    # Need to import here to avoid circular import
                    from weko_workflow.api import WorkActivity
                    activity = (
                        WorkActivity
                        .get_activity_by_id(activity_info['activity_id']))

                    if (activity and activity.workflow
                            and activity.workflow.location):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='workflow.location is in activity')
                        workflow_storage_location = activity.workflow.location
                if workflow_storage_location is None:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='workflow_storage_location is None')
                    workflow_storage_location = Location.get_default()
                if(deposit_bucket.location.id != workflow_storage_location.id):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='deposit_bucket.location.id is not '
                                        'equal to workflow_storage_location.id')
                    # Set workflow storage location to bucket default location
                    deposit_bucket.default_location = (
                        workflow_storage_location.id)
                    db.session.merge(deposit_bucket)

            # save item metadata
            self.save_or_update_item_metadata()

            if self.jrc and len(self.jrc):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='jrc is not empty')
                if record and record.json and '_oai' in record.json:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='_oai is in record.json')
                    self.jrc['_oai'] = record.json.get('_oai')
                if ('path' in self.jrc and '_oai' in self.jrc
                        and ('sets' not in self.jrc['_oai']
                        or not self.jrc['_oai']['sets'])):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='path is in jrc and _oai is in jrc and '
                                        'sets is not in jrc[_oai] or sets is '
                                        'empty')
                    setspec_list = self.jrc['path'] or []
                    if setspec_list:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='setspec_list is not None')
                        self.jrc['_oai'].update({"sets": setspec_list})
                # upload item metadata to Elasticsearch
                set_timestamp(self.jrc, self.created, self.updated)

                # Get file contents
                self.get_content_files()

                try:
                    # Upload file content to search engine
                    self.indexer.upload_metadata(self.jrc,
                                                self.pid.object_uuid,
                                                self.revision_id)
                    feedback_mail_list = (
                        FeedbackMailList.get_mail_list_by_item_id(self.id))
                    if feedback_mail_list:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='feedback_mail_list is not None')
                        self.update_feedback_mail()
                    else:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='feedback_mail_list is None')
                        self.remove_feedback_mail()
                except search.TransportError as ex:
                    weko_logger(
                        key='WEKO_DEPOSIT_FAILED_UPLOAD_FILE_CONTENT_TO_ELASTICSEARCH',
                        uuid=self.pid.object_uuid, ex=ex)
                    err_passing_config = current_app.config.get(
                        'WEKO_DEPOSIT_ES_PARSING_ERROR_PROCESS_ENABLE')
                    parse_err = current_app.config.get(
                        'WEKO_DEPOSIT_ES_PARSING_ERROR_KEYWORD')
                    if (err_passing_config
                            and parse_err in ex.info["error"]["reason"]):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='err_passing_config is True and '
                                            'parse_err is in ex.info')
                        self.delete_content_files()
                        self.indexer.upload_metadata(self.jrc,
                                                    self.pid.object_uuid,
                                                    self.revision_id,
                                                    True)
                        record_id = self['_deposit']['id']
                        weko_logger(key='WEKO_DEPOSIT_FAILED_PARSE_FILE_ITEM',
                                    record_id=record_id)
                    else:
                        raise WekoDepositError(
                            ex=ex,
                            msg="Upload metadata to Elasticsearch error."
                        ) from ex
                except Exception as ex:
                    weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
                    raise WekoDepositError(ex=ex) from ex

                # Remove large base64 files for release memory
                if self.jrc.get('content'):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='content is in jrc')
                    weko_logger(key='WEKO_COMMON_FOR_START')
                    for i, content in enumerate(self.jrc['content']):
                        weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=i, element=content)
                        if content.get('file'):
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch='file is in content')
                            del content['file']
                    weko_logger(key='WEKO_COMMON_FOR_END')

        # fix schema url
        if record and record.json and '$schema' in record.json:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='$schema is in record.json')
            record.json.pop('$schema')
            if record.json.get('_buckets'):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='_buckets is in record.json')
                self._update_version_id(record.json,
                                        record.json['_buckets']['deposit'])
            flag_modified(record, 'json')
            db.session.merge(record)

    def newversion(self, pid=None, is_draft=False):
        """Create a new version of the deposit.

        1. Check if a newer version than the pid that is passed as an \
            argument exists.
        2. Update the draft_id then call the create() method to generate \
            a new deposit.
        3. Update both the database and elasticsearch.

        Args:
            pid(dict):
                Used to check for the lastest pid. Defaults to none.<br>
                Example:

                {'path':['1557820086539'],
                'owner': '1',
                'recid': '34.1',
                'title': ['test deposit'],
                'pubdate': {
                    'attribute_name': 'PubDate',
                    'attribute_value': '2022-06-07'},
                'item_title': 'test deposit',
                'author_link': [],
                'item_type_id': '15',
                'publish_date': '2022-06-07',
                'publish_status': '1',
                'weko_shared_id': -1,
                'item_1617186331708': {
                    'attribute_name': 'Title',
                    'attribute_value_mlt': [{
                        'subitem_1551255647225': 'test deposit',
                        'subitem_1551255648112': 'ja'}]},
                'item_1617258105262': {
                    'attribute_name': 'Resource Type',
                    'attribute_value_mlt': [{
                        'resourceuri': 'http://purl.org/coar/resource_type/c_5794',
                        'resourcetype': 'conference paper'}]},
                'item_1617605131499': {
                    'attribute_name': 'File',
                    'attribute_type': 'file',
                    'attribute_value_mlt': [{
                        'url': {
                            'url':'https://192.168.56.48/record/34.1/files/tagmanifest-sha256.txt'
                        },
                        'date': [{
                            'dateType': 'Available',
                            'dateValue': '2022-06-07'
                        }],
                        'format': 'text/plain',
                        'filename': 'tagmanifest-sha256.txt',
                        'filesize': [{'value': '323 B'}],
                        'accessrole': 'open_access',
                        'version_id': 'cd317125-600e-4961-89b6-9bb520f342c7',
                        'mimetype': 'text/plain'
                    }]
                },
                'relation_version_is_last': True,
                '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json',
                '_deposit': {
                    'id': '34.1',
                    'status': 'draft',
                    'owners': [1],
                    'created_by': 1
                },
                '_buckets': {'deposit': '87a563d7-537f-41aa-afd6-fed5e3cb4dc2'},
                'control_number': '34.1',
                '_oai': {
                    'id': 'oai:weko3.example.org:00000034.1',
                    'sets': ['1557820086539']
                    }
                }


            is_draft (boolean, optional):
                flag for registering the parent_id of pidverioning
                (Default: ``False``)

        Returns:
            deposit: newly created deposit object

        Raises:
            PIDInvalidAction(): Invalid operation on persistent identifier
                in current state.
            AttributeError:
        """
        deposit = None

        if not self.is_published():
            raise PIDInvalidAction()

        # Check that there is not a newer draft version for this record
        # and this is the latest version
        parent_pid = PIDNodeVersioning(pid=pid).parents.one_or_none()
        versioning = PIDNodeVersioning(pid=parent_pid)
        record = WekoDeposit.get_record(pid.object_uuid)
        if not pid.status == PIDStatus.REGISTERED:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='pid status is not registered')
            weko_logger(key='WEKO_DEPOSIT_PID_STATUS_NOT_REGISTERED',
                        pid=pid)
            raise WekoDepositError(msg="PID status is not registered.")

        if not record or not versioning.exists or versioning.draft_child:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='record is None or versioning does not exists '
                                'or draft_child exists')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
            return None

        data = record.dumps()
        owners = data['_deposit']['owners']
        keys_to_remove = ('_deposit', 'doi', '_oai',
                        '_files', '_buckets', '$schema')
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, k in enumerate(keys_to_remove):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=k)
            data.pop(k, None)
        weko_logger(key='WEKO_COMMON_FOR_END')

        draft_id = '{0}.{1}'.format(
            pid.pid_value,
            0 if is_draft else get_latest_version_id(pid.pid_value))

        # NOTE: We call the superclass `create()` method, because
        # we don't want a new empty bucket, but
        # an unlocked snapshot of the old record's bucket.
        deposit = super().create(data, recid=draft_id)
        # Injecting owners is required in case of creating new
        # version this outside of request context

        deposit['_deposit']['owners'] = owners

        recid = PersistentIdentifier.get(
            'recid', str(data['_deposit']['id']))
        depid = PersistentIdentifier.get(
            'depid', str(data['_deposit']['id']))

        PIDNodeVersioning(
            pid=parent_pid).insert_draft_child(
            child=recid)
        PIDNodeDraft(pid=recid).insert_child(depid)
        if is_draft:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='is_draft is True')
            with db.session.begin_nested():
                # Set relation type of draft record is 3: Draft
                parent_pid = PIDNodeVersioning(pid=recid).parents.one_or_none()
                relation = PIDRelation.query. \
                    filter_by(parent=parent_pid,
                            child=recid).one_or_none()
                relation.relation_type = 3
            db.session.merge(relation)

        snapshot = (
            record.files.bucket
            .snapshot(lock=False)
        )
        snapshot.locked = False
        deposit['_buckets'] = {'deposit': str(snapshot.id)}
        RecordsBuckets.create(record=deposit.model,
                            bucket=snapshot)

        index = {'index': self.get('path', []),
                'actions': self.get('publish_status')}
        if 'activity_info' in session:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='activity_info is in session')
            del session['activity_info']
        if is_draft:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='is_draft is True')
            from weko_workflow.utils import convert_record_to_item_metadata
            item_metadata = convert_record_to_item_metadata(record)
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='is_draft is False')
            item_metadata = ItemsMetadata.get_record(
                pid.object_uuid).dumps()
        item_metadata.pop('id', None)
        args = [index, item_metadata]
        deposit.update(*args)
        deposit.commit()
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=deposit)
        return deposit

    def get_content_files(self):
        """Get content file metadata.

        This method gets the content file metadata and updates the file url.

        Args:
            None

        Raises:
            WekoDepositError: Upload metadata to Elasticsearch error.
        """
        from weko_workflow.utils import get_url_root

        contents = []
        fmd = self.get_file_data()
        if fmd:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='fmd is not empty')
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, file in enumerate(self.files):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=file)

                if isinstance(fmd, list):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='fmd is list')
                    weko_logger(key='WEKO_COMMON_FOR_START')

                    for j, lst in enumerate(fmd):
                        weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=j, element=lst)

                        filename = lst.get('filename')

                        if file.obj.key == filename:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch='file.obj.key is equal to '
                                                'filename')

                            lst.update({'mimetype': file.obj.mimetype})
                            lst.update(
                                {'version_id': str(file.obj.version_id)})

                            # update file url
                            url_metadata = lst.get('url', {})
                            url_metadata['url'] = (
                                '{}record/{}/files/{}'.format(
                                    get_url_root(), self['recid'], filename)
                            )

                            lst.update({'url': url_metadata})

                            # update file_files's json
                            file.obj.file.update_json(lst)

                            # upload file metadata to search engine
                            try:
                                mimetypes = current_app.config[
                                    'WEKO_MIMETYPE_WHITELIST_FOR_ES']
                                content = lst.copy()
                                attachment = {}
                                if file.obj.mimetype in mimetypes:
                                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                                branch='file.obj.mimetype is in'
                                                        ' mimetypes')
                                    try:
                                        reader = parser.from_file(
                                            file.obj.file.uri)
                                        attachment["content"] = "".join(
                                            reader["content"].splitlines())
                                    except FileNotFoundError as ex:
                                        weko_logger(
                                            key='WEKO_DEPOSIT_FAILED_FIND_FILE',
                                            ex=ex)
                                        raise WekoDepositError(ex=ex,
                                                msg="File not found.") from ex
                                    except Exception as ex:
                                        weko_logger(
                                            key='WEKO_COMMON_ERROR_UNEXPECTED',
                                            ex=ex)
                                        raise WekoDepositError(ex=ex) from ex

                                content.update({"attachment": attachment})
                                contents.append(content)
                            except WekoDepositError as ex:
                                # raise
                                pass
                            except Exception as ex:
                                weko_logger(
                                    key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
                                # raise WekoDepositError(ex=ex) from ex
                            break
            weko_logger(key='WEKO_COMMON_FOR_END')
            self.jrc.update({'content': contents})

    def get_file_data(self):
        """Get file data.

        This method gets the file data from the item metadata.
        Args:
            None

        Returns:
            file_data(list): item_filedata
            example:
            ```
            [{'version_id': 'b27b05d9-e19f-47fb-b6f5-7f031b1ef8fe',
            'filename': 'tagmanifest-sha256.txt',
            'filesize': [{'value': '323 B'}],
            'format': 'text/plain',
            'date': [{'dateValue': '2022-06-07','dateType': 'Available'}],
            'accessrole': 'open_access',
            'url': {'url': \
            'https://192.168.56.48/record/34/files/tagmanifest-sha256.txt'}}]"
            ```
        """
        file_data = []
        data = self.data or self.item_metadata
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, key in enumerate(data):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=key)

            if isinstance(data.get(key), list):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='data.get(key) is list')
                weko_logger(key='WEKO_COMMON_FOR_START')

                for i, item in enumerate(data.get(key)):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=i, element=item)
                    if ((isinstance(item, dict)
                            or isinstance(item, list))
                            and 'filename' in item):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='filename is in item')
                        file_data.extend(data.get(key))
                        break
        weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=file_data)
        return file_data

    def save_or_update_item_metadata(self):
        """Save or update item metadata.

        Save when register a new item type, Update when edit an item.

        Args:
            None
        """
        deposit_owners = self.get('_deposit', {}).get('owners')
        owner = str(deposit_owners[0] if deposit_owners else 1)
        if owner:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='owner is not None')
            dc_owner = self.data.get("owner", None)
            if not dc_owner:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='dc_owner is None')
                self.data.update({"owner": owner})

        if ItemMetadata.query.filter_by(id=self.id).first():
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='ItemMetadata is not None')
            obj = ItemsMetadata.get_record(self.id)
            obj.update(self.data)
            if self.data.get('deleted_items'):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='deleted_items is not None')
                weko_logger(key='WEKO_COMMON_FOR_START')
                for i, key in enumerate(self.data.get('deleted_items')):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=i, element=key)
                    if key in obj:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='key is in obj')
                        obj.pop(key)
                weko_logger(key='WEKO_COMMON_FOR_END')
            obj.commit()
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='ItemMetadata is None')
            if self.data.get('deleted_items'):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='deleted_items is not None')
                self.data.pop('deleted_items')
            ItemsMetadata.create(self.data, id_=self.pid.object_uuid,
                                item_type_id=self.get('item_type_id'))

    def delete_old_file_index(self):
        """Delete old file index before file upload when edit an item.

        Args:
            None

        Returns:
            None
        """
        if self.is_edit:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='is_edit is not empty')
            lst = ObjectVersion.get_by_bucket(
                self.files.bucket, True).filter_by(is_head=False).all()
            klst = []

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, obj in enumerate(lst):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=obj)
                if obj.file_id:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{obj.file_id} is not empty")
                    klst.append(obj.file_id)
            weko_logger(key='WEKO_COMMON_FOR_END')
            if klst:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='klst is not empty')
                self.indexer.delete_file_index(klst, self.pid.object_uuid)

    def delete_item_metadata(self, data):
        """Delete item metadata if item changes to empty.

        Args:
            data (dict):
            The item's metadata that will be deleted.
            example:
            ```
            {'pid': {'type': 'depid', 'value': '34', 'revision_id': 0},
            'lang': 'ja',
            'owner': '1',
            'title': 'test deposit',
            'owners': [1],
            'status': 'published',
            '$schema': '/items/jsonschema/15',
            'pubdate': '2022-06-07',
            'created_by': 1,
            'owners_ext': {
                'email': 'wekosoftware@nii.ac.jp',
                'username': '',
                'displayname': ''},
            'shared_user_id': -1,
            'item_1617186331708': [{
                'subitem_1551255647225': 'test deposit',
                'subitem_1551255648112': 'ja'
                }],
            'item_1617258105262': {
                'resourceuri': 'http://purl.org/coar/resource_type/c_5794',
                'resourcetype': 'conference paper'
                },
            'item_1617605131499': [{
                'url': {
                    'url': 'https://weko3.example.org/record/34/files/tagmanifest-sha256.txt'
                    },
                'date': [{
                    'dateType': 'Available',
                    'dateValue': '2022-06-07'
                    }],
                'format': 'text/plain',
                'filename': 'tagmanifest-sha256.txt',
                'filesize': [{'value': '323 B'}],
                'accessrole': 'open_access',
                'version_id': 'b27b05d9-e19f-47fb-b6f5-7f031b1ef8fe'
                }]
            }
            ```

        Returns:
            None

        """
        current_app.logger.debug("self: {}".format(self))
        current_app.logger.debug("data: {}".format(data))

        del_key_list = self.keys() - data.keys()
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, key in enumerate(del_key_list):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=key)
            if (isinstance(self[key], dict)
                    and 'attribute_name' in self[key]):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{self[key]} is dict")
                self.pop(key)
        weko_logger(key='WEKO_COMMON_FOR_END')

    def record_data_from_act_temp(self):
        """Record data from.

        Args:
            None

        Returns:
                bool: True
                dict | list: data
                or
                bool: False
                None
        """
        def _delete_empty(data):
            """Delete data.

            Args:
                dict | list: data

            Returns:
                    bool: True
                    dict: data
                    or
                    bool: False
                    None
            """
            if isinstance(data, dict):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='data is dict')
                result = {}
                flg = False
                if len(data) == 0:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{len(data)} == 0")
                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
                    return flg, result
                else:
                    weko_logger(key='WEKO_COMMON_FOR_START')
                    for i, (k, v) in enumerate(data.items()):
                        weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=i, element=k)
                        not_empty, dd = _delete_empty(v)
                        if not_empty:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch='not_empty is not empty')
                            flg = True
                            result[k] = dd
                    weko_logger(key='WEKO_COMMON_FOR_END')
                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
                    return flg, result
            elif isinstance(data, list):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='data is list')
                result = []
                flg = False
                if len(data) == 0:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{len(data)} == 0")
                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
                    return flg, None
                else:
                    weko_logger(key='WEKO_COMMON_FOR_START')
                    for i, d in enumerate(data):
                        weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=i, element=d)
                        not_empty, dd = _delete_empty(d)
                        if not_empty:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch='not_empty is not empty')
                            flg = True
                            result.append(dd)
                    weko_logger(key='WEKO_COMMON_FOR_END')
                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
                    return flg, result
            else:
                if data:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='data is not empty')
                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=data)
                    return True, data
                else:
                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
                    return False, None

        def _get_title_lang(itemtype_id,_data):
            """Get title lang.

            Args:
                None

            Returns:
                True
                dict: data
            or
            False
            None
            """
            # Need to import here to avoid circular import
            from weko_items_autofill.utils import get_title_pubdate_path

            path = get_title_pubdate_path(itemtype_id).get("title")
            lang = ""
            title = ""
            if "title_parent_key" in path and path["title_parent_key"] in _data:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch="'title_parent_key' in path"
                                    f"and {path['title_parent_key']} in _data")
                temp_record = _data[path["title_parent_key"]]
                if "title_value_lst_key" in path:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='title_value_lst_key in path')
                    weko_logger(key='WEKO_COMMON_FOR_START')
                    for i, p in enumerate(path["title_value_lst_key"]):
                        weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=i, element=p)
                        if (isinstance(temp_record, list)
                            and len(temp_record)>0 and p in temp_record[0]):
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch="temp_record is list"
                                        "and len(temp_record) > 0"
                                        f"and {p} is in {temp_record}")
                            title = temp_record[0][p]
                        elif p in temp_record:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch=f"p in {temp_record}")
                            title = temp_record[p]
                    weko_logger(key='WEKO_COMMON_FOR_END')
                if "title_lang_lst_key" in path:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='title_lang_lst_key in path')
                    weko_logger(key='WEKO_COMMON_FOR_START')
                    for i, p in enumerate(path["title_lang_lst_key"]):
                        weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=i, element=p)
                        if (isinstance(temp_record, list)
                                and len(temp_record)>0
                                and p in temp_record[0]):
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch="temp_record is list"
                                        "and len(temp_record) > 0"
                                        f"and {p} in {temp_record}")
                            lang = temp_record[0][p]
                        elif p in temp_record:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch='p in temp_record')
                            lang = temp_record[p]
                    weko_logger(key='WEKO_COMMON_FOR_END')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=title)
            return title, lang

        pid = PersistentIdentifier.query.filter_by(
            pid_type="recid", pid_value=self.get("recid")).one_or_none()
        if pid:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='pid is not empty')
            item_id = pid.object_uuid
            from weko_workflow.api import WorkActivity
            activity = WorkActivity().get_workflow_activity_by_item_id(item_id)

            if activity:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='activity is not empty')
                itemtype_id = activity.workflow.itemtype_id
                schema = "/items/jsonschema/{}".format(itemtype_id)
                temp_data = activity.temp_data
                if temp_data:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='temp_data is not empty')
                    data = json.loads(temp_data).get("metainfo")
                    title, lang = _get_title_lang(itemtype_id,data)
                    rtn_data = {}
                    deleted_items=[]

                    weko_logger(key='WEKO_COMMON_FOR_START')
                    for k, v in data.items():
                        flg, child_data  = _delete_empty(v)
                        if flg:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch='flg is not empty')
                            rtn_data[k] = child_data
                        else:
                            deleted_items.append(k)
                    weko_logger(key='WEKO_COMMON_FOR_END')
                    # if activity.approval1 == None:
                    #     deleted_items.append("approval1")
                    # if activity.approval2 == None:
                    #     deleted_items.append("approval2")
                    rtn_data["deleted_items"] = deleted_items
                    rtn_data["$schema"] = schema
                    rtn_data["title"] = title if title else activity.title
                    rtn_data["lang"] = lang

                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=rtn_data)
                    return rtn_data

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
        return None

    def convert_item_metadata(self, index_obj, data=None):
        """Convert Item Metadata.
        1. Convert Item Metadata
        2. Inject index tree id to dict
        3. Set Publish Status

        Args:
            index_obj (dict):
                The target item's metadata index information
                example: {'index': ['1557820086539'], 'actions': '1'}"
            data (dict):
                The target item's metadata.<br>
                example:

                {
                'pid': {
                    'type': 'depid', 'value': '34', 'revision_id': 0
                },
                'lang': 'ja',
                'owner': '1',
                'title': 'test deposit',
                'owners': [1],
                'status': 'published',
                '$schema': '/items/jsonschema/15',
                'pubdate': '2022-06-07',
                'created_by': 1,
                'owners_ext': {
                    'email': 'wekosoftware@nii.ac.jp',
                    'username': '',
                    'displayname': ''
                },
                'shared_user_id': -1,
                'item_1617186331708': [{
                    'subitem_1551255647225': 'test deposit',
                    'subitem_1551255648112': 'ja'
                }],
                'item_1617258105262': {
                    'resourceuri': 'http://purl.org/coar/resource_type/c_5794',
                    'resourcetype': 'conference paper'
                },
                'item_1617605131499': [{
                    'url': {
                        'url':
                            'https://weko3.example.org/record/34/files/tagmanifest-sha256.txt'
                    },
                    'date': [{
                        'dateType': 'Available',
                        'dateValue': '2022-06-07'
                    }],
                    'format': 'text/plain',
                    'filename': 'tagmanifest-sha256.txt',
                    'filesize': [{'value': '323 B'}],
                    'accessrole': 'open_access',
                    'version_id': 'b27b05d9-e19f-47fb-b6f5-7f031b1ef8fe'
                }]
                }


        Returns:
            dc: OrderedDict item_metada
            data.get('deleted_items'): deleted item data list

        Raises:
            PIDResolveRESTError(description='Any tree index has been deleted'):
                Any tree index has been deleted
            RuntimeError: fail convert item_metadata
        """
        # if this item has been deleted
        self.delete_es_index_attempt(self.pid)
        try:
            if not data:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='data is empty')

                redis_connection = RedisConnection()
                datastore = redis_connection.connection(
                    db=current_app.config['CACHE_REDIS_DB'], kv = True)
                cache_key = current_app.config[
                    'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(
                    pid_value=self.pid.pid_value)

                # Check exist item cache before delete
                if datastore.redis.exists(cache_key):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f'{datastore.redis.exists(cache_key)} is not empty')
                    data_str = datastore.get(cache_key)

                    if not index_obj.get('is_save_path'):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{index_obj.get('is_save_path')} is empty")
                        datastore.delete(cache_key)
                    data = json.loads(data_str.decode('utf-8'))

                if not data:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='data is empty')
                    data = self.record_data_from_act_temp()
        except RedisError as ex:
            weko_logger(key='WEKO_COMMON_ERROR_REDIS', ex=ex)
            abort(500, 'Failed to register item!')
        except WekoRedisError as ex:
            weko_logger(key='WEKO_COMMON_ERROR_REDIS', ex=ex)
            abort(500, 'Failed to register item!')
        except Exception as ex:
            weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            abort(500, 'Failed to register item!')

        # Get index path

        index_lst = index_obj.get('index', [])
        # Prepare index id list if the current index_lst is a path list
        if index_lst:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='index_lst is not empty')
            index_id_lst = []

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, _index in enumerate(index_lst):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=_index)
                indexes = str(_index).split('/')
                index_id_lst.append(indexes[len(indexes) - 1])
            weko_logger(key='WEKO_COMMON_FOR_END')
            index_lst = index_id_lst

        plst = Indexes.get_path_list(index_lst)
        if not plst or len(index_lst) != len(plst):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="plst is empty"
                        f"or len({index_lst}) != len({plst})")
            raise PIDResolveRESTError(
                description='Any tree index has been deleted')

        # Convert item meta data
        try:
            deposit_owners = self.get('_deposit', {}).get('owners')
            owner_id = str(deposit_owners[0] if deposit_owners else 1)
            dc, jrc, is_edit = json_loader(data, self.pid, owner_id=owner_id)
            dc['publish_date'] = data.get('pubdate')
            dc['title'] = [data.get('title')]
            dc['relation_version_is_last'] = True
            self.data = data
            self.jrc = jrc
            self.is_edit = is_edit
            self._convert_jpcoar_data_to_es()
        except RuntimeError as ex:
            weko_logger(key='WEKO_DEPOSIT_FAILED_CONVERT_ITEM_METADATA',
                        pid=self.pid, ex=ex)
            raise WekoDepositError(ex=ex,
                                msg="Convert item metadata error.") from ex
        except Exception as ex:
            weko_logger(key="WEKO_COMMON_ERROR_UNEXPECTED", ex=ex)
            abort(500, 'MAPPING_ERROR')

        # Save Index Path on ES
        jrc.update({"path": index_lst})
        # current_app.logger.debug(jrc)
        # add at 20181121 start
        sub_sort = {}
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, pth in enumerate(index_lst):
            # es setting
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=pth)
            sub_sort[pth[-13:]] = ""
        weko_logger(key='WEKO_COMMON_FOR_END')
        dc.update({"path": index_lst})
        pubs = PublishStatus.NEW.value
        actions = index_obj.get('actions')
        if actions == 'publish' or actions == PublishStatus.PUBLIC.value:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"actions == 'publish'"
                        f"or actions == {PublishStatus.PUBLIC.value}")
            pubs = PublishStatus.PUBLIC.value
        elif 'id' in data:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='id in data')
            recid = PersistentIdentifier.query.filter_by(
                pid_type='recid', pid_value=data['id']).first()
            rec = RecordMetadata.query.filter_by(id=recid.object_uuid).first()
            pubs = rec.json['publish_status']

        ps = {"publish_status": pubs}
        jrc.update(ps)
        dc.update(ps)
        if data:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='data is not empty')
            self.delete_item_metadata(data)

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=dc)
        return dc, data.get('deleted_items')

    def _convert_description_to_object(self):
        """ Convert description to object.

        Args:
            None

        Returns:
            None

        """
        description_key = "description"
        if isinstance(self.jrc, dict) and self.jrc.get(description_key):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{self.jrc} is dict"
                            f"and {self.jrc.get(description_key)} is not empty")
            _description = self.jrc.get(description_key)
            _new_description = []
            if isinstance(_description, list):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{_description} is list")
                weko_logger(key='WEKO_COMMON_FOR_START')
                for i, data in enumerate(_description):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=i, element=data)
                    if isinstance(data, str):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{data} is str")
                        _new_description.append({"value": data})
                    else:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{data} is not str")
                        _new_description.append(data)
                weko_logger(key='WEKO_COMMON_FOR_END')
            if _new_description:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{_new_description} is not empty")
                self.jrc[description_key] = _new_description

    def _convert_jpcoar_data_to_es(self):
        """Convert data jpcoar to es.

        Args:
            None

        Returns:
            None

        """
        # Convert description to object.
        self._convert_description_to_object()

        # Convert data for geo location.
        self._convert_data_for_geo_location()

    def _convert_data_for_geo_location(self):
        """Convert geo location data to object.

        Args:
            None

        Returns:
            None

        """
        def _convert_geo_location(value):
            """Convert geo location to object.

            Args:
                list: value

            Returns:
                list: _point

            """
            _point = []
            if isinstance(value.get("pointLongitude"), list) and isinstance(
                    value.get("pointLatitude"), list):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{value.get('pointLongitude')} is list"
                                f"and {value.get('pointLatitude')} is list")
                lat_len = len(value.get("pointLatitude"))
                weko_logger(key='WEKO_COMMON_FOR_START')
                for _idx, _value in enumerate(value.get("pointLongitude")):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=_idx, element=_value)
                    _point.append({
                        "lat": value.get("pointLatitude")[
                            _idx] if _idx < lat_len else "",
                        "lon": _value
                    })
                weko_logger(key='WEKO_COMMON_FOR_END')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=_point)
            return _point

        def _convert_geo_location_box():
            """Convert geo location to box.

            Args:
                list: value

            Returns:
                list: point_box

            """
            point_box = {}
            jpcoar_north_east_point = {
                "pointLatitude": v.get("northBoundLatitude"),
                "pointLongitude": v.get("eastBoundLongitude"),
            }
            jpcoar_south_west_point = {
                "pointLatitude": v.get("southBoundLatitude"),
                "pointLongitude": v.get("westBoundLongitude"),
            }
            es_north_east_point = _convert_geo_location(
                jpcoar_north_east_point)
            es_south_west_point = _convert_geo_location(
                jpcoar_south_west_point)
            if es_north_east_point:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='es_north_east_point is not empty')
                point_box['northEastPoint'] = es_north_east_point
            if es_south_west_point:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='es_south_west_point is not empty')
                point_box['southWestPoint'] = es_south_west_point
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=point_box)
            return point_box

        geo_location_key = "geoLocation"
        if isinstance(self.jrc, dict) and self.jrc.get(geo_location_key):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{self.jrc} is dict"
                            f"and {self.jrc.get(geo_location_key)} is not empty")
            geo_location = self.jrc.get(geo_location_key)
            new_data = {}
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (k, v) in enumerate(geo_location.items()):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=k)
                if "geoLocationPlace" == k:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"'geoLocationPlace' == {k}")
                    new_data[k] = v
                elif "geoLocationPoint" == k:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"'geoLocationPoint' == {k}")
                    point = _convert_geo_location(v)
                    if point:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='point is not empty')
                        new_data[k] = point
                elif "geoLocationBox" == k:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"'geoLocationBox' == {k}")
                    point = _convert_geo_location_box()
                    if point:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='point is not empty')
                        new_data[k] = point
            weko_logger(key='WEKO_COMMON_FOR_END')
            if new_data:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='new_data is not empty')
                self.jrc[geo_location_key] = new_data

    @classmethod
    def delete_by_index_tree_id(cls, index_id: str, ignore_items: list = []):
        """Delete by index tree id.

        Args:
            index_id (str): index_id
            ignore_items (list):
                list of items that will be ingnored,
                therefore will not be deleted

        Returns:
            None

        """
        if index_id:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='index_id is not empty')
            index_id = str(index_id)
        obj_ids = next((cls.indexer.get_pid_by_es_scroll(index_id)), [])
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, obj_uuid in enumerate(obj_ids):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=obj_uuid)
            r = RecordMetadata.query.filter_by(id=obj_uuid).first()
            if r.json['recid'].split('.')[0] in ignore_items:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{r.json['recid'].split('.')[0]} in ignore_items")
                continue
            r.json['path'].remove(index_id)
            flag_modified(r, 'json')
            if r.json and not r.json['path']:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{r.json} is not empty"
                                f"and {r.json['path']} is empty")

                # Need to import here to avoid circular import
                from weko_records_ui.utils import soft_delete
                soft_delete(obj_uuid)
            else:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{r.json} is empty"
                                f"or {r.json['path']} is not empty")
                dep = WekoDeposit(r.json, r)
                dep.indexer.update_es_data(dep, update_revision=False)
        weko_logger(key='WEKO_COMMON_FOR_END')

    def update_pid_by_index_tree_id(self, path):
        """Update pid by index tree id (not use).

        Args:
            path (str):
                The index_tree_path that will run the update

        Returns:
            bool: "True: process success False: process failed"

        """
        p = PersistentIdentifier
        try:
            dt = datetime.now(timezone.utc)
            with db.session.begin_nested():
                weko_logger(key='WEKO_COMMON_FOR_START')
                for i, result in enumerate(self.indexer.get_pid_by_es_scroll(path)):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=i, element=result)
                    db.session.query(p).filter(
                        p.object_uuid.in_(result),
                        p.object_type == 'rec').update(
                            {p.status: 'D', p.updated: dt},
                            synchronize_session=False
                        )
                    result.clear()
                weko_logger(key='WEKO_COMMON_FOR_END')
            db.session.commit()
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=True)
            return True
        except SQLAlchemyError as ex:
            weko_logger(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
            db.session.rollback()
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=False)
            return False
        except Exception as ex:
            weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            db.session.rollback()
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=False)
            return False

    def update_item_by_task(self, *args, **kwargs):
        """Update item by task.

        Args:
            *args: usable within weko but is not being used.
                (Default: ``empty``)
            **kwargs: usable within weko but is not being used.
                (Default: ``empty``)

        Returns:
            None

        """
        return super(Deposit, self).commit(*args, **kwargs)

    def delete_es_index_attempt(self, pid):
        """Delete Elasticsearch index attempt.

        Args:
            pid (:obj: `PersistentIdentifier`):
                The item's pid information.
                Erase data related to status deletion.

        Returns:
            None

        Raises:
            PIDResolveRESTError: This item has been deleted. Invalid PID.
        """
        # if this item has been deleted
        if pid.status == PIDStatus.DELETED:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"pid.status == {PIDStatus.DELETED}")
            # attempt to delete index on es
            try:
                self.indexer.delete(self)
            except ElasticsearchException as ex:
                weko_logger(key='WEKO_COMMON_ERROR_ELASTICSEARCH', ex=ex)
            except Exception as ex:
                weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            # weko_logger(key='WEKO_DEPOSIT_ITEM_HAS_BEEN_DELETED', pid=pid)
            # raise PIDResolveRESTError(description='This item has been deleted')


    def update_author_link(self, author_link):
        """Update author link.

        Update author_link list.

        Args:
            list:author_link

        Returns:
            None

        """
        item_id = self.id
        if author_link:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="author_link is not empty")
            author_link_info = {
                "id": item_id,
                "author_link": author_link
            }
            self.indexer.update_author_link(author_link_info)

    def update_feedback_mail(self):
        """Update feedback mail.

        Update feedback mail list.

        Args:
            None

        Returns:
            None

        """
        item_id = self.id
        mail_list = FeedbackMailList.get_mail_list_by_item_id(item_id)
        if mail_list:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="mail_list is not empty")
            feedback_mail = {
                "id": item_id,
                "mail_list": mail_list
            }
            self.indexer.update_feedback_mail_list(feedback_mail)

    def remove_feedback_mail(self):
        """Remove feedback mail.

        Remove feedback mail list.

        Args:
            None

        Returns:
            None

        """
        feedback_mail = {
            "id": self.id,
            "mail_list": []
        }
        self.indexer.update_feedback_mail_list(feedback_mail)

    def clean_unuse_file_contents(self, item_id, pre_object_versions,
                                    new_object_versions, is_import=False):
        """Clean unused file contents.

        Remove file not used after replaced in keep version mode.

        Args:
            item_id (int):
                item_id of the file to be deleted.
            pre_object_versions (list):
                information of the file to be deleted.
                "ex: [87a563d7-537f-41aa-afd6-fed5e3cb4dc2:cd317125-600e-4961-89b6-9bb520f342c7:test.txt]"
            new_object_versions (list):
                information of the new file to be created
                "ex: [87a563d7-537f-41aa-afd6-fed5e3cb4dc2:cd317125-600e-4961-89b6-9bb520f342c7:test.txt]"
            is_import (boolean):
                import flag

        Returns:
            None

        """
        # Need to import here to avoid circular import
        from weko_workflow.utils import update_cache_data

        pre_file_ids = [obv.file_id for obv in pre_object_versions]
        new_file_ids = [obv.file_id for obv in new_object_versions]
        diff_list = list(set(pre_file_ids) - set(new_file_ids))
        unuse_file_ids = [data[0] for data in
                            ObjectVersion.num_version_link_to_files(diff_list)
                            if data[1] <= 1]
        list_unuse_uri = []
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, obv in enumerate(pre_object_versions):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=obv)
            if obv.file_id in unuse_file_ids:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{obv.file_id} in unuse_file_ids")
                obv.remove()
                obv.file.delete()
                if is_import:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='is_import is not empty')
                    list_unuse_uri.append(obv.file.uri)
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='is_import is empty')
                    obv.file.storage().delete()
        weko_logger(key='WEKO_COMMON_FOR_END')
        if list_unuse_uri:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='list_unuse_uri is not empty')
            cache_key = (
                current_app
                .config['WEKO_SEARCH_UI_IMPORT_UNUSE_FILES_URI']
                .format(item_id))
            update_cache_data(cache_key, list_unuse_uri, 0)

    def merge_data_to_record_without_version(self, pid, keep_version=False,
                                                is_import=False):
        """Merge data to record without version.

        Update changes to current record by record from PID.

        Args:
            pid (:obj:`PersistentIdentifier`):
                pid information of the item to be updated.
                "ex <PersistentIdentifier recid:1.0 / rec:5210fd22-576a-4241-8005-4c1f7ab6077a (R)>"
            keep_version (boolean,optional):
                version keep flag
                (Default: ``False``)
            is_import (boolean,optional):
                import flag
                (Default: ``False``)

        Returns:
            bool: Description of return value

        """
        with db.session.begin_nested():
            # update item_metadata
            index = {'index': self.get('path', []),
                        'actions': self.get('publish_status')}
            item_metadata = ItemsMetadata.get_record(pid.object_uuid).dumps()
            item_id = item_metadata.get('id')
            item_metadata.pop('id', None)
            item_metadata.pop('control_number', None)

            # Clone bucket
            _deposit = WekoDeposit.get_record(pid.object_uuid)
            # Get draft bucket's data
            sync_bucket = RecordsBuckets.query.filter_by(
                record_id=self.id).first()
            if sync_bucket:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='sync_bucket is not empty')
                sync_bucket.bucket.locked = False
                snapshot = Bucket.get(
                    _deposit.files.bucket.id).snapshot(lock=False)
                bucket = Bucket.get(sync_bucket.bucket_id)
                if keep_version:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='keep_version is not empty')
                    self.clean_unuse_file_contents(item_id, bucket.objects,
                                                snapshot.objects, is_import)
                snapshot.locked = False
                sync_bucket.bucket = snapshot
                bucket.locked = False

                if not RecordsBuckets.query.filter_by(
                        bucket_id=bucket.id).all():
                    weko_logger(
                        key='WEKO_COMMON_IF_ENTER',
                        branch=f"bucket_id = {bucket.id} is not in RecordsBuckets")
                    bucket.remove()

                bucket = {
                    "_buckets": {
                        "deposit": str(snapshot.id)
                    }
                }

                args = [index, item_metadata]
                self.update(*args)
                # Update '_buckets'
                super(WekoDeposit, self).update(bucket)
                self.commit()
                # update records_metadata
                flag_modified(self.model, 'json')
                db.session.add(self.model)
                db.session.add(sync_bucket)

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=True)
        return self.__class__(self.model.json, model=self.model)

    def prepare_draft_item(self, recid):
        """Prepare draft item.

        Create draft version of main record.
        1. Call the newversion() method using recid as an argument then create a deposit.

        Args:
            recid (dict):
                item meta_data's draft version

        Returns:
            obj:
                returns the created draft_deposit

        """
        draft_deposit = self.newversion(recid, is_draft=True)

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=draft_deposit)
        return draft_deposit

    def delete_content_files(self):
        """Delete content files

        Delete 'file' from content file metadata.

        Args:
            None

        Returns:
            None

        """
        if self.jrc.get('content'):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{self.jrc.get('content')} is not empty")
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, content in enumerate(self.jrc['content']):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=content)
                if content.get('file'):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{content.get('file')} is not empty")
                    del content['file']
            weko_logger(key='WEKO_COMMON_FOR_END')


class WekoRecord(Record):
    """Extend Record obj for record ui."""

    file_cls = WekoFileObject
    record_fetcher = staticmethod(weko_deposit_fetcher)

    @property
    def pid(self):
        """Return an instance of record PID.

        Args:
            None

        Returns:
            PersistentIdentifier: record PID

        """
        pid = self.record_fetcher(self.id, self)
        obj = PersistentIdentifier.get(pid.pid_type, pid.pid_value)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=obj)
        return obj

    @property
    def pid_recid(self):
        """Return an instance of record PID.

        Args:
            None

        Returns:
            PersistentIdentifier: record PID

        """
        pid = self.record_fetcher(self.id, self)
        obj = PersistentIdentifier.get('recid', pid.pid_value)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=obj)
        return obj

    # TODO:
    @property
    def hide_file(self):
        """Whether the file property is hidden.

        Args:
            None

        Returns:
            bool: hide_file

        Note: This function just works fine if file property has value.
        """
        hide_file = False
        item_type_id = self.get('item_type_id')
        solst, meta_options = get_options_and_order_list(item_type_id)
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, lst in enumerate(solst):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=lst)
            key = lst[0]
            val = self.get(key)
            option = meta_options.get(key, {}).get('option')
            # Just get 'File'
            if not (val and option) or val.get('attribute_type') != "file":
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{val and option} is empty")
                continue
            if option.get("hidden"):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{option.get('hidden')} is not empty")
                hide_file = True
            break
        weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=hide_file)
        return hide_file

    @property
    def navi(self):
        """Return the path name.

        Args:
            None

        Returns:
            str: comm_navs

        """
        navs = Indexes.get_path_name(self.get('path', []))

        community = request.args.get('community', None)
        if not community:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='community is empty')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=navs)
            return navs

        # Need to import here to avoid circular import
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(community)
        comm_navs = [item for item in navs if str(
            comm.index.id) in item.path.split('/')]
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=comm_navs)
        return comm_navs

    @property
    def item_type_info(self):
        """Return the information of item type.

        Args:
            None

        Returns:
            The :class:`ItemTypes` instance.

        """
        item_type = ItemTypes.get_by_id(self.get('item_type_id'))
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=item_type.item_type_name.name)
        return '{}({})'.format(item_type.item_type_name.name, item_type.tag)

    @staticmethod
    def switching_language(data):
        """Switching language.

        Args:
            data (_type_): _description_

        Returns:
            _type_: _description_
        """
        current_lang = current_i18n.language
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, value in enumerate(data):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=value)
            if value.get('language', '') == current_lang:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{value.get('language', '')} is current_lang")
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=value.get('title', ''))
                return value.get('title', '')
        weko_logger(key='WEKO_COMMON_FOR_END')

        if len(data) > 0:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{len(data)} > 0")
            if data[0].get('language',None) == None:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{data[0].get('language',None)} is None")
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=data[0].get('title', ''))
                return data[0].get('title', '')

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, value in enumerate(data):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=value)
            if value.get('language', '') == 'en':
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{value.get('language', '')} is en")
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=value.get('title', ''))
                return value.get('title', '')
        weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, value in enumerate(data):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=value)
            if value.get('language', ''):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{value.get('language', '')} is not empty")
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=value.get('title', ''))
                return value.get('title', '')
        weko_logger(key='WEKO_COMMON_FOR_END')

        if len(data) > 0:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{len(data)} > 0")
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=data[0].get('title', ''))
            return data[0].get('title', '')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value='')
        return ''

    @staticmethod
    def __get_titles_key(item_type_mapping, meta_option, hide_list):
        """Get title keys in item type mapping.

        Args:
            item_type_mapping: item type mapping.
            meta_option: item type option.
            hide_list: hide item list of item type.

        Returns:
            parent_key: parent key of item type mapping.
            title_key: title key of mapping key of item type mapping.
            language_key: language key of property data.
        """
        parent_key = None
        title_key = None
        language_key = None
        if item_type_mapping:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='item_type_mapping is not empty')
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, mapping_key in enumerate(item_type_mapping):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=mapping_key)
                property_data = item_type_mapping.get(mapping_key).get(
                    'jpcoar_mapping')
                prop_hidden = (
                    meta_option.get(mapping_key, {})
                    .get('option', {}).get('hidden', False)
                )
                if (
                    isinstance(property_data, dict)
                    and property_data.get('title')
                    and not prop_hidden
                ):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{property_data} is dict"
                                    f"and {property_data.get('title')} is not empty"
                                    "and prop_hidden is empty")
                    title = property_data.get('title')
                    parent_key = mapping_key
                    title_key = title.get("@value")
                    language_key = title.get("@attributes", {}).get("xml:lang")
                    weko_logger(key='WEKO_COMMON_FOR_START')

                    for i, h in enumerate(hide_list):
                        weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=i, element=h)
                        if parent_key in h and language_key in h:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch=f"{parent_key} in h "
                                            f"and {language_key} in h")
                            language_key = None
                        if parent_key in h and title_key in h:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch=f"{parent_key} in h "
                                            f"and {title_key} in h")
                            title_key = None
                            parent_key = None
                    weko_logger(key='WEKO_COMMON_FOR_END')
                    if parent_key and title_key and language_key:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch=f"{parent_key} "
                                            f"and {title_key} "
                                            f"and {language_key} is not empty")
                        break
            weko_logger(key='WEKO_COMMON_FOR_END')

        result = (parent_key, title_key, language_key)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @property
    def get_titles(self):
        """Get titles of record.

        Args:
            None

        Returns:
            title(list): list of title and language

        """
        # Need to import here to avoid circular import
        from weko_items_ui.utils import get_options_and_order_list, get_hide_list_by_schema_form
        meta_option, item_type_mapping = get_options_and_order_list(
            self.get('item_type_id'))

        hide_list = get_hide_list_by_schema_form(self.get('item_type_id'))
        parent_key, title_key, language_key = self.__get_titles_key(
            item_type_mapping, meta_option, hide_list)
        title_metadata = self.get(parent_key)
        titles = []
        if title_metadata:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='title_metadata is not empty')
            attribute_value = title_metadata.get('attribute_value_mlt')
            if isinstance(attribute_value, list):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{attribute_value} is list")

                weko_logger(key='WEKO_COMMON_FOR_START')
                for i, attribute in enumerate(attribute_value):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=i, element=attribute)
                    tmp = {}
                    if attribute.get(title_key):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f'{attribute.get(title_key)} is not empty')
                        tmp['title'] = attribute.get(title_key)
                    if attribute.get(language_key):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f'{attribute.get(language_key)} is not empty')
                        tmp['language'] = attribute.get(language_key)
                    if tmp.get('title'):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{tmp.get('title')} is not empty")
                        titles.append(tmp.copy())
                weko_logger(key='WEKO_COMMON_FOR_END')
        result = self.switching_language(titles)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @property
    def items_show_list(self):
        """Return the item show list.

        Args:
            None

        Returns:
            items(list): list of item show

        """
        # Need to import here to avoid circular import
        from weko_items_ui.utils import get_hide_list_by_schema_form, del_hide_sub_item
        items = []
        settings = AdminSettings.get('items_display_settings')
        hide_email_flag = not settings.items_display_email
        solst, meta_options = get_options_and_order_list(
            self.get('item_type_id'))
        hide_list = get_hide_list_by_schema_form(self.get('item_type_id'))
        item_type = ItemTypes.get_by_id(self.get('item_type_id'))
        meta_list = item_type.render.get('meta_list', []) if item_type else {}
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, lst in enumerate(solst):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=lst)
            key = lst[0]

            val = self.get(key)
            option = meta_options.get(key, {}).get('option')
            if not val or not option:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{val} or {option} is empty")
                continue

            hidden = option.get("hidden")
            if hidden:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='hidden is not empty')
                continue

            mlt = val.get('attribute_value_mlt')
            if mlt is not None:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='mlt is not None')
                mlt = copy.deepcopy(mlt)

                del_hide_sub_item(key.replace('[]', '').split('.')[0],
                                    mlt, hide_list)
                self.__remove_special_character_of_weko2(mlt)
                nval = {}
                nval['attribute_name'] = val.get('attribute_name')
                nval['attribute_name_i18n'] = lst[2] or val.get(
                    'attribute_name')
                nval['attribute_type'] = val.get('attribute_type')

                if (nval['attribute_name'] == 'Reference'
                        or nval['attribute_type'] == 'file'):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{nval['attribute_name']} == 'Reference'"
                                    f"or {nval['attribute_type']} == 'file'")
                    file_metadata = copy.deepcopy(mlt)
                    if nval['attribute_type'] == 'file':
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{nval['attribute_type']} == 'file'")
                        file_metadata = (
                            self.__remove_file_metadata_do_not_publish(
                                file_metadata)
                        )
                    nval['attribute_value_mlt'] = (
                        get_all_items(
                            file_metadata, copy.deepcopy(solst), True)
                    )
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{nval['attribute_name']} == 'Reference'"
                                    f"or {nval['attribute_type']} == 'file'")
                    is_author = nval['attribute_type'] == 'creator'
                    is_thumbnail = any(
                        'subitem_thumbnail' in data for data in mlt)

                    sys_bibliographic = _FormatSysBibliographicInformation(
                        copy.deepcopy(mlt),
                        copy.deepcopy(solst)
                    )
                    if is_author:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='is_author is not empty')
                        creators = self._get_creator(mlt, hide_email_flag)
                        nval['attribute_value_mlt'] = creators
                    elif is_thumbnail:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='is_thumbnail is not empty')
                        nval['is_thumbnail'] = True
                    elif sys_bibliographic.is_bibliographic():
                        weko_logger(
                            key='WEKO_COMMON_IF_ENTER',
                            branch=f"{sys_bibliographic.is_bibliographic()} "
                                "is not empty")
                        nval['attribute_value_mlt'] = (
                            sys_bibliographic.get_bibliographic_list(False)
                        )
                    else:
                        if meta_list.get(key, {}).get('input_type') == 'text':
                            weko_logger(
                                key='WEKO_COMMON_IF_ENTER',
                                branch="'input_type' in meta_list == 'text'")

                            weko_logger(key='WEKO_COMMON_FOR_START')
                            for i, iter in enumerate(mlt):
                                weko_logger(
                                    key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=i, element=iter)

                                if iter.get('interim'):
                                    weko_logger(
                                        key='WEKO_COMMON_IF_ENTER',
                                        branch=f"{iter.get('interim')} "
                                            "is not empty"
                                    )
                                    iter['interim'] = iter[
                                        'interim'].replace("\n", " ")
                            weko_logger(key='WEKO_COMMON_FOR_END')
                        nval['attribute_value_mlt'] = (
                            get_attribute_value_all_items(
                                key,
                                copy.deepcopy(mlt),
                                copy.deepcopy(solst),
                                is_author,
                                hide_email_flag,
                                True,
                                option.get("oneline", False)
                            )
                        )
                items.append(nval)
            else:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='mlt is none')
                val['attribute_name_i18n'] = lst[2] or val.get(
                    'attribute_name')

                if meta_list.get(key, {}).get('input_type') == 'text':
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch="'input_type' in meta_list == 'text'")
                    if 'attribute_value' in val:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"'attribute_value' in {val}")
                        val['attribute_value'] = (
                            val['attribute_value'].replace("\n", " ")
                        )
                items.append(val)
        weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=items)
        return items

    # TODO:
    @property
    def display_file_info(self):
        """Display file information.

        Args:
            None

        Returns:
            items(list): list of file information

        """
        item_type_id = self.get('item_type_id')

        solst, meta_options = get_options_and_order_list(item_type_id)
        items = []

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, lst in enumerate(solst):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=lst)
            key = lst[0]
            val = self.get(key)

            option = meta_options.get(key, {}).get('option')
            if not val or not option:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{val} or {option} is empty")
                continue

            # Just get data of 'File'
            if val.get('attribute_type') != "file":
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{val.get('attribute_type')} != 'file'")
                continue
            # Check option hide.
            if option.get("hidden"):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{option.get('hidden')} is not empty")
                continue
            mlt = val.get('attribute_value_mlt')
            if mlt is not None:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='mlt is not None')
                # Processing get files.
                mlt = copy.deepcopy(mlt)
                # Get file with current version id.
                file_metadata_temp = []
                exclude_attr = [
                    'displaytype', 'accessrole', 'licensetype', 'licensefree']
                filename = request.args.get("filename", None)
                file_order = int(request.args.get("file_order", -1))

                weko_logger(key='WEKO_COMMON_FOR_START')
                for idx, f in enumerate(mlt):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=idx, element=f)
                    if (f.get('filename') == filename and file_order == -1
                            or file_order == idx):
                        # Exclude attributes which is not use.
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{f.get('filename')} is filename")
                        weko_logger(key='WEKO_COMMON_FOR_START')
                        for i, ea in enumerate(exclude_attr):
                            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                        count=i, element=ea)
                            if f.get(ea, None):
                                weko_logger(key='WEKO_COMMON_IF_ENTER',
                                            branch=f"{f.get(ea, None)} is not empty")
                                del f[ea]
                        weko_logger(key='WEKO_COMMON_FOR_END')
                        file_metadata_temp.append(f)
                weko_logger(key='WEKO_COMMON_FOR_END')
                file_metadata = file_metadata_temp
                nval = {}
                nval['attribute_name'] = val.get('attribute_name')
                nval['attribute_name_i18n'] = lst[2] or val.get(
                    'attribute_name')
                nval['attribute_type'] = val.get('attribute_type')
                # Format structure to display.
                attr_mlt = get_attribute_value_all_items(key, file_metadata,
                                                    copy.deepcopy(solst))
                set_file_date(key, copy.deepcopy(solst), file_metadata,
                                attr_mlt)

                nval['attribute_value_mlt'] = attr_mlt
                items.append(nval)
            else:
                # Processing get pubdate.
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='attribute value mlt is None')
                attr_name = val.get('attribute_value', '')
                val['attribute_name_i18n'] = lst[2] or attr_name
                val['attribute_value_mlt'] = [[[[{
                    val['attribute_name_i18n']: attr_name}]]]]
                items.append(val)
        weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=items)
        return items

    def __remove_special_character_of_weko2(self, metadata):
        """Remove special character of WEKO2.

        Args:
            metadata(dict | list): dict or list of special character

        Returns:
            None:
        """
        if isinstance(metadata, dict):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='metadata is dict')
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (k, val) in enumerate(metadata.items()):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=k)
                if isinstance(val, str):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='val is str')
                    metadata[k] = remove_weko2_special_character(val)
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='val is not str')
                    self.__remove_special_character_of_weko2(val)
            weko_logger(key='WEKO_COMMON_FOR_END')
        elif isinstance(metadata, list):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='metadata is list')
            weko_logger(key='WEKO_COMMON_FOR_START')
            for idx, val in enumerate(metadata):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=idx, element=val)
                if isinstance(val, str):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='val is str')
                    metadata[idx] = remove_weko2_special_character(val)
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='val is not str')
                    self.__remove_special_character_of_weko2(val)
            weko_logger(key='WEKO_COMMON_FOR_END')

    @staticmethod
    def _get_creator(meta_data, hide_email_flag):
        """get creator.

        Args:
            meta_data(list): list of meta data
            hide_email_flag(bool): hide email flag

        Returns:
            creators(list):
        """
        current_app.logger.debug("meta_data:{}".format(meta_data))
        creators = []
        if meta_data:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='meta_data is not empty')
            weko_logger(key='WEKO_COMMON_FOR_START')

            for i, creator_data in enumerate(meta_data):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=creator_data)
                creator_dict = _FormatSysCreator(creator_data).format_creator()
                identifiers = WEKO_DEPOSIT_SYS_CREATOR_KEY['identifiers']
                creator_mails = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_mails']


                if identifiers in creator_data:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{identifiers} in creator_data")
                    creator_dict[identifiers] = creator_data[identifiers]
                if creator_mails in creator_data and not hide_email_flag:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{creator_mails} in creator_data "
                                    "and hide_email_flag is not empty")
                    creator_dict[creator_mails] = creator_data[creator_mails]
                creators.append(creator_dict)
            weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=creators)
        return creators

    def __remove_file_metadata_do_not_publish(self, file_metadata_list):
        """Remove file metadata do not publish.

        Args:
            file_metadata_list(list): File metadata list.

        Returns:
            new_file_metadata_list: New file metadata list.
        """
        new_file_metadata_list = []
        user_id_list = self.get('_deposit', {}).get('owners', [])

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, file in enumerate(file_metadata_list):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=file)
            is_permissed_user = self.__check_user_permission(user_id_list)
            is_open_no = self.is_do_not_publish(file)
            if self.is_input_open_access_date(file):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{self.is_input_open_access_date(file)} "
                                "is not empty")
                if not self.is_future_open_date(self,
                                                file) or is_permissed_user:
                    weko_logger(
                        key='WEKO_COMMON_IF_ENTER',
                        branch=f"{self.is_future_open_date(self, file)} "
                        f"is empty or {is_permissed_user} is not empty")
                    new_file_metadata_list.append(file)
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='permissed user is false')
                    continue
            elif not (is_open_no and not is_permissed_user):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{is_open_no} is empty "
                                    f"and {is_permissed_user} is not empty")
                new_file_metadata_list.append(file)
        weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=new_file_metadata_list)
        return new_file_metadata_list

    @staticmethod
    def __check_user_permission(user_id_list):
        """Check user permission.

        Args:
            user_id_list(list): user id list.

        Returns:
            is_ok(bool): true or false.
        """
        is_ok = False
        # Check guest user
        if not current_user.is_authenticated:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='current user is not authenticated')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=is_ok)
            return is_ok
        # Check registered user
        elif current_user and current_user.id in user_id_list:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='current user is registered')
            is_ok = True
        # Check super users
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='current user is super user')
            super_users = (
                current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
                + current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY']
            )

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, role in enumerate(list(current_user.roles or [])):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=role)
                if role.name in super_users:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{role.name} in super_users")
                    is_ok = True
                    break
            weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=is_ok)
        return is_ok

    @staticmethod
    def is_input_open_access_date(file_metadata):
        """Check access of file is 'Input Open Access Date'.

        Args:
            file_metadata(list): file metadata.

        Returns:
            bool: True is 'Input Open Access Date'.
        """
        access_role = file_metadata.get('accessrole', '')

        result = access_role == 'open_date'
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @staticmethod
    def is_do_not_publish(file_metadata):
        """Check access of file is 'Do not Publish'.

        Args:
            file_metadata(list): file metadata.

        Returns:
            bool: True is 'Do not Publish'.
        """
        access_role = file_metadata.get('accessrole', '')
        result = access_role == 'open_no'
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @staticmethod
    def get_open_date_value(file_metadata):
        """Get value of 'Open Date' in file.

        Args:
            file_metadata(list): file metadata.

        Returns:
            date_value: value of open date.
        """
        date = file_metadata.get('date', [{}])
        date_value = date[0].get('dateValue')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=date_value)
        return date_value

    @staticmethod
    def is_future_open_date(self, file_metadata):
        """Check .

        Args:
            file_metadata(list): file metadata.

        Returns:
            date_value: value of open date.
        """
        # Need to import here to avoid circular import
        from weko_records_ui.utils import is_future
        # Get 'open_date' and convert to datetime.date.
        date_value = self.get_open_date_value(file_metadata)
        if date_value is None:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{date_value} is None")
            date_value = str(date.max)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=is_future(date_value))
        return is_future(date_value)

    @property
    def pid_doi(self):
        """Return pid_value of doi identifier.

        Args:
            None.

        Returns:
            pid_value of doi identifier.
        """
        result = self._get_pid('doi')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @property
    def pid_cnri(self):
        """Return pid_value of cnr identifier.

        Args:
            None.

        Returns:
            pid_value of cnr identifier.
        """
        result = self._get_pid('hdl')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @property
    def pid_parent(self):
        """Return pid_value of parent.

        Args:
            None.

        Returns:
            pid_value of parent.
        """
        parent_pid = PIDNodeVersioning(pid=self.pid_recid).parents.one_or_none()
        pid_ver = PIDNodeVersioning(pid=parent_pid)
        # if pid_ver:
        weko_logger(key='WEKO_COMMON_IF_ENTER',
                    branch='pid_ver is not empty')
        # Get pid parent of draft record
        if ".0" in str(self.pid_recid.pid_value):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"'.0' in {str(self.pid_recid.pid_value)}")
            pid_ver.relation_type = 3
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=pid_ver.parents.one_or_none())
            return pid_ver.parents.one_or_none()
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=pid_ver.parents.one_or_none())
        return pid_ver.parents.one_or_none()
        # weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
        # return None

    @classmethod
    def get_record_by_pid(cls, pid):
        """Get record by pid.

        Args:
            pid: pid of record.
            cls: record of cls.

        Returns:
            record of pid.
        """
        pid = PersistentIdentifier.get('depid', pid)
        result = cls.get_record(id_=pid.object_uuid)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @classmethod
    def get_record_by_uuid(cls, uuid):
        """Get record by uuid.

        Args:
            uuid: uuid of record.
            cls: record of cls.

        Returns:
            record of uuid.
        """
        record = cls.get_record(id_=uuid)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=record)
        return record

    @classmethod
    def get_record_cvs(cls, uuid):
        """Get record cvs.

        Args:
            uuid: uuid of record.
            cls: record of cls.

        Returns:
            record of coverpage.
        """
        record = cls.get_record(id_=uuid)
        result = Indexes.get_coverpage_state(record.get('path'))
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def _get_pid(self, pid_type):
        """Return pid_value from persistent identifier.

       Args:
            pid_type: type of pid.

        Returns:
            None.
        """
        pid_without_ver = get_record_without_version(self.pid_recid)
        if not pid_without_ver:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{pid_without_ver} is empty")
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
            return None
        try:
            return PersistentIdentifier.query.filter_by(
                pid_type=pid_type,
                object_uuid=pid_without_ver.object_uuid,
                status=PIDStatus.REGISTERED
            ).order_by(
                db.desc(PersistentIdentifier.created)
            ).first()
        except PIDDoesNotExistError as ex:
            weko_logger('WEKO_COMMON_FAILED_GET_PID', ex=ex)
            pass
        except Exception as ex:
            weko_logger('WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            raise WekoDepositError(ex=ex) from ex
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=None)
        return None

    def update_item_link(self, pid_value):
        """Update current Item Reference base of IR of pid_value input.

       Args:
            pid_value: value of pid.

        Returns:
            None.
        """
        item_link = ItemLink(self.pid.pid_value)

        items = ItemReference.get_src_references(pid_value).all()

        relation_data = []
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, item in enumerate(items):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=item)
            _item = {
                "item_id": item.dst_item_pid,
                "sele_id": item.reference_type
            }
            relation_data.append(_item)
        weko_logger(key='WEKO_COMMON_FOR_END')
        item_link.update(relation_data)

    def get_file_data(self):
        """Get file data.

       Args:
            None.

        Returns:
            None.
        """
        item_type_id = self.get('item_type_id')
        solst, _ = get_options_and_order_list(item_type_id)
        items = []
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, lst in enumerate(solst):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=lst)
            key = lst[0]
            val = self.get(key)
            if not val:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='val is empty')
                continue
            # Just get data of 'File'.
            if val.get('attribute_type') != "file":
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{val.get('attribute_type')} != 'file'")
                continue
            mlt = val.get('attribute_value_mlt')
            if mlt is not None:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='mlt is not None')
                items.extend(mlt)
        weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=items)
        return items


class _FormatSysCreator:
    """Format system creator for detail page.

    Attributes:
        None.
    """
    def __init__(self, creator):
        """Initialize Format system creator for detail page.

       Args:
            creator: Creator data.

        Returns:
            None.

        """
        # current_app.logger.error("creator:{}".format(creator))
        self.creator = creator
        self.current_language = current_i18n.language
        self.no_language_key = "NoLanguage"
        self._get_creator_languages_order()

    def _get_creator_languages_order(self):
        """Get creator languages order.

       Args:
            None.

        Returns:
            None.

        """
        # Prioriry languages: creator, family, given, alternative, affiliation
        lang_key = OrderedDict()
        lang_key[WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_names']] = (
            WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_lang'])
        lang_key[WEKO_DEPOSIT_SYS_CREATOR_KEY['family_names']] = (
            WEKO_DEPOSIT_SYS_CREATOR_KEY['family_lang'])
        lang_key[WEKO_DEPOSIT_SYS_CREATOR_KEY['given_names']] = (
            WEKO_DEPOSIT_SYS_CREATOR_KEY['given_lang'])
        lang_key[WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_names']] = (
            WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_lang'])

        # Get languages for all same structure languages key
        languages = []
        weko_logger(key='WEKO_COMMON_FOR_START')
        [languages.append(data.get(v)) for k, v in lang_key.items()
        for data in self.creator.get(k, []) if data.get(v) not in languages]
        weko_logger(key='WEKO_COMMON_FOR_END')
        # Get languages affiliation
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, creator_affiliation in enumerate(self.creator.get(
                WEKO_DEPOSIT_SYS_CREATOR_KEY['creatorAffiliations'], [])):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=creator_affiliation)
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, affiliation_name in enumerate(creator_affiliation.get(
                    WEKO_DEPOSIT_SYS_CREATOR_KEY['affiliation_names'], [])):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=affiliation_name)
                if affiliation_name.get(
                    WEKO_DEPOSIT_SYS_CREATOR_KEY[
                        'affiliation_lang']) not in languages:
                    weko_logger(
                        key='WEKO_COMMON_IF_ENTER',
                        branch="'affiliation_lang' not in languages")
                    languages.append(affiliation_name.get(
                        WEKO_DEPOSIT_SYS_CREATOR_KEY['affiliation_lang']))
            weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_FOR_END')
        self.languages = languages

    def _format_creator_to_show_detail(self, language: str, parent_key: str,
                                        lst: list) -> NoReturn:
        """Get creator name to show on item detail.

       Args:
            language: language.
            parent_key: parent key.
            lst: creator name list.

        Returns:
            None.

        """
        name_key = ''
        lang_key = ''
        if parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_names']:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"parent_key == {WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_names']}")
            name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_name']
            lang_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_lang']
        elif parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['family_names']:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"parent_key == {WEKO_DEPOSIT_SYS_CREATOR_KEY['family_names']}")
            name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['family_name']
            lang_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['family_lang']
        elif parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['given_names']:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"parent_key == {WEKO_DEPOSIT_SYS_CREATOR_KEY['given_names']}")
            name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['given_name']
            lang_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['given_lang']
        elif parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_names']:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"parent_key == {WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_names']}")
            name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_name']
            lang_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_lang']
        elif parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_type']: #? ADDED 20231017 CREATOR TYPE BUG FIX
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"parent_key == {WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_type']}")
            return
        if parent_key in self.creator:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{parent_key} in {self.creator}")
            lst_value = self.creator[parent_key]
            if len(lst_value) > 0:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{len(lst_value)} > 0")
                weko_logger(key='WEKO_COMMON_FOR_START')
                for i in range(len(lst_value)):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=i)
                    if lst_value[i] and lst_value[i].get(lang_key) == language:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{lst_value[i]} is not empty "
                                        f"and {lst_value[i].get(lang_key)} == language")
                        if name_key in lst_value[i]:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch=f"name_key in {lst_value[i]}")
                            lst.append(lst_value[i][name_key])
                            break
                weko_logger(key='WEKO_COMMON_FOR_END')

    def _get_creator_to_show_popup(self, creators: Union[list, dict],
                                    language: any,
                                    creator_list: list,
                                    creator_list_temp: list = None) -> NoReturn:
        """Format creator to show on popup.

        Args:
            creators (Union[list, dict]): Creators information.
            language (any): Language.
            creator_list (list): Creator list.
            creator_list_temp (list, optional):  Creator temporary list.
                                                    Defaults to None.

        Returns:
            NoReturn: _description_
        """
        def _run_format_affiliation(affiliation_max, affiliation_min,
                                    languages,
                                    creator_lists,
                                    creator_list_temps):
            """Format affiliation creator.

        Args:
            affiliation_max: Affiliation max.
            affiliation_min: Affiliation min.
            languages: Language.
            creator_lists: Creator lists.
            creator_list_temps: Creator lists temps.

        Returns:
            None.

            """
            weko_logger(key='WEKO_COMMON_FOR_START')
            for index in range(len(affiliation_max)):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=index, element=index)
                if index < len(affiliation_min):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"index < {len(affiliation_min)}")
                    affiliation_max[index].update(
                        affiliation_min[index])
                    self._get_creator_to_show_popup(
                        [affiliation_max[index]],
                        languages, creator_lists,
                        creator_list_temps)
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"index >= {len(affiliation_min)}")
                    self._get_creator_to_show_popup(
                        [affiliation_max[index]],
                        languages, creator_lists,
                        creator_list_temps)
            weko_logger(key='WEKO_COMMON_FOR_END')
        def format_affiliation(affiliation_data):
            """Format affiliation creator.

            Args:
                affiliation_data: Affiliation data.

            Returns:
                None.

            """

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, creator in enumerate(affiliation_data):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=creator)
                affiliation_name_format = creator.get('affiliationNames', [])
                affiliation_name_identifiers_format = creator.get(
                    'affiliationNameIdentifiers', [])
                if len(affiliation_name_format) >= len(
                        affiliation_name_identifiers_format):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"len(affiliation_name_format) >= "
                                    f"{len(affiliation_name_identifiers_format)}")
                    affiliation_max = affiliation_name_format
                    affiliation_min = affiliation_name_identifiers_format
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"len(affiliation_name_format) < "
                                    f"{len(affiliation_name_identifiers_format)}")
                    affiliation_max = affiliation_name_identifiers_format
                    affiliation_min = affiliation_name_format

                _run_format_affiliation(affiliation_max, affiliation_min,
                                        language,
                                        creator_list,
                                        creator_list_temp)
            weko_logger(key='WEKO_COMMON_FOR_END')
        if isinstance(creators, dict):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{creators} is dict")
            creator_list_temp = []
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (key, value) in enumerate(creators.items()):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=key)

                if (key in [WEKO_DEPOSIT_SYS_CREATOR_KEY['identifiers'],
                            WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_mails'],
                            WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_type']]): #? ADDED 20231017 CREATOR TYPE BUG FIX
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"key in 'WEKO_DEPOSIT_SYS_CREATOR_KEY'")
                    continue
                if key == WEKO_DEPOSIT_SYS_CREATOR_KEY['creatorAffiliations']:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"key in 'WEKO_DEPOSIT_SYS_CREATOR_KEY'")
                    format_affiliation(value)
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"key not in 'WEKO_DEPOSIT_SYS_CREATOR_KEY'")
                    self._get_creator_to_show_popup(value, language,
                                                    creator_list,
                                                    creator_list_temp)
            weko_logger(key='WEKO_COMMON_FOR_END')
            if creator_list_temp:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='creator_list_temp is not empty')
                if language:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='language is not empty')
                    creator_list.append({language: creator_list_temp})
                # else:
                #     weko_logger(key='WEKO_COMMON_IF_ENTER',
                #                 branch='language is empty')
                #     creator_list.append(
                #         {self.no_language_key: creator_list_temp})
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='creators is not dict')

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, creator_data in enumerate(creators):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=creator_data)
                self._get_creator_based_on_language(creator_data,
                                                    creator_list_temp,
                                                    language)
            weko_logger(key='WEKO_COMMON_FOR_END')

    @staticmethod
    def _get_creator_based_on_language(creator_data: dict,
                                        creator_list_temp: list,
                                        language: str) -> NoReturn:
        """Get creator based on language.

        Args:
            creator_data: creator data.
            creator_list_temp: creator temporary list.
            language: language code.

        Returns:
            None.

        """
        count = 0

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, (k, v) in enumerate(creator_data.items()):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=k)
            if 'Lang' in k:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"Lang' in {k}")

                if not language:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='language is empty')
                    count = count + 1
                elif v == language:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{v} == language")
                    creator_list_temp.append(creator_data)
        weko_logger(key='WEKO_COMMON_FOR_END')
        if count == 0 and not language:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch="count  == 0 and "
                                    "language is empty")
            creator_list_temp.append(creator_data)

    def format_creator(self) -> dict:
        """Format creator data to display on detail screen.

        Args:
            None.

        Returns:
            <dict> The creators are formatted.

        """
        creator_lst = []
        rtn_value = {}
        creator_type = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_type'] #? ADDED 20231017 CREATOR TYPE BUG FIX
        creator_names = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_names']
        family_names = WEKO_DEPOSIT_SYS_CREATOR_KEY['family_names']
        given_names = WEKO_DEPOSIT_SYS_CREATOR_KEY['given_names']
        alternative_names = WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_names']
        list_parent_key = [
            creator_type, #? ADDED 20231017 CREATOR TYPE BUG FIX
            creator_names,
            family_names,
            given_names,
            alternative_names
        ]

        # Get default creator name to show on detail screen.
        self._get_default_creator_name(list_parent_key,
                                       creator_lst)

        rtn_value['name'] = creator_lst
        creator_list_tmp = []
        creator_list = []

        # Get creators are displayed on creator pop up.
        self._get_creator_to_display_on_popup(creator_list_tmp)

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, creator_data in enumerate(creator_list_tmp):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=creator_data)
            if isinstance(creator_data, dict):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{creator_data} is dict")
                creator_temp = {}
                weko_logger(key='WEKO_COMMON_FOR_START')
                for i, (k, v) in enumerate(creator_data.items()):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=i, element=k)
                    if isinstance(v, list):
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{v} is list")
                        merged_data = {}
                        self._merge_creator_data(v, merged_data)
                        creator_temp[k] = merged_data
                weko_logger(key='WEKO_COMMON_FOR_END')
                creator_list.append(creator_temp)
        weko_logger(key='WEKO_COMMON_FOR_END')
        # Format creators
        formatted_creator_list = []
        self._format_creator_on_creator_popup(creator_list,
                                              formatted_creator_list)

        rtn_value.update({'order_lang': formatted_creator_list})
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=rtn_value)
        return rtn_value

    # TODO:
    def _format_creator_on_creator_popup(self, creators: Union[dict, list],
                                         des_creator: Union[
                                             dict, list]) -> NoReturn:
        """Format creator on creator popup.

        Args:
            creators: dict and list of creators.
            des_creator: dict and list of des_creator.

        Returns:
            None.

        """
        if isinstance(creators, list):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{creators} is list")

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, creator_data in enumerate(creators):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=creator_data)
                creator_tmp = {}
                self._format_creator_on_creator_popup(creator_data,
                                                      creator_tmp)
                des_creator.append(creator_tmp)
            weko_logger(key='WEKO_COMMON_FOR_END')
        elif isinstance(creators, dict):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{creators} is dict")
            alternative_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY[
                'alternative_name']
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (key, value) in enumerate(creators.items()):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=key)
                des_creator[key] = {}
                if key != self.no_language_key and isinstance(value, dict):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"key != {self.no_language_key} "
                                    f"and {value} is dict")
                    self._format_creator_name(value, des_creator[key])
                    des_creator[key][alternative_name_key] = value.get(
                        alternative_name_key, [])
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"key == {self.no_language_key} "
                                    f"and {value} is not dict")
                    des_creator[key] = value.copy()
                self._format_creator_affiliation(value.copy(),
                                                 des_creator[key])
            weko_logger(key='WEKO_COMMON_FOR_END')

    @staticmethod
    def _format_creator_name(creator_data: dict,
                             des_creator: dict) -> NoReturn:
        """Format creator name.

        Args:
            creator_data: Creator value.
            des_creator: Creator des creator.

        Returns:
            None.

        """
        creator_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_name']
        family_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['family_name']
        given_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['given_name']
        creator_name = creator_data.get(creator_name_key)
        family_name = creator_data.get(family_name_key)
        given_name = creator_data.get(given_name_key)
        if creator_name:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{creator_name} is not empty")
            des_creator[creator_name_key] = creator_name
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{creator_name} is empty")
            if not family_name:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{family_name} is empty")
                des_creator[creator_name_key] = given_name
            elif not given_name:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{given_name} is empty")
                des_creator[creator_name_key] = family_name
            else:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{family_name} and {given_name} is not empty")
                lst = []

                weko_logger(key='WEKO_COMMON_FOR_START')
                for idx, item in enumerate(family_name):
                    weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                count=idx, element=item)
                    _creator_name = item
                    if len(given_name) > idx:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{len(given_name)} > idx")
                        _creator_name += " " + given_name[idx]
                    lst.append(_creator_name)
                weko_logger(key='WEKO_COMMON_FOR_END')
                des_creator[creator_name_key] = lst

    @staticmethod
    def _format_creator_affiliation(creator_data: dict,
                                    des_creator: dict) -> NoReturn:
        """Format creator affiliation.

        Args:
            creator_data: Creator data.
            des_creator: Creator des creator.

        Returns:
            None.

        """
        def _get_max_list_length() -> int:
            """Get max length of list.

            Args:
                None.

            Returns:
                The max length of list.

            """
            max_data = max(
                [len(identifier_schema), len(affiliation_name),
                 len(identifier), len(identifier_uri)])
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=max_data)
            return max_data

        identifier_schema_key = WEKO_DEPOSIT_SYS_CREATOR_KEY[
            'affiliation_name_identifier_scheme']
        affiliation_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['affiliation_name']
        identifier_key = WEKO_DEPOSIT_SYS_CREATOR_KEY[
            'affiliation_name_identifier']
        identifier_uri_key = WEKO_DEPOSIT_SYS_CREATOR_KEY[
            'affiliation_name_identifier_URI']
        identifier_schema = creator_data.get(identifier_schema_key, [])
        affiliation_name = creator_data.get(affiliation_name_key, [])
        identifier = creator_data.get(identifier_key, [])
        identifier_uri = creator_data.get(identifier_uri_key, [])
        list_length = _get_max_list_length()
        idx = 0
        identifier_name_list = []
        identifier_list = []

        weko_logger(key='WEKO_COMMON_WHILE_START')
        while idx < list_length:
            weko_logger(key='WEKO_COMMON_WHILE_LOOP_ITERATION',
                        count="", element=idx)
            tmp_data = ""
            if len(identifier_schema) > idx:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{len(identifier_schema)} > idx")
                tmp_data += identifier_schema[idx]
            if len(affiliation_name) > idx:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{len(affiliation_name)} > idx")
                tmp_data += " " + affiliation_name[idx]
            identifier_name_list.append(tmp_data)

            identifier_tmp = {
                "identifier": "",
                "uri": "",
            }
            if len(identifier) > idx:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{len(identifier)} > idx")
                identifier_tmp['identifier'] = identifier[idx]
            if len(identifier_uri) > idx:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{len(identifier_uri)} > idx")
                identifier_tmp['uri'] = identifier_uri[idx]
            identifier_list.append(identifier_tmp)
            idx += 1
        weko_logger(key='WEKO_COMMON_WHILE_END')

        des_creator[affiliation_name_key] = identifier_name_list
        des_creator[identifier_key] = identifier_list

    def _get_creator_to_display_on_popup(self, creator_list: list):
        """Get creator to display on popup.

        Args:
            creator_list: Creator list.

        Returns:
            None.

        """
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, lang in enumerate(self.languages):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=lang)
            self._get_creator_to_show_popup(self.creator, lang,
                                            creator_list)
        weko_logger(key='WEKO_COMMON_FOR_END')

    def _merge_creator_data(self, creator_data: Union[list, dict],
                            merged_data: dict) -> NoReturn:
        """Merge creator data.

        Args:
            creator_data: Creator data.
            merged_data: Merged data.
        Returns:
            None.

        """
        def merge_data(key, value):
            if isinstance(merged_data.get(key), list):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{merged_data.get(key)} is list")
                merged_data[key].append(value)
            else:
                merged_data[key] = [value]

        if isinstance(creator_data, list):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{creator_data} is list")
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, data in enumerate(creator_data):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=data)
                self._merge_creator_data(data, merged_data)
            weko_logger(key='WEKO_COMMON_FOR_END')
        elif isinstance(creator_data, dict):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{creator_data} is dict")
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (k, v) in enumerate(creator_data.items()):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=k)
                if isinstance(v, str):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{v} is str")
                    merge_data(k, v)
            weko_logger(key='WEKO_COMMON_FOR_END')

    def _get_default_creator_name(self, list_parent_key: list,
                                  creator_names: list) -> NoReturn:
        """Get default creator name.

        Args:
            list_parent_key: parent list key.
            creator_names: Creators name.

        Returns:
            None.

        """
        def _get_creator(_language):
            """Get default creator name.

            Args:
                _language: language.

            Returns:
                None.

            """

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, parent_key in enumerate(list_parent_key):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=parent_key)
                self._format_creator_to_show_detail(_language,
                                                    parent_key, creator_names)
            weko_logger(key='WEKO_COMMON_FOR_END')
            if creator_names:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='creator_names is not empty')
                return

        _get_creator(self.current_language)
        # if current language has no creator

        if not creator_names:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='creator_names is empty')
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, lang in enumerate(self.languages):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=lang)
                _get_creator(lang)
                # if creator_names:
                #     weko_logger(key='WEKO_COMMON_IF_ENTER',
                #                 branch='creator_names is not empty')
                #     break
            weko_logger(key='WEKO_COMMON_FOR_END')


class _FormatSysBibliographicInformation:
    """Format system Bibliographic Information for detail page."""

    def __init__(self, bibliographic_meta_data_lst, props_lst):
        """Initialize format system Bibliographic Information for detail page.

        Args:
            bibliographic_meta_data_lst: bibliographic meta data list
            props_lst: Property list

        Returns:
            None.

        """
        # current_app.logger.error("bibliographic_meta_data_lst:{}".format(bibliographic_meta_data_lst))
        # current_app.logger.error("props_lst:{}".format(props_lst))

        self.bibliographic_meta_data_lst = bibliographic_meta_data_lst
        self.props_lst = props_lst

    def is_bibliographic(self):
        """Check bibliographic information.

        Args:
            None.

        Returns:
            None.

        """

        def check_key(_meta_data):
            """Check bibliographic information.

            Args:
                meta_data: meta data.

            Returns:
                None.

            """

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, key in enumerate(current_app.config.get('WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_SYS_KEY')):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=key)
                if key in _meta_data:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"k in {_meta_data}")
                    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=True)
                    return True
            weko_logger(key='WEKO_COMMON_FOR_END')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=False)
            return False

        meta_data = self.bibliographic_meta_data_lst
        if isinstance(meta_data, dict):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{meta_data} is dict")
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=check_key(meta_data))
            return check_key(meta_data)
        elif isinstance(meta_data, list) and len(meta_data) > 0 and isinstance(
                meta_data[0], dict):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{meta_data} is list "
                            f"and len(meta_data) > 0 "
                            f"and {meta_data[0]} is dict")
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=check_key(meta_data[0]))
            return check_key(meta_data[0])

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=False)
        return False

    def get_bibliographic_list(self, is_get_list):
        """Get bibliographic information list.

            Args:
                is_get_list: is get list.

            Returns:
                bibliographic list.

        """
        bibliographic_list = []

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, bibliographic in enumerate(self.bibliographic_meta_data_lst):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=bibliographic)
            title_data, magazine, length = self._get_bibliographic(
                bibliographic, is_get_list)
            bibliographic_list.append({
                'title_attribute_name': title_data,
                'magazine_attribute_name': magazine,
                'length': length
            })
        weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=bibliographic_list)
        return bibliographic_list

    def _get_bibliographic(self, bibliographic, is_get_list):
        """Get bibliographic information data.

            Args:
                is_get_list: is get list.
                bibliographic.

            Returns:
                title_data: title data.
                magazine.
                length.

        """
        title_data = []
        language = ''
        if bibliographic.get('bibliographic_titles'):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{bibliographic.get('bibliographic_titles')} is not empty")
            if is_get_list:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='is_get_list is not empty')
                current_lang = current_i18n.language
                # if not current_lang:
                #     weko_logger(key='WEKO_COMMON_IF_ENTER',
                #                 branch='current lang is empty')
                #     current_lang = 'en'
                title_data, language = self._get_source_title_show_list(
                    bibliographic.get('bibliographic_titles'), current_lang)
            else:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='is_get_list is empty')
                title_data = self._get_source_title(
                    bibliographic.get('bibliographic_titles'))
        if is_get_list:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='is_get_list is not empty')
            # if not language:
            #     weko_logger(key='WEKO_COMMON_IF_ENTER',
            #                 branch='language is empty')
            #     language = current_lang
            bibliographic_info, length = self._get_bibliographic_show_list(
                bibliographic, language)
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='is_get_list is empty')
            bibliographic_info, length = self._get_bibliographic_information(
                bibliographic)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=title_data)
        return title_data, bibliographic_info, length

    def _get_property_name(self, key):
        """Get property name.

            Args:
                key: Property key.

            Returns:
                key.

        """
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, lst in enumerate(self.props_lst):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=lst)
            if key == lst[0].split('.')[-1]:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"key == {lst[0].split('.')[-1]}")
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=lst[2])
                return lst[2]
        weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=key)
        return key

    @staticmethod
    def _get_translation_key(key, lang):
        """Get translation key.

            Args:
                key: Property key.
                lang: : Language.

            Returns:
                Translation key.

        """
        bibliographic_translation = current_app.config.get(
            'WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS')
        if key in bibliographic_translation:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"k in {bibliographic_translation}")
            weko_logger(key='WEKO_COMMON_RETURN_VALUE',
                        value=bibliographic_translation.get(key, {}).get(lang, ''))
            return bibliographic_translation.get(key, {}).get(lang, '')

    def _get_bibliographic_information(self, bibliographic):
        """Get bibliographic information data.

            Args:
                bibliographic.

            Returns:
                bibliographic_info_list: bibliographic info list.

        """
        bibliographic_info_list = []

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, key in enumerate(current_app.config.get('WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_KEY')):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=key)
            if key == 'p.':
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{key} == 'p.'")
                page = self._get_page_tart_and_page_end(
                    bibliographic.get('bibliographicPageStart'),
                    bibliographic.get('bibliographicPageEnd'))
                if page != '':
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{page} != ''")
                    bibliographic_info_list.append({key: page})
            elif key == 'bibliographicIssueDates':
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='key is bibliographicIssueDates')
                dates = self._get_issue_date(
                    bibliographic.get(key))
                if dates:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='dates is not empty')
                    bibliographic_info_list.append(
                        {self._get_property_name(key): " ".join(
                            str(x) for x in dates)})
            elif bibliographic.get(key):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='bibliographic is not empty')
                bibliographic_info_list.append(
                    {self._get_property_name(key): bibliographic.get(key)})
        weko_logger(key='WEKO_COMMON_FOR_END')
        length = len(bibliographic_info_list) if len(
            bibliographic_info_list) else 0
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=bibliographic_info_list)
        return bibliographic_info_list, length

    def _get_bibliographic_show_list(self, bibliographic, language):
        """Get bibliographic show list data.

            Args:
                bibliographic.
                language.

            Returns:
                bibliographic_info_list: bibliographic info list.

        :param bibliographic:
        :return:
        """
        bibliographic_info_list = []

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, key in enumerate(current_app.config.get('WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_KEY')):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=key)
            if key == 'p.':
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{key} == 'p.'")
                page = self._get_page_tart_and_page_end(
                    bibliographic.get('bibliographicPageStart'),
                    bibliographic.get('bibliographicPageEnd'))
                if page != '':
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{page} != ''")
                    bibliographic_info_list.append({key: page})
            elif key == 'bibliographicIssueDates':
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='key is bibliographicIssueDates')
                dates = self._get_issue_date(
                    bibliographic.get(key))
                if dates:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch='dates is not empty')
                    bibliographic_info_list.append(
                        {self._get_translation_key(key, language): " ".join(
                            str(x) for x in dates)})
            elif bibliographic.get(key):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{bibliographic.get(key)} != ''")
                bibliographic_info_list.append({
                    self._get_translation_key(key, language): bibliographic.get(
                        key)
                })
        weko_logger(key='WEKO_COMMON_FOR_END')
        length = len(bibliographic_info_list) if len(
            bibliographic_info_list) else 0
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=bibliographic_info_list)
        return bibliographic_info_list, length

    @staticmethod
    def _get_source_title(source_titles):
        """Get source title.

        Args:
            source_titles(list): source titles.

        Returns:
            title_data(list): list of title data.
        """
        title_data = []
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, source_title in enumerate(source_titles):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=source_title)
            title = (source_title['bibliographic_titleLang'] + ' : '
                if source_title.get('bibliographic_titleLang') else '')
            title += source_title[
                'bibliographic_title'] if source_title.get(
                'bibliographic_title') else ''
            title_data.append(title)
        weko_logger(key='WEKO_COMMON_FOR_END')
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=title_data)
        return title_data

    @staticmethod
    def _get_source_title_show_list(source_titles, current_lang):
        """Get source title in show list.

        Args:
            current_lang(str): current language.
            source_titles(list): source titles.

        Returns:
            title_data_none_lang(list): list of title and language.
        """
        value_en = None
        value_latn = None
        title_data_lang = []
        title_data_none_lang = []
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, source_title in enumerate(source_titles):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=source_title)
            key = source_title.get('bibliographic_titleLang')
            value = source_title.get('bibliographic_title')
            if not value:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{value} is empty")
                continue
            elif current_lang == key:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{current_lang} == key")

                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=key)
                return value, key
            else:
                if key:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='key is not empty')
                    if key == 'en':
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{key} == 'en'")
                        value_en = value
                    elif key == 'ja-Latn':
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{key} == 'ja-Latn'")
                        value_latn = value
                    else:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{key} == 'other'")
                        title = {}
                        title[key] = value
                        title_data_lang.append(title)
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{key} is empty")
                    title_data_none_lang.append(value)
        weko_logger(key='WEKO_COMMON_FOR_END')

        if len(title_data_none_lang) > 0:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{len(title_data_none_lang)} > 0")
            if source_titles[0].get('bibliographic_title')==title_data_none_lang[0]:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{source_titles[0].get('bibliographic_title')} "
                                f"== {title_data_none_lang[0]}")
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=title_data_none_lang[0])
                return title_data_none_lang[0],''

        if value_latn:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='value_latn is not empty')
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=value_latn)
            return value_latn, 'ja-Latn'

        if value_en and (current_lang != 'ja' or
                         not current_app.config.get("WEKO_RECORDS_UI_LANG_DISP_FLG", False)):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{value_en} is not empty "
                            f"and ({current_lang} != 'ja' or "
                            f"'WEKO_RECORDS_UI_LANG_DISP_FLG' is False")
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=value_en)
            return value_en, 'en'

        if len(title_data_lang) > 0:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"{len(title_data_lang)} > 0")
            if (current_lang != 'en'
                    or not current_app.config.get(
                        "WEKO_RECORDS_UI_LANG_DISP_FLG", False)):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"{current_lang} != 'en' or"
                                "'WEKO_RECORDS_UI_LANG_DISP_FLG' is False")

                result = (list(title_data_lang[0].values())[0],
                    list(title_data_lang[0])[0])
                weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
                return result
            else:
                weko_logger(key='WEKO_COMMON_FOR_START')
                for t in title_data_lang:
                    if list(t)[0] != 'ja':
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch=f"{list(t)[0]} != 'ja'")
                        result = list(t.values())[0], list(t)[0]
                        weko_logger(
                            key='WEKO_COMMON_RETURN_VALUE', value=result)
                        return result
                    weko_logger(key='WEKO_COMMON_FOR_END')
        result = ((title_data_none_lang[0], 'ja')
                  if len(title_data_none_lang) > 0 else (None, 'ja'))
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    @staticmethod
    def _get_page_tart_and_page_end(page_start, page_end):
        """Get page start and page end.

        Args:
            page_start(str): page start.
            page_end(str): page end.

        Returns:
            page(str): page.
        """
        page = ''
        page += page_start if page_start is not None else ''
        if page_end is not None:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='page_end is not None')
            temp = page_end if page == '' else '-' + page_end
            page += temp if page_end else ''

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=page)
        return page

    @staticmethod
    def _get_issue_date(issue_date):
        """Get issue dates.

        Args:
            issue_date(list): list of issue date.

        Returns:
            date(list): list of issue date.
        """
        date = []
        issue_type = 'Issued'
        if isinstance(issue_date, list):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='issue_date is list')
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, issued_date in enumerate(issue_date):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=issued_date)
                if (issued_date.get('bibliographicIssueDate')
                        and issued_date.get(
                            'bibliographicIssueDateType') == issue_type):
                    weko_logger(
                        key='WEKO_COMMON_IF_ENTER',
                        branch=f"'bibliographicIssueDate' is in issued_date "
                            "and 'bibliographicIssueDateType' in issued_date "
                            "== issue_type"
                    )
                    date.append(issued_date.get('bibliographicIssueDate'))
            weko_logger(key='WEKO_COMMON_FOR_END')
        elif (isinstance(issue_date, dict)
                and issue_date.get('bibliographicIssueDate')
                and issue_date.get('bibliographicIssueDateType') == issue_type):
            weko_logger(
                key='WEKO_COMMON_IF_ENTER',
                branch=f"'issue_date' is dict and 'bibliographicIssueDate' is "
                    "in issue_date and 'bibliographicIssueDateType' in "
                    "issue_date == issue_type")
            date.append(issue_date.get('bibliographicIssueDate'))
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=date)
        return date
