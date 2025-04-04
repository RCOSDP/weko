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
# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

import json
import pytest
import uuid
from flask import url_for
from mock import patch, MagicMock
from elasticsearch.exceptions import NotFoundError
from invenio_indexer.api import RecordIndexer

from invenio_accounts.testutils import login_user_via_session
from invenio_search import current_search_client
from flask import current_app
from weko_authors.models import Authors, AuthorsPrefixSettings, AuthorsAffiliationSettings
from weko_authors.views import dbsession_clean

def assert_role(response,is_permission,status_code=403):
    if is_permission:
        assert response.status_code != status_code
    else:
        assert response.status_code == status_code

class MockIndexer():
    def __init__(self):
        self.client = self.MockClient()

    class MockClient():
        def __init__(self):
            pass

        def search(self, index=None, doc_type=None, body=None):
            return {"hits": {"hits": [{"_source":
                    {"authorNameInfo": "", "authorIdInfo": "", "emailInfo": ""}
                    }]}}

        def index(self, index=None, doc_type=None, body=None):
            return {}

        def get(self, index=None, doc_type=None, id=None, body=None):
            return {"_source": {"authorNameInfo": {},
                                "authorIdInfo": {},
                                "emailInfo": {},
                                "affiliationInfo":{}
                                }
                    }

        def update(self, index=None, doc_type=None, id=None, body=None):
            return {"_source": {"authorNameInfo": "", "authorIdInfo": "",
                                "emailInfo": ""}}


def get_json(response):
    """Get JSON from response."""
    return json.loads(response.get_data(as_text=True))

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_acl_guest(client):
    """
    Test of create author.
    :param client: The flask client.
    """
    url = url_for("weko_authors.create")
    res = client.post(url,content_type='text/plain')
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/add",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_create_acl_users(client, users, index, is_permission):
    url = url_for("weko_authors.create")
    login_user_via_session(client=client, email=users[index]['email'])
    res = client.post(url,content_type='text/plain')
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_author(client, users, mocker):
    """
    Test of create author.
    :param client: The flask client.
    """
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for("weko_authors.create")
    
    # 条件: Content-Typeがapplication/jsonではない場合
    # 入力: Content-Typeがtext/plain
    # 期待結果: ステータスコード200、メッセージ"Header Error"
    res = client.post(url, content_type='text/plain')
    assert res.status_code == 200
    assert get_json(res) == {"msg": "Header Error"}
    
    # 条件: WEKO IDが設定されていない場合
    # 入力: authorIdInfoにidTypeが1のauthorIdが存在しない
    # 期待結果: ステータスコード500、メッセージ"Please set WEKO ID."
    input_data = {
        "authorIdInfo": [{"idType": "2", "authorId": "0123"}]
    }
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Please set WEKO ID."}
    
    # 条件: WEKO IDが半角数字でない場合
    # 入力: authorIdInfoにidTypeが1のauthorIdが半角数字でない
    # 期待結果: ステータスコード500、メッセージ"Please set the WEKOID in the half digit."
    input_data = {
        "authorIdInfo": [{"idType": "1", "authorId": "abc"}]
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(False, "not half digit"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Please set the WEKOID in the half digit."}
    
    # 条件: WEKO IDが既に存在する場合
    # 入力: authorIdInfoにidTypeが1のauthorIdが既に存在する
    # 期待結果: ステータスコード500、メッセージ"The value is already in use as WEKO ID."
    input_data = {
        "authorIdInfo": [{"idType": "1", "authorId": "123"}]
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(False, "already exists"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "The value is already in use as WEKO ID."}
    
    # 条件: affiliation start dateとend dateがyyyy-MM-dd形式でない場合
    # 入力: affiliation start dateとend dateがyyyy-MM-dd形式でない
    # 期待結果: ステータスコード500、メッセージ"Please set the affiliation start date and end date in the format yyyy-MM-dd."
    input_data = {
        "authorIdInfo": [{"idType": "1", "authorId": "123"}],
        "affiliationInfo": [{"startDate": "2021/01/01", "endDate": "2021/12/31"}]
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(True, ""))
    mocker.patch('weko_authors.views.check_period_date', return_value=(False, "not date format"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Please set the affiliation start date and end date in the format yyyy-MM-dd."}
    
    # 条件: affiliation start dateがend dateより後の場合
    # 入力: affiliation start dateがend dateより後
    # 期待結果: ステータスコード500、メッセージ"The end date must be after the start date."
    input_data = {
        "authorIdInfo": [{"idType": "1", "authorId": "123"}],
        "affiliationInfo": [{"startDate": "2022-01-01", "endDate": "2021-12-31"}]
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(True, ""))
    mocker.patch('weko_authors.views.check_period_date', return_value=(False, "start is after end"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "The end date must be after the start date."}
    
    # 条件: 正常な入力
    # 入力: 正常なauthorIdInfoとaffiliationInfo
    # 期待結果: ステータスコード200、メッセージ"Success"
    input_data = {
        "authorIdInfo": [{"idType": "1", "authorId": "123"}],
        "affiliationInfo": [{"startDate": "2021-01-01", "endDate": "2021-12-31"}]
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(True, ""))
    mocker.patch('weko_authors.views.check_period_date', return_value=(True, ""))
    mocker.patch('weko_authors.views.WekoAuthors.create', return_value=None)
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 200
    assert get_json(res) == {"msg": "Success"}
    
    # 条件: WekoAuthors.createで例外が発生する場合
    # 入力: 正常なauthorIdInfoとaffiliationInfo
    # 期待結果: ステータスコード500、メッセージ"Failed"
    input_data = {
        "authorIdInfo": [{"idType": "1", "authorId": "123"}],
        "affiliationInfo": [{"startDate": "2021-01-01", "endDate": "2021-12-31"}]
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(True, ""))
    mocker.patch('weko_authors.views.check_period_date', return_value=(True, ""))
    mocker.patch('weko_authors.views.WekoAuthors.create', side_effect=Exception("test_error"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Failed"}            

    # 条件: validate_weko_idで例外が発生する場合
    # 入力: 正常なauthorIdInfoとaffiliationInfo
    # 期待結果: ステータスコード500、メッセージ"Failed"
    input_data = {
        "authorIdInfo": [{"idType": "1", "authorId": "123"}],
        "affiliationInfo": [{"startDate": "2021-01-01", "endDate": "2021-12-31"}]
    }
    mocker.patch('weko_authors.views.validate_weko_id', side_effect=Exception("test_error"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Failed"} 

    
    
# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_author_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_update_author_acl_guest(client):
    """
    Test of update author data.
    :param client: The flask client.
    """
    url = url_for("weko_authors.update_author")
    res = client.post(url, content_type='plain/text')
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/edit",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_author_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_update_author_acl_users(client, users, index, is_permission):
    url = url_for("weko_authors.update_author")
    login_user_via_session(client=client, email=users[index]['email'])
    res = client.post(url, content_type='plain/text')
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_update_author(client, users, mocker):
    """
    Test of create author.
    :param client: The flask client.
    """
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for("weko_authors.update_author")
    
    # 条件: Content-Typeがapplication/jsonではない場合
    # 入力: Content-Typeがtext/plain
    # 期待結果: ステータスコード200、メッセージ"Header Error"
    res = client.post(url, content_type='text/plain')
    assert res.status_code == 200
    assert get_json(res) == {"msg": "Header Error"}
    
    # 条件: WEKO IDが設定されていない場合
    # 入力: authorIdInfoにidTypeが1のauthorIdが存在しない
    # 期待結果: ステータスコード500、メッセージ"Please set WEKO ID."
    input_data = {
            "forceChangeFlag": "false",
            "author":{
            "pk_id": "1",
            "authorIdInfo": [{"idType": "2", "authorId": "0123"}]
            }
        }
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Please set WEKO ID."}
    
    # 条件: WEKO IDが半角数字でない場合
    # 入力: authorIdInfoにidTypeが1のauthorIdが半角数字でない
    # 期待結果: ステータスコード500、メッセージ"Please set the WEKOID in the half digit."
    input_data = {
        "forceChangeFlag": "false",
        "author":{
        "pk_id": "1",
        "authorIdInfo": [{"idType": "1", "authorId": "abc"}]
        }
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(False, "not half digit"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Please set the WEKOID in the half digit."}
    
    # 条件: WEKO IDが既に存在する場合
    # 入力: authorIdInfoにidTypeが1のauthorIdが既に存在する
    # 期待結果: ステータスコード500、メッセージ"The value is already in use as WEKO ID."
    input_data = {
        "forceChangeFlag": "false",
        "author":{
            "pk_id": "1",
            "authorIdInfo": [{"idType": "1", "authorId": "123"}]
        }
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(False, "already exists"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "The value is already in use as WEKO ID."}
    
    # 条件: affiliation start dateとend dateがyyyy-MM-dd形式でない場合
    # 入力: affiliation start dateとend dateがyyyy-MM-dd形式でない
    # 期待結果: ステータスコード500、メッセージ"Please set the affiliation start date and end date in the format yyyy-MM-dd."
    input_data = {
        "forceChangeFlag": "false",
        "author":{
            "pk_id": "1",
            "authorIdInfo": [{"idType": "1", "authorId": "123"}],
            "affiliationInfo": [{"startDate": "2021/01/01", "endDate": "2021/12/31"}]
        }
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(True, ""))
    mocker.patch('weko_authors.views.check_period_date', return_value=(False, "not date format"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Please set the affiliation start date and end date in the format yyyy-MM-dd."}
    
    # 条件: affiliation start dateがend dateより後の場合
    # 入力: affiliation start dateがend dateより後
    # 期待結果: ステータスコード500、メッセージ"The end date must be after the start date."
    input_data = {
        "forceChangeFlag": "false",
        "author":{
            "pk_id": "1",
            "authorIdInfo": [{"idType": "1", "authorId": "123"}],
            "affiliationInfo": [{"startDate": "2022-01-01", "endDate": "2021-12-31"}]
        }
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(True, ""))
    mocker.patch('weko_authors.views.check_period_date', return_value=(False, "start is after end"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "The end date must be after the start date."}
    
    # 条件: 正常な入力
    # 入力: 正常なauthorIdInfoとaffiliationInfo
    # 期待結果: ステータスコード200、メッセージ"Success"
    input_data = {
        "forceChangeFlag": "false",
        "author":{
            "pk_id": "1",
            "authorIdInfo": [{"idType": "1", "authorId": "123"}],
            "affiliationInfo": [{"startDate": "2021-01-01", "endDate": "2021-12-31"}]
        }
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(True, ""))
    mocker.patch('weko_authors.views.check_period_date', return_value=(True, ""))
    mocker.patch('weko_authors.views.WekoAuthors.update', return_value=None)
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 200
    assert get_json(res) == {"msg": "Success"}
    
    # 条件: WekoAuthors.updateで例外が発生する場合
    # 入力: 正常なauthorIdInfoとaffiliationInfo
    # 期待結果: ステータスコード500、メッセージ"Failed"
    input_data = {
        "forceChangeFlag": "false",
        "author":{
            "pk_id": "1",
            "authorIdInfo": [{"idType": "1", "authorId": "123"}],
            "affiliationInfo": [{"startDate": "2021-01-01", "endDate": "2021-12-31"}]
        }
    }
    mocker.patch('weko_authors.views.validate_weko_id', return_value=(True, ""))
    mocker.patch('weko_authors.views.check_period_date', return_value=(True, ""))
    mocker.patch('weko_authors.views.WekoAuthors.update', side_effect=Exception("test_error"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Failed"}            

    # 条件: validate_weko_idで例外が発生する場合
    # 入力: 正常なauthorIdInfoとaffiliationInfo
    # 期待結果: ステータスコード500、メッセージ"Failed"
    input_data = {
        "forceChangeFlag": "false",
        "author":{
            "pk_id": "1",
            "authorIdInfo": [{"idType": "1", "authorId": "123"}],
            "affiliationInfo": [{"startDate": "2021-01-01", "endDate": "2021-12-31"}]
        }
    }
    mocker.patch('weko_authors.views.validate_weko_id', side_effect=Exception("test_error"))
    res = client.post(url, data=json.dumps(input_data), content_type='application/json')
    assert res.status_code == 500
    assert get_json(res) == {"msg": "Failed"} 

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_author_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_delete_author_acl_guest(client):
    """
    Test of delete author data.
    :param client: The flask client.
    """
    url = url_for("weko_authors.delete_author")
    res = client.post(url,content_type='plain/text')
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/delete",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_author_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_delete_author_acl_users(client, users, index, is_permission):
    url = url_for("weko_authors.delete_author")
    login_user_via_session(client=client, email=users[index]['email'])
    res = client.post(url, content_type="plain/text")
    assert_role(res, is_permission)
    

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('base_app',[dict(
    is_es=True
)],indirect=['base_app'])
def test_delete_author(client, db,users, esindex, create_author, mocker):
    """
    Test of delete author data.
    :param client: The flask client.
    """
    test_data = {
        "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
        "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
        "emailInfo": [{"email": "example@com"}],
        "is_deleted":"false"
    }
    
    
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for("weko_authors.delete_author")
    mocker.patch("weko_authors.views.get_count_item_link", return_value=0)
    
    id = 1
    es_id = create_author(json.loads(json.dumps(test_data)), id)
    
    input = {"pk_id": str(id),"Id":es_id}
    res = client.post(url,json=input)
    assert res.status_code == 200
    result = Authors.query.filter_by(id=id).one()
    assert result.is_deleted == True
    res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=es_id)
    assert res["_source"]["is_deleted"] == "true"
    
    id = 2
    es_id = create_author(json.loads(json.dumps(test_data)), id)
    
    with patch("weko_authors.db.session.commit",side_effect=Exception("test_error")):
        input = {"pk_id": str(id),"Id":es_id}
        res = client.post(url,json=input)
        assert res.status_code == 200
        result = Authors.query.filter_by(id=id).one()
        assert result.is_deleted == False
        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=es_id)
        assert res["_source"]["is_deleted"] == "false"

    # author is linked to items
    input = {"pk_id": str(id),"Id":es_id}
    with patch("weko_authors.views.get_count_item_link", retutn_value=1):
        res = client.post(url, json=input)
        assert res.status_code == 500
        assert res.get_data().decode("utf-8") == 'The author is linked to items and cannot be deleted.'

    # content_type is not json
    res = client.post(url, content_type="plain/text")
    assert res.status_code == 200
    assert get_json(res) == {"msg": "Header Error"}
    

        
    
# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_acl_guest(client):
    """
    Test of search and get author data.
    :param client: The flask client.
    """
    url = url_for("weko_authors.get")
    res = client.post(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/search",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_get_acl_users(client, users, index, is_permission):
    url = url_for("weko_authors.get")
    login_user_via_session(client=client, email=users[index]['email'])
    with patch('weko_authors.views.RecordIndexer', side_effect=MockIndexer):
        res = client.post(url, json={})
        assert_role(res, is_permission)


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get(client, users):
    """
    Test of search and get author data.
    :param client: The flask client.
    """
    class MockClient():
        def __init__(self,data):
            self.data = data
        def search(self,index=None,doc_type=None, body=None):
            return self.data[index]
    url = url_for("weko_authors.get")
    login_user_via_session(client=client, email=users[0]['email'])
    
    input = {"searchKey": "example", "pageNumber": 1, "numOfPage": 10,
             "sortKey": "name", "sortOrder": "asc"}
    data = {
        "test-authors":{"hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}}, # author_id_info is false
        ]}},
        "test-weko":{"hits":{"total":1}}
    }
    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data)
    test = {
        "hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}},
        ]},
        "item_cnt":{"aggregations":{"item_count":{"buckets":[{"key":"xxx","doc_count":1}]}}}
    }
    with patch("weko_authors.views.RecordIndexer",return_value=record_indexer):
        res = client.post(url, json=input)
        assert res.status_code == 200
        assert get_json(res) == test

    input = {"searchKey": "", "pageNumber": 1, "numOfPage": 10,
             "sortKey": "name", "sortOrder": "asc"}
    data = {
        "test-authors":{"hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}}, # author_id_info is false
        ]}},
        "test-weko":{"hits":{"total":1}}
    }
    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data)
    test = {
        "hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}},
        ]},
        "item_cnt":{"aggregations":{"item_count":{"buckets":[{"key":"xxx","doc_count":1}]}}}
    }
    with patch("weko_authors.views.RecordIndexer",return_value=record_indexer):
        res = client.post(url, json=input)
        assert res.status_code == 200
        assert get_json(res) == test

    input = {"searchKey": "example", "pageNumber": 1, "numOfPage": None,
             "sortKey": "name", "sortOrder": "asc"}
    data = {
        "test-authors":{"hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}}, # author_id_info is false
        ]}},
        "test-weko":{"hits":{"total":1}}
    }
    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data)
    test = {
        "hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}},
        ]},
        "item_cnt":{"aggregations":{"item_count":{"buckets":[{"key":"xxx","doc_count":1}]}}}
    }
    with patch("weko_authors.views.RecordIndexer",return_value=record_indexer):
        res = client.post(url, json=input)
        assert res.status_code == 200
        assert get_json(res) == test

    input = {"searchKey": "example", "pageNumber": None, "numOfPage": 10,
             "sortKey": "name", "sortOrder": "asc"}
    data = {
        "test-authors":{"hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}}, # author_id_info is false
        ]}},
        "test-weko":{"hits":{"total":1}}
    }
    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data)
    test = {
        "hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}},
        ]},
        "item_cnt":{"aggregations":{"item_count":{"buckets":[{"key":"xxx","doc_count":1}]}}}
    }
    with patch("weko_authors.views.RecordIndexer",return_value=record_indexer):
        res = client.post(url, json=input)
        assert res.status_code == 200
        assert get_json(res) == test

    input = {"searchKey": "example", "pageNumber": 1, "numOfPage": 10,
             "sortKey": "", "sortOrder": ""}
    data = {
        "test-authors":{"hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}}, # author_id_info is false
        ]}},
        "test-weko":{"hits":{"total":1}}
    }
    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data)
    test = {
        "hits":{"hits":[
            {"_source":{"authorIdInfo":[{"authorId":"test_id"}], 'pk_id':'xxx'}},
        ]},
        "item_cnt":{"aggregations":{"item_count":{"buckets":[{"key":"xxx","doc_count":1}]}}}
    }
    with patch("weko_authors.views.RecordIndexer",return_value=record_indexer):
        res = client.post(url, json=input)
        assert res.status_code == 200
        assert get_json(res) == test


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_getById_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_getById_acl_guest(client):
    """
    Test of get author data by id.
    :param client: The flask client.
    """
    url = url_for("weko_authors.getById")
    res = client.post(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/search_edit",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_getById_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_getById_acl_users(client,users, index, is_permission):
    url = url_for("weko_authors.getById")
    login_user_via_session(client=client, email=users[index]['email'])
    with patch("weko_authors.views.RecordIndexer", side_effect=MockIndexer):
        res = client.post(url, json={})
        assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_getById -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_getById(client, users, mocker):
    """
    Test of get author data by id.
    :param client: The flask client.
    """
    class MockClient:
        def __init__(self,data):
            self.data = data
        def search(self,index=None,doc_type=None,body=None):
            return self.data
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for("weko_authors.getById")

    record_indexer = RecordIndexer()
    record_indexer.client=MockClient({"test":"test_search_result"})
    mocker.patch("weko_authors.views.RecordIndexer",return_value=record_indexer)
    
    # search_key is none
    input = {}
    res = client.post(url, json=input)
    assert res.status_code == 200
    assert res.get_data().decode("utf-8") == '{"test": "test_search_result"}'
    
    # search_key is not noen
    input = {"Id":"test_id"}
    res = client.post(url, json=input)
    assert res.status_code == 200
    assert res.get_data().decode("utf-8") == '{"test": "test_search_result"}'

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_mapping_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_mapping_acl_guest(client):
    """
    Test of mapping author data.
    :param client: The flask client.
    """
    url = url_for("weko_authors.mapping")
    res = client.post(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/input",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_mapping_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_mapping_acl_users(client, users, index, is_permission):
    url = url_for("weko_authors.mapping")
    login_user_via_session(client=client, email=users[index]['email'])
    input = {"id": "1"}
    with patch('weko_authors.views.RecordIndexer', side_effect=MockIndexer):
        res = client.post(url, json=input)
        assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_mapping(client, users, authors_prefix_settings, authors_affiliation_settings):
    """
    Test of mapping author data.
    :param client: The flask client.
    """
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for("weko_authors.mapping")
    class MockClient:
        def __init__(self, value):
            self.data = value
        def get(self,index=None,doc_type=None,id=None):
            return self.data
    input = {"id": "1"}
    data = {
        "_source":{
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "花子",
                    "fullName": "テスト 花子",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "true"
                },
                {
                    "familyName": "テスト",
                    "firstName": "ハナコ",
                    "fullName": "テスト ハナコ",
                    "language": "ja-Kana",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "false"
                },
                {
                    "fullName": "テスト 花子",
                    "language": "ja",
                    "nameFormat": "fullNm",
                    "nameShowFlg": "true"
                },
            ],
            "authorIdInfo": [
                { "authorId": "1234", "authorIdShowFlg": "true", "idType": "2"},
                { "authorId": "2345", "authorIdShowFlg": "false", "idType": "2" }, # authorIdInfo.authorIdShowFlg = false
                { "authorId": "3456", "authorIdShowFlg": "true", "idType": "1000" } # _author_id, uri is not existed
            ],
            "emailInfo": [
                { "email": "test.hanako@test.org" }
            ],
            "affiliationInfo":[
                {
                    "identifierInfo":[
                        {
                            "affiliationId": "9876",
                            "affiliationIdType": "1",
                            "identifierShowFlg": "true"
                        },
                        { # identifierInfo.identifierShoFlg is false
                            "affiliationId": "8765",
                            "affiliationIdType": "1",
                            "identifierShowFlg": "false"
                        },
                        { # identifierInfo.affiliationId is none
                            "affiliationId": "",
                            "affiliationIdType": "1",
                            "identifierShowFlg": "true"
                        },
                        { # _affiliation_id, uri is none
                            "affiliationId": "7654",
                            "affiliationIdType": "1000",
                            "identifierShowFlg": "true"
                        }
                    ],
                    "affiliationNameInfo":[
                        {
                            "affiliationName": "テスト1",
                            "affiliationNameLang": "ja",
                            "affiliationNameShowFlg": "true"
                        },
                        {
                            "affiliationName": "テスト2",
                            "affiliationNameLang": "ja",
                            "affiliationNameShowFlg": "false"
                        },
                        {
                            "affiliationName": "",
                            "affiliationNameLang": "ja",
                            "affiliationNameShowFlg": "true"
                        }
                    ]
                }
            ]
        }
    }
    test = [
        {
            "author_affiliation":{
                "affiliations":{"identifiers":{"key":"nameIdentifiers","values": {"identifier":"nameIdentifier","scheme":"nameIdentifierScheme","uri":"nameIdentifierURI"}},
                                               "names": {"key": "affiliationNames","values":{"lang":"lang","name":"affiliationName"}}},
                "contributorAffiliations": {"identifiers":{"key":"contributorAffiliationNameIdentifiers","values":{"identifier":"contributorAffiliationNameIdentifier","scheme":"contributorAffiliationScheme","uri":"contributorAffiliationURI"}},
                                                           "names":{"key":"contributorAffiliationNames","values":{"lang":"contributorAffiliationNameLang","name":"contributorAffiliationName"}}},
                "creatorAffiliations": {"identifiers":{"key":"affiliationNameIdentifiers","values":{"identifier":"affiliationNameIdentifier","scheme":"affiliationNameIdentifierScheme","uri":"affiliationNameIdentifierURI"}},
                                                       "names":{"key":"affiliationNames","values":{"lang":"affiliationNameLang","name":"affiliationName"}}}
            },
            "author_mail": {"contributorMails": "contributorMail","creatorMails":"creatorMail","mails":"mail"},
            "author_name": {"contributorNames": ["contributorName","lang"],"creatorNames":["creatorName","creatorNameLang"],"names":["name","nameLang"]},
            "creatorAffiliations": [
                {"affiliationNameIdentifiers": [{"affiliationNameIdentifier":"9876",
                                                 "affiliationNameIdentifierScheme":"ISNI",
                                                 "affiliationNameIdentifierURI":"http://www.isni.org/isni/9876"},
                                                {"affiliationNameIdentifier":"7654",
                                                 "affiliationNameIdentifierScheme":"",
                                                 "affiliationNameIdentifierURI":""}],
                 "affiliationNames": [{"affiliationName":"テスト1","affiliationNameLang":"ja"}]}
            ],
            "creatorMails":[{"creatorMail": "test.hanako@test.org"}],
            "creatorNames": [{"creatorName": "テスト 花子","creatorNameLang":"ja"}],
            "familyNames":[{"familyName":"テスト","familyNameLang":"ja"}],
            "givenNames":[{"givenName":"花子","givenNameLang":"ja"}],
            "nameIdentifiers":[{"nameIdentifier":"1234",
                                "nameIdentifierScheme":"ORCID",
                                "nameIdentifierURI":"https://orcid.org/1234"},
                               {"nameIdentifier":"3456",
                                "nameIdentifierScheme":"",
                                "nameIdentifierURI":""}]
        }
    ]
    record_indexer = RecordIndexer()
    record_indexer.client = MockClient(data)
    with patch('weko_authors.views.RecordIndexer', return_value=record_indexer):
        res = client.post(url,json=input)
        assert res.status_code == 200
        assert json.loads(res.get_data().decode("utf-8"))==test
        
    data = {"_source": {"authorNameInfo": {},
                                "authorIdInfo": {},
                                "emailInfo": {},
                                "affiliationInfo":{}
                                }
                    }
    test = [
        {
          "author_affiliation": {
            "affiliations": {"identifiers": {"key": "nameIdentifiers","values": {"identifier": "nameIdentifier","scheme": "nameIdentifierScheme","uri": "nameIdentifierURI"}},
                                             "names": {"key": "affiliationNames","values": { "lang": "lang", "name": "affiliationName" }}},
            "contributorAffiliations": {"identifiers": {"key": "contributorAffiliationNameIdentifiers","values": {"identifier": "contributorAffiliationNameIdentifier","scheme": "contributorAffiliationScheme","uri": "contributorAffiliationURI"}},
                                        "names": {"key": "contributorAffiliationNames","values": {"lang": "contributorAffiliationNameLang","name": "contributorAffiliationName"}}},
            "creatorAffiliations": {"identifiers": {"key": "affiliationNameIdentifiers","values": {"identifier": "affiliationNameIdentifier","scheme": "affiliationNameIdentifierScheme","uri": "affiliationNameIdentifierURI"}},
                                    "names": {"key": "affiliationNames","values": { "lang": "affiliationNameLang", "name": "affiliationName" }}}
          },
          "author_mail": {"contributorMails": "contributorMail","creatorMails": "creatorMail","mails": "mail"},
          "author_name": {"contributorNames": ["contributorName", "lang"],"creatorNames": ["creatorName", "creatorNameLang"],"names": ["name", "nameLang"]}
        }
    ]

    record_indexer = RecordIndexer()
    record_indexer.client = MockClient(data)
    with patch('weko_authors.views.RecordIndexer', return_value=record_indexer):
        res = client.post(url,json=input)
        assert res.status_code == 200
        assert json.loads(res.get_data().decode("utf-8"))==test


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_gatherById_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_gatherById_acl_guest(client):
    """
    Test of gather author data by id.
    :param client: The flask client.
    """
    url = url_for("weko_authors.gatherById")
    res = client.post(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/gather",_external=True)


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_gatherById_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_gatherById_acl_users(client, users, index, is_permission):
    """
    Test of gather author data by id.
    :param client: The flask client.
    """
    url = url_for("weko_authors.gatherById")
    login_user_via_session(client=client, email=users[index]['email'])
    input = {'idFrom': ['1', '2'], 'idFromPkId': ['1', '2'], 'idTo': '1'}
    mock_indexer = MagicMock(side_effect=MockIndexer)
    with patch('weko_authors.views.RecordIndexer', mock_indexer):
        with patch('weko_deposit.tasks.update_items_by_authorInfo'):
            res = client.post(url, json=input)
            assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_gatherById -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_gatherById(client, users, authors):
    url = url_for("weko_authors.gatherById")
    login_user_via_session(client=client, email=users[0]['email'])
    
    class MockClient:
        def __init__(self, value):
            self.data = value
        def search(self,index=None, body=None):
            id = body["query"]["match"]["_id"]
            return self.data[index][id]
        def update(self,index=None,doc_type=None,id=None,body=None):
            pass
    
    input = {
        "idFrom":["1","2"],
        "idFromPkId":["1","2"],
        "idTo":"3"
    }
    
    # raise Exception
    with patch("weko_authors.views.db.session.commit", side_effect=Exception("test_error")):
        res = client.post(url, json=input)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code": 204, "msg": "Failed"}
        assert Authors.query.filter_by(id="1").one().gather_flg == 0
        assert Authors.query.filter_by(id="2").one().gather_flg == 0
    
    input = {
        "idFrom":["1","2"],
        "idFromPkId":["1","2"],
        "idTo":"1"
    }
    data = {
        "test-authors":{
            "1":{"hits":{"hits":[{"_source":{"test_source":"value"}}]}},
            "2":{"hits":{"hits":[{"_id":"author_1"}]}}
        }
    }
    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data)
    with patch("weko_authors.views.RecordIndexer", return_value=record_indexer):
        with patch('weko_deposit.tasks.update_items_by_authorInfo'):
            res = client.post(url, json=input)
            assert json.loads(res.data) == {"code": 0, "msg": "Success"}
            assert Authors.query.filter_by(id="1").one().gather_flg == 0
            assert Authors.query.filter_by(id="2").one().gather_flg == 1

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_prefix_list_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_prefix_list_acl_guest(client):
    url = url_for("weko_authors.get_prefix_list")
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/search_prefix",_external=True)

#.tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_prefix_list_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_get_prefix_list_acl_users(client, users, authors_prefix_settings, index, is_permission):
    url = url_for("weko_authors.get_prefix_list")
    login_user_via_session(client=client, email=users[index]['email'])

    res = client.get(url)
    assert_role(res, is_permission)
    
# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_prefix_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_prefix_list(client, db, users):
    url = url_for("weko_authors.get_prefix_list")
    login_user_via_session(client=client, email=users[0]['email'])
    
    # not exist settings
    res = client.get(url)
    assert res.status_code == 200
    assert get_json(res) == []
    
    orcid = AuthorsPrefixSettings(name="ORCID",scheme="ORCID",url="https://orcid.org/##")
    db.session.add(orcid)
    db.session.commit()
    
    res = client.get(url)
    assert res.status_code == 200
    result = get_json(res)[0]
    assert result["name"] == "ORCID"
    assert result["scheme"] == "ORCID"
    assert result["url"] == "https://orcid.org/##"
    assert result["id"] == 1
    


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_affiliation_list_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_affiliation_list_acl_guest(client):
    url = url_for("weko_authors.get_affiliation_list")
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/search_affiliation",_external=True)

#.tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_affiliation_list_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_get_affiliation_list_acl_users(client, users, authors_prefix_settings, index, is_permission):
    url = url_for("weko_authors.get_affiliation_list")
    login_user_via_session(client=client, email=users[index]['email'])

    res = client.get(url)
    assert_role(res, is_permission)
    
# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_affiliation_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_affiliation_list(client, db, users):
    url = url_for("weko_authors.get_affiliation_list")
    login_user_via_session(client=client, email=users[0]['email'])
    
    # not exist settings
    res = client.get(url)
    assert res.status_code == 200
    assert get_json(res) == []
    
    orcid = AuthorsAffiliationSettings(name="ISNI",scheme="ISNI",url="http://www.isni.org/isni/##")
    db.session.add(orcid)
    db.session.commit()
    
    res = client.get(url)
    assert res.status_code == 200
    result = get_json(res)[0]
    assert result["name"] == "ISNI"
    assert result["scheme"] == "ISNI"
    assert result["url"] == "http://www.isni.org/isni/##"
    assert result["id"] == 1
    
# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_list_schema_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_list_schema_acl_guest(client):
    url = url_for("weko_authors.get_list_schema")
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/list_vocabulary",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_list_schema_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_get_list_schema_acl_users(client, users, index, is_permission):
    url = url_for("weko_authors.get_list_schema")
    login_user_via_session(client=client, email=users[index]['email'])
    res = client.get(url)
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_list_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_list_schema(client, users):
    url = url_for("weko_authors.get_list_schema")
    login_user_via_session(client=client, email=users[0]['email'])
    test = {
        "list":['e-Rad', 'NRID', 'ORCID', 'ISNI', 'VIAF', 'AID','kakenhi', 'Ringgold', 'GRID', 'ROR', 'Other'],
        "index":10
    }
    res = client.get(url)
    assert get_json(res) == test
    
    
# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_list_affiliation_schema_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_list_affiliation_schema_acl_guest(client):
    url = url_for("weko_authors.get_list_affiliation_schema")
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/list_affiliation_scheme",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_list_affiliation_schema_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_get_list_affiliation_schema_acl_users(client, users, index, is_permission):
    url = url_for("weko_authors.get_list_affiliation_schema")
    login_user_via_session(client=client, email=users[index]['email'])
    res = client.get(url)
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_list_affiliation_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_list_affiliation_schema(client, users):
    url = url_for("weko_authors.get_list_affiliation_schema")
    login_user_via_session(client=client, email=users[0]['email'])
    test = {
        "list": ['ISNI', 'GRID', 'Ringgold', 'kakenhi', 'Other'],
        "index": 4
    }
    res = client.get(url)
    assert get_json(res) == test


#.tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_prefix_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_update_prefix_acl_guest(client):
    """
    Test of update author prefix.
    :param client: The flask client.
    """
    url = url_for("weko_authors.update_prefix")
    res = client.post(url)
    assert res.location == url_for('security.login',next="/api/authors/edit_prefix",_external=True)


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_prefix_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_update_prefix_acl_users(client, users, authors_prefix_settings, index, is_permission):
    """
    Test of update author prefix.
    :param client: The flask client.
    """
    # login
    url = url_for("weko_authors.update_prefix")
    login_user_via_session(client=client, email=users[index]['email'])
    input = {"schema":"None"}
    res = client.post(url,json=input)
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_update_prefix(client, users, authors_prefix_settings):
    url = url_for("weko_authors.update_prefix")
    login_user_via_session(client=client, email=users[0]['email'])
    
    # try to update the scheme of setting with ORCID in scheme to a non-existing scheme
    id = 2
    input = {"id":id,"scheme":"None","name":"none_name","url":"https://test_none/##"}
    res = client.post(url,json=input)
    result = AuthorsPrefixSettings.query.filter_by(id=id).one()
    assert result.scheme == "None"
    assert result.name == "none_name"
    assert result.url == "https://test_none/##"
    assert get_json(res) == {"code":200,"msg":'Success'}
    
    # try to update the scheme of setting with KAKEN2 in scheme to a existing scheme
    id = 4
    input = {"id":id,"scheme":"CiNii","name":"CiNii","url":"https://new_url/##"}
    res = client.post(url,json=input)
    assert get_json(res) == {"code":400,"msg":'Specified scheme is already exist.'}
    
    # raise Exception
    res = client.post(url,data="not_correct_data")
    assert get_json(res) == {"code":204,"msg":'Failed'}


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_prefix_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_delete_prefix_acl_guest(client, authors_prefix_settings):
    """
    Test of delete author prefix.
    :param client: The flask client.
    """
    # delete prefix
    id = authors_prefix_settings[0].id
    url = url_for('weko_authors.delete_prefix', id=id)
    res = client.delete(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/delete_prefix/1",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_prefix_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_delete_prefix_acl_users(client, users, authors_prefix_settings, index, is_permission):
    """
    Test of delete author prefix.
    :param client: The flask client.
    """
    # login for delete prefix
    login_user_via_session(client=client, email=users[index]['email'])
    url = url_for('weko_authors.delete_prefix', id=1)
    res = client.delete(url)
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_delete_prefix(client, users, authors_prefix_settings):
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for('weko_authors.delete_prefix', id=1)
    res = client.delete(url)
    assert get_json(res) == {"msg": "Success"}
    assert AuthorsPrefixSettings.query.filter_by(id=1).one_or_none() is None


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_prefix_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_prefix_acl_guest(client):
    """
    Test of create author prefix.
    :param client: The flask client.
    """
    url = url_for("weko_authors.create_prefix")
    res = client.put(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/add_prefix",_external=True)


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_prefix_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_create_prefix_acl_users(client, users, index, is_permission):
    """
    Test of create author prefix.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[index]['email'])
    url = url_for("weko_authors.create_prefix")

    input = {'name': 'test0', 'scheme': 'test0', 'url': 'https://test0/##'}
    res = client.put(url,json=input)
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_prefix(client, users):
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for("weko_authors.create_prefix")
    
    input = {'name': 'test0', 'scheme': 'test0', 'url': 'https://test0/##'}
    # not exist scheme setting
    res = client.put(url,json=input)
    assert get_json(res) == {"code":200,"msg":"Success"}
    assert AuthorsPrefixSettings.query.filter_by(name="test0").one()
    
    # exist scheme setting
    res = client.put(url,json=input)
    assert get_json(res) == {"code":400,"msg":'Specified scheme is already exist.'}
    
    # raise exception
    with patch("weko_authors.views.get_author_prefix_obj", side_effect=Exception("test_error")):
        res = client.put(url,json=input)
        assert get_json(res) == {"code":204,"msg":'Failed'}

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_affiliation_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_update_affiliation_acl_guest(client):
    url = url_for("weko_authors.update_affiliation")
    res = client.post(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/edit_affiliation",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_affiliation_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_update_affiliation_acl_users(client, users, authors_affiliation_settings, index, is_permission):
    login_user_via_session(client=client, email=users[index]['email'])
    url = url_for("weko_authors.update_affiliation")
    input = {'id':1,'name': 'ISNI', 'scheme': 'ISNI', 'url': 'https://test0/##'}
    res = client.post(url,json=input)
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_update_affiliation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_update_affiliation(client, users, authors_affiliation_settings):
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for("weko_authors.update_affiliation")
    
    # try to update the scheme of setting with ISNI in scheme to a non-existing scheme
    input = {'id':1,'name': 'none_name', 'scheme': 'None', 'url': 'https://new_none/##'}
    res = client.post(url,json=input)
    result = AuthorsAffiliationSettings.query.filter_by(id=1).one()
    assert result.name == "none_name"
    assert result.scheme == "None"
    assert result.url == "https://new_none/##"
    assert get_json(res) == {"code":200,"msg":"Success"}
    
    # try to update the scheme of setting with GRID in scheme to a existing scheme
    input = {'id':2,'name': 'Ringgold', 'scheme': 'Ringgold', 'url': 'https://new_none/##'}
    res = client.post(url,json=input)
    assert get_json(res) == {"code":400, "msg": "Specified scheme is already exist."}
    
    # raise Exception
    with patch("weko_authors.views.get_author_affiliation_obj", side_effect=Exception("test_error")):
        res = client.post(url,json=input)
        assert get_json(res) == {"code":204, "msg": "Failed"}

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_prefix_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_delete_affiliation_acl_guest(client, authors_affiliation_settings):
    """
    Test of delete author prefix.
    :param client: The flask client.
    """
    # delete prefix
    url = url_for('weko_authors.delete_affiliation', id=1)
    res = client.delete(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/delete_affiliation/1",_external=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_prefix_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_delete_affiliation_acl_users(client, users, authors_affiliation_settings, index, is_permission):
    """
    Test of delete author affiliation.
    :param client: The flask client.
    """
    # login for delete affiliation
    login_user_via_session(client=client, email=users[index]['email'])
    url = url_for('weko_authors.delete_affiliation', id=1)
    res = client.delete(url)
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_delete_affiliation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_delete_affiliation(client, users, authors_affiliation_settings):
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for('weko_authors.delete_affiliation', id=1)
    res = client.delete(url)
    assert get_json(res) == {"msg": "Success"}
    assert AuthorsAffiliationSettings.query.filter_by(id=1).one_or_none() is None


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_affiliation_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_affiliation_acl_guest(client):
    """
    Test of create author affiliation.
    :param client: The flask client.
    """
    url = url_for("weko_authors.create_affiliation")
    res = client.put(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/api/authors/add_affiliation",_external=True)


# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_affiliation_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0,True), # sysadmin
    (1,True), # repoadmin
    (2,True), # comadmin
    (3,True), # contributor
    (4,False), # generaluser
    (5,False), # originalroleuser
    (6,True), # originalroleuser2
    (7,False), # user
    (8,False), # student  
])
def test_create_affiliation_acl_users(client, users, index, is_permission):
    """
    Test of create author affiliation.
    :param client: The flask client.
    """
    # login
    login_user_via_session(client=client, email=users[index]['email'])
    url = url_for("weko_authors.create_affiliation")

    input = {'name': 'test0', 'scheme': 'test0', 'url': 'https://test0/##'}
    res = client.put(url,json=input)
    assert_role(res, is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_create_affiliation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_affiliation(client, users):
    login_user_via_session(client=client, email=users[0]['email'])
    url = url_for("weko_authors.create_affiliation")
    
    input = {'name': 'test0', 'scheme': 'test0', 'url': 'https://test0/##'}
    # not exist scheme setting
    res = client.put(url,json=input)
    assert get_json(res) == {"code":200,"msg":"Success"}
    assert AuthorsAffiliationSettings.query.filter_by(name="test0").one()
    
    # exist scheme setting
    res = client.put(url,json=input)
    assert get_json(res) == {"code":400,"msg":'Specified scheme is already exist.'}
    
    # raise exception
    with patch("weko_authors.views.get_author_affiliation_obj", side_effect=Exception("test_error")):
        res = client.put(url,json=input)
        assert get_json(res) == {"code":204,"msg":'Failed'}

# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_dbsession_clean(app, db):
    from weko_records.models import ItemTypeName
    # exist exception
    itemtype_name1 = ItemTypeName(id=1,name="テスト1",has_site_license=True, is_active=True)
    db.session.add(itemtype_name1)
    dbsession_clean(None)
    assert ItemTypeName.query.filter_by(id=1).first().name == "テスト1"

    # raise Exception
    itemtype_name2 = ItemTypeName(id=2,name="テスト2",has_site_license=True, is_active=True)
    db.session.add(itemtype_name2)
    with patch("weko_items_autofill.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert ItemTypeName.query.filter_by(id=2).first() is None

    # not exist exception
    itemtype_name3 = ItemTypeName(id=3,name="テスト3",has_site_license=True, is_active=True)
    db.session.add(itemtype_name3)
    dbsession_clean(Exception)
    assert ItemTypeName.query.filter_by(id=3).first() is None


#     def get_max_weko_id():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_views.py::test_get_max_weko_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_max_weko_id(client, users, mocker ):
    class MockClient():
        def __init__(self,data):
            self.data = data
        def search(self,index=None,body=None,scroll='2m'):
            return self.data[index]
        def scroll(self,scroll_id='scroll_id',scroll='2m'):
            self.data['test-authors']['hits'] ={"hits":{"hits":[]}}
            return self.data['test-authors']['hits']

    url = url_for("weko_authors.get_max_weko_id")
    login_user_via_session(client=client, email=users[0]['email'])

    data = {
    "test-authors": {
        "hits": {
            "hits": [
                {"_source": {"authorIdInfo": [{"authorId": "2",'idType': '1'}]}, 'pk_id': 'xxx'}
            ]
        },
        "_scroll_id": "AAA"
    },
    "test-weko": {
        "hits": {
            "total": 1
        }
    }
    }

    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data)
    mocker.patch("weko_authors.views.RecordIndexer",return_value=record_indexer)
    test = {'max_author_id': 2}
    res = client.get(url)
    assert get_json(res) == test

    data_2 = {
    "test-authors": {
        "hits": {
            "hits": [
                {"_source": {}, 'pk_id': 'xxx'}
            ]
        },
        "_scroll_id": "AAA"
    },
    "test-weko": {
        "hits": {
            "total": 1
        }
    }
    }

    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data_2)
    mocker.patch("weko_authors.views.RecordIndexer",return_value=record_indexer)
    test = {'max_author_id': 0}
    res = client.get(url)
    assert get_json(res) == test


    data_3 = {
    "test-authors": {
        "hits": {
            "hits": [
                {"_source": {"authorIdInfo": [{"authorId": "2",'idType': '1'}]}, 'pk_id': 'xxx'}
            ]
        },
        "_scroll_id": "AAA"
    },
    "test-weko": {
        "hits": {
            "total": 1
        }
    }
    }

    record_indexer = RecordIndexer()
    record_indexer.client=MockClient(data_3)
    mocker.patch("weko_authors.views.RecordIndexer",return_value=record_indexer)
    test = {'max_author_id': 0}
    res = client.get(url)
    assert get_json(res) == test