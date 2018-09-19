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
    Extends the FeedGenerator to add Dubline Core Elements to the feeds.

    Dubline core partly taken from
    http://purl.org/dc/elements/1.1/
"""

from lxml import etree

from feedgen.ext.dc import DcBaseExtension

class DcWekoBaseExtension(DcBaseExtension):
    """DC Elements extension.
    """

    def __init__(self):
        self._dcelem_publisher = None
        self._dcelem_publisher_lang = None
        super().__init__()

    def _extend_xml(self, xml_elem):
        '''Extend xml_elem with set DC fields.
        :param xml_elem: etree element
        '''
        DCELEMENTS_NS = 'http://purl.org/dc/elements/1.1/'
        XMLELEMENTS_NS = 'http://www.w3.org/XML/1998/namespace'

        for elem in ['contributor', 'coverage', 'creator', 'date',
                     'description', 'language', 'publisher', 'relation',
                     'rights', 'source', 'subject', 'title', 'type', 'format',
                     'identifier']:
            if hasattr(self, '_dcelem_%s' % elem):
                values = getattr(self, '_dcelem_%s' % elem) or []
                for i in range(len(values)):
                    val = values[i]
                    node = etree.SubElement(xml_elem,
                                            '{%s}%s' % (DCELEMENTS_NS, elem))
                    node.text = val
                    if elem == 'publisher':
                        if hasattr(self, '_dcelem_%s_lang' % elem):
                            langs = getattr(self, '_dcelem_%s_lang' % elem) or []
                            if i < len(langs):
                                node.set('{%s}lang' % XMLELEMENTS_NS, langs[i])

    def dc_publisher(self, publisher=None, lang=None, replace=False):
        '''Get or set the dc:publisher which is an entity responsible for
        making the resource available.
        For more information see:
        http://dublincore.org/documents/dcmi-terms/#elements-publisher
        :param publisher: Publisher or list of publishers.
        :param replace: Replace alredy set publishers (deault: False).
        :returns: List of publishers.
        '''
        if publisher is not None:
            if not isinstance(publisher, list):
                publisher = [publisher]
            if replace or not self._dcelem_publisher:
                self._dcelem_publisher = []
            self._dcelem_publisher += publisher

        if lang is not None:
            if not isinstance(lang, list):
                lang = [lang]
            if replace or not self._dcelem_publisher_lang:
                self._dcelem_publisher_lang = []
            self._dcelem_publisher_lang += lang

        return self._dcelem_publisher

class DcWekoEntryExtension(DcWekoBaseExtension):
    """Dublin Core Elements extension for podcasts.
    """
    def extend_atom(self, entry):
        '''Add dc elements to an atom item. Alters the item itself.
        :param entry: An atom entry element.
        :returns: The entry element.
        '''
        self._extend_xml(entry)
        return entry

    def extend_rss(self, item):
        '''Add dc elements to a RSS item. Alters the item itself.
        :param item: A RSS item element.
        :returns: The item element.
        '''
        self._extend_xml(item)
        return item
