from mock import patch, MagicMock
import json
import uuid
import pytest
import logging
from _pytest.logging import LogCaptureFixture
from logging import INFO, ERROR
from flask import current_app
from elasticsearch.exceptions import NotFoundError
from invenio_indexer.api import RecordIndexer
from invenio_search import current_search_client
from mock import patch, MagicMock


from weko_authors.api import WekoAuthors
from weko_authors.models import Authors, AuthorsPrefixSettings, AuthorsAffiliationSettings
from weko_authors.config import WEKO_AUTHORS_FILE_MAPPING

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

class MockClient():
    def __init__(self):
        self.index_ = self.MockIndex()
        self.return_value=""
    def index(self,index,doc_type,id,body):
        return self.index_
    def delete(self,index,doc_type,id):
        pass
    def set_return(self,value):
        self.return_value=value
    def search(self,index,doc_type=None,body=None):
        return self.return_value
    def update(self,index,doc_type,id,body):
        pass
    class MockIndex():
        def __init__(self):
            self.data = {}
        def get(self,type,value):
            return self.data.get(type)
        def set(self,type,data):
            self.data[type]=data

# class WekoAuthors(object):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestWekoAuthors:
#     def create(cls, data):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_create(self,app,db,esindex, mocker, users):
        id = 1
        es_id = uuid.uuid4()
        with patch("weko_authors.api.Authors.get_sequence",return_value=id):
            with patch("weko_authors.api.uuid.uuid4",return_value = es_id):
                data = {"authorIdInfo":[]}
                WekoAuthors.create(data)
                db.session.commit()
                author = Authors.query.filter_by(id=id).one()
                test = {"authorIdInfo": [], "gather_flg": 0, "id": str(es_id), "pk_id": "1"}
                assert author
                assert author.json == test
                res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=str(es_id))
                assert res["_source"]["pk_id"]==str(id)

        id = 2
        es_id = uuid.uuid4()
        with patch("weko_authors.api.Authors.get_sequence",return_value=id):
            with patch("weko_authors.api.uuid.uuid4",return_value = es_id):
                with patch("weko_authors.api.db.session.add",side_effect=Exception("test_error")):
                    with pytest.raises(Exception):
                        data = {"authorIdInfo":[]}
                        WekoAuthors.create(data)

                    author = Authors.query.filter_by(id=id).one_or_none()
                    assert author == None
                    with pytest.raises(NotFoundError):
                        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=str(es_id))

        from invenio_communities.models import Community
        com1 = Community.query.get("comm01")
        id = 3
        es_id = uuid.uuid4()
        with patch("weko_authors.api.Authors.get_sequence",return_value=id):
            with patch("weko_authors.api.uuid.uuid4",return_value = es_id):
                data = {
                    "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
                    "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
                    "emailInfo": [{"email": "example@com"}],
                    "is_deleted":"false",
                    "communityIds": ["comm01"],
                }
                WekoAuthors.create(data)
                db.session.commit()
                author = Authors.query.filter_by(id=id).one()
                test = {
                    "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
                    "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
                    "emailInfo": [{"email": "example@com"}],
                    "is_deleted":"false",
                    "gather_flg": 0,
                    "id": str(es_id),
                    "pk_id": "3"
                }
                assert author
                assert author.json == test
                assert author.communities[0].id == com1.id
                res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=str(es_id))
                assert res["_source"]["pk_id"]==str(id)
                assert res["_source"]["communityIds"]==["comm01"]

#     def update(cls, author_id, data):
#         def update_es_data(data):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_update(self,app,db,esindex,create_author,mocker, users):
        mocker.patch("weko_deposit.tasks.update_items_by_authorInfo.delay")
        test_data = {
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":"false"
        }

        author_id=1
        es_id = create_author(json.loads(json.dumps(test_data)), author_id)

        # is_deleted is false,
        data={
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":False
        }
        WekoAuthors.update(author_id,data)
        db.session.commit()
        author = Authors.query.filter_by(id=author_id).one()
        assert author.json["is_deleted"] == False
        assert author.communities == []
        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=es_id)
        assert res["_source"]["is_deleted"] == False
        assert res["_source"]["communityIds"] == []

        # set communityIDs
        data = {
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted": False,
            "communityIds": ["comm01"]
        }
        WekoAuthors.update(author_id,data)
        db.session.commit()
        author = Authors.query.filter_by(id=author_id).one()
        assert author.communities[0].id == "comm01"
        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=es_id)
        assert res["_source"]["communityIds"] == ["comm01"]

        # is_deleted is true
        data={
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":True
        }
        WekoAuthors.update(author_id,data)
        db.session.commit()
        author = Authors.query.filter_by(id=author_id).one()
        assert author.json["is_deleted"] == True
        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=es_id)
        assert res["_source"]["is_deleted"] == True

        author_id=2
        es_id = create_author(json.loads(json.dumps(test_data)), author_id)
        with patch("weko_authors.api.db.session.merge",side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                WekoAuthors.update(author_id,data)
            db.session.rollback()
            author = Authors.query.filter_by(id=author_id).one()
            assert author.is_deleted==False
            res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=es_id)
            assert res["_source"]["is_deleted"] == "false"

        # not hit in es
        author_id=3
        es_id = str(uuid.uuid4())
        test_data = {
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":"false",
            "pk_id":str(author_id),
            "id":es_id
        }
        author = Authors(id=author_id,json=test_data)
        db.session.add(author)
        db.session.commit()
        with pytest.raises(NotFoundError):
            res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=str(es_id))
        data={
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":True
        }
        WekoAuthors.update(author_id,data)
        db.session.commit()
        assert Authors.query.filter_by(id=author_id).one().is_deleted==True
        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=str(es_id))
        assert res["_source"]["is_deleted"] == True

        # not es_id in data
        es_id1 = str(uuid.uuid4())
        es_id2 = str(uuid.uuid4())
        author_id=4
        test_data = {
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":"false",
            "pk_id":str(author_id),
            "id":""
        }
        es_data = json.loads(json.dumps(test_data))
        test_data["id"] = es_id1
        author = Authors(id=author_id,json=test_data)
        db.session.add(author)
        db.session.commit()
        current_search_client.index(
            index=app.config["WEKO_AUTHORS_ES_INDEX_NAME"],
            doc_type=app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
            id=es_id2,
            body=es_data,
            refresh='true')
        data={
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":True
        }
        WekoAuthors.update(author_id,data)
        db.session.commit()
        assert Authors.query.filter_by(id=author_id).one().is_deleted==True
        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=str(es_id))
        assert res["_source"]["is_deleted"] == True

        # es_author['hits']['hits'][0].get('_id') == es_id is true
        test_data = {
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":"false"
        }

        author_id=5
        es_id = create_author(json.loads(json.dumps(test_data)), author_id)
        author = Authors.query.filter_by(id=author_id).one()
        id = author.json["id"]

        # is_deleted is false,
        data={
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":False
        }
        mock_author = MagicMock(spec=Authors)
        mock_author.json = {
            "id": "551b447c-ad9a-4001-8cb0-60f824579991",
            "pk_id": "2",
            "emailInfo": [{"email": "example@com"}],
            "is_deleted": "false",
            "authorIdInfo": [{"idType": "2", "authorId": "01234", "authorIdShowFlg": "true"}],
            "authorNameInfo": [
                {
                    "fullName": "",
                    "language": "ja-Kana",
                    "firstName": "ハナコ",
                    "familyName": "テスト",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "true",
                }
            ],
        }
        es_author = {
            'hits': {
                'total': 1,
                'hits': [
                    {
                        '_id': id,
                        '_source': {
                        }
                    }
                ]
            }
        }
        RecordIndexer().client.search = MagicMock(return_value=es_author)
        mock_filter_by =mocker.patch("weko_authors.api.Authors.query.filter_by")
        mock_filter_by.return_value.one.return_value = mock_author
        WekoAuthors.update(author_id,data)
        db.session.commit()
        author = Authors.query.filter_by(id=author_id).one()
        assert author.json["is_deleted"] == False
        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=es_id)
        assert res["_source"]["is_deleted"] == False

        # if es_author['hits']['total'] > 0 is false
        test_data = {
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":"false"
        }

        author_id=6
        es_id = create_author(json.loads(json.dumps(test_data)), author_id)

        # is_deleted is false,
        data={
            "authorNameInfo": [{"familyName": "テスト","firstName": "ハナコ","fullName": "","language": "ja-Kana","nameFormat": "familyNmAndNm","nameShowFlg": "true"}],
            "authorIdInfo": [{"idType": "2","authorId": "01234","authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "example@com"}],
            "is_deleted":False
        }
        search_data = {
            "hits": {
                "total": 0,
                "hits": [],
            },
        }
        mock_indexer = RecordIndexer()
        mock_indexer.client = MockClient()
        mock_indexer.client.search = MagicMock(return_value=search_data)
        mocker.patch("weko_authors.api.RecordIndexer", return_value=mock_indexer)
        mocker.patch("weko_authors.api.current_user", return_value=True)
        WekoAuthors.update(author_id,data)
        db.session.commit()
        author = Authors.query.filter_by(id=author_id).one()
        assert author.json["is_deleted"] == False
        res = current_search_client.get(index=current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"],doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],id=es_id)
        assert res["_source"]["is_deleted"] == "false"

#     def get_all(cls, with_deleted=True, with_gather=True):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_all(self,app,authors):
        result = WekoAuthors.get_all()
        assert authors
        result = WekoAuthors.get_all(False,False)
        assert authors


#     def get_records_count(cls, with_deleted=True, with_gather=True):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_records_count -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_records_count(self,app,authors, mocker):
        result = WekoAuthors.get_records_count(with_deleted=True, with_gather=True)
        assert result == 4

        result = WekoAuthors.get_records_count(with_deleted=True, with_gather=False)
        assert result == 3

        result = WekoAuthors.get_records_count(with_deleted=False, with_gather=True)
        assert result == 3

        with pytest.raises(Exception):
            mocker.patch.object(Authors, 'id', return_value = "test_id")
            result = WekoAuthors.get_records_count(with_deleted=False, with_gather=True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_records_count_with_community -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_records_count_with_community(self, app, db, authors, community):
        authors[1].communities = [community[0]]
        authors[2].communities = [community[0]]
        authors[3].communities = [community[0]]
        db.session.commit()
        result = WekoAuthors.get_records_count(
            with_deleted=True, with_gather=True, community_ids=["community1"])
        assert result == 3

        result = WekoAuthors.get_records_count(
            with_deleted=True, with_gather=False, community_ids=["community1"])
        assert result == 2

        result = WekoAuthors.get_records_count(
            with_deleted=False, with_gather=True, community_ids=["community1"])
        assert result == 2

#     def get_author_for_validation(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_author_for_validation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_author_for_validation(self,authors,mocker):
        mocker.patch("weko_authors.api.WekoAuthors.get_all",return_value=authors)

        authors_result, external_result = WekoAuthors.get_author_for_validation()
        assert authors_result == {"1":True,"2":True,"3":True,"4":False}
        assert external_result == {"1":{"1":["1"],"2":["2"]},"2":{"1234":["1"],"5678":["2"]},"3":{"12345":["1"]}}


#     def get_id_prefix_all(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_id_prefix_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_id_prefix_all(self,authors,authors_prefix_settings,db):
        test = [1, 2, 3, 4, 5]
        results = WekoAuthors.get_id_prefix_all()
        result_list = []
        for result in results:
            result_list.append(result.id)
        assert result_list == test

        AuthorsPrefixSettings.query.delete()
        db.session.commit()
        result = WekoAuthors.get_id_prefix_all()
        assert result == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_id_prefix_all_with_community -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_id_prefix_all_with_community(self, authors_prefix_settings, db, community):
        authors_prefix_settings[0].communities = [community[0]]
        db.session.commit()

        results = WekoAuthors.get_id_prefix_all(community_ids=["community1"])
        assert results == [authors_prefix_settings[0]]

        AuthorsPrefixSettings.query.delete()
        db.session.commit()
        result = WekoAuthors.get_id_prefix_all(community_ids=["community1"])
        assert result == []


#     def get_scheme_of_id_prefix(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_scheme_of_id_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_scheme_of_id_prefix(self,authors,mocker,authors_prefix_settings,db):
        # with patch('weko_authors.api.WekoAuthors.get_scheme_of_id_prefix') as mock_func:
            # mock_func.side_effect = WekoAuthors.get_id_prefix_all()

        test = ['WEKO', 'ORCID', 'CiNii', 'KAKEN2', 'ROR']
        results = WekoAuthors.get_scheme_of_id_prefix()
        assert results == test
        with patch("weko_authors.api.WekoAuthors.get_id_prefix_all", return_value=[]):
            results = WekoAuthors.get_scheme_of_id_prefix()
            assert results == []



#     def get_affiliation_id_all(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_affiliation_id_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_affiliation_id_all(self,authors,mocker,authors_affiliation_settings,db):
        test = [1, 2, 3, 4]
        results = WekoAuthors.get_affiliation_id_all()
        result_list = []
        for result in results:
            result_list.append(result.id)
        assert result_list == test

        AuthorsAffiliationSettings.query.delete()
        db.session.commit()
        result = WekoAuthors.get_affiliation_id_all()
        assert result == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_affiliation_id_all_with_community -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_affiliation_id_all_with_community(self, authors_affiliation_settings, db, community):
        authors_affiliation_settings[0].communities = [community[0]]
        db.session.commit()

        results = WekoAuthors.get_affiliation_id_all(community_ids=["community1"])
        assert results == [authors_affiliation_settings[0]]

        AuthorsAffiliationSettings.query.delete()
        db.session.commit()
        result = WekoAuthors.get_affiliation_id_all(community_ids=["community1"])
        assert result == []


#     def get_scheme_of_affiliaiton_id(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_scheme_of_affiliaiton_id -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_scheme_of_affiliaiton_id(self,authors,mocker,authors_affiliation_settings,db):
        test = ['ISNI', 'GRID', 'Ringgold', 'kakenhi']
        results = WekoAuthors.get_scheme_of_affiliaiton_id()
        assert results == test
        with patch("weko_authors.api.WekoAuthors.get_affiliation_id_all", return_value=[]):
            results = WekoAuthors.get_scheme_of_affiliaiton_id()
            assert results == []


#     def test_get_affiliation_identifier_scheme_info(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_affiliation_identifier_scheme_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_affiliation_identifier_scheme_info(self,authors_affiliation_settings,db):
        test = {
            "1": {"scheme": "ISNI", "url": "http://www.isni.org/isni/##"},
            "2": {"scheme": "GRID", "url": "https://www.grid.ac/institutes/##"},
            "3": {"scheme": "Ringgold", "url": None},
            "4": {"scheme": "kakenhi", "url": None},
        }
        result = WekoAuthors.get_affiliation_identifier_scheme_info()
        assert result == test

        AuthorsAffiliationSettings.query.delete()
        db.session.commit()
        result = WekoAuthors.get_affiliation_identifier_scheme_info()
        assert result == {}


#     def prepare_export_prefix(cls, target_prefix, prefixes):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_prepare_export_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_prepare_export_prefix(self,authors_affiliation_settings,db,authors_prefix_settings):
        data = [
            ['ORCID', 'ORCID', 'https://orcid.org/##', None, None],
            ['CiNii', 'CiNii', 'https://ci.nii.ac.jp/author/##', None, None],
            ['KAKEN2', 'KAKEN2', 'https://nrid.nii.ac.jp/nrid/##', None, None],
            ['ROR', 'ROR', 'https://ror.org/##', None, None]
        ]
        tests = WekoAuthors.get_id_prefix_all()
        result = WekoAuthors.prepare_export_prefix('id_prefix', tests, 1)
        assert result == data

        data = [
            ['ISNI', 'ISNI', 'http://www.isni.org/isni/##', None, None, None],
            ['GRID', 'GRID', 'https://www.grid.ac/institutes/##', None, None, None],
            ['Ringgold', 'Ringgold', None, None, None, None],
            ['kakenhi', 'kakenhi', None, None, None, None]
        ]
        tests = WekoAuthors.get_affiliation_id_all()
        result = WekoAuthors.prepare_export_prefix('id_prefix', tests, 2)
        assert result == data

        data = [
            ['WEKO', 'WEKO', None, None],
            ['ORCID', 'ORCID', 'https://orcid.org/##', None],
            ['CiNii', 'CiNii', 'https://ci.nii.ac.jp/author/##', None],
            ['KAKEN2', 'KAKEN2', 'https://nrid.nii.ac.jp/nrid/##', None],
            ['ROR', 'ROR', 'https://ror.org/##', None]
        ]
        tests = WekoAuthors.get_id_prefix_all()
        result = WekoAuthors.prepare_export_prefix('affiliation_id', tests, 0)
        assert result == data

        test = []
        result = WekoAuthors.prepare_export_prefix('id_prefix', test, 1)
        assert result == []




#     def get_identifier_scheme_info(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_identifier_scheme_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_identifier_scheme_info(self,db,authors_prefix_settings):
        test = {
            "1":{"scheme":"WEKO","url":None},
            "2":{"scheme":"ORCID","url":"https://orcid.org/##"},
            "3":{"scheme":"CiNii","url":"https://ci.nii.ac.jp/author/##"},
            "4":{"scheme":"KAKEN2","url":"https://nrid.nii.ac.jp/nrid/##"},
            "5":{"scheme":"ROR","url":"https://ror.org/##"}
        }
        result = WekoAuthors.get_identifier_scheme_info()
        assert result == test

        AuthorsPrefixSettings.query.delete()
        db.session.commit()
        result = WekoAuthors.get_identifier_scheme_info()
        assert result == {}

    #     def get_by_range(cls, start_point, sum, with_deleted=True, with_gather=True):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_by_range -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_by_range(self, app, authors, mocker):
        result = WekoAuthors.get_by_range(0, 10, False, False)
        authors_copy = authors
        authors_copy.pop()
        assert authors_copy == result
        result = WekoAuthors.get_by_range(0, 10, True, False)
        assert authors == result
        result = WekoAuthors.get_by_range(0, 10, False, True)
        assert authors == result
        with pytest.raises(Exception):
            mocker.patch.object(Authors, 'id', return_value = None)
            WekoAuthors.get_by_range(0, 10, True, True)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_by_range_with_community -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_by_range_with_community(self, app, db, authors, community):
        authors[1].communities = [community[0]]
        authors[2].communities = [community[0]]
        authors[3].communities = [community[0]]
        db.session.commit()

        result = WekoAuthors.get_by_range(0, 10, False, False, community_ids=["community1"])
        authors_copy = authors.copy()
        authors_copy.pop(0)
        authors_copy.pop(2)
        assert authors_copy == result

        result = WekoAuthors.get_by_range(0, 10, True, False, community_ids=["community1"])
        assert authors_copy == result

        result = WekoAuthors.get_by_range(0, 10, False, True, community_ids=["community1"])
        assert authors_copy == result

        result = WekoAuthors.get_by_range(0, 10, True, True, community_ids=["community1"])
        authors_copy = authors.copy()
        authors_copy.pop(0)
        assert authors_copy == result

#     def get_pk_id_by_weko_id(cls, weko_id):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_pk_id_by_weko_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_pk_id_by_weko_id(self, app, mocker):
        data = {
            "hits": {
                "total": 1,
                "hits": [
                    {
                        "_source": {
                            "authorIdInfo": [
                                {"idType": "1", "authorId": "1111", "authorIdShowFlg": "true"},
                                {"idType": "2", "authorId": "1111", "authorIdShowFlg": "true"},
                            ],
                            "pk_id": "1",
                        },
                    },
                ],
            },
        }
        mock_indexer = RecordIndexer()
        mocker.patch("weko_authors.api.RecordIndexer",return_value=mock_indexer)
        mock_indexer.client = MockClient()
        mock_indexer.client.return_value=data
        result = WekoAuthors.get_pk_id_by_weko_id("1111")
        assert result == "1"
        result = WekoAuthors.get_pk_id_by_weko_id("-1")
        assert result == -1

#     def get_weko_id_by_pk_id(cls, pk_id):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_weko_id_by_pk_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_weko_id_by_pk_id(self, app, mocker, authors):
        result = WekoAuthors.get_weko_id_by_pk_id("1")
        assert result == "1"
        result = WekoAuthors.get_weko_id_by_pk_id("-1")
        assert result == None
        with pytest.raises(Exception):
            result = WekoAuthors.get_weko_id_by_pk_id("3")
        with pytest.raises(Exception):
            result = WekoAuthors.get_weko_id_by_pk_id("4")
        with pytest.raises(Exception):
            WekoAuthors.get_weko_id_by_pk_id("test_pk_id")


from sqlalchemy.exc import SQLAlchemyError

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsMappingMaxItem -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestWekoAuthorsMappingMaxItem:
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsMappingMaxItem::test_mapping_max_item_normal_case -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_mapping_max_item_normal_case(self, app, db, authors, mocker, community):
        mappings = [{'json_id': 'authorIdInfo', 'child': [{'json_id': 'idType'}, {'json_id': 'authorId'}]}]
        affiliation_mappings = {'json_id': 'affiliationInfo', 'child': [{'json_id': 'identifierInfo', 'child': [{'json_id': 'idType'}, {'json_id': 'affiliationId'}]}]}
        community_mappings = {"label_en": "Community", "label_jp": "コミュニティ", "json_id": "communityIds"}
        records_count = 2

        result_mappings, result_affiliation_mappings, result_community_mappings = WekoAuthors.mapping_max_item(mappings, affiliation_mappings, community_mappings, records_count)
        assert result_mappings[0]['max'] > 1
        assert 'max' in result_affiliation_mappings
        assert 'max' in result_community_mappings

        result_mappings, result_affiliation_mappings, result_community_mappings = WekoAuthors.mapping_max_item(mappings, None, None, records_count)
        assert result_mappings[0]['max'] > 1
        assert result_affiliation_mappings["max"]== [{'identifierInfo': 2, 'affiliationNameInfo': 1, 'affiliationPeriodInfo': 1}]
        assert result_community_mappings["max"] == 1

        # Authors is None
        mocker.patch("weko_authors.api.WekoAuthors.get_by_range",return_value=[])
        result_mappings, result_affiliation_mappings, result_community_mappings = WekoAuthors.mapping_max_item(mappings, None, community_mappings, records_count)
        assert result_mappings[0]["max"] == 1
        assert result_affiliation_mappings["max"] == []
        assert result_community_mappings["max"] == 1

        # Author dont has element
        author = {
            "authorIdInfo": [],
            "affiliationInfo": [{
                "affiliationNameInfo": [],
                "identifierInfo": []
                }]
        }
        mappings = [{'json_id': 'authorIdInfo', "max":0, 'child': [{'json_id': 'idType'}, {'json_id': 'authorId'}]}]
        mock_authors = [Authors(json=author)]
        mocker.patch("weko_authors.api.WekoAuthors.get_by_range",return_value=mock_authors)
        result_mappings, result_affiliation_mappings, result_community_mappings = WekoAuthors.mapping_max_item(mappings, None, community_mappings, records_count)

        assert result_mappings
        assert result_affiliation_mappings
        assert result_community_mappings

        # Author related communities
        authors[0].communities = [community[0]]
        authors[1].communities = [community[0], community[1]]
        mock_authors = [authors[0], authors[1]]
        mocker.patch("weko_authors.api.WekoAuthors.get_by_range",return_value=mock_authors)
        result_mappings, result_affiliation_mappings, result_community_mappings = WekoAuthors.mapping_max_item(mappings, None, community_mappings, records_count)
        assert result_mappings[0]['max'] > 1
        assert result_affiliation_mappings["max"]== [{'identifierInfo': 2, 'affiliationNameInfo': 1, 'affiliationPeriodInfo': 1}]
        assert result_community_mappings["max"] == 2


# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsMappingMaxItem::test_mapping_max_item_sqlalchemy_error -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_mapping_max_item_sqlalchemy_error(self, app, db, authors):
        with patch('weko_authors.api.WekoAuthors.get_records_count', side_effect=SQLAlchemyError):
            with pytest.raises(SQLAlchemyError):
                WekoAuthors.mapping_max_item(None, None, None, None)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsMappingMaxItem::test_mapping_max_item_other_exception -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_mapping_max_item_other_exception(self, app, db, authors):
        with patch('weko_authors.api.WekoAuthors.get_records_count', side_effect=Exception):
            with pytest.raises(Exception):
                WekoAuthors.mapping_max_item(None, None, None, None)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsMappingMaxItem::test_mapping_max_item_retry -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_mapping_max_item_retry(self, app, db, authors, mocker):
        mappings = [{'json_id': 'authorIdInfo', 'child': [{'json_id': 'idType'}, {'json_id': 'authorId'}]}]
        affiliation_mappings = {'json_id': 'affiliationInfo', 'child': [{'json_id': 'identifierInfo', 'child': [{'json_id': 'idType'}, {'json_id': 'affiliationId'}]}]}
        records_count = 2

        # Mock get_by_range to return a fixed value
        mocker.patch("weko_authors.api.WekoAuthors.get_by_range", return_value=authors)

        # Mock db.session.rollback and sleep to verify retry mechanism
        with patch('weko_authors.api.db.session.rollback') as mock_rollback, \
                patch('weko_authors.api.sleep') as mock_sleep:

            # First call to mapping_max_item raises SQLAlchemyError, second call succeeds
            with patch("weko_authors.api.WekoAuthors.get_records_count", side_effect=[SQLAlchemyError, 2]):
                result_mappings, result_affiliation_mappings, result_community_mappings = WekoAuthors.mapping_max_item(mappings, affiliation_mappings, None, None)

                # Verify that rollback and sleep were called
                mock_rollback.assert_called_once()
                mock_sleep.assert_called_once()

                # Verify the results
                assert result_mappings
                assert result_affiliation_mappings
                assert result_community_mappings

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsPrepareExport -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestWekoAuthorsPrepareExport:
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsPrepareExport::test_prepare_export_data_full_data -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_prepare_export_data_full_data(self, app, db, authors_prefix_settings, authors_affiliation_settings, authors2, mocker):
        res_header, res_label_en, res_label_jp, res_row_data = WekoAuthors.prepare_export_data(None, None, None, None, None, None, 0, 2)

        assert res_header
        assert res_label_en
        assert res_label_jp
        assert res_row_data == [['1', '1', 'テスト', '太郎', 'ja', 'familyNmAndNm', 'Y', 'ORCID', '1234', 'Y', 'CiNii', '12345', 'Y', 'test.taro@test.org', '', None, None, None, None, None, None, '', 'ja', 'Y', None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                                ['2', '2', 'test', 'smith', 'en', 'familyNmAndNm', 'Y', 'ORCID', '5678', 'Y', None, None, None, 'test.smith@test.org', '', 'ISNI', '1234', 'Y', 'GRID', '12345', 'Y', '', 'ja', 'Y', None, None, 'ISNI', '1234', 'Y', 'GRID', '12345', 'Y', '', 'ja', 'Y', None, None, None]]


    @pytest.fixture
    def mock_dependencies(self, app, db):
        """テストに必要な依存関係をモック化するフィクスチャ"""
        with patch('weko_authors.api.WekoAuthors.mapping_max_item') as mock_mapping_max_item, \
            patch('weko_authors.api.WekoAuthors.get_by_range') as mock_get_by_range, \
            patch('weko_authors.api.WekoAuthors.get_identifier_scheme_info') as mock_get_identifier_scheme_info, \
            patch('weko_authors.api.WekoAuthors.get_affiliation_identifier_scheme_info') as mock_get_affiliation_identifier_scheme_info, \
            patch('weko_authors.api.WekoAuthors.get_records_count') as mock_get_records_count:

            # 各モックのデフォルト設定
            mock_mapping_max_item.return_value = ([], {})
            mock_get_by_range.return_value = []
            mock_get_identifier_scheme_info.return_value = {}
            mock_get_affiliation_identifier_scheme_info.return_value = {}
            mock_get_records_count.return_value = 0

            yield {
                'mock_mapping_max_item': mock_mapping_max_item,
                'mock_get_by_range': mock_get_by_range,
                'mock_get_identifier_scheme_info': mock_get_identifier_scheme_info,
                'mock_get_affiliation_identifier_scheme_info': mock_get_affiliation_identifier_scheme_info,
                'mock_get_records_count': mock_get_records_count
            }


    # .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsPrepareExport::test_prepare_export_data_all_params_provided -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_prepare_export_data_all_params_provided(self, app, db, mock_dependencies):
        """
        正常系：全てのパラメータが適切に指定されている場合
        """
        # テストデータ設定
        mappings = [
            {'json_id': 'simple_field', 'label_en': 'Simple Field', 'label_jp': 'シンプルフィールド'},
            {'json_id': 'authorIdInfo', 'label_en': 'Author ID', 'label_jp': '著者ID', 'max': 2, 'child': [
                {'json_id': 'idType', 'label_en': 'ID Type', 'label_jp': 'ID種別'},
                {'json_id': 'authorId', 'label_en': 'Author ID', 'label_jp': '著者ID'}
            ]},
            {'json_id': 'masked_field', 'label_en': 'Masked Field', 'label_jp': 'マスクフィールド', 'mask': {'1': 'one', '2': 'two'}},
            {'json_id': 'weko_id', 'label_en': 'WEKO ID', 'label_jp': 'WEKO ID'}
        ]

        affiliation_mappings = {
            'json_id': 'affiliationInfo',
            'child': [
                {'json_id': 'identifierInfo', 'child': [
                    {'json_id': 'affiliationIdType', 'label_en': 'Affiliation ID Type', 'label_jp': '所属ID種別'}
                ]},
                {'json_id': 'affiliationNameInfo', 'child': [
                    {'json_id': 'affiliationName', 'label_en': 'Affiliation Name', 'label_jp': '所属名'},
                    {'json_id': 'language', 'label_en': 'Language', 'label_jp': '言語', 'mask': {'ja': '日本語', 'en': '英語'}}
                ]}
            ],
            'max': [
                {'identifierInfo': 1, 'affiliationNameInfo': 2, 'affiliationPeriodInfo': 0}
            ]
        }

        community_mappings = {
            "label_en": "Community", "label_jp": "コミュニティ", "json_id": "communityIds", "max": 1
        }

        authors = [
            MagicMock(json={
                'simple_field': 'simple value',
                'masked_field': '1',
                'authorIdInfo': [
                    {'idType': '1', 'authorId': 'weko123'},
                    {'idType': '2', 'authorId': 'orcid456'}
                ],
                'affiliationInfo': [
                    {
                        'identifierInfo': [
                            {'affiliationIdType': '1', 'affiliationId': 'aff123'}
                        ],
                        'affiliationNameInfo': [
                            {'affiliationName': 'University A', 'language': 'en'},
                            {'affiliationName': '大学A', 'language': 'ja'}
                        ]
                    }
                ]
            }, communities=[MagicMock(id="community1")])
        ]

        schemes = {
            '1': {'scheme': 'WEKO', 'url': 'http://weko.example.com'},
            '2': {'scheme': 'ORCID', 'url': 'http://orcid.org'}
        }

        aff_schemes = {
            '1': {'scheme': 'ROR', 'url': 'http://ror.org'}
        }

        start = 0
        size = 10

        # 関数実行
        result = WekoAuthors.prepare_export_data(
            mappings, affiliation_mappings, community_mappings, authors, schemes, aff_schemes, start, size
        )

        # 結果検証
        row_header, row_label_en, row_label_jp, row_data = result

        # ヘッダーと表示ラベルの検証
        assert row_header[0].startswith('#')
        assert row_label_en[0].startswith('#')
        assert row_label_jp[0].startswith('#')

        # データ行の検証
        assert len(row_data) == 1  # 1件の著者データ
        author_row = row_data[0]

        # 単純フィールドが正しく処理されていることを確認
        assert 'simple value' in author_row

        # マスク処理が正しく適用されていることを確認
        assert 'one' in author_row

        # WEKO IDが正しく抽出されていることを確認
        assert 'weko123' in author_row

        # IDスキームが正しく変換されていることを確認
        assert 'ORCID' in author_row

        # 所属情報が正しく処理されていることを確認
        assert 'University A' in author_row
        assert '英語' in author_row or 'en' in author_row

        # コミュニティ情報が正しく処理されていることを確認
        assert 'community1' in author_row

        # モック関数が呼び出されていないことを確認（すべてのパラメータが提供されているため）
        mock_dependencies['mock_mapping_max_item'].assert_not_called()
        mock_dependencies['mock_get_by_range'].assert_not_called()
        mock_dependencies['mock_get_identifier_scheme_info'].assert_not_called()
        mock_dependencies['mock_get_affiliation_identifier_scheme_info'].assert_not_called()


    def test_prepare_export_data_auto_fetch_params(self, app, db, mock_dependencies):
        """
        正常系：パラメータが一部指定されていない場合の自動補完
        """
        # モックの準備
        test_mappings = [{'json_id': 'test_field', 'label_en': 'Test', 'label_jp': 'テスト'}]
        test_aff_mappings = {'json_id': 'affiliationInfo', 'max': [], 'child': []}
        test_com_mappings = {'json_id': 'communityIds', 'label_en': 'Community', 'label_jp': 'コミュニティ'}
        test_authors = [MagicMock(json={'test_field': 'test value'})]

        mock_dependencies['mock_mapping_max_item'].return_value = (test_mappings, test_aff_mappings, test_com_mappings)
        mock_dependencies['mock_get_by_range'].return_value = test_authors
        mock_dependencies['mock_get_identifier_scheme_info'].return_value = {'1': {'scheme': 'TEST'}}
        mock_dependencies['mock_get_affiliation_identifier_scheme_info'].return_value = {'1': {'scheme': 'TEST_AFF'}}

        # 関数実行（すべてNoneで渡す）
        result = WekoAuthors.prepare_export_data(None, None, None, None, None, None, 0, 10)

        # 結果検証
        row_header, row_label_en, row_label_jp, row_data = result

        # 各モックが正しく呼び出されたことを確認
        mock_dependencies['mock_mapping_max_item'].assert_called_once()
        mock_dependencies['mock_get_by_range'].assert_called_once_with(0, 10, False, False)
        mock_dependencies['mock_get_identifier_scheme_info'].assert_called_once()
        mock_dependencies['mock_get_affiliation_identifier_scheme_info'].assert_called_once()

        # 返されたデータが期待通りであることを確認
        assert '#test_field' in row_header[0]
        assert '#Test' in row_label_en[0]
        assert '#テスト' in row_label_jp[0]
        assert row_data[0][0] == 'test value'


    def test_prepare_export_data_different_mapping_types(self, app, db, mock_dependencies):
        """
        正常系：異なる種類のmappingパターンの処理
        """
        # 異なるタイプのマッピングを含むテストデータを設定
        mappings = [
            # childなしマッピング
            {'json_id': 'simple_field', 'label_en': 'Simple Field', 'label_jp': 'シンプルフィールド'},
            # childありマッピング
            {'json_id': 'complex_field', 'label_en': 'Complex Field', 'label_jp': '複合フィールド', 'max': 2, 'child': [
                {'json_id': 'sub_field1', 'label_en': 'Sub Field 1', 'label_jp': 'サブフィールド1'},
                {'json_id': 'sub_field2', 'label_en': 'Sub Field 2', 'label_jp': 'サブフィールド2'}
            ]}
        ]

        affiliation_mappings = {
            'json_id': 'affiliationInfo',
            'child': [],
            'max': []
        }

        community_mappings = {
            "label_en": "Community", "label_jp": "コミュニティ", "json_id": "communityIds",
        }

        authors = [
            MagicMock(json={
                'simple_field': 'simple value',
                'complex_field': [
                    {'sub_field1': 'value1_1', 'sub_field2': 'value1_2'},
                    {'sub_field1': 'value2_1', 'sub_field2': 'value2_2'}
                ],
                'affiliationInfo': []
            })
        ]

        # 関数実行
        result = WekoAuthors.prepare_export_data(
            mappings, affiliation_mappings, community_mappings, authors, {}, {}, 0, 10
        )

        # 結果検証
        row_header, row_label_en, row_label_jp, row_data = result

        # ヘッダーに期待される項目が含まれていることを確認
        assert any('simple_field' in header for header in row_header)
        assert any('complex_field[0].sub_field1' in header for header in row_header)
        assert any('complex_field[1].sub_field2' in header for header in row_header)

        # ラベルに期待される項目が含まれていることを確認
        assert any('Simple Field' in label for label in row_label_en)
        assert any('Sub Field 1[0]' in label for label in row_label_en)
        assert any('サブフィールド2[1]' in label for label in row_label_jp)

        # データ行の値が正しいことを確認
        author_row = row_data[0]
        assert 'simple value' in author_row
        assert 'value1_1' in author_row
        assert 'value2_2' in author_row


    def test_prepare_export_data_author_id_info(self, app, db, mock_dependencies):
        """
        正常系：authorIdInfoの特殊処理
        """
        # authorIdInfoを含むテストデータを設定
        mappings = [
            {'json_id': 'authorIdInfo', 'label_en': 'Author ID', 'label_jp': '著者ID', 'max': 2, 'child': [
                {'json_id': 'idType', 'label_en': 'ID Type', 'label_jp': 'ID種別'},
                {'json_id': 'authorId', 'label_en': 'Author ID', 'label_jp': '著者ID'}
            ]}
        ]

        affiliation_mappings = {
            'json_id': 'affiliationInfo',
            'child': [],
            'max': []
        }

        community_mappings = {
            "label_en": "Community", "label_jp": "コミュニティ", "json_id": "communityIds",
        }

        authors = [
            MagicMock(json={
                'authorIdInfo': [
                    {'idType': '1', 'authorId': 'weko123'},
                    {'idType': '2', 'authorId': 'orcid456'},
                    {'idType': '3', 'authorId': 'scopus789'}
                ],
                'affiliationInfo': []
            })
        ]

        schemes = {
            '1': {'scheme': 'WEKO', 'url': 'http://weko.example.com'},
            '2': {'scheme': 'ORCID', 'url': 'http://orcid.org'},
            '3': {'scheme': 'Scopus', 'url': 'http://scopus.com'}
        }

        # 関数実行
        result = WekoAuthors.prepare_export_data(
            mappings, affiliation_mappings, community_mappings, authors, schemes, {}, 0, 10
        )

        # 結果検証
        row_header, row_label_en, row_label_jp, row_data = result

        # IDが正しく処理されていることを確認
        author_row = row_data[0]

        # WEKO ID（index 0）がスキップされ、index 1と2のデータが処理されていることを確認
        assert 'ORCID' in author_row
        assert 'orcid456' in author_row
        assert 'Scopus' in author_row
        assert 'scopus789' in author_row


    @pytest.fixture
    def sample_mappings(self):
        """Fixture for sample mappings."""
        return [
            {
                'json_id': 'familyName',
                'label_en': 'Family Name',
                'label_jp': '姓'
            },
            {
                'json_id': 'firstName',
                'label_en': 'First Name',
                'label_jp': '名'
            },
            {
                'json_id': 'gender',
                'label_en': 'Gender',
                'label_jp': '性別',
                'mask': {'m': 'Male', 'f': 'Female', 'o': 'Other'}
            },
            {
                'json_id': 'authorIdInfo',
                'label_en': 'Author ID',
                'label_jp': '著者ID',
                'max': 2,
                'child': [
                    {
                        'json_id': 'idType',
                        'label_en': 'ID Type',
                        'label_jp': 'ID種別'
                    },
                    {
                        'json_id': 'authorId',
                        'label_en': 'Author ID',
                        'label_jp': '著者ID'
                    }
                ]
            },
            {
                'json_id': 'weko_id',
                'label_en': 'WEKO ID',
                'label_jp': 'WEKO ID'
            }
        ]


    @pytest.fixture
    def sample_affiliation_mappings(self):
        """Fixture for sample affiliation mappings."""
        return {
            'json_id': 'affiliationInfo',
            'child': [
                {
                    'json_id': 'identifierInfo',
                    'child': [
                        {
                            'json_id': 'affiliationIdType',
                            'label_en': 'Affiliation ID Type',
                            'label_jp': '所属ID種別'
                        },
                        {
                            'json_id': 'affiliationId',
                            'label_en': 'Affiliation ID',
                            'label_jp': '所属ID'
                        }
                    ]
                },
                {
                    'json_id': 'affiliationNameInfo',
                    'child': [
                        {
                            'json_id': 'language',
                            'label_en': 'Language',
                            'label_jp': '言語',
                            'mask': {'en': 'English', 'ja': 'Japanese'}
                        },
                        {
                            'json_id': 'affiliationName',
                            'label_en': 'Affiliation Name',
                            'label_jp': '所属名'
                        }
                    ]
                }
            ],
            'max': [
                {
                    'identifierInfo': 2,
                    'affiliationNameInfo': 2,
                    'affiliationPeriodInfo': 1
                }
            ]
        }

    @pytest.fixture
    def sample_community_mappings(self):
        """Fixture for sample community mappings."""
        return {
            "label_en": "Community",
            "label_jp": "コミュニティ",
            "json_id": "communityIds",
            "max": 1
        }

    @pytest.fixture
    def sample_authors(self):
        """Fixture for sample authors."""
        return [
            MagicMock(
                json={
                    'familyName': 'Smith',
                    'firstName': 'John',
                    'gender': 'm',
                    'authorIdInfo': [
                        {'idType': '2', 'authorId': 'ORCID001'}
                    ],
                    'affiliationInfo': [
                        {
                            'identifierInfo': [
                                {'affiliationIdType': '1', 'affiliationId': 'UNI001'},
                                {'affiliationIdType': '2', 'affiliationId': 'GRID001'}
                            ],
                            'affiliationNameInfo': [
                                {'language': 'en', 'affiliationName': 'University A'},
                                {'language': 'ja', 'affiliationName': '大学A'}
                            ]
                        }
                    ]
                }
            )
        ]


    @pytest.fixture
    def sample_schemes(self):
        """Fixture for sample ID schemes."""
        return {
            '1': {'scheme': 'WEKO', 'url': 'https://weko.org'},
            '2': {'scheme': 'ORCID', 'url': 'https://orcid.org'}
        }


    @pytest.fixture
    def sample_aff_schemes(self):
        """Fixture for sample affiliation ID schemes."""
        return {
            '1': {'scheme': 'University ID', 'url': 'https://university.org'},
            '2': {'scheme': 'GRID', 'url': 'https://grid.ac'}
        }


    def test_mask_processing(self, app, db, sample_mappings, sample_affiliation_mappings, sample_community_mappings,
                             sample_authors, sample_schemes, sample_aff_schemes):
        """Test case 7: mask processing is correctly applied."""
        row_header, row_label_en, row_label_jp, row_data = WekoAuthors.prepare_export_data(
            sample_mappings,
            sample_affiliation_mappings,
            sample_community_mappings,
            sample_authors,
            sample_schemes,
            sample_aff_schemes,
            0,
            10
        )

        # Check if mask processing was applied for gender
        assert row_data[0][2] == 'Male'  # The gender 'm' should be masked to 'Male'

        # Check if mask processing was applied for affiliation language
        # Finding the index for affiliationInfo[0].affiliationNameInfo[0].language
        language_index = row_header.index('affiliationInfo[0].affiliationNameInfo[0].language')
        assert row_data[0][language_index] == 'English'  # 'en' should be masked to 'English'


    def test_affiliation_info_processing(self, app, db, sample_mappings, sample_affiliation_mappings, sample_community_mappings,
                                         sample_authors, sample_schemes, sample_aff_schemes):
        """Test case 8: affiliation information is correctly processed."""
        row_header, row_label_en, row_label_jp, row_data = WekoAuthors.prepare_export_data(
            sample_mappings,
            sample_affiliation_mappings,
            sample_community_mappings,
            sample_authors,
            sample_schemes,
            sample_aff_schemes,
            0,
            10
        )

        # Check if affiliationIdType is correctly processed with scheme lookup
        # Find index for affiliationInfo[0].identifierInfo[0].affiliationIdType
        aff_id_type_index = row_header.index('affiliationInfo[0].identifierInfo[0].affiliationIdType')
        assert row_data[0][aff_id_type_index] == 'University ID'

        # Check if affiliationId is correctly included
        aff_id_index = row_header.index('affiliationInfo[0].identifierInfo[0].affiliationId')
        assert row_data[0][aff_id_index] == 'UNI001'

        # Check if affiliationName is correctly included
        aff_name_index = row_header.index('affiliationInfo[0].affiliationNameInfo[0].affiliationName')
        assert row_data[0][aff_name_index] == 'University A'

        # Check if headers and labels are correctly formatted for nested structure
        assert 'affiliationInfo[0].identifierInfo[0].affiliationIdType' in row_header
        assert 'Affiliation ID Type[0][0]' in row_label_en
        assert '所属ID種別[0][0]' in row_label_jp


    @patch('weko_authors.api.WekoAuthors.mapping_max_item')
    @patch('weko_authors.api.WekoAuthors.get_by_range')
    @patch('weko_authors.api.WekoAuthors.get_identifier_scheme_info')
    @patch('weko_authors.api.WekoAuthors.get_affiliation_identifier_scheme_info')
    def test_affiliation_info_missing_data(self, mock_aff_scheme, mock_scheme, mock_get, mock_map,
                                        sample_mappings, sample_affiliation_mappings, sample_community_mappings,
                                        sample_schemes, sample_aff_schemes, app, db):
        """Test case 8: handling of missing affiliation data."""
        # Author with partial affiliation data
        authors_with_missing = [
            MagicMock(
                json={
                    'familyName': 'Doe',
                    'firstName': 'Jane',
                    'gender': 'f',
                    'authorIdInfo': [
                        {'idType': '1', 'authorId': 'WEKO002'}
                    ],
                    'affiliationInfo': [
                        {
                            # Missing identifierInfo
                            'affiliationNameInfo': [
                                {'language': 'en', 'affiliationName': 'University B'}
                                # Only one name, not two as in max
                            ]
                        }
                    ]
                }
            )
        ]

        # Configure mocks to return our test data
        mock_map.return_value = (sample_mappings, sample_affiliation_mappings, sample_community_mappings)
        mock_get.return_value = authors_with_missing
        mock_scheme.return_value = sample_schemes
        mock_aff_scheme.return_value = sample_aff_schemes

        row_header, row_label_en, row_label_jp, row_data = WekoAuthors.prepare_export_data(
            None,  # Let the method fetch mappings
            None,  # Let the method fetch affiliation mappings
            None,  # Let the method fetch community mappings
            None,  # Let the method fetch authors
            None,  # Let the method fetch schemes
            None,  # Let the method fetch affiliation schemes
            0,
            10
        )

        # Check if missing affiliationIdType is correctly handled as None
        aff_id_type_index = row_header.index('affiliationInfo[0].identifierInfo[0].affiliationIdType')
        assert row_data[0][aff_id_type_index] is None

        # Check if missing second affiliationNameInfo is correctly handled as None
        aff_name_index = row_header.index('affiliationInfo[0].affiliationNameInfo[1].affiliationName')
        assert row_data[0][aff_name_index] is None

        # Verify all expected headers are present
        assert 'affiliationInfo[0].identifierInfo[1].affiliationId' in row_header
        assert 'affiliationInfo[0].affiliationNameInfo[0].language' in row_header

        # Verify headers and labels match
        assert len(row_header) == len(row_label_en)
        assert len(row_header) == len(row_label_jp)

#     def get_used_scheme_of_id_prefix(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsGetUsedSchemeOfIdPrefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestWekoAuthorsGetUsedSchemeOfIdPrefix:
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_used_scheme_of_id_prefix_1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_used_scheme_of_id_prefix_1(self, app, authors, authors_prefix_settings):
        result = WekoAuthors.get_used_scheme_of_id_prefix()
        assert result == (['ORCID', 'CiNii'], {1: 'WEKO', 2: 'ORCID', 3: 'CiNii', 4: 'KAKEN2', 5: 'ROR'})

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_used_scheme_of_id_prefix_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_used_scheme_of_id_prefix_2(self, app, authors_prefix_settings):
        result = WekoAuthors.get_used_scheme_of_id_prefix()
        assert result == ([], {1: 'WEKO', 2: 'ORCID', 3: 'CiNii', 4: 'KAKEN2', 5: 'ROR'})

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_used_scheme_of_id_prefix_3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_used_scheme_of_id_prefix_3(self, app, authors):
        result = WekoAuthors.get_used_scheme_of_id_prefix()
        assert result == ([None], {})

#     def get_used_scheme_of_affiliation_id(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthorsGetUsedSchemeOfAffiliationId -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestWekoAuthorsGetUsedSchemeOfAffiliationId:
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_used_scheme_of_affiliation_id_1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_used_scheme_of_affiliation_id_1(self, app, authors, authors_affiliation_settings):
        result = WekoAuthors.get_used_scheme_of_affiliation_id()
        assert result == (['ISNI', 'GRID'], {1: 'ISNI', 2: 'GRID', 3: 'Ringgold', 4: 'kakenhi'})

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_used_scheme_of_affiliation_id_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_used_scheme_of_affiliation_id_2(self, app, authors_affiliation_settings):
        result = WekoAuthors.get_used_scheme_of_affiliation_id()
        assert result == ([], {1: 'ISNI', 2: 'GRID', 3: 'Ringgold', 4: 'kakenhi'})

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_used_scheme_of_affiliation_id_3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_get_used_scheme_of_affiliation_id_3(self, app, authors):
        result = WekoAuthors.get_used_scheme_of_affiliation_id()
        assert result == ([None], {})
