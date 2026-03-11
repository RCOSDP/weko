import pytest
import importlib

@pytest.fixture
def migration_module():
    mod = importlib.import_module("invenio_communities.alembic.1b352b00f1ed_add_columns")
    return mod

def test_upgrade_calls_add_column_and_create_fk(mocker, migration_module):
    mocker.patch("alembic.op.f", lambda name: name)
    mock_add_column = mocker.patch("alembic.op.add_column")
    mock_create_fk = mocker.patch("alembic.op.create_foreign_key")
    migration_module.upgrade()

    assert mock_add_column.call_count == 2
    called_args = [call[0][0] for call in mock_add_column.call_args_list]
    assert all(arg == "communities_community" for arg in called_args)

    mock_create_fk.assert_called_once()
    fk_args = mock_create_fk.call_args[0]
    assert fk_args[1] == "communities_community"
    assert fk_args[2] == "accounts_role"

def test_downgrade_calls_drop_column_and_constraint(mocker, migration_module):
    mocker.patch("alembic.op.f", lambda name: name)
    mock_drop_column = mocker.patch("alembic.op.drop_column")
    mock_drop_constraint = mocker.patch("alembic.op.drop_constraint")
    migration_module.downgrade()

    mock_drop_constraint.assert_called_once()
    constraint_args = mock_drop_constraint.call_args[0]
    assert constraint_args[0].startswith("fk_communities_community_group_id_accounts_role")
    assert constraint_args[1] == "communities_community"

    assert mock_drop_column.call_count == 2
    called_args = [call[0][0] for call in mock_drop_column.call_args_list]
    assert all(arg == "communities_community" for arg in called_args)