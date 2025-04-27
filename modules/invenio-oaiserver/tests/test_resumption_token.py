

from invenio_oaiserver.resumption_token import (
    _schema_from_verb,
    serialize,
    serialize_file_response,
    ResumptionTokenSchema
)

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_resumption_token.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp


#def _schema_from_verb(verb, partial=False):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_resumption_token.py::test_schema_from_verb -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_schema_from_verb():
    verb = "GetRecord"
    result = _schema_from_verb(verb)
    assert result

#def serialize(pagination, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_resumption_token.py::test_serialize -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_serialize(app,mocker):
    class MockPagenation():
        def __init__(self,has_next,next_num,_scroll_id):
            self.has_next=has_next
            self.next_num = next_num
            self._scroll_id = _scroll_id
    result = serialize(MockPagenation(False,10,0),verb="GetRecord")
    assert result is None
    
    mock_dump = mocker.patch("invenio_oaiserver.resumption_token.URLSafeTimedSerializer.dumps")
    result = serialize(MockPagenation(True,10,0),verb="GetRecord",identifier="test_identifier",metadataPrefix="jpcoar_1.0")
    args, _ = mock_dump.call_args
    assert args[0]["page"] == 10
    assert args[0]["kwargs"] == {"identifier":"test_identifier","metadataPrefix":"jpcoar_1.0"}
    
    mock_dump = mocker.patch("invenio_oaiserver.resumption_token.URLSafeTimedSerializer.dumps")
    result = serialize(MockPagenation(True,10,2),verb="GetRecord",identifier="test_identifier",metadataPrefix="jpcoar_1.0")
    args, _ = mock_dump.call_args
    assert args[0]["page"] == 10
    assert args[0]["scroll_id"] == 2
    assert args[0]["kwargs"] == {"identifier":"test_identifier","metadataPrefix":"jpcoar_1.0"}

#class ResumptionToken(fields.Field):
#    def _deserialize(self, value, attr, data):
#class ResumptionTokenSchema(Schema):
#    def load(self, data, many=None, partial=None):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_resumption_token.py::test_ResumptionTokenSchema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_ResumptionTokenSchema(app,mocker):

    data = {"resumptionToken":"test_token","verb":"GetRecord","kwargs":{"identifier":"test_identifier","metadataPrefix":"jpcoar_1.0"}}
    mocker.patch("invenio_oaiserver.resumption_token.URLSafeTimedSerializer.loads",return_value={"kwargs":data["kwargs"]})
    result = ResumptionTokenSchema().load(data)
    assert result


def serialize_file_response(app, mocker):
    app.config.update(SECRET_KEY='test_key')
    param = {'verb': 'ListRecords', 'data_id': 'test_id', 'metadataPrefix': 'ddi', 'expirationDate': 'test_expiration_date'}

    # If not required.
    token = serialize_file_response(100, 100, **param)
    assert token is None

    token = serialize_file_response(100, 500, **param)
    assert token is not None

