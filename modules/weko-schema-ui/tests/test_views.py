import uuid

from weko_schema_ui.models import OAIServerSchema
from weko_schema_ui.views import dbsession_clean

# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_views.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_dbsession_clean(app, db, db_oaischema):
    dbsession_clean('test')
    dbsession_clean(None)

    model = OAIServerSchema(id=uuid.uuid4(), schema_name='oai_dc_mapping',
                            form_data=None, xsd=None,
                            namespaces=None,
                            schema_location=None,
                            isvalid=None,
                            target_namespace=None)
    db.session.add(model)
    dbsession_clean(None)
    