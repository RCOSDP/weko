
import pytest
from mock import patch

from flask import current_app
from werkzeug.local import LocalProxy
from click.testing import CliRunner
from sqlalchemy_utils.functions import create_database

from invenio_db import InvenioDB

from invenio_db.cli import abort_if_false, create, drop,\
    init, destroy

# .tox/c1/bin/pytest --cov=invenio_db tests/test_cli.py -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_db tests/test_cli.py::test_abort_if_false -v -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
def test_abort_if_false(mocker):
    class MockCtx:
        def abort(self):
            pass
    abort_if_false(MockCtx(),None,"test_value")
    abort_if_false(MockCtx(),None,None)

## .tox/c1/bin/pytest --cov=invenio_db tests/test_cli.py::test_create -v -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
#@pytest.mark.parametrize("verbose",[True,False])
#def test_create(app,db,script_info, mock_entry_points,verbose):
#    idb = InvenioDB(app,db=db)
#    args = ["--verbose"]if verbose else []
#    runner = CliRunner()
#    result = runner.invoke(
#        create,
#        args,
#        obj=script_info
#    )
#    assert "Created all tables!" in result.output
#    if verbose:
#        assert " Creating table" in result.output

    

# .tox/c1/bin/pytest --cov=invenio_db tests/test_cli.py::test_drop -v -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
@pytest.mark.parametrize("verbose",[True,False])
def test_drop(app,db,script_info, mock_entry_points, verbose):
    idb = InvenioDB(app,db=db)
    args = ["--yes-i-know"]
    if verbose:
        args.append("--verbose") 
    runner = CliRunner()
    result = runner.invoke(
        drop,
        args,
        obj=script_info
    )
    assert "Dropping all tables!" in result.output
    if verbose:
        assert " Dropping table" in result.output


# .tox/c1/bin/pytest --cov=invenio_db tests/test_cli.py::test_init -v -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
def test_init(app,db,script_info, mock_entry_points, mocker):
    idb = InvenioDB(app)
    from invenio_db import cli, db
    if cli.database_exists(str(db.engine.url)):
        cli.drop_database(db.engine.url)
    mock_spy = mocker.spy(cli,"create_database")
    
    # not exist db
    runner = CliRunner()
    result = runner.invoke(
        init,
        obj=script_info
    )
    assert "Creating database" in result.output
    assert mock_spy.call_count == 1
    
    # exist db
    runner = CliRunner()
    result = runner.invoke(
        init,
        obj=script_info
    )
    assert "Creating database" in result.output
    assert mock_spy.call_count == 1


# .tox/c1/bin/pytest --cov=invenio_db tests/test_cli.py::test_destroy -v -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
def test_destroy(app,db,script_info,mock_entry_points,mocker):
    idb = InvenioDB(app)
    from invenio_db import cli
    mock_spy = mocker.spy(cli,"drop_database")
    # raise FileNotFoundError
    runner = CliRunner()
    result = runner.invoke(
        destroy,
        ["--yes-i-know"],
        obj=script_info
    )
    assert "Destroying database" in result.output
    # assert "Sqlite database has not been initialised" in result.output
    assert mock_spy.call_count == 1
    
    _db = LocalProxy(lambda: current_app.extensions['sqlalchemy'].db)
    create_database(str(_db.engine.url))
    # exist file
    runner = CliRunner()
    result = runner.invoke(
        destroy,
        ["--yes-i-know"],
        obj=script_info
    )
    assert "Destroying database" in result.output
    mock_spy.call_count == 2
    
    # _db.engine.name != sqlite
    with patch("sqlalchemy.engine.base.Engine.name",return_value="postgres"):
        runner = CliRunner()
        result = runner.invoke(
            destroy,
            ["--yes-i-know"],
            obj=script_info
        )
        assert "Destroying database" in result.output
        mock_spy.call_count == 3
    
