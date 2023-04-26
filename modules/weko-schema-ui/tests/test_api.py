import uuid
import json
import pytest

from invenio_records.errors import MissingModelError
from weko_schema_ui.api import WekoSchema

# class WekoSchema(RecordBase):
    # def create(cls, uuid, sname, fdata, xsd, schema, ns=None, isvalid=True, target_namespace=''):
    # def get_record(cls, id_, with_deleted=False):
    # def get_record_by_name(cls, name, with_deleted=False):
    # def get_records(cls, ids, with_deleted=False):
    # def get_all(cls, with_deleted=False):
    # def delete(self, force=False):
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_api.py::test_WekoSchema_func -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_WekoSchema_func(app, db):
    id = uuid.uuid4()
    fdata = {"name": "jpcoar", "file_name": "jpcoar_scm.xsd", "root_name": "jpcoar"}
    xsd = {
        "dc:title": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 1,
                "attributes": [
                    {"use": "optional", "name": "xml:lang", "ref": "xml:lang"}
                ],
            }
        }
    }
    schema = "https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"
    namespaces = {
        "": "https://github.com/JPCOAR/schema/blob/master/1.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "xs": "http://www.w3.org/2001/XMLSchema",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "xml": "http://www.w3.org/XML/1998/namespace",
        "dcndl": "http://ndl.go.jp/dcndl/terms/",
        "oaire": "http://namespace.openaire.eu/schema/oaire/",
        "jpcoar": "https://github.com/JPCOAR/schema/blob/master/1.0/",
        "dcterms": "http://purl.org/dc/terms/",
        "datacite": "https://schema.datacite.org/meta/kernel-4/",
        "rioxxterms": "http://www.rioxx.net/schema/v2.0/rioxxterms/",
    }
    rec = WekoSchema.create(id, 'test', fdata, json.dumps(xsd), schema, namespaces, True, '')
    assert rec == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}

    rec = WekoSchema.get_record(id, False)
    assert rec == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}
    rec = WekoSchema.get_record(id, True)
    assert rec == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}

    rec = WekoSchema.get_record_by_name('test', False)
    assert rec == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}
    rec = WekoSchema.get_record_by_name('test', True)
    assert rec == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}

    rec = WekoSchema.get_records([id], False)
    assert rec == [{'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}]
    rec = WekoSchema.get_records([id], True)
    assert rec == [{'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}]
    
    rec = WekoSchema.get_all(False)
    assert len(rec) == 1
    assert rec[0].form_data == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}
    rec = WekoSchema.get_all(True)
    assert len(rec) == 1
    assert rec[0].form_data == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}
    
    rec = WekoSchema.get_record_by_name('test', False)
    rec = rec.delete(False)
    assert rec == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}
    rec = rec.delete(True)
    assert rec == {'file_name': 'jpcoar_scm.xsd', 'name': 'jpcoar', 'root_name': 'jpcoar'}
    rec.model = None
    with pytest.raises(MissingModelError):
        rec = rec.delete(False)

    # def delete_by_id(self, pid):
