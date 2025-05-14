# .tox/c1/bin/pytest --cov=weko_workflow tests/test_cli.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

from weko_workflow.cli import workflow,init_workflow_tables
import pytest

# def workflow():
def test_workflow(app):
    runner = app.test_cli_runner()
    result = runner.invoke(workflow)
    assert result.exit_code == 0
    

# def init_workflow_tables(tables):
#     def init_action_status():
#     def init_action():
#     def init_flow():
#     def init_workflow():
#     def init_gakuninrdm_data():
def test_init_workflow_tables(app, db, db_itemtype, users):
    runner = app.test_cli_runner()
    result = runner.invoke(init_workflow_tables,["action_status,Action,Flow"])
    assert result.output ==  'workflow db has been initialised.\n'
    assert result.exit_code == 0

    result = runner.invoke(init_workflow_tables,["gakuninrdm_data"])
    assert result.output == "workflow db has been initialised.\n"
    assert result.exit_code == 0
