import pytest
import importlib

@pytest.fixture
def migration_module():
    mod = importlib.import_module("invenio_communities.alembic.2d9884d0e3fa_create_community_tables")
    return mod

def test_upgrade_creates_tables(mocker, migration_module):
    mock_create_table = mocker.patch("alembic.op.create_table")
    migration_module.upgrade()
    assert mock_create_table.call_count == 3
    table_names = [call[0][0] for call in mock_create_table.call_args_list]
    assert "communities_community" in table_names
    assert "communities_community_record" in table_names
    assert "communities_featured_community" in table_names

def test_downgrade_drops_tables(mocker, migration_module):
    mock_drop_table = mocker.patch("alembic.op.drop_table")
    migration_module.downgrade()
    assert mock_drop_table.call_count == 3
    drop_names = [call[0][0] for call in mock_drop_table.call_args_list]
    assert "communities_community" in drop_names
    assert "communities_community_record" in drop_names
    assert "communities_featured_community" in drop_names