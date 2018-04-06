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

"""Utilities for download file."""

import unicodedata
import mimetypes

from flask import abort, current_app, render_template, request
from flask_security import current_user
from weko_groups.api import Group, Membership, MembershipState
from werkzeug.datastructures import Headers
from werkzeug.urls import url_quote
from invenio_files_rest.views import ObjectResource
from invenio_records_files.utils import record_file_factory

from .api import FilesMetadata, ItemTypes


def weko_view_method(pid, record, template=None, **kwargs):
    r"""Display Weko view.

    Sends record_viewed signal and renders template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :returns: The rendered template.
    """
    flst = FilesMetadata.get_records(pid.pid_value)
    frecord = []

    if len(flst) > 0:
        for fj in flst:
            frecord.append(fj.dumps())

    item_type=ItemTypes.get_by_id(id_=record['item_type_id'])
    item_type_info = "{}({})".format(item_type.item_type_name.name,
                                     item_type.tag)
    return render_template(
        template,
        pid=pid,
        record=record,
        files=frecord,
        item_type_info=item_type_info
    )


def prepare_response(pid_value, fd=True):
    """
     prepare response data and header
    :param pid_value:
    :param full:
    :return:
    """

    fn = request.view_args.get("filename")

    flst = FilesMetadata.get_records(pid_value)
    for fj in flst:
        if fj.dumps().get("display_name") == fn:
            stream = fj.model.contents[:]
            displaytype = fj.model.json.get("displaytype")
            file_name = fj.model.json.get("file_name")
            break

    headers = Headers()
    headers['Content-Length'] = len(stream)
    try:
        filenames = {'filename': fn.encode('latin-1')}
    except UnicodeEncodeError:
        filenames = {'filename*': "UTF-8''%s" % url_quote(fn)}
        encoded_filename = (unicodedata.normalize('NFKD', fn)
            .encode('latin-1', 'ignore'))
        if encoded_filename:
            filenames['filename'] = encoded_filename

    if fd:
        headers.add('Content-Disposition', 'attachment', **filenames)
        mimetype = 'application/octet-stream'
    else:
        headers['Content-Type'] = 'text/plain; charset=utf-8'
        headers.add('Content-Disposition', 'inline')
        mimetype = mimetypes.guess_type(request.view_args.get("filename"))[0]
        # if 'detail' in displaytype and '.pdf' in file_name:
        #     from PyPDF2.pdf import PdfFileWriter, PdfFileReader
        #     import io
        #     source = PdfFileReader(io.BytesIO(stream), strict=True)
        #     fp = source.getPage(0)
        #     writer = PdfFileWriter()
        #     writer.addPage(fp)
        #     f = io.BytesIO()
        #     writer.write(f)
        #     stream = f.getvalue()

    rv = current_app.response_class(
        stream,
        mimetype=mimetype,
        headers=headers,
        direct_passthrough=True,
    )

    return rv


def file_preview_ui(pid, record, _record_file_factory=None, **kwargs):
    """

    :param pid:
    :param record:
    :param _record_file_factory:
    :param kwargs:
    :return:
    """

    return prepare_response(pid.pid_value, False)


def file_download_ui(pid, record, _record_file_factory=None, **kwargs):
    """File download view for a given record.

    Plug this method into your ``RECORDS_UI_ENDPOINTS`` configuration:

    .. code-block:: python

        RECORDS_UI_ENDPOINTS = dict(
            recid=dict(
                # ...
                route='/records/<pid_value/files/<filename>',
                view_imp='invenio_records_files.utils:file_download_ui',
                record_class='invenio_records_files.api:Record',
            )
        )

    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The record metadata.
    """
    _record_file_factory = _record_file_factory or record_file_factory
    # Extract file from record.
    fileobj = _record_file_factory(
        pid, record, kwargs.get('filename')
    )

    if not fileobj:
        abort(404)

    obj = fileobj.obj

    # Check group permission
    check_download_permission(fileobj.get('groups'))

    # Check permissions
    ObjectResource.check_object_permission(obj)

    # Send file.
    return ObjectResource.send_object(
        obj.bucket, obj,
        expected_chksum=fileobj.get('checksum'),
        logger_data={
            'bucket_id': obj.bucket_id,
            'pid_type': pid.pid_type,
            'pid_value': pid.pid_value,
        },
    )


def check_download_permission(group_id):
    """Check download permission.
    :param group_id: Group_id
    """
    user_id = current_user.get_id()
    if group_id:
        if user_id:
            query = Group.query.filter_by(id=group_id).join(Membership)\
                .filter_by(user_id=user_id, state=MembershipState.ACTIVE)
            if query.count() < 1:
                abort(403)
        else:
            abort(403)
