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

"""Weko Journal celery tasks."""

import datetime
import os

import numpy
from celery import shared_task
from flask import Blueprint, current_app

from .api import Journals
from .models import Journal_export_processing

blueprint = Blueprint(
    'weko_index_tree',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@shared_task(ignore_result=True)
def export_journal_task(p_path):
    """
    Output the file name of KBART2 extended format.

    included last update date to the file "Own institution repository URL"
    + "/weko/kbart/filelist.txt"
    Output journal info with KBART2 extended format by tsv format to
    "Own institution repository URL" +
    "/weko/kbart/{Repository name}_Global_AllTitles_{Last update date}.txt"

    export journal information to file.

    :param p_path:
    """
    current_app.logger.debug('Export journal task is running.')
    try:
        # Get processing status to verify whether there is another working task
        db_processing_status = Journal_export_processing.get()

        if db_processing_status is None:
            db_processing_status = Journal_export_processing()
            db_processing_status.status = False

        if db_processing_status.status:
            current_app.logger.error(
                '[{0}] Execution failed due to '
                'multiple execution errors'.format(3)
            )
            return {}
        db_processing_status.status = True
        db_processing_status.save_export_info(db_processing_status)

        # Get file name of journal info with KBART2 format.
        # Own institution repository URL" +  "/weko/kbart/{Repository
        # name}_Global_AllTitles_{Last update date}.txt
        kbart_folder = 'weko/kbart'
        filelist_path = os.path.join(
            current_app.static_folder, kbart_folder, "filelist.txt")

        # UtokyoRepository_Global_AllTitles_2018-12-12.txt
        # {0}: {Repository name}, {1}: {Last update date}
        repository_name = current_app.config['OAISERVER_REPOSITORY_NAME']

        current_date = datetime.datetime.today().strftime('%Y-%m-%d')

        repository_filename = "{0}_AllTitles_{1}.txt".format(
            repository_name, current_date)

        repository_data_path = os.path.join(
            current_app.static_folder, kbart_folder, repository_filename)

        # Build header.
        header = [
            "publication_title",
            "print_identifier",
            "online_identifier",
            "date_first_issue_online",
            "num_first_vol_online",
            "num_first_issue_online",
            "date_last_issue_online",
            "num_last_vol_online",
            "num_last_issue_online",
            "title_url",
            "first_author",
            "title_id",
            "embargo_info",
            "coverage_depth",
            "notes",
            "publisher_name",
            "publication_type",
            "date_monograph_published_print",
            "date_monograph_published_online",
            "monograph_volume",
            "monograph_edition",
            "first_editor",
            "parent_publication_title_id",
            "preceding_publication_title_id",
            "access_type",
            "language",
            "title_alternative",
            "title_transcription",
            "ncid",
            "ndl_callno",
            "ndl_bibid",
            "jstage_code",
            "ichushi_code",
            "deleted"
        ]

        header_string = "\t".join(header)

        # Get journal data.
        journals = Journals.get_all_journals()
        journals_list = []
        if journals is not None:
            for item in journals:
                # get data
                journal_data = []
                journal_data.append(
                    convert_none_to_blank(item.publication_title))
                journal_data.append(
                    convert_none_to_blank(item.print_identifier))
                journal_data.append(
                    convert_none_to_blank(item.online_identifier))
                journal_data.append(
                    convert_none_to_blank(item.date_first_issue_online))
                journal_data.append(
                    convert_none_to_blank(item.num_first_vol_online))
                journal_data.append(
                    convert_none_to_blank(item.num_first_issue_online))
                journal_data.append(
                    convert_none_to_blank(item.date_last_issue_online))
                journal_data.append(
                    convert_none_to_blank(item.num_last_vol_online))
                journal_data.append(
                    convert_none_to_blank(item.num_last_issue_online))
                site_url = current_app.config['THEME_SITEURL'] 
                if not site_url.endswith('/'):
                    site_url = site_url + '/'
                journal_data.append(
                   site_url + convert_none_to_blank(
                        item.title_url))
                journal_data.append(convert_none_to_blank(item.first_author))
                journal_data.append(convert_none_to_blank(item.title_id))
                journal_data.append(convert_none_to_blank(item.embargo_info))
                journal_data.append(convert_none_to_blank(item.coverage_depth))
                journal_data.append(convert_none_to_blank(item.coverage_notes))
                journal_data.append(convert_none_to_blank(item.publisher_name))
                journal_data.append(
                    convert_none_to_blank(item.publication_type))
                journal_data.append(
                    convert_none_to_blank(item.date_monograph_published_print))
                journal_data.append(
                    convert_none_to_blank(item.date_monograph_published_online))
                journal_data.append(
                    convert_none_to_blank(item.monograph_volume))
                journal_data.append(
                    convert_none_to_blank(item.monograph_edition))
                journal_data.append(convert_none_to_blank(item.first_editor))
                journal_data.append(
                    convert_none_to_blank(item.parent_publication_title_id))
                journal_data.append(
                    convert_none_to_blank(item.preceding_publication_title_id))
                journal_data.append(convert_none_to_blank(item.access_type))
                journal_data.append(convert_none_to_blank(item.language))
                journal_data.append(
                    convert_none_to_blank(item.title_alternative))
                journal_data.append(
                    convert_none_to_blank(item.title_transcription))
                journal_data.append(convert_none_to_blank(item.ncid))
                journal_data.append(convert_none_to_blank(item.ndl_callno))
                journal_data.append(convert_none_to_blank(item.ndl_bibid))
                journal_data.append(convert_none_to_blank(item.jstage_code))
                journal_data.append(convert_none_to_blank(item.ichushi_code))
                journal_data.append(convert_none_to_blank(item.deleted))

                # add to list.
                journals_list.append(journal_data)

        data = numpy.asarray(journals_list)

        # create folder if not exist
        directory = os.path.join(
            current_app.static_folder, kbart_folder)

        if not os.path.exists(directory):
            os.makedirs(directory)

        # Save data to file.
        numpy.savetxt(repository_data_path, data, "%s", delimiter="\t",
                      header=header_string, footer='', comments='')

        # save file list
        if os.path.exists(filelist_path):
            os.remove(filelist_path)

        filelist_data = []
        filelist_data.append(repository_filename)
        filelist_data_saved = numpy.asarray(filelist_data)

        numpy.savetxt(filelist_path, filelist_data_saved, "%s", "")

        db_processing_status.status = False
        db_processing_status.save_export_info(db_processing_status)
        return journals_list
        # jsonList = json.dumps({"results" : results})
        # Save journals information to file
    except Exception as ex:
        current_app.logger.error(
            '[{0}] [{1}] End with unknown error. Error:{2}'.format(
                1, 'Export Journal Task', ex)
        )

    db_processing_status.status = False
    db_processing_status.save_export_info(db_processing_status)
    return {}


def convert_none_to_blank(input_value):
    """Convert None to blank.

    :param input_value: input data
    :return: Blank if input value is None.
    """
    if input_value is None:
        return ''
    else:
        return input_value
