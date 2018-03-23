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

"""Blueprint for weko-records-ui."""

import six
from flask import Blueprint, current_app, abort, request, redirect, url_for, make_response,render_template
from invenio_records_ui.utils import obj_or_import_string

blueprint = Blueprint(
    'weko_records_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


def publish(pid, record, template=None, **kwargs):
    r"""Record publish  status change view.

    Change record publish status with given status and renders record export template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :return: The rendered template.
    """

    from invenio_db import db
    from weko_deposit.api import WekoIndexer
    status = request.values.get('status')
    publish_status = record.get('publish_status')
    if not publish_status:
        record.update({'publish_status':(status or '0')})
    else:
        record['publish_status'] = (status or '0')

    record.commit()
    db.session.commit()

    indexer = WekoIndexer()
    indexer.update_publish_status(record)

    return redirect(url_for(".recid", pid_value=pid.pid_value))

    # resp = make_response(render_template(template,  pid=pid, record=record,))
    # resp.headers.extend(dict(location=url_for(".recid", pid_value=pid.pid_value)))
    # return resp


def export(pid, record, template=None, **kwargs):
    r"""Record serialization view.

    Serializes record with given format and renders record export template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :return: The rendered template.
    """
    formats = current_app.config.get('RECORDS_UI_EXPORT_FORMATS', {}).get(
        pid.pid_type)
    schema_type = request.view_args.get('format')
    fmt = formats.get(schema_type)

    if fmt is False:
        # If value is set to False, it means it was deprecated.
        abort(410)
    elif fmt is None:
        abort(404)
    else:
        if "json" not in schema_type:
            record.update({"@export_schema_type": schema_type})
        serializer = obj_or_import_string(fmt['serializer'])
        data = serializer.serialize(pid, record)
        if isinstance(data, six.binary_type):
            data = data.decode('utf8')

        # return render_template(
        #     template, pid=pid, record=record, data=data,
        #     format_title=fmt['title'],
        # )
        response = make_response(data)
        response.headers['Content-Type'] = 'text/xml' if "json" not in schema_type else 'text/plain'
        return response


@blueprint.app_template_filter("get_image_src")
def get_image_src(mimetype):
    """ Get image src by file type
    :param mimetype:
    :return src: dict
    """
    src = ""
    if "text/" in mimetype:
        src = "icon_16_txt.jpg"
    elif "officedocument.wordprocessingml" in mimetype:
        src = "icon_16_doc.jpg"
    elif "officedocument.spreadsheetml" in mimetype:
        src = "icon_16_xls.jpg"
    elif "officedocument.presentationml" in mimetype:
        src = "icon_16_ppt.jpg"
    elif "msword" in mimetype:
        src = "icon_16_doc.jpg"
    elif "excel" in mimetype:
        src = "icon_16_xls.jpg"
    elif "powerpoint" in mimetype:
        src = "icon_16_ppt.jpg"
    elif "zip" in mimetype or "rar" in mimetype:
        src = "icon_16_zip.jpg"
    elif "audio/" in mimetype:
        src = "icon_16_music.jpg"
    elif "xml" in mimetype:
        src = "icon_16_xml.jpg"
    elif "image/" in mimetype:
        src = "icon_16_picture.jpg"
    elif "pdf" in mimetype:
        src = "icon_16_pdf.jpg"
    elif "video/" in mimetype:
        if "flv" in mimetype:
            src = "icon_16_flash.jpg"
        else:
            src = "icon_16_movie.jpg"
    else:
        src = "icon_16_others.jpg"

    return "/static/images/icon/" + src


@blueprint.app_template_filter("get_license_icon")
def get_license_icon(type):
    """
     Get License type icon
    :param type:
    :return:
    """
    lic_dict = {
        "license_1": "Creative Commons : 表示",
        "license_2": "Creative Commons : 表示 - 継承",
        "license_3": "Creative Commons : 表示 - 改変禁止",
        "license_4": "Creative Commons : 表示 - 非営利",
        "license_5": "Creative Commons : 表示 - 非営利 - 継承",
        "license_6": "Creative Commons : 表示 - 非営利 - 改変禁止",
    }

    src = ""
    if "license_free" in type:
        src = ""
    elif "license_0" in type:
        src = "88x31(1).png"
    elif "license_1" in type:
        src = "88x31(2).png"
    elif "license_2" in type:
        src = "88x31(3).png"
    elif "license_3" in type:
        src = "88x31(4).png"
    elif "license_4" in type:
        src = "88x31(5).png"
    elif "license_5" in type:
        src = "88x31(6).png"
    else:
        src = ""

    lst = []
    src = "/static/images/default/" + src if len(src) > 0 else ""
    lst.append(src)
    lst.append(lic_dict.get(type, ""))

    return lst
