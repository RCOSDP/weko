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

from flask import current_app, json, request, url_for

from invenio_records_rest.serializers.json import JSONSerializer
from weko_records.api import Mapping
from .feed import WekoFeedGenerator
from datetime import datetime
import pytz, copy
from .opensearch import OpensearchExtension, OpensearchEntryExtension
from .prism import PrismExtension, PrismEntryExtension
from .dc import DcWekoBaseExtension, DcWekoEntryExtension
from weko_index_tree.api import Index

class AtomSerializer(JSONSerializer):
    """
    Serialize search result to atom format.
    """

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.
        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
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

        # Set title
        index_meta = {}
        _keywords = request.args.get('q', '')
        _indexId = request.args.get('index_id')

        if _indexId:
            index = Index.query.filter_by(id=_indexId).one_or_none()
            _indexName = index.index_name
            index_meta[_indexId] = _indexName if _indexName else \
                'Nonexistent Index'

            fg.title('WEKO OpenSearch: ' + str(index_meta[_indexId]))
        else:
            fg.title('WEKO OpenSearch: ' + str(_keywords))

        # Set link
        fg.link(href=request.url)

        # Set id
        fg.id(request.url)

        # Set updated
        fg.updated(datetime.now(pytz.utc))

        # Set totalResults
        _totalResults = search_result['hits']['total']
        fg.opensearch.totalResults(str(_totalResults))

        # Set startIndex
        _startIndex = request.args.get('page')
        fg.opensearch.startIndex(str(_startIndex))

        # Set itemPerPage
        _itemPerPage = request.args.get('size')
        fg.opensearch.itemsPerPage(str(_itemPerPage))

        if not _keywords and not _indexId:
            return fg.atom_str(pretty=True)

        jpcoar_map = {}
        for hit in search_result['hits']['hits']:

            item_metadata = hit['_source']['_item_metadata']

            item_type_id = item_metadata['item_type_id']
            type_mapping = Mapping.get_record(item_type_id)

            if item_type_id in jpcoar_map:
                item_map = jpcoar_map[item_type_id]
            else:
                item_map = self.get_mapping(type_mapping, 'jpcoar_mapping')
                jpcoar_map[item_type_id] = item_map

            fe = fg.add_entry()

            # Set title
            if 'title_en' in item_metadata:
                _enTitle = item_metadata['title_en']['attribute_value']
            if 'title_ja' in item_metadata:
                _jaTitle = item_metadata['title_ja']['attribute_value']

            if 'lang' in item_metadata:
                _lang = item_metadata['lang']['attribute_value']
            if _lang:
                if(_lang == 'en'):
                    if _enTitle:
                        fe.title(_enTitle)
                    elif _jaTitle:
                        fe.title(_jaTitle)
                else:
                    if _jaTitle:
                        fe.title(_jaTitle)
                    elif _enTitle:
                        fe.title(_enTitle)
            else:
                if _enTitle:
                    fe.title(_enTitle)
                if _jaTitle:
                    fe.title(_jaTitle)

            # Set link
            _pid = item_metadata['control_number']
            item_url = request.host_url + 'records/' + _pid
            fe.link(href=item_url, rel='alternate', type='text/xml')

            # Set oai
            _oai = item_metadata['_oai']['id']
            item_url = request.host_url + 'oai2d?verb=GetRecord&metadataPrefix=jpcoar&identifier=' + _oai
            fe.link(href=item_url, rel='alternate', type='text/xml')

            # Set id
            fe.id(item_url)

            # Set weko id
            fe.dc.dc_identifier(_pid)

            # Set aggregationType
            _aggregationType = 'type.@value'
            if _aggregationType in item_map:
                item_id = item_map[_aggregationType].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    type_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    aggregationTypes = type_metadata[item_map[_aggregationType]]
                    if aggregationTypes:
                        if isinstance(aggregationTypes, list):
                            for aggregationType in aggregationTypes:
                                fe.prism.aggregationType(aggregationType)
                        else:
                            fe.prism.aggregationType(aggregationTypes)

            # Set item type
            fe.dc.dc_type(hit['_source']['itemtype'])

            # Set mimeType
            _mimeType = 'file.mimeType.@value'
            if _mimeType in item_map:
                item_id = item_map[_mimeType].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    file_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    mime_types = file_metadata[item_map[_mimeType]]
                    if mime_types:
                        if isinstance(mime_types, list):
                            for mime_type in mime_types:
                                fe.dc.dc_format(mime_type)
                        else:
                            fe.dc.dc_format(mime_types)

            # Set file uri
            _uri = 'file.URI.@value'
            if _uri in item_map:
                item_id = item_map[_uri].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    uri_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    uri_list = uri_metadata[item_map[_uri]]
                    if uri_list:
                        if isinstance(uri_list, list):
                            for uri in uri_list:
                                fe.dc.dc_identifier(uri, False)
                        else:
                            fe.dc.dc_identifier(uri_list, False)

            # Set author info
            request_lang = request.args.get('lang')
            _creatorName_attr_lang = 'creator.creatorName.@attributes.xml:lang'
            _creatorName_value = 'creator.creatorName.@value'
            if _creatorName_value in item_map:
                item_id = item_map[_creatorName_value].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    creator_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    creator_names = creator_metadata[
                        item_map[_creatorName_value]]
                    creator_name_langs = creator_metadata[
                        item_map[_creatorName_attr_lang]]

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
                                    fe.author({'name':creator_names,
                                               'lang':creator_name_langs})
                            else:
                                fe.author({'name': creator_names,
                                           'lang':creator_name_langs})

            # Set publisher
            _publisher_attr_lang = 'publisher.@attributes.xml:lang'
            _publisher_value = 'publisher.@value'
            if _publisher_value in item_map:
                item_id = item_map[_publisher_value].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    publisher_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    publisher_names = publisher_metadata[
                        item_map[_publisher_value]]
                    publisher_name_langs = publisher_metadata[
                        item_map[_publisher_attr_lang]]

                    if publisher_name_langs:
                        if isinstance(publisher_name_langs, list):
                            for i in range(len(publisher_name_langs)):
                                publisher_name_lang = publisher_name_langs[i]
                                if request_lang:
                                    if publisher_name_lang == request_lang:
                                        fe.dc.dc_publisher(publisher_names[i],
                                                           publisher_name_lang)
                                else:
                                    fe.dc.dc_publisher(publisher_names[i],
                                                       publisher_name_lang)
                        else:
                            if request_lang:
                                if publisher_name_langs == request_lang:
                                    fe.dc.dc_publisher(publisher_names,
                                                       publisher_name_langs)
                            else:
                                fe.dc.dc_publisher(publisher_names,
                                                   publisher_name_langs)

            # Set subject
            if _indexId:
                fe.dc.dc_subject(index_meta[_indexId])
            else:
                indexes = item_metadata['path'][0].split('/')
                indexId = indexes[len(indexes) - 1]

                if indexId in index_meta:
                    indexName = index_meta[indexId]
                else:
                    index = Index.query.filter_by(id=indexId).one_or_none()
                    indexName = index.index_name
                    index_meta[indexId] = indexName

                fe.dc.dc_subject(indexName)

            # Set publicationName
            _sourceTitle_value = 'sourceTitle.@value'
            if _sourceTitle_value in item_map:
                item_id = item_map[_sourceTitle_value].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    sourceTitle_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    source_titles = sourceTitle_metadata[
                        item_map[_sourceTitle_value]]

                    if source_titles:
                        if isinstance(source_titles, list):
                            for source_title in source_titles:
                                fe.prism.publicationName(source_title)
                        else:
                            fe.prism.publicationName(source_titles)

            # Set sourceIdentifier
            _sourceIdentifier_value = 'sourceIdentifier.@value'
            if _sourceIdentifier_value in item_map:
                item_id = item_map[_sourceIdentifier_value].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    sourceIdentifier_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    source_identifiers = sourceIdentifier_metadata[
                        item_map[_sourceIdentifier_value]]

                    if source_identifiers:
                        if isinstance(source_identifiers, list):
                            for source_identifier in source_identifiers:
                                fe.prism.issn(source_identifier)
                        else:
                            fe.prism.issn(source_identifiers)

            # Set volume
            _volume = 'volume'
            if _volume in item_map:
                item_id = item_map[_volume].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    volume_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    volumes = volume_metadata[item_map[_volume]]

                    if volumes:
                        if isinstance(volumes, list):
                            for volume in volumes:
                                fe.prism.volume(volume)
                        else:
                            fe.prism.volume(volumes)

            # Set number
            _issue = 'issue'
            if _issue in item_map:
                item_id = item_map[_issue].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    issue_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    issues = issue_metadata[item_map[_issue]]

                    if issues:
                        if isinstance(issues, list):
                            for issue in issues:
                                fe.prism.number(issue)
                        else:
                            fe.prism.number(issues)

            # Set startingPage
            _pageStart = 'pageStart'
            if _pageStart in item_map:
                item_id = item_map[_pageStart].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    pageStart_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    pageStarts = pageStart_metadata[item_map[_pageStart]]

                    if pageStarts:
                        if isinstance(pageStarts, list):
                            for pageStart in pageStarts:
                                fe.prism.startingPage(pageStart)
                        else:
                            fe.prism.startingPage(pageStarts)

            # Set endingPage
            _pageEnd = 'pageEnd'
            if _pageEnd in item_map:
                item_id = item_map[_pageEnd].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    pageEnd_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    pageEnds = pageEnd_metadata[item_map[_pageEnd]]

                    if pageEnds:
                        if isinstance(pageEnds, list):
                            for pageEnd in pageEnds:
                                fe.prism.endingPage(pageEnd)
                        else:
                            fe.prism.endingPage(pageEnds)

            # Set publicationDate
            _date = 'date.@value'
            if _date in item_map:
                item_id = item_map[_date].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    date_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    dates = date_metadata[item_map[_date]]

                    if dates:
                        if isinstance(dates, list):
                            for date in dates:
                                fe.prism.publicationDate(date)
                        else:
                            fe.prism.publicationDate(dates)

            # Set content
            _description_attr_lang = 'description.@attributes.xml:lang'
            _description_value = 'description.@value'
            if _description_value in item_map:
                item_id = item_map[_description_value].split('.')[0]

                # Get item data
                if item_id in item_metadata:
                    description_metadata = self.get_metadata_from_map(
                        item_metadata[item_id], item_id)

                    descriptions = description_metadata[
                        item_map[_description_value]]
                    description_langs = description_metadata[
                        item_map[_description_attr_lang]]

                    if description_langs:
                        if isinstance(description_langs, list):
                            for i in range(len(description_langs)):
                                description_lang = description_langs[i]
                                if request_lang:
                                    if description_lang == request_lang:
                                        fe.content(descriptions[i], description_lang)
                                else:
                                    fe.content(descriptions[i], description_lang)
                        else:
                            if request_lang:
                                if description_langs == request_lang:
                                    fe.content(descriptions, description_langs)
                            else:
                                fe.content(descriptions, description_langs)

            # Set updated
            _updated = hit['_source']['_updated']
            if _updated:
                fe.updated(_updated)

            # Set creationDate
            _creationDate = hit['_source']['_created']
            if _creationDate:
                fe.prism.creationDate(_creationDate)

            # Set modificationDate
            _modificationDate = hit['_source']['_updated']
            if _modificationDate:
                fe.prism.modificationDate(_modificationDate)

        return fg.atom_str(pretty=True)

    def get_mapping(self, item_type_mapping, mapping_type):
        """
        Format itemtype mapping data. [Key:Schema, Value:ItemId]
        :param item_type_mapping:
        :param mapping_type:
        :return:
        """

        def get_schema_key_info(schema, parent_key, schema_json={}):

            for k, v in schema.items():
                key = parent_key + '.' + k if parent_key else k
                if isinstance(v, dict):
                    child_key = copy.deepcopy(key)
                    get_schema_key_info(v, child_key, schema_json)
                else:
                    schema_json[key] = v

            return schema_json

        schema = {}
        for item_id, maps in item_type_mapping.items():
            if isinstance(maps[mapping_type], dict):
                item_schema = get_schema_key_info(maps[mapping_type], '', {})
                for k, v in item_schema.items():
                    item_schema[k] = item_id + '.' + v if v else item_id
                schema.update(item_schema)

        return schema

    def get_metadata_from_map(self, item_data, item_id):
        """
        Get item metadata from search result.
        :param item_data:
        :param item_id:
        :return:
        """

        def get_sub_item_data(props, parent_key=''):
            key = parent_key if parent_key else ''
            value = {}

            if isinstance(props, list):
                for prop in props:
                    for k, v in prop.items():
                        if isinstance(v, list) or isinstance(v, dict):
                            value.update(get_sub_item_data(v, key))
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
                        value.update(get_sub_item_data(v, key))
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
