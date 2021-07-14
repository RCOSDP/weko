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

"""Utils for weko-authors."""

import csv
import io
import traceback
from copy import deepcopy
from sys import stdout

from flask import current_app
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.models import FileInstance, Location
from invenio_indexer.api import RecordIndexer

from .api import WekoAuthors
from .config import WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY, \
    WEKO_AUTHORS_EXPORT_CACHE_URL_KEY, WEKO_AUTHORS_TSV_MAPPING
from .models import AuthorsPrefixSettings


def get_author_setting_obj(scheme):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsPrefixSettings).filter(
            AuthorsPrefixSettings.scheme == scheme).one_or_none()
    except Exception as ex:
        current_app.logger.debug(ex)
    return None


def check_email_existed(email: str):
    """Check email has existed.

    :param email: email string.
    :returns: author info.
    """
    body = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"gather_flg": 0}},
                    {"term": {"emailInfo.email.raw": email}}
                ]
            }
        }
    }

    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=body
    )

    if result['hits']['total']:
        return {
            'email': email,
            'author_id': result['hits']['hits'][0]['_source']['pk_id']
        }
    else:
        return {
            'email': email,
            'author_id': ''
        }


def get_export_status():
    """Get export status from cache."""
    return current_cache.get(WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY) or {}


def set_export_status(start_time=None, task_id=None):
    """Set export status into cache."""
    data = get_export_status() or dict()
    if start_time:
        data['start_time'] = start_time
    if task_id:
        data['task_id'] = task_id

    current_cache.set(WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY, data, timeout=0)
    return data


def delete_export_status():
    """Delete export status."""
    current_cache.delete(WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY)


def get_export_url():
    """Get exported info from cache."""
    return current_cache.get(WEKO_AUTHORS_EXPORT_CACHE_URL_KEY) or {}


def save_export_url(start_time, end_time, file_uri):
    """Save exported info into cache."""
    data = dict(
        start_time=start_time,
        end_time=end_time,
        file_uri=file_uri
    )

    current_cache.set(WEKO_AUTHORS_EXPORT_CACHE_URL_KEY, data, timeout=0)
    return data


def export_authors():
    """Export all authors."""
    file_uri = None
    try:
        mappings = deepcopy(WEKO_AUTHORS_TSV_MAPPING)
        authors = WekoAuthors.get_all(with_deleted=False, with_gather=False)
        schemes = WekoAuthors.get_identifier_scheme_info()
        row_header, row_label_en, row_label_jp, row_data = \
            WekoAuthors.prepare_export_data(mappings, authors, schemes)

        # write csv data to a stream
        csv_io = io.StringIO()
        writer = csv.writer(csv_io, delimiter='\t',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerows([row_header, row_label_en, row_label_jp, *row_data])
        reader = io.BufferedReader(io.BytesIO(
            csv_io.getvalue().encode("utf-8")))

        # save data into location
        cache_url = get_export_url()
        if not cache_url:
            file = FileInstance.create()
            file.set_contents(
                reader, default_location=Location.get_default().uri)
        else:
            file = FileInstance.get_by_uri(cache_url['file_uri'])
            file.writable = True
            file.set_contents(reader)

        file_uri = file.uri if file else None
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        current_app.logger.error(ex)
        traceback.print_exc(file=stdout)

    return file_uri
