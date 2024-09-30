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

"""Weko Serializers."""

from __future__ import absolute_import, print_function

import json

from flask import has_request_context
from flask_security import current_user
from invenio_pidrelations.contrib.versioning import PIDNodeVersioning
from invenio_records_files.api import Record
from invenio_records_rest.serializers.json import JSONSerializer

from weko_records.serializers.pidrelations import serialize_related_identifiers

# from ..permissions import has_read_files_permission


class WekoJSONSerializer(JSONSerializer):
    """JSON serializer.

    Adds or removes files from depending on access rights and provides a
    context to the request serializer.
    """

    def preprocess_record(self, pid, record, links_factory=None):
        """Include files for single record retrievals."""
        result = super(WekoJSONSerializer, self).preprocess_record(
            pid, record, links_factory=links_factory
        )
        # Add/remove files depending on access right.
        if isinstance(record, Record) and '_files' in record:
            if not has_request_context():
                result['files'] = record['_files']
            else:
                result['metadata'].pop('_buckets', None)

        # Serialize PID versioning as related identifiers
        
        pv = PIDNodeVersioning(pid=pid).parents.one_or_none()
        if pv is not None:
            rels = serialize_related_identifiers(pid)
            if rels:
                result['metadata'].setdefault(
                    'related_identifiers', []).extend(rels)
        return result

    def preprocess_search_hit(self, pid, record_hit, links_factory=None,
                              **kwargs):
        """Prepare a record hit from search engine for serialization."""
        result = super(WekoJSONSerializer, self).preprocess_search_hit(
            pid, record_hit, links_factory=links_factory, **kwargs
        )
        # Add files if in search hit (only public files exists in index)
        if '_files' in record_hit['_source']:
            result['files'] = record_hit['_source']['_files']
        elif '_files' in record_hit:
            result['files'] = record_hit['_files']
        else:
            # delete the bucket if no files
            result['metadata'].pop('_buckets', None)
        return result

    def dump(self, obj, context=None):
        """Serialize object with schema."""
        return self.schema_class(context=context).dump(obj).data

    def transform_record(self, pid, record, links_factory=None):
        """Transform record into an intermediate representation."""
        return self.dump(
            self.preprocess_record(pid, record, links_factory=links_factory),
            context={'pid': pid}
        )

    def transform_search_hit(self, pid, record_hit, links_factory=None):
        """Transform search result hit into an intermediate representation."""
        return self.dump(
            self.preprocess_search_hit(
                pid, record_hit, links_factory=links_factory),
            context={'pid': pid}
        )

    def serialize_exporter(self, pid, record):
        """Serialize a single record for the exporter."""
        return json.dumps(
            self.transform_search_hit(pid, record)
        ).encode('utf8') + b'\n'
