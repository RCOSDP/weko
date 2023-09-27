from flask import Flask
from invenio_communities.serializers.response import _format_args
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_serializers_response.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_serializers_response.py::test_format_args -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_format_args(instance_path):
    # raise runtime_error
    result = _format_args()
    assert result == {"indent": None, "separators": (",", ":")}
    
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        JSONIFY_PRETTYPRINT_REGULAR=True
    )
    with app.app_context():
        with app.test_request_context():
            result = _format_args()
            assert result == {"indent":2,"separators":(", ", ": ")}
