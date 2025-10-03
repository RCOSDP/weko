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

"""Module tests."""

import pytest
import uuid
import os
from tests.helpers import json_data, create_record_with_pdf
from mock import patch, MagicMock
from weko_authors.models import AuthorsAffiliationSettings,AuthorsPrefixSettings
from weko_deposit.api import WekoIndexer
from weko_deposit.tasks import update_items_by_authorInfo, extract_pdf_and_update_file_contents, update_file_content

[
    {
        "recid": "1",
        "year": 1985,
        "stars": 4,
        "title": ["test_item1"],
        "item_title": "test_item1",
        "_deposit": {
            "id": "3",
            "pid": { "type": "depid", "value": "3", "revision_id": 0 },
            "owner": "1",
            "owners": [1],
            "status": "published",
            "created_by": 1,
            "owners_ext": {
                "email": "wekosoftware@nii.ac.jp",
                "username": "",
                "displayname": ""
            }
        }
    },
]
class MockRecordsSearch:
    class MockQuery:
        class MockExecute:
            def __init__(self):
                pass
            def to_dict(self):
                record_hit={'hits': {'hits': json_data('data/record_hit1.json'), 'total': 2}}
                return record_hit
        def __init__(self):
            pass
        def execute(self):
            return self.MockExecute()
    def __init__(self, index=None):
        pass
    
    def update_from_dict(self,query=None):
        return self.MockQuery()

class MockRecordIndexer:
    def bulk_index(self, query):
        pass

    def process_bulk_queue(self, es_bulk_kwargs):
        pass

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_update_authorInfo -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_authorInfo(app, db, records,mocker):
    app.config.update(WEKO_SEARCH_MAX_RESULT=1)
    mocker.patch("weko_deposit.tasks.WekoDeposit.update_author_link")
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], {})
    _target = {
        'authorNameInfo': [
            {'nameShowFlg': False}
        ],
        'authorIdInfo': [
            {'authorIdShowFlg': False}
        ],
        'affiliationInfo': [
        ],
        'emailInfo': []
    }
    
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], _target)

    weko = AuthorsPrefixSettings(
        id=1,
        name="WEKO",
        scheme="WEKO"
    )
    orcid = AuthorsPrefixSettings(
        id=2,
        name="ORCID",
        scheme="ORCID",
        url="https://orcid.org/##"
    )
    cinii = AuthorsPrefixSettings(
        id=3,
        name="CiNii",
        scheme="CiNii",
        url="https://ci.nii.ac.jp/author/"
    )
    db.session.add(weko)
    db.session.add(orcid)
    db.session.add(cinii)
    isni = AuthorsAffiliationSettings(
        id=1,
        name="ISNI",
        scheme="ISNI",
        url="http://www.isni.org/isni/##"
    )
    grid = AuthorsAffiliationSettings(
        id=2,
        name="GRID",
        scheme="GRID",
        url="https://www.grid.ac/institutes/"
    )
    ringgold = AuthorsAffiliationSettings(
        id=3,
        name="Ringgold",
        scheme="Ringgold",
    )
    db.session.add(isni)
    db.session.add(grid)
    db.session.add(ringgold)
    db.session.commit()
    

    _target = {
        'authorNameInfo': [
            {"nameShowFlg":False},
            {
                'nameShowFlg': True,
                'familyName': 'Test Fname',
                'language': 'en',
                'firstName': 'Test Gname'
            }
        ],
        'authorIdInfo': [
            {"authorIdShowFlg":False},
            {
                'authorIdShowFlg': True,
                'idType': '', # not prefix_info
                'authorId':'1'
            },
            {
                "authorIdShowFlg":True,
                "idType":"1", # prefix_info[url] is none
                'authorId':'2'
            },
            {
                "authorIdShowFlg":True,
                "idType":"2", # prefix_info[url] contain ##
                'authorId':'3'
            },
            {
                "authorIdShowFlg":True,
                "idType":"3", # prefix_info[url] not contain ##
                'authorId':'4'
            }
        ],
        'affiliationInfo': [
            {
                'identifierInfo': [
                    {'identifierShowFlg': False},
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"",
                        "affiliationId":"aaa"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"1", # url contain ##
                        "affiliationId":"bbb"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"2", # url not contain ##
                        "affiliationId":"ccc"
                    },
                    {
                        "identifierShowFlg":True,
                        "affiliationIdType":"3", # not url
                        "affiliationId":"ddd"
                    }
                ],
                'affiliationNameInfo': [
                    {"affiliationNameShowFlg":False},
                    {
                        'affiliationNameShowFlg': True,
                        'affiliationName': 'A01',
                        'affiliationNameLang': 'en'
                    }
                ]
            }
        ],
        'emailInfo': [
            {
                'email': 'test@nii.ac.jp'
            }
        ]
    }
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch("weko_deposit.tasks.RecordsSearch", mock_recordssearch):
        with patch("weko_deposit.tasks.RecordIndexer", MockRecordIndexer):
            update_items_by_authorInfo(["1","xxx"], _target)

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_extract_pdf_and_update_file_contents -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_extract_pdf_and_update_file_contents(app, db, location, caplog):
    indexer = WekoIndexer()
    indexer.get_es_index()

    app.config["WEKO_DEPOSIT_FILESIZE_LIMIT"] = 100 * 1024 # 1KB
    rec_uuid = uuid.uuid4()
    pdf_files, deposit = create_record_with_pdf(rec_uuid,1)
    mock_pdf_msg = "This is test pdf"
    mock_tika_msg = "this is test word"
    test_data = {}
    num_pdf = 0
    num_not_pdf = 0
    test_file_data = {}
    
    # Create the number of pdf files to analyze, the number of tika files, 
    # and the value to be passed to the method to update es
    for filename, info in pdf_files.items():
        file = info.get("file")
        if file.obj.mimetype == 'application/pdf':
            
            is_pdf = True
            if filename == "not_exist.pdf":
                test_file_data[filename] = ""
            else:
                test_file_data[filename] = mock_pdf_msg
                num_pdf += 1
        else:
            num_not_pdf += 1
            is_pdf = False
            test_file_data[filename] = mock_tika_msg
        test_data[filename] = {
            "uri":file.obj.file.uri,
            "size":file.obj.file.size,
            "is_pdf": is_pdf
        }
        
    with patch("weko_deposit.utils.extract_text_from_pdf", return_value=mock_pdf_msg) as mock_pdf, \
        patch("weko_deposit.utils.extract_text_with_tika", return_value=mock_tika_msg) as mock_tika:
        with patch("weko_deposit.tasks.update_file_content") as mock_update:
            extract_pdf_and_update_file_contents(test_data, deposit.id)
            assert mock_pdf.call_count == num_pdf
            assert mock_tika.call_count == num_not_pdf
            mock_update.assert_called_with(rec_uuid,test_file_data)
            
            # Check if temporary files have been deleted
            for call in mock_pdf.call_args_list:
                args, _ = call
                filepath = args[0]
                assert os.path.exists(filepath) == False

            for call in mock_tika.call_args_list:
                args, _ = call
                filepath = args[0]
                assert os.path.exists(filepath) == False
                
            assert "Resource not found: b'not_exist_dir1'" in caplog.text
            caplog.clear()
            
            from fs.errors import ResourceNotFoundError
            # error in extract_text_from_pdf
            # Check if temporary files have been deleted
            with patch("weko_deposit.utils.extract_text_from_pdf", side_effect=FileNotFoundError("test exception")) as mock_pdf,\
                    patch("weko_deposit.utils.extract_text_with_tika", side_effect=ResourceNotFoundError("test_exception")) as mock_tika:
                extract_pdf_and_update_file_contents(test_data, deposit.id)
                assert mock_pdf.call_count == num_pdf
                assert "test exception" in caplog.text
                caplog.clear()
                
                for call in mock_pdf.call_args_list:
                    args, _ = call
                    filepath = args[0]
                    assert os.path.exists(filepath) == False

                for call in mock_tika.call_args_list:
                    args, _ = call
                    filepath = args[0]
                    assert os.path.exists(filepath) == False

        from elasticsearch.exceptions import NotFoundError, ConflictError
        # raise ConflictError in update_file_content
        with patch("weko_deposit.tasks.update_file_content", side_effect=ConflictError()) as mock_update:
            extract_pdf_and_update_file_contents(test_data, deposit.id)
            assert mock_update.call_count == 3 # retry 3 times
            assert f"Failed to update file content after 3 attempts. record_uuid: {rec_uuid}" in caplog.text
            caplog.clear()
        # raise ConflictError in update_file_content
        with patch("weko_deposit.tasks.update_file_content", side_effect=NotFoundError()) as mock_update:
            extract_pdf_and_update_file_contents(test_data, deposit.id)
            assert mock_update.call_count == 3 # retry 3 times
            assert f"Failed to update file content after 3 attempts. record_uuid: {rec_uuid}" in caplog.text
            caplog.clear()
            

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_tasks.py::test_update_file_content -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_update_file_content(app, db, location):
    indexer = WekoIndexer()
    indexer.get_es_index()
    rec_uuid = uuid.uuid4()
    pdf_files, deposit = create_record_with_pdf(rec_uuid,1)

    file_datas = {}
    for filename, data in pdf_files.items():
        file_datas[filename] = f"this is {filename}"

    update_file_content(rec_uuid,file_datas)

    result = indexer.client.get(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        doc_type="item-v1.0.0",
        id=deposit.id
    )
    attachments = [r["attachment"] for r in result["_source"]["content"]]
    test = [
        {"content":"this is test_file_1.2M.pdf"},
        {"content":"this is test_file_82K.pdf"},
        {},
        {"content":"this is not_exist.pdf"},
    ]
    assert attachments == test