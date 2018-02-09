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
        if 'detail' in displaytype and '.pdf' in file_name:
            from PyPDF2.pdf import PdfFileWriter, PdfFileReader
            import io
            source = PdfFileReader(io.BytesIO(stream), strict=True)
            fp = source.getPage(0)
            writer = PdfFileWriter()
            writer.addPage(fp)
            f = io.BytesIO()
            writer.write(f)
            stream = f.getvalue()

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
    r"""Dowload file.

    :param pid: PID object.
    :param record: Record object.
    :param _record_file_factory: record file factory object
    :param \*\*kwargs: Additional view arguments based on URL rule.
    """

    fn = request.view_args.get("filename")

    # Check permissions
    check_download_permission(record, fn)

    return prepare_response(pid.pid_value)


def check_download_permission(record, fn):
    """Check download permission.

    :param record: Record object.
    :param fn: File name
    """
    user_id = current_user.get_id()
    grn = get_groups(record, fn)
    if grn is not None:
        if user_id:
            query = Group.query.filter_by(name=grn).join(Membership)\
                .filter_by(user_id=user_id, state=MembershipState.ACTIVE)
            if query.count() < 1:
                abort(403)
        else:
            abort(403)


def get_groups(record, fn):
    """Get file groups name.

    :param record: Record object.
    :param fn: file name
    :return grn: group name
    """
    fm = record.get("filemeta")
    grn = None
    if isinstance(fm, dict):
        avm = fm.get("attribute_value_mlt")
        if isinstance(avm, list):
            for mlt in avm:
                if isinstance(mlt, dict):
                    if fn == mlt.get("filename"):
                        grn = mlt.get("group")
                        break
    return grn
