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

import traceback
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
from .tasks import (extract_pdf_and_update_file_contents,
                    extract_pdf_and_update_file_contents_with_index_api)
from .api import WekoDeposit

def update_pdf_contents_es(record_ids):
    """register the contents of the record PDF file in elasticsearch
    Args:
        record_ids (list): List of record uuids
    """
    deposits = WekoDeposit.get_records(record_ids)
    for dep in deposits:
        file_infos = dep.get_pdf_info()
        extract_pdf_and_update_file_contents.apply_async((file_infos, str(dep.id)))


def update_pdf_contents_es_with_index_api(record_ids):
    """register the contents of the record PDF file in elasticsearch
    Args:
        record_ids (list): List of record uuids
    """
    deposits = WekoDeposit.get_records(record_ids)
    for dep in deposits:
        try:
            file_infos = dep.get_pdf_info()
            extract_pdf_and_update_file_contents_with_index_api.apply_async((
                file_infos, str(dep.id)))
        except NoResultFound:
            current_app.logger.error(f"Record with UUID: {dep.id} was not found in the item_metadata table.")
            traceback.print_exc()
