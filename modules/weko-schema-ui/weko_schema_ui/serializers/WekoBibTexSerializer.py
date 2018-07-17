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

import six
import xml.etree.ElementTree as ET

from datetime import datetime

from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from .wekoxml import WekoXMLSerializer
from ..schema import SchemaTree, cache_schema

class WekoBibTexSerializer():
    """Weko BibTex Serializer."""

    def serialize(self, pid, record):
        """Serialize to bibtex from jpcoar record.

        :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        :param record: The :class:`invenio_records.api.Record` instance.
        :returns: The object serialized.
        """
        jpcoar_data = self.get_jpcoar_data(pid, record)

        db = BibDatabase()
        if self.is_article(jpcoar_data):
            db.entries.append(self.get_article(jpcoar_data))

        writer = BibTexWriter()

        return writer.write(db)


    def get_jpcoar_data(self, pid, record):
        """Get jpcoar record.
        :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        :param record: The :class:`invenio_records.api.Record` instance.
        :returns: The object serialized.
        """
        record.update({'@export_schema_type': 'jpcoar'})
        serializer = WekoXMLSerializer()
        data = serializer.serialize(pid, record)
        # if isinstance(data, six.binary_type):
        # data = data.decode('utf8')

        return data


    def is_article(self, jpcoar_data):
        """

        :param jpcoar_data:
        :return:
        """
        root = ET.fromstring(jpcoar_data)
        ns = cache_schema('jpcoar_mapping').get('namespaces')

        article_list = ["journal article",
                        "departmental bulletin paper",
                        "article"]
        type = ''
        for element in root.findall('.//dc:type', ns):
            type = element.text

        if type not in article_list:
            return False

        creator = '{' + ns['jpcoar'] + '}' + 'creatorName'
        title = '{' + ns['dc'] + '}' + 'title'
        sourceTitle = '{' + ns['jpcoar'] + '}' + 'sourceTitle'
        date = '{' + ns['datacite'] + '}' + 'date'

        required_cols = [creator, title, sourceTitle, date]

        if not self.contains_all(root, ns, required_cols):
            return False

        return True


    def contains_all(self, root, ns, field_list):

        for field in field_list:
            if len(root.findall('.//' + field, ns)) == 0:
                return False

        return True

    def get_article(self, jpcoar_data):
        """
        :param jpcoar_data:
        :return:
        """
        root = ET.fromstring(jpcoar_data)
        ns = cache_schema('jpcoar_mapping').get('namespaces')

        creator = '{' + ns['jpcoar'] + '}' + 'creatorName'
        title = '{' + ns['dc'] + '}' + 'title'
        sourceTitle = '{' + ns['jpcoar'] + '}' + 'sourceTitle'
        volume = '{' + ns['jpcoar'] + '}' + 'volume'
        issue = '{' + ns['jpcoar'] + '}' + 'issue'
        page_start = '{' + ns['jpcoar'] + '}' + 'pageStart'
        page_end = '{' + ns['jpcoar'] + '}' + 'pageEnd'
        date = '{' + ns['datacite'] + '}' + 'date'

        article_col_map = {'author': creator,
                           'title': title,
                           'journal': sourceTitle,
                           'volume': volume,
                           'number': issue,
                           'page_start': page_start,
                           'page_end': page_end,
                           'date': date}
        data = {}
        page_start = ''
        page_end = ''
        for field in article_col_map.keys():
            elements = root.findall('.//' + article_col_map[field], ns)
            if len(elements) != 0:
                value = ''
                for ele in elements:
                    if value != '':
                        value += ' and ' if field == 'author' else ', '
                    value += ele.text

                if field == 'page_start':
                    page_start = value
                elif field == 'page_end':
                    page_end = value
                elif field == 'date':
                    date = datetime.strptime(value, '%Y-%m-%d')
                    data['year'] = str(date.year)
                    data['month'] = str(date.month)
                else:
                    data[field] = value

        data['pages'] = str(page_start) + '--' + str(page_end)

        data['ENTRYTYPE'] = 'article'
        data['ID'] = '1'

        return data

    def get_item_id(self, root):

        item_id = 'BibTex'
        namespace = root.tag.split('{')[1].split('}')[0]
        request_tag = '{' + namespace + '}' + 'request'
        for element in root:
            if request_tag == element.tag:
                subs = element.get('identifier').split('/')
                item_id = subs[len(subs) - 1]

        return item_id
