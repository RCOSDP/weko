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
from weko_deposit.utils import update_pdf_contents_es, update_pdf_contents_es_with_index_api
from sqlalchemy.orm.exc import NoResultFound
import types
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

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_utils.py::test_update_pdf_contents_es_with_index_api -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_pdf_contents_es_with_index_api(app, mocker):
    record_ids = ['id1', 'id2']
    # Normal case: get_pdf_info and apply_async are called
    class DummyDep:
        def __init__(self, id): self.id = id
        def get_pdf_info(self): return {'file': 'info'}
    dummy_deps = [DummyDep(rid) for rid in record_ids]
    with patch("weko_deposit.utils.WekoDeposit.get_records", return_value=dummy_deps):
        with patch("weko_deposit.utils.extract_pdf_and_update_file_contents_with_index_api.apply_async") as mock_task:
            update_pdf_contents_es_with_index_api(record_ids)
            # apply_async is called for each record
            for i, call in enumerate(mock_task.call_args_list):
                args, _ = call
                assert args[0] == ({'file': 'info'}, record_ids[i])

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_utils.py::test_update_pdf_contents_es_with_index_api_noresult -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_pdf_contents_es_with_index_api_noresult(app, mocker):
    record_ids = ['id1']
    # When NoResultFound occurs: logger.error and traceback.print_exc are called
    class DummyDep:
        def __init__(self, id): self.id = id
        def get_pdf_info(self): raise NoResultFound()
    dummy_logger = types.SimpleNamespace(error=lambda msg: setattr(dummy_logger, 'logged', msg))
    dummy_trace = types.SimpleNamespace(print_exc=lambda: setattr(dummy_trace, 'called', True))
    with patch("weko_deposit.utils.WekoDeposit.get_records", return_value=[DummyDep('id1')]):
        with patch("weko_deposit.utils.current_app", types.SimpleNamespace(logger=dummy_logger)):
            with patch("weko_deposit.utils.traceback", types.SimpleNamespace(print_exc=dummy_trace.print_exc)):
                update_pdf_contents_es_with_index_api(record_ids)
                assert hasattr(dummy_logger, 'logged')
                assert hasattr(dummy_trace, 'called')
