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

"""WEKO BibTex Serializer."""

import xml.etree.ElementTree as ET

from datetime import datetime

from flask import abort
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from .wekoxml import WekoXMLSerializer
from ..schema import SchemaTree, cache_schema

class WekoBibTexSerializer():
    """Weko bibtex serializer."""

    def __init__(self):

        # Load namespace
        self.ns = cache_schema('jpcoar_mapping').get('namespaces')

        # JPCOAR types
        self.article_types = ['conference paper', 'data paper', 'editorial',
                              'journal article', 'periodical',
                              'review article', 'article',
                              'departmental bulletin paper']

        self.book_types = ['book', 'book part']
        self.inproceedings_types = ['conference proceedings']
        self.techreport_types = ['technical report', 'report', 'research report']
        self.unpublished_types = ['conference object', 'conference poster']

        self.misc_types = ['thesis', 'bachelor thesis', 'master thesis',
                           'doctoral thesis', 'learning material',
                           'dataset', 'software', 'other',
                           'cartographic material', 'map', 'image',
                           'still image', 'moving image', 'video',
                           'lecture', 'patent', 'internal report',
                           'policy report', 'report part', 'working paper',
                           'sound', 'interactive resource',
                           'musical notation', 'research proposal',
                           'technical documentation', 'workflow']

        # JPCOAR elements
        creator_name = '{' + self.ns['jpcoar'] + '}' + 'creatorName'
        title = '{' + self.ns['dc'] + '}' + 'title'
        source_title = '{' + self.ns['jpcoar'] + '}' + 'sourceTitle'
        volume = '{' + self.ns['jpcoar'] + '}' + 'volume'
        issue = '{' + self.ns['jpcoar'] + '}' + 'issue'
        page_start = '{' + self.ns['jpcoar'] + '}' + 'pageStart'
        page_end = '{' + self.ns['jpcoar'] + '}' + 'pageEnd'
        date = '{' + self.ns['datacite'] + '}' + 'date'
        publisher = '{' + self.ns['dc'] + '}' + 'publisher'
        type = '{' + self.ns['datacite'] + '}' + 'description'
        mime_type = '{' + self.ns['jpcoar'] + '}' + 'mimeType'
        contributor_name = '{' + self.ns['jpcoar'] + '}' + 'contributor' + \
                           '//' + '{' + self.ns['jpcoar'] + '}' + 'affiliationName'

        # [BibTex]Article columns
        self.article_cols_required = {'author': creator_name,
                                      'title': title,
                                      'journal': source_title,
                                      'date': date}

        self.article_cols_all = {'author': creator_name,
                                 'title': title,
                                 'journal': source_title,
                                 'volume': volume,
                                 'number': issue,
                                 'page_start': page_start,
                                 'page_end': page_end,
                                 'date': date}

        # [BibTex]Book columns
        self.book_cols_required = {'author': creator_name,
                                   'title': title,
                                   'publisher': publisher,
                                   'date': date}

        self.book_cols_all = {'author': creator_name,
                              'title': title,
                              'volume': volume,
                              'number': issue,
                              'publisher': publisher,
                              'date': date}

        # [BibTex]Booklet columns
        self.booklet_cols_required = {'title': title}

        self.booklet_cols_all = {'author': creator_name,
                                 'title': title,
                                 'howpublished': mime_type,
                                 'date': date}

        # [BibTex]Inbook columns
        self.inbook_cols_required = {'author': creator_name,
                                     'title': title,
                                     'page_start': page_start,
                                     'page_end': page_end,
                                     'publisher': publisher,
                                     'date': date}

        self.inbook_cols_all = {'author': creator_name,
                                'title': title,
                                'volume': volume,
                                'number': issue,
                                'page_start': page_start,
                                'page_end': page_end,
                                'publisher': publisher,
                                'date': date,
                                'type': type}

        # [BibTex]Incollection columns
        self.incollection_cols_required = {'author': creator_name,
                                           'title': title,
                                           'booktitle': source_title,
                                           'publisher': publisher,
                                           'date': date}

        self.incollection_cols_all = {'author': creator_name,
                                      'title': title,
                                      'booktitle': source_title,
                                      'volume': volume,
                                      'number': issue,
                                      'page_start': page_start,
                                      'page_end': page_end,
                                      'publisher': publisher,
                                      'date': date,
                                      'type': type}

        # [BibTex]Inproceedings columns
        self.inproceedings_cols_required = {'author': creator_name,
                                            'title': title,
                                            'booktitle': source_title,
                                            'date': date}

        self.inproceedings_cols_all = {'author': creator_name,
                                       'title': title,
                                       'booktitle': source_title,
                                       'volume': volume,
                                       'number': issue,
                                       'page_start': page_start,
                                       'page_end': page_end,
                                       'publisher': publisher,
                                       'date': date}

        # [BibTex]Techreport columns
        self.techreport_cols_required = {'author': creator_name,
                                         'title': title,
                                         'date': date,
                                         'institution': contributor_name}

        self.techreport_cols_all = {'author': creator_name,
                                    'title': title,
                                    'number': issue,
                                    'date': date,
                                    'institution': contributor_name,
                                    'type': type}

        # [BibTex]Unpublished columns
        self.unpublished_cols_required = {'author': creator_name,
                                          'title': title}

        self.unpublished_cols_all = {'author': creator_name,
                                     'title': title,
                                     'date': date}

        # [BibTex]Misc columns
        self.misc_cols_all = {'author': creator_name,
                              'title': title,
                              'howpublished': mime_type,
                              'date': date}

    def serialize(self, pid, record):
        """Serialize to bibtex from jpcoar record.

        :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        :param record: The :class:`invenio_records.api.Record` instance.
        :returns: The object serialized.
        """
        # Get JPCOAR data(XML) and ElementTree root
        jpcoar_data = self.get_jpcoar_data(pid, record)
        root = ET.fromstring(jpcoar_data)

        if self.is_empty(root):
            return 'This item has no mapping info.'

        db = BibDatabase()
        # Article
        if self.is_bibtex_type(root,
                               self.article_types,
                               self.article_cols_required):

            db.entries.append(self.get_bibtex_data(root,
                                                   self.article_cols_all,
                                                   'article'))
        # Incollection
        elif self.is_bibtex_type(root,
                                 self.book_types,
                                 self.incollection_cols_required):

            db.entries.append(self.get_bibtex_data(root,
                                                   self.incollection_cols_all,
                                                   'incollection'))
        # Inbook
        elif self.is_bibtex_type(root,
                                 self.book_types,
                                 self.inbook_cols_required):

            db.entries.append(self.get_bibtex_data(root,
                                                   self.inbook_cols_all,
                                                   'inbook'))
        # Book
        elif self.is_bibtex_type(root,
                                 self.book_types,
                                 self.book_cols_required):

            db.entries.append(self.get_bibtex_data(root,
                                                   self.book_cols_all,
                                                   'book'))
        # Booklet
        elif self.is_bibtex_type(root,
                                 self.book_types,
                                 self.booklet_cols_required):

            db.entries.append(self.get_bibtex_data(root,
                                                   self.booklet_cols_all,
                                                   'booklet'))
        # Inproceedings
        elif self.is_bibtex_type(root,
                                 self.inproceedings_types,
                                 self.inproceedings_cols_required):

            db.entries.append(self.get_bibtex_data(root,
                                                   self.inproceedings_cols_all,
                                                   'inproceedings'))
        # Techreport
        elif self.is_bibtex_type(root,
                                 self.techreport_types,
                                 self.techreport_cols_required):

            db.entries.append(self.get_bibtex_data(root,
                                                   self.techreport_cols_all,
                                                   'techreport'))
        # Unpublished
        elif self.is_bibtex_type(root,
                                      self.unpublished_types,
                                      self.unpublished_cols_required):

            db.entries.append(self.get_bibtex_data(root,
                                                   self.unpublished_cols_all,
                                                   'unpublished'))
        # Misc
        elif self.is_misc_type(root):
            db.entries.append(self.get_bibtex_data(root,
                                                   self.misc_cols_all,
                                                   'misc'))
        # Unknown type
        else:
            return 'This item has no mapping info.'

        writer = BibTexWriter()

        return writer.write(db)

    @staticmethod
    def get_jpcoar_data(pid, record):
        """Get jpcoar record.
        :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        :param record: The :class:`invenio_records.api.Record` instance.
        :returns: The object serialized.
        """
        record.update({'@export_schema_type': 'jpcoar'})
        serializer = WekoXMLSerializer()
        data = serializer.serialize(pid, record)

        return data

    def is_empty(self, root):
        """
        Determine whether the jpcoar record is empty.
        :param root:
        :return:
        """
        elements = root.findall('.//jpcoar:jpcoar', self.ns)
        if len(elements) == 0 or len(list(elements[0])) == 0:
            return True

        return False

    def is_bibtex_type(self, root, bibtex_types, bibtex_cols_required):
        """
        Determine jpcoar record types(except misc).
        :return:
        """
        type_value = ''
        for element in root.findall('.//dc:type', self.ns):
            type_value = element.text

        if type_value.lower() not in bibtex_types:
            return False

        if not self.contains_all(root, bibtex_cols_required.values()):
            return False

        return True

    def is_misc_type(self, root):
        """
        Determine jpcoar record type(misc).
        :param root:
        :return:
        """
        type_value = ''
        for element in root.findall('.//dc:type', self.ns):
            type_value = element.text

        if type_value.lower() in self.misc_types or \
            type_value.lower() in self.article_types or \
            type_value.lower() in  self.book_types or \
            type_value.lower() in self.inproceedings_types or \
            type_value.lower() in self.techreport_types or \
            type_value.lower() in self.unpublished_types:

            return True

        return False

    def contains_all(self, root, field_list):
        """
        Determine whether all required items exist.
        :param root:
        :param field_list:
        :return:
        """
        for field in field_list:
            if len(root.findall('.//' + field, self.ns)) == 0:
                return False

        return True

    def get_bibtex_data(self, root, bibtex_cols_all={}, entry_type='article'):
        """
        Get bibtex data from jpcoar record.
        :param root:
        :param bibtex_cols_all:
        :param entry_type:
        :return:
        """

        # Initialization
        data = {}
        page_start = ''
        page_end = ''
        xml_ns = '{' + self.ns['xml'] + '}'

        # Create book record
        for field in bibtex_cols_all.keys():
            elements = root.findall('.//' + bibtex_cols_all[field], self.ns)
            if len(elements) != 0:

                value = ''
                dates = []
                for element in elements:
                    if field == 'date' and (element.get('dateType') is not None and
                                            element.get('dateType').lower() == 'issued'):
                        dates.append(element.text)
                        continue
                    elif field == 'type' and (element.get('descriptionType') is None or
                                              element.get('descriptionType').lower() != 'other'):
                        continue
                    elif field == 'author' and (element.get(xml_ns + 'lang') is None or
                                                element.get(xml_ns + 'lang').lower() != 'en'):
                        continue

                    if value != '':
                        value += ' and ' if field == 'author' else ', '
                    value += element.text

                if field == 'page_start':
                    page_start = value
                elif field == 'page_end':
                    page_end = value
                elif field == 'date' and len(dates) != 0:
                    data['year'], data['month'] = self.get_dates(dates)
                elif value != '':
                    data[field] = value

        if page_start != '' and page_end != '':
            data['pages'] = str(page_start) + '--' + str(page_end)

        data['ENTRYTYPE'] = entry_type
        data['ID'] = self.get_item_id(root)

        return data

    @staticmethod
    def get_item_id(root):
        """
        Get item id from jpcoar record.
        :param root:
        :return:
        """
        item_id = ''
        namespace = 'http://www.openarchives.org/OAI/2.0/'
        request_tag = '{' + namespace + '}' + 'request'
        for element in root:
            if request_tag == element.tag:
                subs = element.get('identifier').split('/')
                item_id = subs[len(subs) - 1]

        return item_id

    @staticmethod
    def get_dates(dates):
        """
        Get year and month from date.
        :param dates:
        :return:
        """
        year = ''
        month = ''
        for element in dates:
            date = datetime.strptime(element, '%Y-%m-%d')
            year += ', ' if year != '' else ''
            month += ', ' if month != '' else ''

            year += str(date.year)
            month += date.strftime('%b')

        return year, month
