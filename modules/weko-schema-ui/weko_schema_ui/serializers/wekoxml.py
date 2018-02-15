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

"""WEKO based serializer."""

from invenio_records.api import Record
from invenio_records_rest.serializers.marshmallow import MarshmallowSerializer

from ..utils import dumps, dumps_etree


class WekoXMLSerializer(MarshmallowSerializer):
    """WekoXML serializer."""

    def __init__(self, xslt_filename=None, schema_class=None,
                 replace_refs=False):
        """Initialize serializer.

        :param dojson_model: The DoJSON model able to convert JSON through the
            ``do()`` function.
        :param xslt_filename: XSLT filename. (Default: ``None``)
        :param schema_class: The schema class. (Default: ``None``)
        :param replace_refs: Boolean value to configure if replace the ``$ref``
            keys within the JSON. (Default: ``False``)
        """
        self.dumps_kwargs = dict(xslt_filename=xslt_filename) if \
            xslt_filename else {}

        self.schema_class = schema_class
        super(WekoXMLSerializer, self).__init__(replace_refs=replace_refs)

    def serialize(self, pid, record, links_factory=None):
        """Serialize a single record and persistent identifier.

        :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        :param record: The :class:`invenio_records.api.Record` instance.
        :param links_factory: Factory function for the link generation,
            which are added to the response.
        :returns: The object serialized.
        """
        return dumps(self.transform_record(pid, record, links_factory),
                     **self.dumps_kwargs)

    def serialize_oaipmh(self, pid, record, schema_type):
        """Serialize a single record for OAI-PMH.

        :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        :param record: The :class:`invenio_records.api.Record` instance.
        :returns: The object serialized.
        """
        obj = self.transform_record(pid, record['_source']) \
            if isinstance(record['_source'], Record) \
            else self.transform_search_hit(pid, record)

        return dumps_etree(obj, schema_type)
