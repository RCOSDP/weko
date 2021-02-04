import pytest

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
    return create_ui

# customize the "app_config" from the pytest_invenio.fixtures for our purpose
@pytest.fixture(scope='module')
def app_config(app_config):
    app_config['ACCOUNTS_USE_CELERY'] = False
    app_config['LOGIN_DISABLED'] = False
    app_config['SECRET_KEY'] = 'hai'
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

    app_config['BROKER_URL'] = 'amqp://guest:guest@rabbitmq:5672//'
    app_config['CELERY_BROKER_URL'] = 'amqp://guest:guest@rabbitmq:5672//'
    app_config['INDEXER_DEFAULT_INDEX'] = '{}weko-item-v1.0.0'. \
        format(app_config['SEARCH_INDEX_PREFIX'])
    app_config['WEKO_ITEMS_UI_APPLICATION_FOR_LIFE'] = "ライフ利用申請"
    app_config['WEKO_ITEMS_UI_APPLICATION_FOR_ACCUMULATION'] = "累積利用申請"
    app_config['WEKO_ITEMS_UI_APPLICATION_FOR_COMBINATIONAL_ANALYSIS'] = \
        "組合せ分析利用申請"
    app_config['WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES'] = "都道府県利用申請"
    app_config['WEKO_ITEMS_UI_APPLICATION_FOR_LOCATION_INFORMATION'] = \
        "地点情報利用申請"
    app_config['WEKO_ITEMS_UI_USAGE_REPORT'] = "利用報告"
    app_config['WEKO_ITEMS_UI_OUTPUT_REPORT'] = "成果物登録"
    app_config['WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST'] = [
        app_config['WEKO_ITEMS_UI_APPLICATION_FOR_LIFE'],
        app_config['WEKO_ITEMS_UI_APPLICATION_FOR_ACCUMULATION'],
        app_config['WEKO_ITEMS_UI_APPLICATION_FOR_COMBINATIONAL_ANALYSIS'],
        app_config['WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES'],
        app_config['WEKO_ITEMS_UI_APPLICATION_FOR_LOCATION_INFORMATION'],
    ]
    app_config['WEKO_RECORDS_UI_DOWNLOAD_DAYS'] = 7
    app_config['WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME'] = 'Usage Report'
    app_config['WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION'] = \
        'Item Registration for Usage Application'

    app_config['WEKO_RECORDS_UI_USAGE_APPLICATION_WORKFLOW_DICT'] = [
        {
            'life': [
                {
                    'role': 'General',
                    'workflow_name': 'Life Usage Application - General'
                },
                {
                    'role': 'Student',
                    'workflow_name': 'Life Usage Application - Student'
                },
                {
                    'role': 'Graduated Student',
                    'workflow_name':
                        'Life Usage Application - Graduated Student'
                }
            ]
        }
    ]
    

 

    

 

    return app_config