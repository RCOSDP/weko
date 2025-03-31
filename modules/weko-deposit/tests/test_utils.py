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

from weko_deposit.api import WekoDeposit
from weko_deposit.utils import update_pdf_contents_es

from mock import patch
import uuid
from tests.helpers import create_record_with_pdf


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_utils.py::test_update_pdf_contents_es -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_pdf_contents_es(app, db, location, mocker):
    record_ids = []
    pdf_file_infos = []
    for i in range(1,4):
        rec_uuid = uuid.uuid4()
        pdf_files, deposit = create_record_with_pdf(rec_uuid, i)
        record_ids.append(rec_uuid)
        file_info = {}
        for file_name, file_obj in pdf_files.items():
            file_info[file_name] = {"uri":file_obj.obj.file.uri,"size":file_obj.obj.file.size}

        pdf_file_infos.append(file_info)
    with patch("weko_deposit.utils.extract_pdf_and_update_file_contents.apply_async") as mock_task:
        update_pdf_contents_es(record_ids)
        args_list = mock_task.call_args_list
        i = 0
        for args, _ in args_list:
            test = pdf_file_infos[i]
            assert args[0] == (test,str(record_ids[i]))
            i+=1