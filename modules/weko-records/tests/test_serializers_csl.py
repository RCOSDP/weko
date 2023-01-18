import pytest
from tests.helpers import json_data

from weko_records.serializers.csl import ObjectType

# neet to fix
# class ObjectType(object):
#     def get(cls, value):
#     def get_types(cls):
#     def get_subtypes(cls, type_):
#     def get_by_dict(cls, value):
#     def get_openaire_subtype(cls, value):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_csl.py::test_get_openaire_subtype -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_openaire_subtype(app, db):
    _value = { 
        'communities': [], 
        'resource_type': {
            'openaire_subtype': 'oa_type_test'
        },
        'subtype': 'test_subtype',
        'type': 'test_type'
    }
    with pytest.raises(Exception) as e:
        res = ObjectType.get(_value)
    assert e.type==FileNotFoundError

    with pytest.raises(Exception) as e:
        res = ObjectType.get_types()
    assert e.type==FileNotFoundError

    with pytest.raises(Exception) as e:
        res = ObjectType.get_subtypes('')
    assert e.type==FileNotFoundError

    res = ObjectType.get_by_dict(None)
    assert res==None

    with pytest.raises(Exception) as e:
        res = ObjectType.get_by_dict(_value)
    assert e.type==NameError

    _value.pop('subtype')
    with pytest.raises(Exception) as e:
        res = ObjectType.get_by_dict(_value)
    assert e.type==FileNotFoundError

    with pytest.raises(Exception) as e:
        res = ObjectType.get_openaire_subtype(_value)
    assert e.type==NameError
