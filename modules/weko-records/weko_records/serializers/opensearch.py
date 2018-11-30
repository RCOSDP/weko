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

"""
    Extends the FeedGenerator to add Opensearch Elements to the feeds.

    opensearch partly taken from
    http://a9.com/-/spec/opensearch/1.1/

"""

from lxml import etree

from feedgen.ext.base import BaseExtension


class OpensearchBaseExtension(BaseExtension):
    """Opensearch Elements extension.
    """

    def __init__(self):
        # http://a9.com/-/spec/opensearch/1.1/
        self._oselem_totalResults = None
        self._oselem_startIndex = None
        self._oselem_itemsPerPage = None

    def extend_ns(self):
        return {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}

    def _extend_xml(self, xml_elem):
        """Extend xml_elem with set opensearch fields.

        :param xml_elem: etree element
        """
        OPENSEARCHELEMENTS_NS = 'http://a9.com/-/spec/opensearch/1.1/'

        for elem in ['totalResults', 'startIndex', 'itemsPerPage']:
            if hasattr(self, '_oselem_%s' % elem):
                for val in getattr(self, '_oselem_%s' % elem) or []:
                    node = etree.SubElement(xml_elem,
                                            '{%s}%s' % (OPENSEARCHELEMENTS_NS, elem))
                    node.text = val

    def extend_atom(self, atom_feed):
        """Extend an Atom feed with the set opensearch fields.

        :param atom_feed: The feed root element
        :returns: The feed root element
        """

        self._extend_xml(atom_feed)

        return atom_feed

    def extend_rss(self, rss_feed):
        """Extend a RSS feed with the set opensearch fields.

        :param rss_feed: The feed root element
        :returns: The feed root element.
        """
        channel = rss_feed[0]
        self._extend_xml(channel)

        return rss_feed

    def extend_jpcoar(self, jpcoar_feed):
        """Extend a JPCOAR feed with the set opensearch fields.

        :param jpcoar_feed: The feed root element
        :returns: The feed root element.
        """
        header = jpcoar_feed[0]
        self._extend_xml(header)

        return jpcoar_feed

    def totalResults(self, totalResults=None, replace=False):
        """Get or set the opensearch:totalResults which is an entity responsible for
        making totalResults to the resource.

        :param totalResults: totalResults.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of contributors.
        """
        if totalResults is not None:
            if not isinstance(totalResults, list):
                totalResults = [totalResults]
            if replace or not self._oselem_totalResults:
                self._oselem_totalResults = []
            self._oselem_totalResults += totalResults
        return self._oselem_totalResults

    def startIndex(self, startIndex=None, replace=False):
        """Get or set the opensearch:startIndex which is an entity responsible for
        making startIndex to the resource.

        :param startIndex: startIndex.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of contributors.
        """
        if startIndex is not None:
            if not isinstance(startIndex, list):
                startIndex = [startIndex]
            if replace or not self._oselem_startIndex:
                self._oselem_startIndex = []
            self._oselem_startIndex += startIndex
        return self._oselem_startIndex

    def itemsPerPage(self, itemsPerPage=None, replace=False):
        """Get or set the opensearch:itemsPerPage which is an entity responsible for
        making itemsPerPage to the resource.

        :param itemsPerPage: totalResults.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of contributors.
        """
        if itemsPerPage is not None:
            if not isinstance(itemsPerPage, list):
                itemsPerPage = [itemsPerPage]
            if replace or not self._oselem_itemsPerPage:
                self._oselem_itemsPerPage = []
            self._oselem_itemsPerPage += itemsPerPage
        return self._oselem_itemsPerPage

class OpensearchExtension(OpensearchBaseExtension):
    """Opensearch Elements extension.
    """


class OpensearchEntryExtension(OpensearchBaseExtension):
    """Opensearch Elements extension.
    """
    def extend_atom(self, entry):
        """Add Opensearch elements to an atom item. Alters the item itself.

        :param entry: An atom entry element.
        :returns: The entry element.
        """
        self._extend_xml(entry)
        return entry

    def extend_rss(self, item):
        """Add Opensearch elements to a RSS item. Alters the item itself.

        :param item: A RSS item element.
        :returns: The item element.
        """
        self._extend_xml(item)
        return item
