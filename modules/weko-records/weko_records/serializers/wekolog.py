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
"""Extends the FeedGenerator to add wekolog Elements to the feeds.

wekolog partly taken from
http://wekolog.org/namespaces/basic/1.0/
"""

from feedgen.ext.base import BaseExtension
from lxml import etree


class WekologBaseExtension(BaseExtension):
    """Wekolog Elements extension."""

    def __init__(self):
        """Init."""
        # http://wekolog.org/namespaces/basic/1.0/
        self._wekolog_terms = None
        self._wekolog_view = None
        self._wekolog_download = None

    def extend_ns(self):
        """Extend ns."""
        return {'wekolog': 'http://wekolog.org/namespaces/basic/1.0/'}

    def _extend_xml(self, xml_elem):
        """Extend xml_elem with set Wekolog fields.

        :param xml_elem: etree element
        """
        WEKOLOGELEMENTS_NS = 'http://wekolog.org/namespaces/basic/1.0/'

        elems = ['terms', 'view', 'download']
        for elem in elems:
            if hasattr(self, '_wekolog_%s' % elem):
                for val in getattr(self, '_wekolog_%s' % elem) or []:
                    node = etree.SubElement(xml_elem, '{%s}%s' % (WEKOLOGELEMENTS_NS, elem))
                    node.text = val

    def extend_atom(self, atom_feed):
        """Extend an Atom feed with the set Wekolog fields.

        :param atom_feed: The feed root element
        :returns: The feed root element
        """
        self._extend_xml(atom_feed)

        return atom_feed

    def extend_rss(self, rss_feed):
        """Extend a RSS feed with the set Wekolog fields.

        :param rss_feed: The feed root element
        :returns: The feed root element.
        """
        channel = rss_feed[0]
        self._extend_xml(channel)

        return rss_feed

    def extend_jpcoar(self, jpcoar_feed):
        """Extend a JPCOAR feed with the set Wekolog fields.

        :param jpcoar_feed: The feed root element
        :returns: The feed root element.
        """
        header = jpcoar_feed[0]
        self._extend_xml(header)

        return jpcoar_feed

    def terms(self, terms=None, replace=False):
        """Get or set the wekolog:terms.

        which is an entity responsible for making terms to the resource.

        :param terms: terms.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of terms.
        """
        if terms is not None:
            if not isinstance(terms, list):
                terms = [terms]
            if replace or not self._wekolog_terms:
                self._wekolog_terms = []
            self._wekolog_terms += terms
        return self._wekolog_terms

    def view(self, view=None, replace=False):
        """Get or set the wekolog:view.

        which is an entity responsible for making view to the resource.

        :param view: view.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of view.
        """
        if view is not None:
            if not isinstance(view, list):
                view = [view]
            if replace or not self._wekolog_view:
                self._wekolog_view = []
            self._wekolog_view += view
        return self._wekolog_view

    def download(self, download=None, replace=False):
        """Get or set the wekolog:download.

        which is an entity responsible for making download to the resource.

        :param download: download.
        :param replace: Replace alredy set contributors (deault: False).
        :returns: List of download.
        """
        if download is not None:
            if not isinstance(download, list):
                download = [download]
            if replace or not self._wekolog_download:
                self._wekolog_download = []
            self._wekolog_download += download
        return self._wekolog_download


class WekologExtension(WekologBaseExtension):
    """Wekolog Elements extension."""


class WekologEntryExtension(WekologBaseExtension):
    """Wekolog Elements extension."""

    def extend_atom(self, entry):
        """Add Wekolog elements to an atom item. Alters the item itself.

        :param entry: An atom entry element.
        :returns: The entry element.
        """
        self._extend_xml(entry)
        return entry

    def extend_rss(self, item):
        """Add Wekolog elements to a RSS item. Alters the item itself.

        :param item: A RSS item element.
        :returns: The item element.
        """
        self._extend_xml(item)
        return item
