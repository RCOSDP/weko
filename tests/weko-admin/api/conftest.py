import pytest

@pytest.fixture(scope='module')
def create_app():
    from invenio_app.factory import create_app
    return create_app