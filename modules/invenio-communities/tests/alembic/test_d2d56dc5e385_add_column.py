import pytest
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

import sys

import importlib

@pytest.fixture
def migration_module():
    mod = importlib.import_module("invenio_communities.alembic.d2d56dc5e385_add_column")
    return mod

def test_upgrade_calls_add_column(mocker, migration_module):
    mock_add_column = mocker.patch("alembic.op.add_column")
    migration_module.upgrade()
    assert mock_add_column.call_count == 4
    called_args = [call[0][0] for call in mock_add_column.call_args_list]
    assert all(arg == "communities_community" for arg in called_args)

def test_downgrade_calls_drop_column(mocker, migration_module):
    mock_drop_column = mocker.patch("alembic.op.drop_column")
    migration_module.downgrade()
    assert mock_drop_column.call_count == 4
    called_args = [call[0][0] for call in mock_drop_column.call_args_list]
    assert all(arg == "communities_community" for arg in called_args)