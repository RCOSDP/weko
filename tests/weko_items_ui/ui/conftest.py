import pytest


@pytest.fixture(scope='module')
def create_app():
    from invenio_app.factory import create_ui
    return create_ui
