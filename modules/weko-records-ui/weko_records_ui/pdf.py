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
import io
import json
import os
import unicodedata
from datetime import datetime

from flask import current_app, send_file
from fpdf import FPDF
from invenio_db import db
from invenio_files_rest.views import ObjectResource
from invenio_pidstore.models import PersistentIdentifier
from PyPDF2 import PdfFileReader, PdfFileWriter, utils
from weko_records.api import ItemMetadata, ItemsMetadata, ItemType, Mapping
from weko_records.serializers.feed import WekoFeedGenerator
from weko_records.serializers.utils import get_mapping, get_metadata_from_map

from .models import PDFCoverPageSettings
from .utils import get_license_pdf, get_pair_value


""" Function counting numbers of full-width character and half-width character\
        differently """


def get_east_asian_width_count(text):
    """Def eat asian width count."""
    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in 'FWA':
            count += 2
        else:
            count += 1
    return count


""" Function making PDF cover page """


def make_combined_pdf(pid, obj_file_uri, fileobj, obj, lang_user):
    """Make the cover-page-combined PDF file.

    :param pid: PID object
    :param file_uri: URI of the file object
    :param lang_user: LANGUAGE of access user
    :return: cover-page-combined PDF file object
    """
    lang_filepath = current_app.config['PDF_COVERPAGE_LANG_FILEPATH']\
        + lang_user + current_app.config['PDF_COVERPAGE_LANG_FILENAME']

    pidObject = PersistentIdentifier.get('recid', pid.pid_value)
    item_metadata_json = ItemsMetadata.get_record(pidObject.object_uuid)
    item_type = ItemsMetadata.get_by_object_id(pidObject.object_uuid)
    item_type_id = item_type.item_type_id
    type_mapping = Mapping.get_record(item_type_id)
    item_map = get_mapping(type_mapping, "jpcoar_mapping")

    with open(lang_filepath) as json_datafile:
        lang_data = json.loads(json_datafile.read())

    # Initialize Instance
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_margins(20.0, 20.0)
    pdf.set_fill_color(100, 149, 237)

    pdf.add_font(
        'IPAexg',
        '',
        current_app.config["JPAEXG_TTF_FILEPATH"],
        uni=True)
    pdf.add_font(
        'IPAexm',
        '',
        current_app.config["JPAEXM_TTF_FILEPATH"],
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
    max_letters_num = 51    # number of maximum letters that can be contained \
    # in the right column
    cc_logo_xposition = 160  # x-position of Creative Commons logos

    # Get the header settings
    record = PDFCoverPageSettings.find(1)
    header_display_type = record.header_display_type
    header_output_string = record.header_output_string
    header_output_image = record.header_output_image
    header_display_position = record.header_display_position

    # Set the header position
    positions = {}
    if header_display_position == 'left':
        positions['str_position'] = 'L'
        positions['img_position'] = 20
    elif header_display_position == 'center' or header_display_position is None:
        positions['str_position'] = 'C'
        positions['img_position'] = 85
    elif header_display_position == 'right':
        positions['str_position'] = 'R'
        positions['img_position'] = 150

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
    else:
        pdf.image(
            header_output_image,
            x=positions['img_position'],
            y=None,
            w=0,
            h=30,
            type='')
        pdf.set_y(55)

    # Title settings
    title = item_metadata_json['title']
    pdf.set_font('IPAexm', '', 20)
    pdf.multi_cell(w1 + w2, title_h, title, 0, 'L', False)
    pdf.ln(h='15')

    # Metadata
    fg = WekoFeedGenerator()
    fe = fg.add_entry()

    _file = 'file.URI.@value'
    _file_item_id = None
    if _file in item_map:
        _file_item_id = item_map[_file].split('.')[0]
        _file_item_id = _file_item_id.replace('fileinfo', 'files')

    _creator = 'creator.creatorName.@value'
    _creator_item_id = None
    if _creator in item_map:
        _creator_item_id = item_map[_creator].split('.')[0]

    publisher_attr_lang = 'publisher.@attributes.xml:lang'
    publisher_value = 'publisher.@value'
    publisher_item_id = None
    publisher_lang_id = None
    publisher_text_id = None

    keyword_attr_lang = 'subject.@attributes.xml:lang'
    keyword_attr_value = 'subject.@value'
    keyword_base = None
    keyword_lang = None

    pdf.set_font('Arial', '', 14)
    pdf.set_font('IPAexg', '', 14)

    if item_metadata_json['lang'] == 'en':
        item_metadata_json['lang'] = 'English'
    elif item_metadata_json['lang'] == 'ja':
        item_metadata_json['lang'] = 'Japanese'
    try:
        lang_field = item_map['language.@value'].split('.')
        if item_metadata_json[lang_field[0]][lang_field[1]] == 'eng':
            item_metadata_json['lang'] = 'English'
        elif item_metadata_json[lang_field[0]][lang_field[1]] == 'jpn':
            item_metadata_json['lang'] = 'Japanese'
    except BaseException:
        pass
    try:
        lang = item_metadata_json.get('lang')
    except (KeyError, IndexError):
        lang = None
    try:
        publisher_item_id = item_map[publisher_attr_lang].split('.')[0]
        publisher_lang_ids = item_map[publisher_attr_lang].split('.')[1:]
        publisher_text_ids = item_map[publisher_value].split('.')[1:]
        publisher = None
        default_publisher = None
        publishers = item_metadata_json[publisher_item_id]
        pair_name_language_publisher = get_pair_value(publisher_text_ids,
                                                      publisher_lang_ids,
                                                      publishers)
        for publisher_name, publisher_lang in pair_name_language_publisher:
            if publisher_lang == lang_user:
                publisher = publisher_name
            if publisher_lang == 'en':
                default_publisher = publisher_name

        if publisher is None:
            publisher = default_publisher
    except (KeyError, IndexError):
        publisher = None
    try:
        pubdate = item_metadata_json.get('pubdate')
    except (KeyError, IndexError):
        pubdate = None
    try:
        keyword_item_id = item_map[keyword_attr_lang].split('.')[0]
        keyword_item_langs = item_map[keyword_attr_lang].split('.')[1:]
        keyword_item_values = item_map[keyword_attr_value].split('.')[1:]
        keyword_base = item_metadata_json.get(keyword_item_id)
        keywords_ja = None
        keywords_en = None

        pair_name_language_keyword = get_pair_value(keyword_item_values,
                                                    keyword_item_langs,
                                                    keyword_base)

        for name, lang in pair_name_language_keyword:
            keyword_lang = lang
            if keyword_lang == 'ja':
                keywords_ja = name
            elif keyword_lang == 'en':
                keywords_en = name

    except (KeyError, IndexError):
        pass
    creator_items = item_metadata_json.get(_creator_item_id)
    if type(creator_items) is dict:
        creator_items = [creator_items]
    creator_mail_list = []
    creator_name_list = []
    creator_affiliation_list = []
    for creator_item in creator_items:
        # Get creator mail
        if creator_item.get('creatorMails'):
            for creator_mail in creator_item.get('creatorMails'):
                if creator_mail.get('creatorMail'):
                    creator_mail_list.append(creator_mail.get('creatorMail'))
        # Get creator name
        default_creator_name_list = []
        if creator_item.get('creatorNames'):
            for creator_name in creator_item.get('creatorNames'):
                if creator_name.get('creatorNameLang') == lang_user:
                    creator_name_list.append(creator_name.get('creatorName'))
                if creator_name.get('creatorNameLang') == 'en':
                    default_creator_name_list.append(creator_name.get(
                        'creatorName'))
        if not creator_name_list and default_creator_name_list:
            creator_name_list = default_creator_name_list
        # Get creator affiliation
        default_creator_affiliation_list = []
        if creator_item.get('affiliation'):
            for creator_affiliation in creator_item.get('affiliation'):
                if creator_affiliation.get('affiliationNameLang') == lang_user:
                    creator_affiliation_list.append(creator_affiliation.get(
                        'affiliationName'))
                if creator_affiliation.get('affiliationNameLang') == 'en':
                    default_creator_affiliation_list.\
                        append(creator_affiliation.get('affiliationName'))
        if not creator_affiliation_list and default_creator_affiliation_list:
            creator_affiliation_list = default_creator_affiliation_list

    seperator = ', '
    metadata_dict = {
        "lang": lang,
        "publisher": publisher,
        "pubdate": pubdate,
        "keywords_ja": keywords_ja,
        "keywords_en": keywords_en,
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
        "{} (Ja): {}".format(
            lang_data["Metadata"]["KEY"],
            metadata_dict["keywords_ja"]),
        "{} (En): {}".format(
            lang_data["Metadata"]["KEY"],
            metadata_dict["keywords_en"]),
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
    metadata_lfnum = int(metadata.count('\n'))
    for item in metadata_list:
        metadata_lfnum += int(get_east_asian_width_count(item)
                              ) // max_letters_num

    url = ''  # will be modified later
    url_lfnum = int(get_east_asian_width_count(url)) // max_letters_num

    oa_policy = ''  # will be modified later
    oa_policy_lfnum = int(
        get_east_asian_width_count(oa_policy)) // max_letters_num

    # Save top coordinate
    top = pdf.y
    # Calculate x position of next cell
    offset = pdf.x + w1
    pdf.multi_cell(w1,
                   meta_h,
                   lang_data["Title"]["METADATA"]
                   + '\n' * (metadata_lfnum + 1),
                   1,
                   'C',
                   True)
    # Reset y coordinate
    pdf.y = top
    # Move to computed offset
    pdf.x = offset
    pdf.multi_cell(w2, meta_h, metadata, 1, 'L', False)
    top = pdf.y
    pdf.multi_cell(w1,
                   url_oapolicy_h,
                   lang_data["Title"]["URL"] + '\n' * (url_lfnum + 1),
                   1,
                   'C',
                   True)
    pdf.y = top
    pdf.x = offset
    pdf.multi_cell(w2, url_oapolicy_h, url, 1, 'L', False)
    top = pdf.y
    pdf.multi_cell(w1,
                   url_oapolicy_h,
                   lang_data["Title"]["OAPOLICY"]
                   + '\n' * (oa_policy_lfnum + 1),
                   1,
                   'C',
                   True)
    pdf.y = top
    pdf.x = offset
    pdf.multi_cell(w2, url_oapolicy_h, oa_policy, 1, 'L', False)
    pdf.ln(h=1)

    # Footer
    pdf.set_font('Courier', '', 10)
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

    """ Convert PDF cover page data as bytecode """
    output = pdf.output(dest='S').encode('latin-1')
    b_output = io.BytesIO(output)

    # Combine cover page and existing pages
    cover_page = PdfFileReader(b_output)
    f = open(obj_file_uri, "rb")
    existing_pages = PdfFileReader(f)

    # In the case the PDF file is encrypted by the password, ''(i.e. not
    # encrypted intentionally)
    if existing_pages.isEncrypted:
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
    if existing_pages.isEncrypted:
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

    combined_pages = PdfFileWriter()
    combined_pages.addPage(cover_page.getPage(0))
    for page_num in range(existing_pages.numPages):
        existing_page = existing_pages.getPage(page_num)
        combined_pages.addPage(existing_page)

    # Download the newly generated combined PDF file
    try:
        combined_filename = 'CV_' + datetime.now().strftime('%Y%m%d') + '_' + \
                            item_metadata_json[_file_item_id][0].get("filename")

    except (KeyError, IndexError):
        combined_filename = 'CV_' + title + '.pdf'
    combined_filepath = "/code/invenio/{}.pdf".format(combined_filename)
    combined_file = open(combined_filepath, "wb")
    combined_pages.write(combined_file)
    combined_file.close()

    return send_file(
        combined_filepath,
        as_attachment=True,
        attachment_filename=combined_filename,
        mimetype='application/pdf',
        cache_timeout=-1)
