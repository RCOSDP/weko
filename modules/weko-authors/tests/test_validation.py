
from mock import patch
import pytest
from weko_authors.contrib.validation import (
    validate_by_extend_validator,
    validate_required,
    validate_map,
    validate_identifier_scheme,
    validate_external_author_identifier,
    validate_affiliation_period_end,
    validate_digits_for_wekoid,
    validate_affiliation_identifier_scheme,
    validate_affiliation_period_start,
    check_weko_id_is_exits_for_import
)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp


# def validate_by_extend_validator(values=[], validator={}):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_by_extend_validator -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_by_extend_validator():
    item = 'item'
    values = [{'key': 'authorIdInfo[0].idType', 'reduce_keys': ['authorIdInfo', 0, 'idType'], 'value': 'ORCID'}]
    validator = {
        'class_name': 'weko_authors.contrib.validation',
        'func_name': 'validate_identifier_scheme'
    }
    with patch("weko_authors.contrib.validation.validate_identifier_scheme", return_value=["test_error"]):
        result = validate_by_extend_validator(item, values, validator)
        assert result == ["test_error"]
    
    # values and validator is none
    result = validate_by_extend_validator(item)
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
    item = 'item'
    result = validate_identifier_scheme(item)
    assert result == []
    
    # value is in schemes
    item = 'item'
    values = [{"key":"authorIdInfo[0].idType","reduce_keys":["authorIdInfo",0,"idType"],"value":"WEKO"}]
    result = validate_identifier_scheme(item, values)
    assert result == []
    
    # value is not in schemes
    item = 'item'
    values = [{"key":"authorIdInfo[0].idType","reduce_keys":["authorIdInfo",0,"idType"],"value":"NON-EXIST-SCHEME"}]
    result = validate_identifier_scheme(item, values)
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

# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::TestValidateAffiliationPeriodEnd -vv -s --cov-branch --cov-report=html --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestValidateAffiliationPeriodEnd:
    """validate_affiliation_period_end関数のテストクラス"""

    @pytest.fixture
    def error_messages(self):
        """エラーメッセージを返すフィクスチャ"""
        return {
            'format_error': "External Affiliation Period must be in the format: yyyy-MM-dd, blank. {}",
            'period_error': "Period end must be after Period start."
        }

    def test_empty_values(self):
        """
        正常系
        条件：値のリストが空
        入力：item={}, values=[]
        期待結果：空のエラーリスト
        """
        item = {}
        values = []
        result = validate_affiliation_period_end(item, values)
        assert result == []

    def test_period_end_none(self):
        """
        正常系
        条件：periodEndが空の場合
        入力：item={}, values=[{'value': None, 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：空のエラーリスト
        """
        item = {}
        values = [{'value': None, 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert result == []

    def test_period_end_empty_string(self):
        """
        正常系
        条件：periodEndが空文字の場合
        入力：item={}, values=[{'value': '', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：空のエラーリスト
        """
        item = {}
        values = [{'value': '', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert result == []

    def test_period_end_invalid_format(self):
        """
        異常系
        条件：periodEndのフォーマットが不正な場合
        入力：item={}, values=[{'value': '2023/01/01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：フォーマットエラーメッセージを含むリスト
        """
        item = {}
        values = [{'value': '2023/01/01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert len(result) == 1
        assert "External Affiliation Period must be in the format: yyyy-MM-dd, blank. 2023/01/01" in result

    def test_period_end_valid_format_period_start_none(self):
        """
        正常系
        条件：periodEndのフォーマットが正しく、periodStartがNoneの場合
        入力：item={'affiliations': [{'periodStart': None}]}, values=[{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：空のエラーリスト
        """
        item = {'affiliations': [{'periodStart': None}]}
        values = [{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert result == []

    def test_period_end_valid_format_period_start_empty(self):
        """
        正常系
        条件：periodEndのフォーマットが正しく、periodStartが空文字の場合
        入力：item={'affiliations': [{'periodStart': ''}]}, values=[{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：空のエラーリスト
        """
        item = {'affiliations': [{'periodStart': ''}]}
        values = [{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert result == []

    def test_period_start_invalid_format(self):
        """
        異常系
        条件：periodEndのフォーマットが正しく、periodStartのフォーマットが不正な場合
        入力：item={'affiliations': [{'periodStart': '2023/01/01'}]}, values=[{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：フォーマットエラーメッセージを含むリスト
        """
        item = {'affiliations': [{'periodStart': '2023/01/01'}]}
        values = [{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert len(result) == 1
        assert "External Affiliation Period must be in the format: yyyy-MM-dd, blank. 2023-01-01" in result

    def test_period_end_before_period_start(self):
        """
        異常系
        条件：periodEndがperiodStartより前の日付の場合
        入力：item={'affiliations': [{'periodStart': '2023-02-01'}]}, values=[{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：期間エラーメッセージを含むリスト
        """
        item = {'affiliations': [{'periodStart': '2023-02-01'}]}
        values = [{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert len(result) == 1
        assert "Period end must be after Period start." in result

    def test_period_end_equal_period_start(self):
        """
        正常系
        条件：periodEndとperiodStartが同じ日付の場合
        入力：item={'affiliations': [{'periodStart': '2023-01-01'}]}, values=[{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：空のエラーリスト（同日は許容される）
        """
        item = {'affiliations': [{'periodStart': '2023-01-01'}]}
        values = [{'value': '2023-01-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert result == []

    def test_period_end_after_period_start(self):
        """
        正常系
        条件：periodEndがperiodStartより後の日付の場合
        入力：item={'affiliations': [{'periodStart': '2023-01-01'}]}, values=[{'value': '2023-02-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        期待結果：空のエラーリスト
        """
        item = {'affiliations': [{'periodStart': '2023-01-01'}]}
        values = [{'value': '2023-02-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']}]
        result = validate_affiliation_period_end(item, values)
        assert result == []

    def test_multiple_values(self):
        """
        正常系と異常系の混合
        条件：複数の値がある場合
        入力：複数の値を持つitem, values
        期待結果：エラーがある項目のみエラーメッセージを含むリスト
        """
        item = {
            'affiliations': [
                {'periodStart': '2023-01-01'},
                {'periodStart': '2023-03-01'},
                {'periodStart': '2023/05/01'},
                {'periodStart': None}
            ]
        }
        values = [
            {'value': '2023-02-01', 'reduce_keys': ['affiliations', 0, 'periodEnd']},
            {'value': '2023-02-01', 'reduce_keys': ['affiliations', 1, 'periodEnd']},
            {'value': '2023-06-01', 'reduce_keys': ['affiliations', 2, 'periodEnd']},
            {'value': '2023-07-01', 'reduce_keys': ['affiliations', 3, 'periodEnd']}
        ]
        result = validate_affiliation_period_end(item, values)
        assert len(result) == 2
        assert "Period end must be after Period start." in result


# def validate_digits_for_wekoid(items, values=[])
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_digits_for_wekoid -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_digits_for_wekoid():
    items = 'items'
    values = [
        {'value': '111'},
    ]
    result = validate_digits_for_wekoid(items, values)
    assert result == []

    values_2 = [
        {'value': ''},
    ]
    result = validate_digits_for_wekoid(items, values_2)
    assert result == ["WEKO ID is required item."]

    values_3 = [
        {'value': '１１１'},
    ]
    result = validate_digits_for_wekoid(items, values_3)
    assert result == ["WEKO ID is Half-width digits only"]


    # def validate_affiliation_identifier_scheme(item, values=[])
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_affiliation_identifier_scheme -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_affiliation_identifier_scheme(authors_affiliation_settings):
    
    
    item = 'item'
    values = [{"key":"authorIdInfo[0].idType","reduce_keys":["authorIdInfo",0,"idType"],"value":"ISNI"}]
    result = validate_affiliation_identifier_scheme(item, values)
    assert result == []

    item = 'item'
    values_2 = [
        {'value': '123'},
    ]
    result = validate_affiliation_identifier_scheme(item, values_2)
    assert result == ["Specified Affiliation Identifier Scheme '123' does not exist."]


#    def validate_affiliation_period_start(item, values=[])
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_validate_affiliation_period_start -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_affiliation_period_start(authors):
    item = 'item'
    values = [
        {'value': '2025-3-17'},
    ]
    result = validate_affiliation_period_start(item, values)
    assert result == []

    values_2 = [
        {'value': '2025317'},
    ]
    result = validate_affiliation_period_start(item, values_2)
    assert result == ["External Affiliation Period must be in the format: yyyy-MM-dd, blank. 2025317"]


#    def check_weko_id_is_exits_for_import(pk_id, weko_id, existed_external_authors_id={})
# .tox/c1/bin/pytest --cov=weko_authors tests/test_validation.py::test_check_weko_id_is_exits_for_import -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_check_weko_id_is_exits_for_import(authors):
    pk_id = '2'
    weko_id = '1'
    existed_external_authors_id = {
        '1': {},
    }
    result = check_weko_id_is_exits_for_import(pk_id, weko_id, existed_external_authors_id)
    assert result == []

    pk_id = '2'
    weko_id = '1'
    existed_external_authors_id = {
        '1': {'1': ["2"],},
    }
    result = check_weko_id_is_exits_for_import(pk_id, weko_id, existed_external_authors_id)
    assert result == []

    pk_id = '3'
    weko_id = '1'
    existed_external_authors_id = {
        '1': {'1': ["2"],},
    }
    result = check_weko_id_is_exits_for_import(pk_id, weko_id, existed_external_authors_id)
    assert result == ["Specified WEKO ID already exist."]