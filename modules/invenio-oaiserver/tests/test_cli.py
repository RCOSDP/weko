import pytest
from mock import patch, MagicMock

from invenio_oaiserver.cli import oaipmh_file_create, file_create
from click.testing import CliRunner


def test_cli(batch_app,db):

    runner = CliRunner()

    with patch('invenio_oaiserver.cli.create_data', return_value='None'):
        runner.invoke(oaipmh_file_create)
        runner.invoke(file_create)

