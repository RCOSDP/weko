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
    Extends the FeedGenerator to add PRISM Elements to the feeds.

    prism partly taken from
    http://prismstandard.org/namespaces/basic/2.0/
"""

from lxml import etree

from feedgen.ext.base import BaseExtension

class PrismBaseExtension(BaseExtension):
    """PRISM Elements extension.
    """

    def __init__(self):
        # http://prismstandard.org/namespaces/basic/2.0/
        self._prism_aggregationType = None
        self._prism_publicationName = None
        self._prism_issn = None
        self._prism_volume = None
        self._prism_number = None
        self._prism_startingPage = None
        self._prism_endingPage = None
        self._prism_publicationDate = None
        self._prism_creationDate = None
        self._prism_modificationDate = None
        self._prism_url = None

    def extend_ns(self):
        return {'prism': 'http://prismstandard.org/namespaces/basic/2.0/'}

    def _extend_xml(self, xml_elem):
        """Extend xml_elem with set Prism fields.

        :param xml_elem: etree element
        """
        PRISMELEMENTS_NS = 'http://prismstandard.org/namespaces/basic/2.0/'

        for elem in ['aggregationType', 'publicationName', 'issn', 'volume', 'number',
                     'startingPage', 'endingPage', 'publicationDate', 'creationDate',
                     'modificationDate', 'url']:

            if hasattr(self, '_prism_%s' % elem):
                for val in getattr(self, '_prism_%s' % elem) or []:

                    node = etree.SubElement(xml_elem,
                                            '{%s}%s' % (PRISMELEMENTS_NS, elem))
                    node.text = val

    def extend_atom(self, atom_feed):
        """Extend an Atom feed with the set Prism fields.

        :param atom_feed: The feed root element
        :returns: The feed root element
        """

        self._extend_xml(atom_feed)

        return atom_feed

    def extend_rss(self, rss_feed):
        """Extend a RSS feed with the set Prism fields.

        :param rss_feed: The feed root element
        :returns: The feed root element.
        """
        channel = rss_feed[0]
        self._extend_xml(channel)

        return rss_feed

    def aggregationType(self, aggregationType=None, replace=False):
        """Get or set the prism:aggregationType which is an entity responsible for
        making totalResults to the resource.

        :param aggregationType: aggregationType.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of aggregationType.
        """
        if aggregationType is not None:
            if not isinstance(aggregationType, list):
                aggregationType = [aggregationType]
            if replace or not self._prism_aggregationType:
                self._prism_aggregationType = []
            self._prism_aggregationType += aggregationType
        return self._prism_aggregationType

    def publicationName(self, publicationName=None, replace=False):
        """Get or set the prism:publicationName which is an entity responsible for
        making publicationName to the resource.

        :param publicationName: publicationName.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of publicationName.
        """
        if publicationName is not None:
            if not isinstance(publicationName, list):
                publicationName = [publicationName]
            if replace or not self._prism_publicationName:
                self._prism_publicationName = []
            self._prism_publicationName += publicationName
        return self._prism_publicationName

    def issn(self, issn=None, replace=False):
        """Get or set the prism:issn which is an entity responsible for
        making issn to the resource.

        :param issn: issn.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of issn.
        """
        if issn is not None:
            if not isinstance(issn, list):
                issn = [issn]
            if replace or not self._prism_issn:
                self._prism_issn = []
            self._prism_issn += issn
        return self._prism_issn

    def volume(self, volume=None, replace=False):
        """Get or set the prism:volume which is an entity responsible for
        making volume to the resource.

        :param volume: volume.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of volume.
        """
        if volume is not None:
            if not isinstance(volume, list):
                volume = [volume]
            if replace or not self._prism_volume:
                self._prism_volume = []
            self._prism_volume += volume
        return self._prism_volume

    def number(self, number=None, replace=False):
        """Get or set the prism:number which is an entity responsible for
        making number to the resource.

        :param number: number.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of number.
        """
        if number is not None:
            if not isinstance(number, list):
                number = [number]
            if replace or not self._prism_number:
                self._prism_number = []
            self._prism_number += number
        return self._prism_number

    def startingPage(self, startingPage=None, replace=False):
        """Get or set the prism:startingPage which is an entity responsible for
        making startingPage to the resource.

        :param startingPage: startingPage.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of startingPage.
        """
        if startingPage is not None:
            if not isinstance(startingPage, list):
                startingPage = [startingPage]
            if replace or not self._prism_startingPage:
                self._prism_startingPage = []
            self._prism_startingPage += startingPage
        return self._prism_startingPage

    def endingPage(self, endingPage=None, replace=False):
        """Get or set the prism:endingPage which is an entity responsible for
        making endingPage to the resource.

        :param endingPage: endingPage.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of endingPage.
        """
        if endingPage is not None:
            if not isinstance(endingPage, list):
                endingPage = [endingPage]
            if replace or not self._prism_endingPage:
                self._prism_endingPage = []
            self._prism_endingPage += endingPage
        return self._prism_endingPage

    def publicationDate(self, publicationDate=None, replace=False):
        """Get or set the prism:publicationDate which is an entity responsible for
        making publicationDate to the resource.

        :param publicationDate: publicationDate.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of publicationDate.
        """
        if publicationDate is not None:
            if not isinstance(publicationDate, list):
                publicationDate = [publicationDate]
            if replace or not self._prism_publicationDate:
                self._prism_publicationDate = []
            self._prism_publicationDate += publicationDate
        return self._prism_publicationDate

    def creationDate(self, creationDate=None, replace=False):
        """Get or set the prism:creationDate which is an entity responsible for
        making creationDate to the resource.

        :param creationDate: creationDate.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of creationDate.
        """
        if creationDate is not None:
            if not isinstance(creationDate, list):
                creationDate = [creationDate]
            if replace or not self._prism_creationDate:
                self._prism_creationDate = []
            self._prism_creationDate += creationDate
        return self._prism_creationDate

    def modificationDate(self, modificationDate=None, replace=False):
        """Get or set the prism:modificationDate which is an entity responsible for
        making modificationDate to the resource.

        :param modificationDate: modificationDate.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of modificationDate.
        """
        if modificationDate is not None:
            if not isinstance(modificationDate, list):
                modificationDate = [modificationDate]
            if replace or not self._prism_modificationDate:
                self._prism_modificationDate = []
            self._prism_modificationDate += modificationDate
        return self._prism_modificationDate

    def url(self, url=None, replace=False):
        """Get or set the prism:url which is an entity responsible for
        making url to the resource.

        :param url: url.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of url.
        """
        if url is not None:
            if not isinstance(url, list):
                url = [url]
            if replace or not self._prism_url:
                self._prism_url = []
            self._prism_url += url
        return self._prism_url


class PrismExtension(PrismBaseExtension):
    """Prism Elements extension.
    """


class PrismEntryExtension(PrismBaseExtension):
    """Prism Elements extension.
    """
    def extend_atom(self, entry):
        """Add Prism elements to an atom item. Alters the item itself.

        :param entry: An atom entry element.
        :returns: The entry element.
        """
        self._extend_xml(entry)
        return entry

    def extend_rss(self, item):
        """Add Prism elements to a RSS item. Alters the item itself.

        :param item: A RSS item element.
        :returns: The item element.
        """
        self._extend_xml(item)
        return item
