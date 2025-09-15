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
from enum import Enum

from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bwriter import BibTexWriter
from flask import current_app

from ..config import WEKO_SCHEMA_DATE_DEFAULT_DATETYPE, WEKO_SCHEMA_DATE_DATETYPE_MAPPING
from ..schema import SchemaTree, cache_schema
from .wekoxml import WekoXMLSerializer


class BibTexTypes(Enum):
    """BibTex Types."""

    ARTICLE = 'article'
    BOOK = 'book'
    BOOKLET = 'booklet'
    CONFERENCE = 'conference'
    INBOOK = 'inbook'
    INCOLLECTION = 'incollection'
    INPROCEEDINGS = 'inproceedings'
    MANUAL = 'manual'
    MASTERSTHESIS = 'mastersthesis'
    MISC = 'misc'
    PHDTHESIS = 'phdthesis'
    PROCEEDINGS = 'proceedings'
    TECHREPORT = 'techreport'
    UNPUBLISHED = 'unpublished'


class BibTexFields(Enum):
    """BibTex Fields."""

    AUTHOR = 'author'
    YOMI = 'yomi'
    TITLE = 'title'
    BOOK_TITLE = 'book'
    JOURNAL = 'journal'
    VOLUME = 'volume'
    NUMBER = 'issue'
    PAGES = 'pages'
    PAGE_START = 'page_start'
    PAGE_END = 'page_end'
    NOTE = 'note'
    PUBLISHER = 'publisher'
    YEAR = 'year'
    MONTH = 'month'
    URL = 'url'
    DOI = 'doi'
    SCHOOL = 'school'
    TYPE = 'type'
    EDITOR = 'editor'
    EDITION = 'edition'
    CHAPTER = 'chapter'
    SERIES = 'series'
    ADDRESS = 'address'
    ORGANIZATION = 'organization'
    KEY = 'key'
    CROSSREF = 'crossref'
    ANNOTE = 'annote'
    INSTITUTION = 'institution'
    HOW_PUBLISHER = 'how publisher'


class WekoBibTexSerializer():
    """Weko bibtex serializer."""

    # Mapping type between Bibtex type and dc:type of jpcoar
    type_mapping = {
        BibTexTypes.ARTICLE: ['journal article',
                              'departmental bulletin paper',
                              'review article', 'data paper', 'periodical',
                              'editorial',
                              'article'],
        BibTexTypes.BOOK: ['book'],
        BibTexTypes.INBOOK: ['book part'],
        BibTexTypes.INPROCEEDINGS: ['conference paper'],
        BibTexTypes.MASTERSTHESIS: ['master thesis'],
        BibTexTypes.MISC: ['research proposal', 'technical documentation',
                           'thesis',
                           'bachelor thesis', 'cartographic material',
                           'map',
                           'lecture', 'conference object', 'conference poster',
                           'image', 'still image', 'moving image', 'video',
                           'sound',
                           'musical notation', 'interactive resource',
                           'learning object', 'patent', 'dataset', 'software',
                           'workflow',
                           'other'],
        BibTexTypes.PHDTHESIS: ['doctoral thesis'],
        BibTexTypes.PROCEEDINGS: ['conference proceedings'],
        BibTexTypes.TECHREPORT: ['report',
                                 'research report',
                                 'working paper',
                                 'technical report',
                                 'policy report',
                                 'internal report',
                                 'report part'],
        BibTexTypes.INCOLLECTION: [],
        BibTexTypes.BOOKLET: [],
        BibTexTypes.CONFERENCE: [],
        BibTexTypes.MANUAL: [],
        BibTexTypes.UNPUBLISHED: []}

    def __init__(self):
        """Init."""
        # Load namespace
        self.__ns = cache_schema('jpcoar_mapping').get('namespaces')
        self.__lst_identifier_type = ['doi', 'hdl', 'url']
        # JPCOAR elements
        jp_jp = '{' + self.__ns['jpcoar'] + '}'
        jp_dc = '{' + self.__ns['dc'] + '}'
        jp_datacite = '{' + self.__ns['datacite'] + '}'
        jp_dcndl = '{' + self.__ns['dcndl'] + '}'
        self.__find_pattern = './/{}'

        self.__fields_mapping = {
            BibTexFields.AUTHOR: jp_jp + 'creatorName',
            BibTexFields.TITLE: jp_dc + 'title',
            BibTexFields.JOURNAL: jp_jp + 'sourceTitle',
            BibTexFields.BOOK_TITLE: jp_jp + 'sourceTitle',
            BibTexFields.VOLUME: jp_jp + 'volume',
            BibTexFields.NUMBER: jp_jp + 'issue',
            BibTexFields.PAGE_START: jp_jp + 'pageStart',
            BibTexFields.PAGE_END: jp_jp + 'pageEnd',
            BibTexFields.PUBLISHER: jp_dc + 'publisher',
            BibTexFields.HOW_PUBLISHER: jp_dc + 'mimeType',
            BibTexFields.YEAR: jp_datacite + 'date',
            BibTexFields.MONTH: jp_datacite + 'date',
            BibTexFields.INSTITUTION: 'none',
            BibTexFields.TYPE: 'none',
            BibTexFields.EDITOR: 'none',
            BibTexFields.EDITION: 'none',
            BibTexFields.CHAPTER: 'none',
            BibTexFields.SERIES: 'none',
            BibTexFields.ADDRESS: 'none',
            BibTexFields.NOTE: jp_datacite + 'description',
            BibTexFields.SCHOOL: jp_jp + 'degreeGrantorName',
            BibTexFields.ORGANIZATION: 'none',
            BibTexFields.KEY: 'none',
            BibTexFields.CROSSREF: 'none',
            BibTexFields.ANNOTE: 'none',
            BibTexFields.DOI: jp_jp + 'identifier',
            BibTexFields.URL: jp_jp + 'identifier',
        }


        date_default = jp_datacite + 'date[@dateType="@DATE_TYPE"]'

        self.base_date_priority = [
            date_default,
        ]

        self.date_priority_mapping = {
            'departmental bulletin paper': [jp_dcndl + 'dateGranted']
        }

    def ____get_bibtex_type_fields(self, bibtex_type):
        """Get all fields of BibTex type.

        @param self:
        @param bibtex_type:
        @return:
        """
        result = {
            BibTexTypes.ARTICLE: self.__get_article_fields(),
            BibTexTypes.BOOK: self.__get_book_fields(),
            BibTexTypes.BOOKLET: self.__get_booklet_fields(),
            BibTexTypes.CONFERENCE: self.__get_conference_fields(),
            BibTexTypes.INBOOK: self.__get_inbook_fields(),
            BibTexTypes.INCOLLECTION: self.__get_incollection_fields(),
            BibTexTypes.INPROCEEDINGS: self.__get_inproceedings_fields(),
            BibTexTypes.MANUAL: self.__get_manual_fields(),
            BibTexTypes.MASTERSTHESIS: self.__get_mastersthesis_fields(),
            BibTexTypes.MISC: self.__get_misc_fields(),
            BibTexTypes.PHDTHESIS: self.__get_phdthesis_fields(),
            BibTexTypes.PROCEEDINGS: self.__get_proceedings_fields(),
            BibTexTypes.TECHREPORT: self.__get_techreport_fields(),
            BibTexTypes.UNPUBLISHED: self.__get_unpublished_fields(),
        }
        return result.get(bibtex_type)

    @staticmethod
    def __get_article_fields():
        """Get article's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.JOURNAL, BibTexFields.YEAR,
                        BibTexFields.VOLUME, BibTexFields.NUMBER,
                        BibTexFields.PAGE_START,
                        BibTexFields.PAGE_END, BibTexFields.MONTH,
                        BibTexFields.NOTE, BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_book_fields():
        """Get book's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.EDITOR,BibTexFields.AUTHOR,
                        BibTexFields.TITLE, BibTexFields.PUBLISHER,
                        BibTexFields.YEAR,
                        BibTexFields.VOLUME, BibTexFields.NUMBER,
                        BibTexFields.MONTH,
                        BibTexFields.EDITION, BibTexFields.SERIES,
                        BibTexFields.ADDRESS,
                        BibTexFields.NOTE, BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_booklet_fields():
        """Get booklet's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.TITLE,
                        BibTexFields.AUTHOR, BibTexFields.HOW_PUBLISHER,
                        BibTexFields.YEAR, BibTexFields.MONTH,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_conference_fields():
        """Get conference's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.BOOK_TITLE, BibTexFields.YEAR,
                        BibTexFields.VOLUME, BibTexFields.NUMBER,
                        BibTexFields.PAGE_START,
                        BibTexFields.PAGE_END, BibTexFields.PUBLISHER,
                        BibTexFields.MONTH,
                        BibTexFields.EDITOR, BibTexFields.SERIES,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.ORGANIZATION, BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_inbook_fields():
        """Get inbook's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR,BibTexFields.EDITOR,
                        BibTexFields.PAGES,BibTexFields.CHAPTER,
                        BibTexFields.TITLE, BibTexFields.YEAR,
                        BibTexFields.PUBLISHER,
                        BibTexFields.VOLUME, BibTexFields.NUMBER,
                        BibTexFields.MONTH,
                        BibTexFields.TYPE, BibTexFields.EDITION,
                        BibTexFields.SERIES,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_incollection_fields():
        """Get incollection's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.BOOK_TITLE, BibTexFields.YEAR,
                        BibTexFields.PUBLISHER,
                        BibTexFields.VOLUME, BibTexFields.NUMBER,
                        BibTexFields.PAGE_START,
                        BibTexFields.PAGE_END, BibTexFields.MONTH,
                        BibTexFields.TYPE, BibTexFields.EDITOR,
                        BibTexFields.EDITION, BibTexFields.CHAPTER,
                        BibTexFields.SERIES,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.ORGANIZATION, BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_inproceedings_fields():
        """Get inproceedings's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.BOOK_TITLE, BibTexFields.YEAR,
                        BibTexFields.VOLUME, BibTexFields.NUMBER,
                        BibTexFields.PAGE_START,
                        BibTexFields.PAGE_END, BibTexFields.PUBLISHER,
                        BibTexFields.MONTH, BibTexFields.EDITOR,
                        BibTexFields.SERIES,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.ORGANIZATION, BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_manual_fields():
        """Get manual's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.TITLE,
                        BibTexFields.AUTHOR, BibTexFields.YEAR,
                        BibTexFields.MONTH, BibTexFields.EDITION,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.ORGANIZATION, BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_mastersthesis_fields():
        """Get mastersthesis's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.YEAR, BibTexFields.SCHOOL,
                        BibTexFields.MONTH, BibTexFields.TYPE,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_phdthesis_fields():
        """Get phdthesis's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.YEAR, BibTexFields.SCHOOL,
                        BibTexFields.MONTH, BibTexFields.TYPE,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_proceedings_fields():
        """Get proceedings's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.TITLE, BibTexFields.YEAR,
                        BibTexFields.VOLUME, BibTexFields.NUMBER,
                        BibTexFields.PUBLISHER, BibTexFields.MONTH,
                        BibTexFields.EDITOR, BibTexFields.SERIES,
                        BibTexFields.ADDRESS, BibTexFields.NOTE,
                        BibTexFields.ORGANIZATION, BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_techreport_fields():
        """Get techreport's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.YEAR, BibTexFields.INSTITUTION,
                        BibTexFields.NUMBER, BibTexFields.MONTH,
                        BibTexFields.TYPE, BibTexFields.ADDRESS,
                        BibTexFields.NOTE, BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_unpublished_fields():
        """Get unpublished's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.NOTE,
                        BibTexFields.YEAR, BibTexFields.MONTH,
                        BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    @staticmethod
    def __get_misc_fields():
        """Get mis's fields.

        @return:
        """
        lst_required = []
        lst_optional = [BibTexFields.AUTHOR, BibTexFields.TITLE,
                        BibTexFields.HOW_PUBLISHER, BibTexFields.YEAR,
                        BibTexFields.MONTH, BibTexFields.NOTE,
                        BibTexFields.KEY]
        lst_required_partial = []
        return {'required': lst_required, 'optional': lst_optional,
                'required_partial': lst_required_partial}

    def serialize(self, pid, record, validate_mode=False):
        """Serialize to bibtex from jpcoar record.

        :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        :param record: The :class:`invenio_records.api.Record` instance.
        :param validate_mode: validate or not
        :returns: The object serialized.
        """
        err_msg = 'Please input all required item.'
        # Get JPCOAR datas(XML) and ElementTree root
        jpcoar_data = self.__get_jpcoar_data(pid, record)
        root = ET.fromstring(jpcoar_data)
        if self.__is_empty(root):
            return err_msg

        db = BibDatabase()
        bibtex_type = self.__get_bibtex_type(root)

        if not bibtex_type:
            current_app.logger.error(
                "Can not find Bibtex type for record {}".format(
                    record.get('recid')))
            return err_msg
        valid, lst_invalid_fields = self.__validate_fields(root, bibtex_type)

        if validate_mode:
            return valid
        elif not validate_mode and not valid:
            if len(lst_invalid_fields) > 0:
                current_app.logger.error(
                    'Missing required fields [{}] for record {}'.format(
                        ','.join(lst_invalid_fields), record.get('recid')))
            return err_msg

        db.entries.append(self.__get_bibtex_data(root, bibtex_type, record))
        writer = BibTexWriter()
        result = writer.write(db)
        return result

    @staticmethod
    def __get_jpcoar_data(pid, record):
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

    def __is_empty(self, root):
        """
        Determine whether the jpcoar record is empty.

        :param root:
        :return:

        """
        elements = root.findall('.//jpcoar:jpcoar', self.__ns)
        if len(elements) == 0 or len(list(elements[0])) == 0:
            return True

        return False

    def __get_bibtex_type(self, root):
        """
        Determine jpcoar record types(except misc).

        :return:

        """
        type_result = None
        type_value = ''
        for element in root.findall('.//dc:type', self.__ns):
            type_value = element.text
        # Determine which type of Bibtex type is it
        for bib_type, item_types in self.type_mapping.items():
            if type_value.lower() in item_types:
                type_result = bib_type
                break
        return type_result

    def __get_date_by_resource_type(self, root, record):
        """Get date by resource type.

        @param root:
        @param record:
        @return:
        """
        type_value = ''
        date_priority_list = []
        date_result = []

        for element in root.findall('.//dc:type', self.__ns):
            type_value = element.text
        
        date_type_mapping = current_app.config.get('WEKO_SCHEMA_DATE_DATETYPE_MAPPING', 
                                                   WEKO_SCHEMA_DATE_DATETYPE_MAPPING)
        default_date_type = current_app.config.get('WEKO_SCHEMA_DATE_DEFAULT_DATETYPE',
                                                    WEKO_SCHEMA_DATE_DEFAULT_DATETYPE)
        self.base_date_priority[0] = self.base_date_priority[0].replace(
            '@DATE_TYPE', date_type_mapping.get(type_value, default_date_type))

        if self.date_priority_mapping.get(type_value):
            date_priority_list = self.date_priority_mapping.get(type_value)
        date_priority_list += self.base_date_priority

        for priority_path in date_priority_list:
            for element in root.findall(
                    self.__find_pattern.format(priority_path), self.__ns):
                if element.text not in date_result:
                    date_result.append(element.text)
            if date_result:
                return date_result

        return record.get('pubdate', {}).get('attribute_value')

    def __validate_fields(self, root, bibtex_type):
        """Validate required fields of bibtex type.

        @param root:
        @param bibtex_type:
        @return:
        """
        def validate_by_att(attribute_name, expected_values):
            valid_date = False
            for element in elements:
                if element.get(attribute_name) and element.get(
                        attribute_name).lower() in expected_values:
                    valid_date = True
            return valid_date

        def validate_partial_req():
            result = True
            # for par_req in fields.get('required_partial'):
            #     partial_valid = False
            #     for field in par_req:
            #         # check for pages because pages is represented for start
            #         # and end page
            #         if field == BibTexFields.PAGES:
            #             start_page = root.findall(self.__find_pattern.format(
            #                 self.__fields_mapping[BibTexFields.PAGE_START]),
            #                 self.__ns)
            #             end_page = root.findall(
            #                 self.__find_pattern.format(self.__fields_mapping[BibTexFields.PAGE_END]),
            #                 self.__ns)
            #             if len(start_page) > 0 and len(end_page) > 0:
            #                 partial_valid = True
            #                 break
            #         else:
            #             field_data = root.findall(
            #                 self.__find_pattern.format(self.__fields_mapping[field]),
            #                 self.__ns)
            #             if len(field_data) > 0:
            #                 partial_valid = True
            #                 break
            #     if not partial_valid:
            #         result = False
            #         lst_invalid_fields.append(par_req[0].value)
            #         lst_invalid_fields.append(par_req[1].value)
            return result

        lst_invalid_fields = []
        identifierType_str = 'identifierType'
        required_valid = True
        fields = self.____get_bibtex_type_fields(bibtex_type)
        # for item_required in fields.get('required'):
        #     elements = root.findall(
        #         self.__find_pattern.format(self.__fields_mapping[item_required]),
        #         self.__ns)
        #     if len(elements) == 0:
        #         required_valid = False
        #         lst_invalid_fields.append(item_required.value)
        #     elif item_required == BibTexFields.YEAR or \
        #             item_required == BibTexFields.MONTH:
        #         date_valid = validate_by_att('dateType', ['issued'])
        #         if not date_valid:
        #             lst_invalid_fields.append(item_required.value)
        #             required_valid = False
        #     elif item_required == BibTexFields.DOI:
        #         doi_valid = validate_by_att(identifierType_str, ['doi'])
        #         if not doi_valid:
        #             lst_invalid_fields.append(item_required.value)
        #             required_valid = False
        #     elif item_required == BibTexFields.URL:
        #         url_valid = validate_by_att(identifierType_str,
        #                                     ['doi', 'hdl', 'uri'])
        #         if not url_valid:
        #             lst_invalid_fields.append(item_required.value)
        #             required_valid = False
        partial_req_valid = validate_partial_req()
        return required_valid and partial_req_valid, lst_invalid_fields

    def __combine_all_fields(self, bibtex_type):
        """Combine all fields of item type.

        @param bibtex_type:
        @return:
        """
        all_fields = []
        all_field_type = self.____get_bibtex_type_fields(bibtex_type)
        if isinstance(all_field_type, dict):
            all_fields = all_field_type.get(
                'required', []) + all_field_type.get('optional', [])
        # partial_req = all_field_type.get('required_partial')
        # for item in partial_req:
        #     if BibTexFields.PAGES in item:
        #         item.remove(BibTexFields.PAGES)
        #         item.extend([BibTexFields.PAGE_START,
        #                     BibTexFields.PAGE_END])
        #     all_fields.extend(item)
        return all_fields

    def __get_bibtex_data(self, root, bibtex_type, record):
        """Get Bibtex data base on Bibtex type.

        @param root:
        @param bibtex_type:
        @param record:
        @return:
        """
        def process_by_att(att, expected_val, existed_lst):
            att_type = element.get(att)
            if att_type and att_type.lower() == expected_val and \
                    element.text not in existed_lst:
                existed_lst.append(element.text)

        def process_author():
            author_lang = element.get(xml_ns + 'lang')
            if not author_lang or author_lang.lower() != 'ja-kana':
                creator[BibTexFields.AUTHOR.value].append(
                    element.text)
            else:
                creator[BibTexFields.YOMI.value].append(
                    element.text)

        def process_url():
            identifier_type = element.get(xml_ns + 'identifierType')
            if identifier_type and identifier_type.lower in self.__lst_identifier_type:
                lst_identifier_type_data[
                    identifier_type.lower].append(element.text)

        data = {}
        page_start = ''
        page_end = ''
        title = ''
        xml_ns = '{' + self.__ns['xml'] + '}'
        and_str = ' and '
        creator = {BibTexFields.AUTHOR.value: [],
                   BibTexFields.YOMI.value: []}
        lst_identifier_type_data = {}
        dois = []
        all_fields = self.__combine_all_fields(bibtex_type)

        for i in self.__lst_identifier_type:
            lst_identifier_type_data[i] = []

        for field in all_fields:
            elements = root.findall(
                self.__find_pattern.format(self.__fields_mapping[field]), self.__ns)
            if len(elements) != 0:
                value = ''
                for element in elements:
                    if element is None or \
                            field in [BibTexFields.YEAR, BibTexFields.MONTH]:
                        continue
                    if field == BibTexFields.AUTHOR:
                        process_author()
                    elif field == BibTexFields.DOI:
                        process_by_att(xml_ns + 'identifierType', 'doi', dois)
                    elif field == BibTexFields.URL:
                        process_url()
                    elif field == BibTexFields.TITLE and title == '':
                        # Get only one title at all
                        title = element.text
                    if value != '':
                        value += and_str if field == BibTexFields.AUTHOR else ', '
                    value += element.text

                if field == BibTexFields.PAGE_START:
                    page_start = value
                elif field == BibTexFields.PAGE_END:
                    page_end = value
                elif field == BibTexFields.AUTHOR:
                    if creator[BibTexFields.AUTHOR.value]:
                        data[field.value] = and_str.join(
                            creator[BibTexFields.AUTHOR.value])
                    if creator[BibTexFields.YOMI.value]:
                        data[BibTexFields.YOMI.value] = and_str.join(
                            creator[BibTexFields.YOMI.value])
                elif field == BibTexFields.DOI and len(dois) > 0:
                    data[field.value] = ','.join(dois)
                elif field == BibTexFields.URL and len():
                    data[field.value] = self.__get_identifier(
                        self.__lst_identifier_type,
                        lst_identifier_type_data)
                elif field == BibTexFields.TITLE and title != '':
                    data[field.value] = title
                elif value != '':
                    data[field.value] = value

        if page_start != '' and page_end != '':
            data['pages'] = str(page_start) + '--' + str(page_end)

        date_by_resource_type = self.__get_date_by_resource_type(root, record)
        data['year'], data['month'] = self.__get_dates(date_by_resource_type)
        data['ENTRYTYPE'] = bibtex_type.value
        data['ID'] = self.__get_item_id(root)

        return data

    @staticmethod
    def __get_item_id(root):
        """
        Get item id from jpcoar record.

        :param root:
        :return:

        """
        item_id = ''
        namespace = 'http://www.openarchives.org/OAI/2.0/'
        request_tag = '{' + namespace + '}' + 'request'
        for element in root:
            if element is not None and request_tag == element.tag:
                subs = element.get('identifier', '').split('/')
                item_id = subs[len(subs) - 1]

        return item_id

    @staticmethod
    def __get_dates(dates):
        """
        Get year and month from date.

        :param dates:
        :return:

        """
        year = ''
        month = ''
        if type(dates) is str:
            dates = [dates]
        for element in dates:
            date_element = element.split('-')
            year += ', ' if year != '' else ''
            month += ', ' if month != '' else ''
            if len(date_element) == 1:
                date = datetime.strptime(element, '%Y')
            elif len(date_element) == 2:
                date = datetime.strptime(element, '%Y-%m')
            else:
                date = datetime.strptime(element, '%Y-%m-%d')
            year += str(date.year)
            if len(date_element) > 1:
                month += date.strftime('%b')

        return year, month

    @staticmethod
    def __get_identifier(identifier_type, identifier_types_data):
        """Get identifier data.

        @param identifier_type:
        @param identifier_types_data:
        @return:
        """
        if identifier_types_data:
            for type in identifier_type:
                if identifier_types_data.get(type) and len(
                        identifier_types_data.get(type)) > 0:
                    return identifier_types_data.get(type)[0]
