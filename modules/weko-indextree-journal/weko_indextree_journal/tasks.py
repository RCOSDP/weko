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

import os
from celery import shared_task
from celery.utils.log import get_task_logger
from flask import current_app, Blueprint
from .api import Journals

logger = get_task_logger(__name__)

blueprint = Blueprint(
    'weko_index_tree',
    __name__,
    template_folder='templates',
    static_folder='static',
)

print("[Log]: Register journal tasks.")
@shared_task(ignore_result=True)
def export_journal_task(p_path):
    """
    Output the file name of KBART2 extended format included
    last update date to the file "Own institution repository URL" ＋「/weko/kbart/filelist.txt」
    Output journal info with KBART2 extended format by tsv format to 
    "Own institution repository URL" ＋「/weko/kbart/{Repository name}_Global_AllTitles_{Last update date}.txt
    export journal information to file.
    :param p_path:
    """
    try:
        # Get file name of journal info with KBART2 format.
        # Own institution repository URL" ＋「/weko/kbart/{Repository name}_Global_AllTitles_{Last update date}.txt
        kbart_folder = 'weko/kbart'
        filelist_path = os.path.join(
            current_app.static_folder, kbart_folder, "filelist.txt")

        # UtokyoRepository_Global_AllTitles_2018-12-12.txt
        # {0}: {Repository name}, {1}: {Last update date}
        repository_name = current_app.config['OAISERVER_REPOSITORY_NAME']
        current_date = datetime.datetime.today().strftime('%Y-%m-%d')

        repository_filename = "{0}_AllTitles_{1}.txt".format(repository_name, current_date)

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
            "jstage_code",
            "ichushi_code",
            "deleted"
        ]

        header_string = "\t".join(header)

        # Get journal data.
        journals = Journals.get_all_journals()
        journals_list = []
        if journals is not None:
            journals_list = list(journals)
        data = numpy.asarray(journals_list)

        # create folder if not exist
        directory = os.path.join(
            current_app.static_folder, kbart_folder)
        if not os.path.exists(directory):
            os.makedirs(directory)

        numpy.savetxt(repository_data_path, journals_list, delimiter="\t", header=header_string)
        numpy.savetxt(filelist_path, [repository_filename])
        # jsonList = json.dumps({"results" : results})
        # Save journals information to file
    except Exception as ex:
        current_app.logger.error(ex)

    return {}