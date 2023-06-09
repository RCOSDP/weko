
from mock import patch
from lxml import etree
from marshmallow.exceptions import ValidationError
from invenio_pidstore.errors import PIDDoesNotExistError
from itsdangerous import BadSignature


from invenio_oaiserver.views.server import validation_error,pid_error,resumptiontoken_error,dbsession_clean

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_views_server.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_views_server.py::test_validation_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_validation_error(app):
    {'email': ['Not a valid email address.'], 'name': ['Missing data for required field.'], 'age': ['age must not be greater than 100.']}
    {'email': 'foo', 'age': '1234'}
    error = ValidationError(
        {"key1":["test_message1"],"verb":["test_message2"],"metadataPrefix":[{"cannotDisseminateFormat":["test_message3"]},"test_message4"]}
    )
    tree, status_code, headers = validation_error(error)
    tree = etree.fromstring(tree)
    for t in tree.findall("./error",namespaces=tree.nsmap):
        attrib = t.attrib["code"] 
        if attrib == "badArgument":
            assert t.text == "test_message1"
        if attrib == "badVerb":
            assert t.text == "test_message2"
        if attrib == "cannotDisseminateFormat":
            assert t.text == "test_message3"
    assert status_code == 422
    assert headers == {"Content-Type": "text/xml"}

    error = ValidationError(
        "test_message",
        field_names=["verb","test_error"]
    )
    tree, status_code, headers = validation_error(error)
    tree = etree.fromstring(tree)
    for t in tree.findall("./error",namespaces=tree.nsmap):
        attrib = t.attrib["code"] 
        if attrib == "badArgument":
            assert t.text == "test_message"
        if attrib == "badVerb":
            assert t.text == "test_message"
    assert status_code == 422
    assert headers == {"Content-Type": "text/xml"}


    error = ValidationError(
        "test_message",
        field_names=[]
    )
    tree, status_code, headers = validation_error(error)
    tree = etree.fromstring(tree)
    for t in tree.findall("./error",namespaces=tree.nsmap):
        attrib = t.attrib["code"] 
        if attrib == "badArgument":
            assert t.text == "test_message"
    assert status_code == 422
    assert headers == {"Content-Type": "text/xml"}
    
    error = ValidationError(
        {},
        data={"messages":[]}
    )
    tree, status_code, headers = validation_error(error)
    tree = etree.fromstring(tree)
    for t in tree.findall("./error",namespaces=tree.nsmap):
        attrib = t.attrib["code"] 
        if attrib == "badArgument":
            assert t.text == None
    assert status_code == 422
    assert headers == {"Content-Type": "text/xml"}

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_views_server.py::test_pid_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_pid_error(app):
    error = PIDDoesNotExistError(pid_type="recid",pid_value=1)
    
    tree, status_code, headers = pid_error(error)
    tree = etree.fromstring(tree)
    for t in tree.findall("./error",namespaces=tree.nsmap):
        attrib = t.attrib["code"] 
        assert attrib == "idDoesNotExist"
        assert t.text == "No matching identifier"
    assert status_code == 422
    assert headers == {"Content-Type":"text/xml"}

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_views_server.py::test_resumptiontoken_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_resumptiontoken_error(app):
    error = BadSignature("test_error")

    tree, status_code, headers = resumptiontoken_error(error)
    tree = etree.fromstring(tree)
    for t in tree.findall("./error",namespaces=tree.nsmap):
        attrib = t.attrib["code"] 
        assert attrib == "badResumptionToken"
        assert t.text == "The value of the resumptionToken argument is invalid or expired."
    assert status_code == 422
    assert headers == {"Content-Type":"text/xml"}

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_views_server.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
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