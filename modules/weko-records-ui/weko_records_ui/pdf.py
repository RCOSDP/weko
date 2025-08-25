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

"""Utilities for making the PDF cover page and newly combined PDFs."""

import errno
import io
import json
import os
import tempfile
import unicodedata
from datetime import datetime

from flask import current_app, flash, redirect, request, send_file
from flask_babelex import gettext as _
from fpdf import FPDF
from invenio_files_rest.views import ObjectResource
from invenio_i18n.ext import current_i18n
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from pypdf import PdfReader, PdfWriter
from weko_deposit.api import WekoRecord
from weko_items_autofill.utils import get_workflow_journal
from weko_records.api import ItemsMetadata, ItemTypes
from weko_records.serializers.feed import WekoFeedGenerator
from weko_records.serializers.utils import get_mapping
from weko_records.utils import get_value_by_selected_lang
from weko_workflow.api import WorkActivity

from weko_records_ui.utils import get_record_permalink, \
    item_setting_show_email,get_values_by_selected_lang

from .models import PDFCoverPageSettings
from .utils import get_license_pdf, get_pair_value


def get_east_asian_width_count(text):
    """Def eat asian width count."""
    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in 'FWA':
            count += 2
        else:
            count += 1
    return count

LANG_CONVERT = {
    "jpn": "Japanese",
    "eng": "English"
}

def make_combined_pdf(pid, fileobj, obj, lang_user):
    """Make the cover-page-combined PDF file.

    :param pid: PID object
    :param fileobj: File metadata
    :param obj: File object
    :param lang_user: LANGUAGE of access user
    :return: cover-page-combined PDF file object
    """
    DPI = 96
    MM_IN_INCH = 25.4
    # tweak these values (in pixels)
    MAX_WIDTH = 800
    MAX_HEIGHT = 500
    # Default height of image in pdf.
    df_height = 30

    def pixels_to_mm(val):
        return val * MM_IN_INCH / DPI

    def resize_to_fit(imgFilename):
        from PIL import Image
        img = Image.open(imgFilename)
        width, height = img.size
        width_scale = MAX_WIDTH / width
        height_scale = MAX_HEIGHT / height
        scale = min(width_scale, height_scale)
        result_width = round(pixels_to_mm(scale * width))
        result_height = round(pixels_to_mm(scale * height))

        return result_width, result_height

    def get_center_position(imgFilename):
        pdf_w, pdf_h = pdf.w, pdf.h
        im_w, im_h = resize_to_fit(imgFilename)
        # Width to height ratio of uploaded image.
        w_to_h_ratio = im_w / im_h
        # Get width image by default height.
        width_image = df_height * w_to_h_ratio
        # Get position x, y.
        position_x = (pdf_w - width_image) / 2
        position_y = (pdf_w - df_height) / 2

        return position_x, position_y

    def get_right_position(imgFilename):
        pdf_w, pdf_h = pdf.w, pdf.h
        im_w, im_h = resize_to_fit(imgFilename)
        # Width to height ratio of uploaded image.
        w_to_h_ratio = im_w / im_h
        # Get width image by default height.
        width_image = df_height * w_to_h_ratio
        # Get position x, y.
        position_x = pdf_w - width_image - 20
        position_y = pdf_w - df_height

        return position_x, position_y

    def get_pid_object(pid_value):
        pid_object = PersistentIdentifier.get('recid', pid_value)
        pv = PIDVersioning(child=pid_object)
        latest_pid = PIDVersioning(parent=pv.parent, child=pid_object).get_children(
            pid_status=PIDStatus.REGISTERED).filter(
            PIDRelation.relation_type == 2).order_by(
            PIDRelation.index.desc()).first()
        cur_pid = pid_object if '.' in pid_value else latest_pid

        return cur_pid

    def get_current_activity_id(pid_object):
        activity = WorkActivity()
        latest_workflow = activity.get_workflow_activity_by_item_id(
            pid_object.object_uuid)
        activity_id = latest_workflow.activity_id if latest_workflow else ''

        return activity_id

    def get_url(pid_value):
        wr = WekoRecord.get_record_by_pid(pid_value)
        model = wr.model
        permalink = get_record_permalink(wr)
        url = ''

        if not permalink:
            sid = 'system_identifier_doi'
            avm = 'attribute_value_mlt'
            ssi = 'subitem_systemidt_identifier'
            if wr.get(sid) and wr.get(sid).get(avm)[0]:
                url = wr[sid][avm][0][ssi]
            else:
                url = request.host_url + 'records/' + pid_value
        else:
            url = permalink

        return url

    def get_oa_policy(activity_id):
        waj = get_workflow_journal(activity_id)
        oa_policy = waj.get('keywords', '')

        return oa_policy
    
    from weko_search_ui.utils import get_data_by_property
    from weko_items_ui.utils import get_options_and_order_list, get_hide_list_by_schema_form
    from weko_records.utils import selected_value_by_language

    from .views import blueprint
    file_path = blueprint.root_path + current_app.config['PDF_COVERPAGE_LANG_FILEPATH']
    file_name = current_app.config['PDF_COVERPAGE_LANG_FILENAME']
    cur_lang = current_i18n.language
    lang_file_path = file_path + cur_lang + file_name

    pid_object = get_pid_object(pid.pid_value)
    item_metadata_json = ItemsMetadata.get_record(pid_object.object_uuid)
    wekoRecord = WekoRecord.get_record_by_pid(pid.pid_value)
    item_type_metadata = ItemsMetadata.get_by_object_id(pid_object.object_uuid)
    item_type_id = item_type_metadata.item_type_id

    item_type = ItemTypes.get_by_id(item_type_id)
    hide_list = []
    if item_type:
        meta_options = get_options_and_order_list(
            item_type_id,
            item_type_data=ItemTypes(item_type.schema, model=item_type),
            mapping_flag=False)
        hide_list = get_hide_list_by_schema_form(schemaform=item_type.render.get('table_row_map', {}).get('form', []))
    else:
        meta_options = get_options_and_order_list(item_type_id, mapping_flag=False)
    item_map = get_mapping(item_type_id, 'jpcoar_mapping', item_type=item_type)

    try:
        with open(lang_file_path) as json_datafile:
            lang_data = json.loads(json_datafile.read())
    except FileNotFoundError:
        lang_file_path = file_path + 'en' + file_name
        with open(lang_file_path) as json_datafile:
            lang_data = json.loads(json_datafile.read())

    # Initialize Instance
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_margins(20.0, 20.0)
    pdf.set_fill_color(100, 149, 237)
    pdf.add_font(
        'IPAexg',
        '',
        blueprint.root_path + current_app.config["JPAEXG_TTF_FILEPATH"],
        uni=True)
    pdf.add_font(
        'IPAexm',
        '',
        blueprint.root_path + current_app.config["JPAEXM_TTF_FILEPATH"],
        uni=True)

    # Parameters such as width and height of rows/columns
    w1 = 40  # width of the left column
    w2 = 130  # width of the right column
    footer_w = 90  # width of the footer cell
    # url_oapolicy_h = 7  # height of the URL & OA-policy
    # height of the URL & OA-policy
    url_oapolicy_h = current_app.config['URL_OA_POLICY_HEIGHT']
    # title_h = 8  # height of the title
    title_h = current_app.config['TITLE_HEIGHT']  # height of the title
    # header_h = 20  # height of the header cell
    header_h = current_app.config['HEADER_HEIGHT']  # height of the header cell
    # footer_h = 4  # height of the footer cell
    footer_h = current_app.config['FOOTER_HEIGHT']  # height of the footer cell
    # meta_h = 9  # height of the metadata cell
    # height of the metadata cell
    meta_h = current_app.config['METADATA_HEIGHT']
    max_letters_num = 51  # number of maximum letters that can be contained \
    # in the right column
    cc_logo_xposition = 160  # x-position of Creative Commons logos

    # Get the header settings
    record = PDFCoverPageSettings.find(1)
    header_display_type = record.header_display_type
    header_output_string = record.header_output_string
    header_output_image_name = record.header_output_image
    header_display_position = record.header_display_position

    # Set the header position
    positions = {}

    if header_display_position == 'left':
        positions['str_position'] = 'L'
        positions['img_position'] = 20
    elif (
        header_display_position == 'center'
        or header_display_position is None
    ):
        positions['str_position'] = 'C'
        x = 0
        if header_output_image_name:
            x, __ = get_center_position(header_output_image_name)
        positions['img_position'] = x
    elif header_display_position == 'right':
        positions['str_position'] = 'R'
        x = 0
        if header_output_image_name:
            x, __ = get_right_position(header_output_image_name)
        positions['img_position'] = x

    # Show header(string or image)
    if header_display_type == 'string':
        pdf.set_font('IPAexm', '', 22)
        pdf.multi_cell(
            w1 + w2,
            header_h,
            header_output_string,
            0,
            positions['str_position'],
            False)
    elif header_output_image_name:
        pdf.image(
            header_output_image_name,
            x=positions['img_position'],
            y=None,
            w=0,
            h=df_height,
            type='')
        pdf.set_y(55)

    # Metadata
    fg = WekoFeedGenerator()
    fe = fg.add_entry()

    # get item key of file
    _file = 'file.URI.@value'
    _file_item_id = None
    if _file in item_map:
        _file_item_id = item_map[_file].split('.')[0]
        _file_item_id = _file_item_id.replace('fileinfo', 'files')

    # get title info
    title_attr_lang = 'title.@attributes.xml:lang'
    title_value = 'title.@value'
    title = item_metadata_json.get('item_title')
    if title_value in item_map:
        # get language
        title_languages, _title_key = get_data_by_property(
            wekoRecord, item_map, title_attr_lang)
        # get value
        title_values, _title_key1 = get_data_by_property(
            wekoRecord, item_map, title_value)
        title = selected_value_by_language(
            title_languages,
            title_values,
            _title_key,
            _title_key1,
            cur_lang,
            wekoRecord,
            meta_options,
            hide_list)

    # Title settings
    pdf.set_font('IPAexm', '', 20)
    pdf.multi_cell(w1 + w2, title_h, title, 0, 'L', False)
    pdf.ln(h='15')

    #pdf.set_font('Arial', '', 14)
    pdf.set_font('IPAexg', '', 14)

    try:
        lang_field = item_map['language.@value'].split('.')
        language = []
        if isinstance(item_metadata_json[lang_field[0]], dict):
            lang_str = item_metadata_json[lang_field[0]][lang_field[1]]
            language.append(LANG_CONVERT.get(lang_str, lang_str))
        elif isinstance(item_metadata_json[lang_field[0]], list):
            for lang_metadata in item_metadata_json[lang_field[0]]:
                lang_str = lang_metadata[lang_field[1]]
                language.append(LANG_CONVERT.get(lang_str, lang_str))
        item_metadata_json['lang'] = language
    except BaseException:
        item_metadata_json['lang'] = [item_metadata_json['lang']] if 'lang' in item_metadata_json else []

    try:
        lang = item_metadata_json.get('lang')
    except (KeyError, IndexError):
        lang = []

    # get publisher info
    publisher_attr_lang = 'publisher.@attributes.xml:lang'
    publisher_value = 'publisher.@value'
    publisher = []
    try:
        for i in item_map[publisher_value].split(','):
            value_key_list = i.split('.')
            publisher_item_id = value_key_list[0]
            prop_hidden = meta_options.get(publisher_item_id, {}).get('option', {}).get('hidden', False)
            for h in hide_list:
                if h.startswith(publisher_item_id) and h.endswith(value_key_list[-1]):
                    prop_hidden = True
            if prop_hidden:
                continue
            for j in item_map[publisher_attr_lang].split(','):
                lang_key_list = j.split('.')
                if publisher_item_id == lang_key_list[0]:
                    publisher_lang_ids = lang_key_list[1:]
                    publisher_text_ids = value_key_list[1:]
                    publishers = item_metadata_json[publisher_item_id]
                    pair_name_language_publisher = get_pair_value(publisher_text_ids,
                                                                  publisher_lang_ids,
                                                                  publishers)
                    multi_lang_value = []
                    for publisher_name, publisher_lang in pair_name_language_publisher:
                        if not publisher_lang:
                            publisher_lang = 'None Language'
                        multi_lang_value.append((publisher_lang, publisher_name))
                    values = get_values_by_selected_lang(multi_lang_value, cur_lang)
                    if values:
                        publisher+=values
    except (KeyError, IndexError):
        publisher = []

    # get pub date info
    try:
        pubdate = item_metadata_json.get('pubdate')
    except (KeyError, IndexError):
        pubdate = None

    # get keyword info
    keyword_attr_lang = 'subject.@attributes.xml:lang'
    keyword_attr_value = 'subject.@value'
    keywords = []
    try:
        for i in item_map[keyword_attr_value].split(','):
            value_key_list = i.split('.')
            keyword_item_id = value_key_list[0]
            prop_hidden = meta_options.get(keyword_item_id, {}).get('option', {}).get('hidden', False)
            for h in hide_list:
                if h.startswith(keyword_item_id) and h.endswith(value_key_list[-1]):
                    prop_hidden = True
            if prop_hidden:
                continue
            for j in item_map[keyword_attr_lang].split(','):
                lang_key_list = j.split('.')
                if keyword_item_id == lang_key_list[0]:
                    keyword_item_langs = lang_key_list[1:]
                    keyword_item_values = value_key_list[1:]
                    keyword_base = item_metadata_json.get(keyword_item_id)
                    pair_name_language_keyword = get_pair_value(keyword_item_values,
                                                                keyword_item_langs,
                                                                keyword_base)
                    multi_lang_value = []
                    for name, keyword_lang in pair_name_language_keyword:
                        if not keyword_lang:
                            keyword_lang = 'None Language'
                        multi_lang_value.append((keyword_lang, name))
                    values = get_values_by_selected_lang(multi_lang_value, cur_lang)
                    if values:
                        keywords+=values
    except (KeyError, IndexError):
        keywords = []

    # get creator info
    _creator = 'creator.creatorName.@value'
    creator_items = []
    if _creator in item_map:
        for k in item_map[_creator].split(','):
            hide_email = False
            hide_name = False
            hide_affiliation = False
            value_key_list = k.split('.')
            _creator_item_id = value_key_list[0]
            prop_hidden = meta_options.get(_creator_item_id, {}).get('option', {}).get('hidden', False)
            for h in hide_list:
                if h.startswith(_creator_item_id) and 'creatorMails' in h:
                    hide_email = True
                elif h.startswith(_creator_item_id) and h.endswith('creatorName'):
                    hide_name = True
                elif h.startswith(_creator_item_id) and 'creatorAffiliations' in h and h.endswith('affiliationName'):
                    hide_affiliation = True
            if prop_hidden:
                continue
            _items_list = item_metadata_json.get(_creator_item_id, [])
            if isinstance(_items_list, dict):
                creator_items += [_items_list]
            elif isinstance(_items_list, list):
                creator_items += _items_list
            for creator_item in creator_items:
                if hide_email and 'creatorMails' in creator_item:
                    creator_item.pop('creatorMails')
                if hide_name and 'creatorNames' in creator_item:
                    creator_item.pop('creatorNames')
                if hide_affiliation and 'creatorAffiliations' in creator_item:
                    creator_item.pop('creatorAffiliations')

    creator_mail_list = []
    creator_name_list = []
    creator_affiliation_list = []

    for creator_item in creator_items:
        # Get creator mail
        if item_setting_show_email():
            creator_mails = creator_item.get('creatorMails', [])

            for creator_mail in creator_mails:
                mail = creator_mail.get('creatorMail', '')
                creator_mail_list.append(mail)

        # Get creator name
        creator_names = creator_item.get('creatorNames', [])
        creator_names_multi_lang = {}
        for creator_name in creator_names:
            name = creator_name.get('creatorName', '')
            name_lang = creator_name.get('creatorNameLang', 'None Language')
            creator_names_multi_lang[name_lang] = name
        creator_name = get_value_by_selected_lang(
            creator_names_multi_lang, cur_lang)
        if creator_name:
            creator_name_list.append(creator_name)

        # Get creator affiliation
        creator_affiliations = creator_item.get('creatorAffiliations', [])
        for creator_affiliation in creator_affiliations:
            affiliations_multi_lang = {}
            affiliation_names = creator_affiliation.get('affiliationNames', [])
            for affiliation_name in affiliation_names:
                name = affiliation_name.get('affiliationName', '')
                name_lang = affiliation_name.get(
                    'affiliationNameLang', 'None Language')
                affiliations_multi_lang[name_lang] = name
            affiliation_name = get_value_by_selected_lang(
                affiliations_multi_lang, cur_lang)
            if affiliation_name:
                creator_affiliation_list.append(affiliation_name)

    seperator = ', '
    metadata_dict = {
        "lang": seperator.join(lang),
        "publisher": seperator.join(publisher),
        "pubdate": pubdate,
        "keywords": seperator.join(keywords),
        "creator_mail": seperator.join(creator_mail_list),
        "creator_name": seperator.join(creator_name_list),
        "affiliation": seperator.join(creator_affiliation_list)
    }

    # Change the values from None to '' for printing
    for key in metadata_dict:
        if metadata_dict[key] is None:
            metadata_dict[key] = ''

    metadata_list = [
        "{}: {}".format(lang_data["Metadata"]["LANG"], metadata_dict["lang"]),
        "{}: {}".format(
            lang_data["Metadata"]["PUBLISHER"],
            metadata_dict["publisher"]),
        "{}: {}".format(
            lang_data["Metadata"]["PUBLICDATE"],
            metadata_dict["pubdate"]),
        "{}: {}".format(
            lang_data["Metadata"]["KEY"],
            metadata_dict["keywords"]),
        "{}: {}".format(
            lang_data["Metadata"]["AUTHOR"],
            metadata_dict["creator_name"]),
        "{}: {}".format(
            lang_data["Metadata"]["EMAIL"],
            metadata_dict["creator_mail"]),
        "{}: {}".format(
            lang_data["Metadata"]["AFFILIATED"],
            metadata_dict["affiliation"])
    ]
    metadata = '\n'.join(metadata_list)

    # Get url
    url = get_url(pid.pid_value)

    # Calculate x position of next cell
    offset = pdf.x + w1

    # Save top coordinate
    top = pdf.y
    # Reset y coordinate
    pdf.y = top
    # Move to computed offset
    pdf.x = offset
    pdf.multi_cell(w2, meta_h, metadata, 1, 'L', False)
    # Get height w2 and calculate line number of metadata
    metadata_lfnum = 0
    height = pdf.y - top
    if height > 0:
        metadata_lfnum = int(height / meta_h)
    # Reset y coordinate
    pdf.y = top
    pdf.multi_cell(w1,
                   meta_h,
                   lang_data["Title"]["METADATA"] + '\n' * metadata_lfnum,
                   1,
                   'C',
                   True)

    # Save top coordinate
    top = pdf.y
    # Reset y coordinate
    pdf.y = top
    # Move to computed offset
    pdf.x = offset
    pdf.multi_cell(w2, url_oapolicy_h, url, 1, 'L', False)
    # Get height w2 and calculate line number of url
    url_lfnum = 0
    height = pdf.y - top
    if height > 0:
        url_lfnum = int(height / url_oapolicy_h)
    # Reset y coordinate
    pdf.y = top
    pdf.multi_cell(w1,
                   url_oapolicy_h,
                   lang_data["Title"]["URL"] + '\n' * url_lfnum,
                   1,
                   'C',
                   True)

    # Footer
    pdf.set_font('IPAexm', '', 10)
    pdf.set_x(108)

    try:
        license = item_metadata_json[_file_item_id][0].get('licensetype')
    except (KeyError, IndexError, TypeError):
        license = None

    list_license_dict = current_app.config['WEKO_RECORDS_UI_LICENSE_DICT']

    for item in list_license_dict:
        if item['value'] == license:
            get_license_pdf(license, item_metadata_json, pdf, _file_item_id,
                            footer_w, footer_h, cc_logo_xposition, item)
            break
    else:
        pdf.multi_cell(footer_w, footer_h, '', 0, 'L', False)

    # Convert PDF cover page data as bytecode
    output = pdf.output(dest='S').encode('latin-1')
    b_output = io.BytesIO(output)

    # Combine cover page and existing pages
    cover_page = PdfReader(b_output, strict=False)
    f = obj.file.storage().open()
    existing_pages = PdfReader(f)

    # In the case the PDF file is encrypted by the password, ''(i.e. not
    # encrypted intentionally)
    if existing_pages.is_encrypted:

        try:
            existing_pages.decrypt('')
        except BaseException:  # Errors such as NotImplementedError
            return ObjectResource.send_object(
                obj.bucket, obj,
                expected_chksum=fileobj.get('checksum'),
                logger_data={
                    'bucket_id': obj.bucket_id,
                    'pid_type': pid.pid_type,
                    'pid_value': pid.pid_value,
                },
                as_attachment=False
            )

    # In the case the PDF file is encrypted by the password except ''
    if existing_pages.is_encrypted:
        return ObjectResource.send_object(
            obj.bucket, obj,
            expected_chksum=fileobj.get('checksum'),
            logger_data={
                'bucket_id': obj.bucket_id,
                'pid_type': pid.pid_type,
                'pid_value': pid.pid_value,
            },
            as_attachment=False
        )

    combined_pages = PdfWriter()
    combined_pages.add_page(cover_page.pages[0])

    for page_num in range(len(existing_pages.pages)):
        existing_page = existing_pages.pages[page_num]
        combined_pages.add_page(existing_page)

    # Download the newly generated combined PDF file
    try:
        download_filename = 'CV_' + fileobj['filename']
    except (KeyError, IndexError):
        download_filename = 'CV_' + title + '.pdf'

    dir_path = tempfile.gettempdir() + '/comb_pdfs/'

    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

    combined_filepath = dir_path + 'CV_{}_{}.pdf'.format(
        datetime.now().strftime('%Y%m%d'), fileobj.file_id)

    with open(combined_filepath, 'wb') as f:
        try:
            combined_pages.write(f)
        except FileNotFoundError as ex:
            current_app.logger.error(ex)
            err_txt = ''.join((
                _('The storage path is incorrect.'),
                '{' + dir_path + '} ',
                _('Please contact the administrator.')
            ))
            flash(err_txt, category='error')
            return redirect(
                current_app.config['RECORDS_UI_ENDPOINTS']['recid']['route'].replace(
                    '<pid_value>', pid.pid_value
                )
            )
        except PermissionError as ex:
            current_app.logger.error(ex)
            err_txt = ''.join((
                _('The storage location cannot be accessed.'),
                '{' + dir_path + '} ',
                _('Please contact the administrator.')
            ))
            flash(err_txt, category='error')
            return redirect(
                current_app.config['RECORDS_UI_ENDPOINTS']['recid']['route'].replace(
                    '<pid_value>', pid.pid_value
                )
            )
        except OSError as ex:
            if ex.errno == errno.ENOSPC:
                current_app.logger.error(ex)
                err_txt = ''.join((
                    _('There is not enough storage space.'),
                    _('Please contact the administrator.')
                ))
                flash(err_txt, category='error')
                return redirect(
                    current_app.config['RECORDS_UI_ENDPOINTS']['recid']['route'].replace(
                        '<pid_value>', pid.pid_value
                    )
                )
        except Exception as ex:
            import traceback
            current_app.logger.error(traceback.print_exc())
            current_app.logger.error(ex)

            return redirect(
                current_app.config['RECORDS_UI_ENDPOINTS']['recid']['route'].replace(
                    '<pid_value>', pid.pid_value
                )
            )

    return send_file(
        combined_filepath,
        as_attachment=True,
        attachment_filename=download_filename,
        mimetype='application/pdf',
        cache_timeout=-1
    )
