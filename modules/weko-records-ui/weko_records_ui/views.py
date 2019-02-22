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
from flask import Blueprint, abort, current_app, render_template, \
    make_response, redirect, request, url_for, flash

from invenio_records_ui.utils import obj_or_import_string
from invenio_records_ui.signals import record_viewed
from weko_index_tree.models import IndexStyle
from .permissions import check_created_id
from weko_search_ui.api import get_search_detail_keyword
from weko_deposit.api import WekoIndexer
from .models import PDFCoverPageSettings
import werkzeug

blueprint = Blueprint(
    'weko_records_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


def publish(pid, record, template=None, **kwargs):
    r"""Record publish  status change view.

    Change record publish status with given status and renders record export
    template.

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
        record.update({'publish_status': (status or '0')})
    else:
        record['publish_status'] = (status or '0')

    record.commit()
    db.session.commit()

    current_app.logger.debug(record)
    indexer = WekoIndexer()
    indexer.update_publish_status(record)

    return redirect(url_for('.recid', pid_value=pid.pid_value))

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
        if 'json' not in schema_type and 'bibtex' not in schema_type:
            record.update({'@export_schema_type': schema_type})

        serializer = obj_or_import_string(fmt['serializer'])
        data = serializer.serialize(pid, record)
        if isinstance(data, six.binary_type):
            data = data.decode('utf8')

        # return render_template(
        #     template, pid=pid, record=record, data=data,
        #     format_title=fmt['title'],
        # )

        response = make_response(data)

        if 'json' in schema_type or 'bibtex' in schema_type:
            response.headers['Content-Type'] = 'text/plain'
        else:
            response.headers['Content-Type'] = 'text/xml'

        return response


@blueprint.app_template_filter('get_image_src')
def get_image_src(mimetype):
    """Get image src by file type.

    :param mimetype:
    :return src: dict
    """
    if 'text/' in mimetype:
        src = 'icon_16_txt.jpg'
    elif 'officedocument.wordprocessingml' in mimetype:
        src = 'icon_16_doc.jpg'
    elif 'officedocument.spreadsheetml' in mimetype:
        src = 'icon_16_xls.jpg'
    elif 'officedocument.presentationml' in mimetype:
        src = 'icon_16_ppt.jpg'
    elif 'msword' in mimetype:
        src = 'icon_16_doc.jpg'
    elif 'excel' in mimetype:
        src = 'icon_16_xls.jpg'
    elif 'powerpoint' in mimetype:
        src = 'icon_16_ppt.jpg'
    elif 'zip' in mimetype or 'rar' in mimetype:
        src = 'icon_16_zip.jpg'
    elif 'audio/' in mimetype:
        src = 'icon_16_music.jpg'
    elif 'xml' in mimetype:
        src = 'icon_16_xml.jpg'
    elif 'image/' in mimetype:
        src = 'icon_16_picture.jpg'
    elif 'pdf' in mimetype:
        src = 'icon_16_pdf.jpg'
    elif 'video/' in mimetype:
        if 'flv' in mimetype:
            src = 'icon_16_flash.jpg'
        else:
            src = 'icon_16_movie.jpg'
    else:
        src = 'icon_16_others.jpg'

    return '/static/images/icon/' + src


@blueprint.app_template_filter('get_license_icon')
def get_license_icon(type):
    """Get License type icon.

    :param type:
    :return:
    """
    lic_dict = {
        'license_0': 'Creative Commons : 表示',
        'license_1': 'Creative Commons : 表示 - 継承',
        'license_2': 'Creative Commons : 表示 - 改変禁止',
        'license_3': 'Creative Commons : 表示 - 非営利',
        'license_4': 'Creative Commons : 表示 - 非営利 - 継承',
        'license_5': 'Creative Commons : 表示 - 非営利 - 改変禁止',
    }

    href_dict = {
        'license_0': 'https://creativecommons.org/licenses/by/4.0/deed.ja',
        'license_1': 'https://creativecommons.org/licenses/by-sa/4.0/deed.ja',
        'license_2': 'https://creativecommons.org/licenses/by-nd/4.0/deed.ja',
        'license_3': 'https://creativecommons.org/licenses/by-nc/4.0/deed.ja',
        'license_4': 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja',
        'license_5': 'https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja',
    }

    if 'license_free' in type:
        src = ''
        lic = ''
        href = '#'
    elif 'license_0' in type:
        src = '88x31(1).png'
        lic = lic_dict.get('license_0')
        href = href_dict.get('license_0')
    elif 'license_1' in type:
        src = '88x31(2).png'
        lic = lic_dict.get('license_1')
        href = href_dict.get('license_1')
    elif 'license_2' in type:
        src = '88x31(3).png'
        lic = lic_dict.get('license_2')
        href = href_dict.get('license_2')
    elif 'license_3' in type:
        src = '88x31(4).png'
        lic = lic_dict.get('license_3')
        href = href_dict.get('license_3')
    elif 'license_4' in type:
        src = '88x31(5).png'
        lic = lic_dict.get('license_4')
        href = href_dict.get('license_4')
    elif 'license_5' in type:
        src = '88x31(6).png'
        lic = lic_dict.get('license_5')
        href = href_dict.get('license_5')
    else:
        src = ''
        lic = ''
        href = '#'

    src = '/static/images/default/' + src if len(src) > 0 else ''
    lst = (src, lic, href)

    return lst


@blueprint.app_template_filter('check_permission')
def check_permission(record):
    """Check Permission on Page.

    :param record:
    :return: result
    """
    return check_created_id(record)


def default_view_method(pid, record, template=None, **kwargs):
    """Display default view.

    Sends record_viewed signal and renders template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :returns: The rendered template.
    """
    record_viewed.send(
        current_app._get_current_object(),
        pid=pid,
        record=record,
    )
    getargs = request.args
    community_id = ""
    ctx = {'community': None}
    if 'community' in getargs:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

    # Get index style
    style = IndexStyle.get(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width if style else '3'
    height = style.height if style else None

    detail_condition=get_search_detail_keyword('')

    weko_indexer = WekoIndexer()
    res = weko_indexer.get_item_link_info(pid= record.get("control_number"))
    if res is not None:
        record["relation"]=res
    else:
        record["relation"] = {}

    return render_template(
        template,
        pid=pid,
        record=record,
        community_id=community_id,
        width=width,
        detail_condition=detail_condition,
        height=height,
        **ctx,
        **kwargs
    )

@blueprint.route('/admin/pdfcoverpage', methods=['GET', 'POST'])
def set_pdfcoverpage_header():
    #limit upload file size : 1MB
    current_app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

    @blueprint.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
    def handle_over_max_file_size(error):
        print("werkzeug.exceptions.RequestEntityTooLarge")
        return 'result : file size is overed.'

    # Save PDF Cover Page Header settings
    if request.method == 'POST':
        record = PDFCoverPageSettings.find(1)
        avail = request.form.get('availability')
        header_display_type = request.form.get('header-display')
        header_output_string = request.form.get('header-output-string')
        header_output_image_file = request.files.get('header-output-image')
        header_output_image_filename = header_output_image_file.filename
        header_output_image = record.header_output_image
        if not header_output_image_filename == '':
            upload_dir = "/code/header-icons/"
            header_output_image = upload_dir + header_output_image_filename
            header_output_image_file.save(header_output_image)
        header_display_position = request.form.get('header-display-position')

        # update PDF cover page settings
        PDFCoverPageSettings.update(1,
                                    avail,
                                    header_display_type,
                                    header_output_string,
                                    header_output_image,
                                    header_display_position
                                    )

        flash('PDF cover page settings have been updated.', category='success')
        return redirect('/admin/pdfcoverpage')

    return redirect('/admin/pdfcoverpage')
