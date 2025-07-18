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

"""WEKO Search Serializer."""

import pickle
from datetime import datetime

import pytz
from flask import request
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from invenio_records_rest.views import RecordsListResource
from invenio_stats.views import QueryRecordViewCount, QueryFileStatsCount
from weko_index_tree.api import Index

from weko_records.api import Mapping
from weko_records.models import ItemType, ItemTypeName, ItemTypeProperty

from .dc import DcWekoBaseExtension, DcWekoEntryExtension
from .feed import WekoFeedGenerator
from .opensearch import OpensearchEntryExtension, OpensearchExtension
from .prism import PrismEntryExtension, PrismExtension
from .wekolog import WekologEntryExtension, WekologExtension


def get_mapping(item_type_mapping, mapping_type):
    """Format itemtype mapping data.

    [Key:Schema, Value:ItemId]
    :param item_type_mapping:
    :param mapping_type:
    :return:
    """
    def get_schema_key_info(schema, parent_key, schema_json={}):

        for k, v in schema.items():
            key = parent_key + '.' + k if parent_key else k
            if isinstance(v, dict):
                child_key = pickle.loads(pickle.dumps(key, -1))
                get_schema_key_info(v, child_key, schema_json)
            else:
                schema_json[key] = v

        return schema_json

    schema = {}
    for item_id, maps in item_type_mapping.items():
        if mapping_type in maps.keys() and isinstance(maps[mapping_type], dict):
            item_schema = get_schema_key_info(maps[mapping_type], '', {})
            for k, v in item_schema.items():
                item_schema[k] = item_id + '.' + v if v else item_id
            schema.update(item_schema)

    return schema


def get_full_mapping(item_type_mapping, mapping_type):
    """Get itemtype mapping data.

    [Key:Schema, Value:ItemId]
    :param item_type_mapping:
    :param mapping_type:
    :return:
    """
    def get_schema_key_info(schema, parent_key, schema_json={}):
        for k, v in schema.items():
            key = parent_key + '.' + k if parent_key else k
            if isinstance(v, dict):
                child_key = pickle.loads(pickle.dumps(key, -1))
                get_schema_key_info(v, child_key, schema_json)
            else:
                properties = schema_json.get(key, [])
                properties.append(v)
                schema_json[key] = properties
        return schema_json

    schema = {}
    for item_id, maps in item_type_mapping.items():
        if mapping_type in maps.keys() \
                and isinstance(maps[mapping_type], dict):
            item_schema = get_schema_key_info(maps[mapping_type], '', {})
            for k, v in item_schema.items():
                properties = schema.get(k, [])
                for val in v:
                    properties.append(item_id + '.' + val if val else item_id)
                schema[k] = properties

    return schema


def get_mapping_inactive_show_list(item_type_mapping, mapping_type):
    """Format itemtype mapping data.

    [Key:Schema, Value:ItemId]
    :param item_type_mapping:
    :param mapping_type:
    :return:
    """
    def get_schema_key_info(schema, parent_key, schema_json={}):

        for k, v in schema.items():
            key = parent_key + '.' + k if parent_key else k
            if isinstance(v, dict):
                child_key = pickle.loads(pickle.dumps(key, -1))
                get_schema_key_info(v, child_key, schema_json)
            else:
                schema_json[key] = v

        return schema_json

    schema = {}
    for item_id, maps in item_type_mapping.items():
        if mapping_type in maps.keys() and isinstance(maps[mapping_type], dict):
            item_schema = get_schema_key_info(maps[mapping_type], '', {})
            temp_schema = {}
            for k, v in item_schema.items():
                tempId = item_id + '.' + v if v else item_id
                if k in schema:
                    k = tempId + k
                temp_schema[k] = tempId
            schema.update(temp_schema)

    return schema


def get_metadata_from_map(item_data, item_id):
    """Get item metadata from search result.

    :param item_data:
    :param item_id:
    :return:
    """
    def get_sub_item_data(props, parent_key=''):
        key = parent_key if parent_key else ''
        value = {}

        if isinstance(props, list):
            for prop in props:
                if type(prop) is str:
                    value[key] = prop
                else:
                    for k, v in prop.items():
                        if isinstance(v, list) or isinstance(v, dict):
                            value.update(get_sub_item_data(v, key + '.' + k))
                        else:
                            sub_key = key + '.' + k if key else k
                            if sub_key in value:
                                if isinstance(value[sub_key], list):
                                    value[sub_key].append(v)
                                else:
                                    _value = value[sub_key]
                                    value[sub_key] = [_value, v]
                            else:
                                value[sub_key] = v
        else:
            for k, v in props.items():
                if isinstance(v, list) or isinstance(v, dict):
                    value.update(get_sub_item_data(v, key + '.' + k))
                else:
                    sub_key = key + '.' + k if key else k
                    if sub_key in value:
                        if isinstance(value[sub_key], list):
                            value[sub_key].append(v)
                        else:
                            _value = value[sub_key]
                            value[sub_key] = [_value, v]
                    else:
                        value[sub_key] = v
        return value

    item_value = {}
    if 'attribute_value' in item_data:
        item_value[item_id] = item_data['attribute_value']
    elif 'attribute_value_mlt' in item_data:
        item_value.update(get_sub_item_data(item_data['attribute_value_mlt'],
                                            item_id))

    return item_value


def get_attribute_schema(schema_id):
    """Get schema of item type property.

    :param schema_id:
    :return: schema in json
    """
    with db.session.no_autoflush:
        schema = ItemTypeProperty.query.filter_by(
            id=schema_id).one_or_none()
        if schema:
            return schema.schema
    return None


def get_item_type_name_id(item_type_id):
    """Get item type name id.

    :param item type id:
    :return: item name id
    """
    with db.session.no_autoflush:
        item_name_id = ItemType.query.filter_by(
            id=item_type_id).one_or_none()
        if item_name_id:
            return item_name_id.name_id
    return 0


def get_item_type_name(item_type_id):
    """Get item type name.

    :param item type id:
    :return: name in string
    """
    with db.session.no_autoflush:
        name_id = get_item_type_name_id(item_type_id)
        if name_id:
            type_name = ItemTypeName.query.filter_by(
                id=name_id).one_or_none()
            if type_name:
                return type_name.name
    return None


def get_wekolog(hit, log_term):
    """Get wekolog property.

    :param
        log_term    : Aggregation date
    :return dict
        log_term    : Aggregation date
        view        : Number of item views
        download    : Number of item downloads
    """

    # get record id
    record_id = hit['_id']

    # get bucket id
    meta_data = RecordMetadata.query.filter_by(id=record_id).first()
    bucket_id = meta_data.json['_buckets']['deposit']

    # get view count
    cls_view_count = QueryRecordViewCount()
    view_count_data = cls_view_count.get_data(record_id, log_term)
    view_count = int(view_count_data.get('total', 0))

    # get download count
    download_total = 0
    query_file_download = QueryFileStatsCount()
    for k, v in meta_data.json.items():
        if isinstance(v, dict) and v.get('attribute_type') == 'file':
            for v2 in v.get('attribute_value_mlt'):
                file_name = v2.get('filename')
                if file_name:
                    stats_count_data = query_file_download.get_data(bucket_id, file_name, log_term)
                    download_count = int(stats_count_data.get('download_total', 0))
                    download_total += download_count

    return {'terms': log_term, 'view': str(view_count), 'download': str(download_total)}


class OpenSearchDetailData:
    """OpenSearch detail data."""

    OUTPUT_ATOM = "atom"
    OUTPUT_RSS = "rss"

    def __init__(self, pid_fetcher, search_result, output_type, links=None,
                 item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param output_type: Output type.
        :param links:Dictionary of links to add to response
        :param item_links_factory:
        """
        self.pid_fetcher = pid_fetcher
        self.search_result = search_result
        self.output_type = output_type
        self.links = links
        self.item_links_factory = item_links_factory
        self.kwargs = kwargs

    def output_open_search_detail_data(self):
        """Output open search detail data.

        :return:
        """
        fg = WekoFeedGenerator()

        # Add extentions
        fg.register_extension('dc',
                              DcWekoBaseExtension,
                              DcWekoEntryExtension)
        fg.register_extension('opensearch',
                              extension_class_feed=OpensearchExtension,
                              extension_class_entry=OpensearchEntryExtension)
        fg.register_extension('prism',
                              extension_class_feed=PrismExtension,
                              extension_class_entry=PrismEntryExtension)
        fg.register_extension('wekolog',
                              extension_class_feed=WekologExtension,
                              extension_class_entry=WekologEntryExtension)

        # Set title
        index_meta = {}
        _keywords = request.args.get('q', '')
        _index_id = request.args.get('index_id', type=str)

        # Set language
        request_lang = request.args.get('lang', '')
        if request_lang not in ['ja', 'en']:
            request_lang = 'ja'
        fg.language(request_lang)

        if _index_id:
            index = None
            if _index_id.isnumeric():
                index = Index.query.filter_by(id=int(_index_id)).one_or_none()
            if request_lang == 'en':
                _index_name = 'Nonexistent Index' if index is None else index.index_name_english
            else:
                _index_name = 'Nonexistent Index' if index is None else index.index_name

            index_meta[_index_id] = 'Unnamed Index' \
                if _index_name is None else _index_name

            fg.title('WEKO OpenSearch : ' + str(index_meta[_index_id]))
        else:
            fg.title('WEKO OpenSearch : ' + str(_keywords))

        # Set link
        fg.link(href=request.url)

        # Set totalResults
        _total_results = self.search_result['hits']['total']
        fg.opensearch.totalResults(str(_total_results))

        if self.output_type == self.OUTPUT_ATOM:
            # Set id
            fg.id(request.url)

            # Set updated
            fg.updated(datetime.now(pytz.utc))
        else:
            # Set date
            fg.dc.dc_date(str(datetime.now(pytz.utc)))

            # Set Request URL
            if int(_total_results) != 0:
                fg.requestUrl(request.url)

        start_page = request.args.get('page_no', type=str)
        start_page = 1 if start_page is None or not start_page.isnumeric() \
            else int(start_page)

        size = request.args.get('list_view_num', type=str)
        size = 20 if size is None or not size.isnumeric() else int(size)
        size = RecordsListResource.adjust_list_view_num(size)

        # Set startIndex
        _start_index = (start_page - 1) * size + 1
        fg.opensearch.startIndex(str(_start_index))

        # Set itemPerPage
        _item_per_page = len(self.search_result['hits']['hits'])
        fg.opensearch.itemsPerPage(str(_item_per_page))

        # Aggregate parameter
        log_term = request.args.get('log_term', '')

        rss_items = []
        jpcoar_map = {}
        for hit in self.search_result['hits']['hits']:
            item_metadata = hit['_source']['_item_metadata']

            item_type_id = item_metadata['item_type_id']
            type_mapping = Mapping.get_record(item_type_id)

            if item_type_id in jpcoar_map:
                item_map = jpcoar_map[item_type_id]
            else:
                item_map = get_mapping(type_mapping, 'jpcoar_mapping')
                jpcoar_map[item_type_id] = item_map

            fe = fg.add_entry()

            # Set title
            fe.title(item_metadata.get('item_title', ''))

            # Set link
            _pid = item_metadata['control_number']
            item_url = request.host_url + 'records/' + _pid
            fe.link(href=item_url, rel='alternate', type='text/xml')

            oai_param = 'oai?verb=GetRecord&metadataPrefix=jpcoar&identifier='
            if self.output_type == self.OUTPUT_ATOM:
                # Set oai
                _oai = hit['_source']['_oai']['id']
                item_url = request.host_url + oai_param + _oai
                fe.link(href=item_url, rel='alternate', type='text/xml')

                # Set id
                fe.id(item_url)

                # Set Y-handle URL
                try:
                    recid = PersistentIdentifier.get('recid', _pid)
                    yhdl = PersistentIdentifier.get_by_object('yhdl', 'rec', recid.object_uuid)
                    yhdl_value = yhdl.pid_value
                    if not yhdl_value.endswith('/'):
                        yhdl_value += '/'
                    fe.link(href=yhdl_value, rel='alternate', type='text/html')
                except:
                    pass
            else:
                # Set oai
                _oai = hit['_source']['_oai']['id']
                oai_url = request.host_url + oai_param + _oai
                fe.seeAlso(oai_url)

                # Set item url
                fe.itemUrl(item_url)

                # Add to channel item list
                rss_items.append(item_url)

            # Set weko id
            fe.dc.dc_identifier(_pid)

            # Set aggregationType
            _aggregation_type = 'type.@value'
            if _aggregation_type in item_map:
                aggregation_type_key = item_map[_aggregation_type]
                item_id = aggregation_type_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    type_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)
                    aggregation_types = None
                    if isinstance(type_metadata, dict):
                        aggregation_types = type_metadata.get(
                            aggregation_type_key)
                    if aggregation_types:
                        if isinstance(aggregation_types, list):
                            for aggregation_type in aggregation_types:
                                fe.prism.aggregationType(aggregation_type)
                        else:
                            fe.prism.aggregationType(aggregation_types)

            # Set item type
            fe.dc.dc_type(hit['_source']['itemtype'])

            # Set mimeType
            _mime_type = 'file.mimeType.@value'
            if _mime_type in item_map:
                mime_type_key = item_map[_mime_type]
                item_id = mime_type_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    file_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)
                    mime_types = None
                    if isinstance(file_metadata, dict):
                        mime_types = file_metadata.get(mime_type_key)
                    if mime_types:
                        if isinstance(mime_types, list):
                            for mime_type in mime_types:
                                fe.dc.dc_format(mime_type)
                        else:
                            fe.dc.dc_format(mime_types)

            # Set file uri
            _uri = 'file.URI.@value'
            if _uri in item_map:
                uri_key = item_map[_uri]
                item_id = uri_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    uri_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)
                    uri_list = None
                    if isinstance(uri_metadata, dict):
                        uri_list = uri_metadata.get(uri_key)
                    if uri_list:
                        if isinstance(uri_list, list):
                            for uri in uri_list:
                                fe.dc.dc_identifier(uri, False)
                        else:
                            fe.dc.dc_identifier(uri_list, False)

            # Set author info
            self._set_author_info(fe, item_map, item_metadata, request_lang)

            # Set publisher
            self._set_publisher(fe, item_map, item_metadata, request_lang)

            # Set subject
            if _index_id and not request.args.get('idx'):
                fe.dc.dc_subject(index_meta[_index_id])
            else:
                index_id = item_metadata['path'][0]

                index_name = None
                if index_id in index_meta:
                    index_name = index_meta[index_id]
                else:
                    index = Index.query.filter_by(id=index_id).one_or_none()
                    if index is not None:
                        if request_lang == 'en':
                            index_name = index.index_name_english
                        else:
                            index_name = index.index_name
                        index_meta[index_id] = index_name
                if index_name:
                    fe.dc.dc_subject(index_name)

            # Set publicationName
            _source_title_value = 'sourceTitle.@value'
            if _source_title_value in item_map:
                source_title_key = item_map[_source_title_value]
                item_id = source_title_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    source_title_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)
                    source_titles = None
                    if isinstance(source_title_metadata, dict):
                        source_titles = source_title_metadata.get(
                            source_title_key)

                    if source_titles:
                        if isinstance(source_titles, list):
                            for source_title in source_titles:
                                fe.prism.publicationName(source_title)
                        else:
                            fe.prism.publicationName(source_titles)

            # Set sourceIdentifier
            self._set_source_identifier(fe, item_map, item_metadata)

            # Set volume
            _volume = 'volume.@value'
            if _volume in item_map:
                volume_key = item_map[_volume]
                item_id = volume_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    volume_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    volumes = None
                    if isinstance(volume_metadata, dict):
                        volumes = volume_metadata.get(volume_key)
                    if volumes:
                        if isinstance(volumes, list):
                            for volume in volumes:
                                fe.prism.volume(volume)
                        else:
                            fe.prism.volume(volumes)

            # Set number
            _issue = 'issue.@value'
            if _issue in item_map:
                issue_key = item_map[_issue]
                item_id = issue_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    issue_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    issues = None
                    if isinstance(issue_metadata, dict):
                        issues = issue_metadata.get(issue_key)

                    if issues:
                        if isinstance(issues, list):
                            for issue in issues:
                                fe.prism.number(issue)
                        else:
                            fe.prism.number(issues)

            # Set startingPage
            _page_start = 'pageStart.@value'
            if _page_start in item_map:
                page_start_key = item_map[_page_start]
                item_id = page_start_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    page_start_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    page_starts = None
                    if isinstance(page_start_metadata, dict):
                        page_starts = page_start_metadata.get(page_start_key)

                    if page_starts:
                        if isinstance(page_starts, list):
                            for page_start in page_starts:
                                fe.prism.startingPage(page_start)
                        else:
                            fe.prism.startingPage(page_starts)

            # Set endingPage
            _page_end = 'pageEnd.@value'
            if _page_end in item_map:
                page_end_key = item_map[_page_end]
                item_id = page_end_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    page_end_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)
                    page_ends = None
                    if isinstance(page_end_metadata, dict):
                        page_ends = page_end_metadata.get(page_end_key)

                    if page_ends:
                        if isinstance(page_ends, list):
                            for page_end in page_ends:
                                fe.prism.endingPage(page_end)
                        else:
                            fe.prism.endingPage(page_ends)

            # Set publicationDate
            self._set_publication_date(fe, item_map, item_metadata)

            # Set content
            self._set_description(fe, item_map, item_metadata, request_lang)

            if self.output_type == self.OUTPUT_ATOM:
                # Set updated
                _updated = hit['_source']['_updated']
                if _updated:
                    fe.updated(_updated)
            else:
                publish_date = item_metadata['pubdate']['attribute_value']
                if publish_date:
                    fe.dc.dc_date(str(datetime.now(pytz.utc)))

                # Set file preview url
                fe.prism.url(item_url)

            # Set creationDate
            _creation_date = hit['_source']['_created']
            if _creation_date:
                fe.prism.creationDate(_creation_date)

            # Set modificationDate
            _modification_date = hit['_source']['_updated']
            if _modification_date:
                fe.prism.modificationDate(_modification_date)

            # Set Wekolog
            if log_term:
                wekolog = get_wekolog(hit, log_term)
                fe.wekolog.terms(wekolog['terms'])
                fe.wekolog.view(wekolog['view'])
                fe.wekolog.download(wekolog['download'])

        if self.output_type == self.OUTPUT_ATOM:
            return fg.atom_str(pretty=True)
        else:
            # Set channel items
            fg.items(rss_items)

            return fg.rss_str(pretty=True)

    def _set_description(self, fe, item_map, item_metadata, request_lang):
        _description_attr_lang = 'description.@attributes.xml:lang'
        _description_value = 'description.@value'
        if _description_value in item_map:
            description_key = item_map[_description_value]
            description_key_lang = item_map[_description_attr_lang]
            item_id = description_key.split('.')[0]
            from weko_records_ui.utils import get_pair_value
            # Get item data
            if item_id in item_metadata:
                description_data = get_pair_value(
                    description_key.split('.')[1:],
                    description_key_lang.split('.')[1:],
                    item_metadata[item_id]['attribute_value_mlt'])
                for description_text, description_lang in description_data:
                    if description_text and description_lang:
                        if request_lang:
                            if description_lang == request_lang:
                                fe.content(description_text, description_lang)
                        else:
                            fe.content(description_text,
                                       description_lang)

    def _set_publication_date(self, fe, item_map, item_metadata):
        if self.output_type == self.OUTPUT_ATOM:
            _date = 'date.@value'
            if _date in item_map:
                date_key = item_map[_date]
                item_id = date_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    date_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)
                    if not isinstance(date_metadata, dict):
                        return
                    dates = date_metadata.get(date_key)

                    if dates:
                        if isinstance(dates, list):
                            for date in dates:
                                fe.prism.publicationDate(date)
                        else:
                            fe.prism.publicationDate(dates)
        else:
            _date_attr_type = 'date.@attributes.dateType'
            _date = 'date.@value'
            if _date in item_map:
                date_key = item_map[_date]
                item_id = date_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    date_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)
                    if not isinstance(date_metadata, dict)\
                            or date_metadata.get(date_key) is None:
                        return
                    dates = date_metadata[date_key]
                    date_types = date_metadata.get(item_map[_date_attr_type])

                    if dates and date_types:
                        if isinstance(dates, list):
                            for i in range(len(dates)):
                                date_type = date_types[i]
                                if date_type and date_type == 'Issued':
                                    fe.prism.publicationDate(dates[i])

                        elif date_types and date_types == 'Issued':
                            fe.prism.publicationDate(dates)

    def _set_publisher(self, fe, item_map, item_metadata, request_lang):
        _publisher_attr_lang = 'publisher.@attributes.xml:lang'
        _publisher_value = 'publisher.@value'
        if _publisher_value in item_map:
            publisher_key = item_map[_publisher_value]
            publisher_key_lang = item_map[_publisher_attr_lang]
            item_id = publisher_key.split('.')[0]
            from weko_records_ui.utils import get_pair_value
            # Get item data
            if item_id in item_metadata:
                publisher_data = get_pair_value(
                    publisher_key.split('.')[1:],
                    publisher_key_lang.split('.')[1:],
                    item_metadata[item_id]['attribute_value_mlt'])
                for publisher_name, publisher_lang in publisher_data:
                    if publisher_name and publisher_lang:
                        if request_lang:
                            if publisher_lang == request_lang:
                                fe.dc.dc_publisher(publisher_name,
                                                   publisher_lang)
                        else:
                            fe.dc.dc_publisher(publisher_name,
                                               publisher_lang)

    def _set_source_identifier(self, fe, item_map, item_metadata):
        if self.output_type == self.OUTPUT_ATOM:
            _source_identifier_value = 'sourceIdentifier.@value'
            if _source_identifier_value in item_map:
                source_identifier_key = item_map[_source_identifier_value]
                item_id = source_identifier_key.split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    source_identifier_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    if not isinstance(source_identifier_metadata, dict) \
                            or source_identifier_metadata.get(
                            source_identifier_key) is None:
                        return
                    source_identifiers = source_identifier_metadata.get(
                        source_identifier_key)

                    if source_identifiers:
                        if isinstance(source_identifiers, list):
                            for source_identifier in source_identifiers:
                                fe.prism.issn(source_identifier)
                        else:
                            fe.prism.issn(source_identifiers)
        else:
            _source_identifier_attr_type = \
                'sourceIdentifier.@attributes.identifierType'
            _source_identifier_value = 'sourceIdentifier.@value'
            if _source_identifier_value in item_map:
                item_id = item_map[_source_identifier_value].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    source_identifier_metadata = get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    source_identifiers = source_identifier_metadata[
                        item_map[_source_identifier_attr_type]]

                    source_identifier_types = source_identifier_metadata[
                        item_map[_source_identifier_value]]

                    if source_identifiers:
                        if isinstance(source_identifiers, list):
                            for i in range(len(source_identifiers)):
                                source_identifier_type = \
                                    source_identifier_types[i]
                                if source_identifier_type \
                                        and source_identifier_type == 'ISSN':
                                    fe.prism.issn(source_identifiers[i])

                        elif source_identifier_types \
                                and source_identifier_types == 'ISSN':
                            fe.prism.issn(source_identifiers)

    def _set_author_info(self, fe, item_map, item_metadata, request_lang):
        _creator_name_value = 'creator.creatorName.@value'
        if _creator_name_value in item_map:
            item_id = item_map[_creator_name_value].split('.')[0]

            # Get item data
            if item_id in item_metadata:
                creator_metadata = get_metadata_from_map(
                    item_metadata[item_id], item_id)

                create_name_key = item_map[_creator_name_value]
                if not isinstance(creator_metadata, dict) \
                        or creator_metadata.get(create_name_key) is None:
                    return

                creator_names = creator_metadata[create_name_key]

                _creator_name_attr_lang = item_id + '.' + 'creatorNameLang'
                creator_name_langs = creator_metadata[
                    _creator_name_attr_lang] \
                    if _creator_name_attr_lang in creator_metadata else None

                if creator_name_langs:
                    if isinstance(creator_name_langs, list):
                        for i in range(len(creator_name_langs)):
                            creator_name_lang = creator_name_langs[i]
                            if request_lang:
                                if creator_name_lang == request_lang:
                                    fe.author({'name': creator_names[i],
                                               'lang': creator_name_lang})
                            else:
                                fe.author({'name': creator_names[i],
                                           'lang': creator_name_lang})
                    else:
                        if request_lang:
                            if creator_name_langs == request_lang:
                                fe.author({'name': creator_names,
                                           'lang': creator_name_langs})
                        else:
                            fe.author({'name': creator_names,
                                       'lang': creator_name_langs})
