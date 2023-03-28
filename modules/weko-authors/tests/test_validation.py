
from mock import patch

from weko_authors.contrib.validation import (
    validate_by_extend_validator,
    validate_required,
    validate_map,
    validate_identifier_scheme,
    validate_external_author_identifier
)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp


# def validate_by_extend_validator(values=[], validator={}):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_by_extend_validator -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_by_extend_validator():
    values = [{'key': 'authorIdInfo[0].idType', 'reduce_keys': ['authorIdInfo', 0, 'idType'], 'value': 'ORCID'}]
    validator = {
        'class_name': 'weko_authors.contrib.validation',
        'func_name': 'validate_identifier_scheme'
    }
    with patch("weko_authors.contrib.validation.validate_identifier_scheme", return_value=["test_error"]):
        result = validate_by_extend_validator(values, validator)
        assert result == ["test_error"]
    
    # values and validator is none
    result = validate_by_extend_validator()
    assert result == []

# def validate_required(item, values=[], required={}):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_required -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_required():
    item = {
        'authorIdInfo': [
            {'idType': 'ORCID', 
             'authorId': '1234', 
             'authorIdShowFlg': 'Y'}
            ], 
    }
    values = [{"key":"authorIdInfo[0].authorId","reduce_keys":["authorIdInfo",0,"authorId"],"value":"1234"}]
    required = {
        'if': ['authorId']
    }
    result = validate_required(item, values, required)
    assert result == []
    
    # not exist required value
    values = [{"key":"authorIdInfo[0].authorId","reduce_keys":["authorIdInfo",0,"authorId"],"value":""}]
    result = validate_required(item, values, required)
    assert result == ["authorIdInfo[0].authorId"]
    
    # is not if_cond
    result = validate_required(item, values, required={})
    assert result == []
    
    
# def validate_map(values=[], _map=[]):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_map -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_map():
    
    map = ['ja', 'ja-Kana', 'en', 'fr',
                'it', 'de', 'es', 'zh-cn', 'zh-tw',
                'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']
    # value in map
    values = [{"key":"authorNameInfo[0].language","reduce_keys":["authorNameInfo",0,"language"],"value":"ja"}]
    result = validate_map(values, map)
    assert result == []
    
    # value not in map
    values = [{"key":"authorNameInfo[0].language","reduce_keys":["authorNameInfo",0,"language"],"value":"none"}]
    result = validate_map(values, map)
    assert result == ["authorNameInfo[0].language"]
    
    # values, _map is none
    result = validate_map(values, _map=[])
    assert result == []


# def validate_identifier_scheme(values=[]):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_identifier_scheme -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_identifier_scheme(authors_prefix_settings):
    # values is none
    result = validate_identifier_scheme()
    assert result == []
    
    # value is in schemes
    values = [{"key":"authorIdInfo[0].idType","reduce_keys":["authorIdInfo",0,"idType"],"value":"WEKO"}]
    result = validate_identifier_scheme(values)
    assert result == []
    
    # value is not in schemes
    values = [{"key":"authorIdInfo[0].idType","reduce_keys":["authorIdInfo",0,"idType"],"value":"NON-EXIST-SCHEME"}]
    result = validate_identifier_scheme(values)
    assert result == ["Specified Identifier Scheme 'NON-EXIST-SCHEME' does not exist."]

# def validate_external_author_identifier(item, values=[],
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_external_author_identifier -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_external_author_identifier(authors):
    item = {
        "pk_id": "1",
        "authorIdInfo": [
            { "authorId": "1", "authorIdShowFlg": "true", "idType": "1" },
            { "authorId": "1234", "authorIdShowFlg": "true", "idType": "2" }
        ]
    }
    values = [{"key":"authorIdInfo[1].idType","reduce_keys":["authorIdInfo",1,"idType"],"value":"ORCID"}]
    existed_external_authors_id = {"2":{"1234":["1"]}}
    result = validate_external_author_identifier(item, values, existed_external_authors_id)
    assert result == None
    
    # authorId is none
    item = {
        "pk_id": "1",
        "authorIdInfo": [
            { "authorId": "1", "authorIdShowFlg": "true", "idType": "1" },
            { "authorId": "", "authorIdShowFlg": "true", "idType": "2" }
        ]
    }
    values = [{"key":"authorIdInfo[1].idType","reduce_keys":["authorIdInfo",1,"idType"],"value":"ORCID"}]
    existed_external_authors_id = {"2":{"":["1"]}}
    result = validate_external_author_identifier(item, values, existed_external_authors_id)
    assert result == None
    
    # pk_id not in weko_ids
    item = {
        "pk_id": "1",
        "authorIdInfo": [
            { "authorId": "2", "authorIdShowFlg": "true", "idType": "1" },
            { "authorId": "1234", "authorIdShowFlg": "true", "idType": "2" }
        ]
    }
    values = [{"key":"authorIdInfo[1].idType","reduce_keys":["authorIdInfo",1,"idType"],"value":"ORCID"}]
    existed_external_authors_id = {"2":{"1234":["2"]}}
    result = validate_external_author_identifier(item, values, existed_external_authors_id)
    assert result == "External author identifier exists in DB.<br/>1234"
