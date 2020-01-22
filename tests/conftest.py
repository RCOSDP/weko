import os
import pytest
from pytest_invenio.fixtures import app_config, app


# need to init this fixture to create app,
# please refer to:
# invenio_app.factory.create_app,
# invenio_app.factory.create_ui
# invenio_app.factory.create_api
# for difference purposes
# please also refer to pytest_invenio.fixtures.app to get
# idea why we need this fixture
@pytest.fixture(scope='module')
def create_app():
    from invenio_app.factory import create_ui
    print("Inside parent")
    return create_ui


# customize the "app_config" from the pytest_invenio.fixtures for our purpose
@pytest.fixture(scope='module')
def app_config(app_config):
    app_config['ACCOUNTS_USE_CELERY'] = False
    app_config['LOGIN_DISABLED'] = False
    app_config['SECRET_KEY'] = 'long_nguyen'
    app_config[
        'SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/test'
    app_config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app_config['SQLALCHEMY_ECHO'] = False
    app_config['TEST_USER_EMAIL'] = 'test_user@example.com'
    app_config['TEST_USER_PASSWORD'] = 'test_password'
    app_config['TESTING'] = True
    app_config['WTF_CSRF_ENABLED'] = False
    app_config['DEBUG'] = False
    app_config['SEARCH_INDEX_PREFIX'] = 'test-tenant123'

    # app_config['CACHE_TYPE'] = 'redis'
    # app_config['CACHE_REDIS_HOST'] = 'redis'
    # app_config['CACHE_REDIS_URL'] = 'redis://redis:6379/14'
    # app_config['ACCOUNTS_SESSION_REDIS_URL'] = 'redis://redis:6379/15'
    return app_config


@pytest.fixture(scope='module')
def client(app):
    with app.test_client() as client:
        return client


@pytest.fixture
def full_record():
    """Full record fixture."""
    record = {'item_1574156725144': {'subitem_usage_location': 'sage location', 'pubdate': '2019-12-08',
                                     '$schema': '/items/jsonschema/19', 'title': 'username'}}
    # record = {'item_1574156725144': {'subitem_usage_location': 'sage location', 'recid': '23', 'pubdate': '2019-12-08',
    #                  '$schema': '/items/jsonschema/19', '_deposit': {'id': '23', 'status': 'draft'}}
    return record
