

from mock import patch
from sqlalchemy import MetaData
from sqlalchemy.pool import QueuePool,NullPool
from sqlalchemy.engine.url import URL

from invenio_db import InvenioDB
from invenio_db.shared import NAMING_CONVENTION,SQLAlchemy

# .tox/c1/bin/pytest --cov=invenio_db tests/test_shared.py -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp

class TestSQLAlchemy:
    # .tox/c1/bin/pytest --cov=invenio_db tests/test_shared.py::TestSQLAlchemy::test_apply_driver_hacks -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
    def test_apply_driver_hacks(self, app, db, mock_entry_points):
        metadata = MetaData(naming_convention=NAMING_CONVENTION)
        InvenioDB(app,db=db)
        idb = SQLAlchemy(metadata=metadata)
        info = URL("sqlite")
        options = {'convert_unicode': True, 'connect_args':{'isolation_level':"test"},'poolclass': NullPool}
        idb.apply_driver_hacks(app,info,options)
        
# .tox/c1/bin/pytest --cov=invenio_db tests/test_shared.py::TestSQLAlchemy::test_set_db_connection_pool -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
    def test_set_db_connection_pool(self,db,app,mock_entry_points):
        metadata = MetaData(naming_convention=NAMING_CONVENTION)
        InvenioDB(app,db=db)
        with patch("invenio_db.shared.import_string",side_effect=Exception("test_error")):
            idb = SQLAlchemy(metadata=metadata)
            options = {}
            idb._SQLAlchemy__set_db_connection_pool(app,options)
            assert options["poolclass"] == QueuePool