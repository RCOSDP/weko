from mock import patch
import pytest
from weko_authors.api import WekoAuthors
from weko_authors.models import Authors
from invenio_indexer.api import RecordIndexer

# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

class MockClient():
    def __init__(self):
        self.index_ = self.MockIndex()
        self.return_value=""
    def index(self,index,doc_type,body):
        return self.index_
    def delete(self,index,doc_type,id):
        pass
    def set_return(self,value):
        self.return_value=value
    def search(self,index,doc_type,body):
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
    def test_create(self,app,db,mocker):
        mocker.patch("weko_authors.api.Authors.get_sequence",return_value=1)
        record_indexer = RecordIndexer()
        record_indexer.client = MockClient()
        record_indexer.client.index("","","").set("_id",1)
        mocker.patch("weko_authors.api.RecordIndexer",return_value=record_indexer)
        data = {
            "authorIdInfo":[]
        }
        WekoAuthors.create(data)
        test ='{"authorIdInfo": [{"authorId": "1", "authorIdShowFlg": "true", "idType": "1"}], "gather_flg": 0, "id": 1, "pk_id": "1"}'
        result = Authors.query.filter_by(id=1).one()
        assert result.id == 1
        assert result.json == test
        
        with patch("weko_authors.api.db.session.add",side_effect=Exception("test_error")):
            data = {
                "authorIdInfo":[]
            }
            with pytest.raises(Exception):
                result = WekoAuthors.create(data)
            
        
            record_indexer = RecordIndexer()
            record_indexer.client = MockClient()
            mocker.patch("weko_authors.api.RecordIndexer",return_value=record_indexer)
            data = {
                "authorIdInfo":[]
            }
            with pytest.raises(Exception):
                result = WekoAuthors.create(data)
            
#     def update(cls, author_id, data):
#         def update_es_data(data):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update(self,app,authors,mocker):
        author_id=1
        data={"is_deleted":False}
        
        record_indexer = RecordIndexer()
        record_indexer.client = MockClient()
        record_indexer.client.set_return({"hits":{"total":1,"hits":[{"_id":1}]}})
        mocker.patch("weko_authors.api.RecordIndexer",return_value=record_indexer)
        WekoAuthors.update(author_id,data)
        
        data={"is_deleted":True}
        record_indexer.client.index("","","").set("_id",1)
        record_indexer.client.set_return({"hits":{"total":1,"hits":[{"_id":None}]}})
        mocker.patch("weko_authors.api.RecordIndexer",return_value=record_indexer)
        WekoAuthors.update(author_id,data)
        
        with patch("weko_authors.api.db.session.merge",side_effect=Exception):
            record_indexer.client.set_return({"hits":{"total":1,"hits":[{"_id":1}]}})
            mocker.patch("weko_authors.api.RecordIndexer",return_value=record_indexer)
            with pytest.raises(Exception):
                WekoAuthors.update(author_id,data)
            
#     def get_all(cls, with_deleted=True, with_gather=True):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_all(self,app,authors):
        result = WekoAuthors.get_all()
        assert authors
        result = WekoAuthors.get_all(False,False)
        print("r:{}".format(result))
        assert authors
#     def get_author_for_validation(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_author_for_validation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_author_for_validation(self,authors,mocker):
        mocker.patch("weko_authors.api.WekoAuthors.get_all",return_value=authors)
        
        authors_result, external_result = WekoAuthors.get_author_for_validation()
        assert authors_result == {"1":True,"2":True}
        assert external_result == {"2":{"1234":["1"],"5678":["2"]}}

#     def get_identifier_scheme_info(cls):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_identifier_scheme_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_identifier_scheme_info(self,db,prefix_settings):
        result = WekoAuthors.get_identifier_scheme_info()
        assert result == {"1":{"scheme":"WEKO","url":None},"2":{"scheme":"ORCID","url":"https://orcid.org/##"}}
        
        for name in prefix_settings:
            db.session.delete(prefix_settings[name])
        db.session.commit()
        result = WekoAuthors.get_identifier_scheme_info()
        assert result == {}
        
#     def prepare_export_data(cls, mappings, authors, schemes):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_api.py::TestWekoAuthors::test_get_identifier_scheme_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_prepare_export_data(self,authors,mocker):
        mocker.patch("weko_authors.api.WekoAuthors.get_all",return_value=authors)
        scheme_info={"1":{"scheme":"WEKO","url":None},"2":{"scheme":"ORCID","url":"https://orcid.org/##"}}
        mocker.patch("weko_authors.api.WekoAuthors.get_identifier_scheme_info",return_value=scheme_info)
        