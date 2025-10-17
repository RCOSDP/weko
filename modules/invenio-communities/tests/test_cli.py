# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Module tests."""

from __future__ import absolute_import, print_function

from mock import patch
from click.testing import CliRunner
from invenio_records.api import Record

from invenio_communities.models import InclusionRequest, Community
from invenio_communities.cli import addlogo, init,request,remove

# .tox/c1/bin/pytest --cov=invenio_communities tests/no_test_cli.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_communities tests/no_test_cli.py::test_cli_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_cli_init(app,db,script_info,location):
    """Test create user CLI."""
    runner = CliRunner()
    # Init a community first time.
    result = runner.invoke(init, obj=script_info)
    assert result.exit_code == 0
    assert "Community init successful." in result.output

    # Init a community when it is already created.
    result = runner.invoke(init, obj=script_info)
    assert 'ucket with UUID 00000000-0000-0000-0000-000000000000 already exists.' in result.output

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_cli.py::test_addlogo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_addlogo(script_info,app,db,communities,instance_path):
    from invenio_files_rest.models import Location, Bucket
    import os
    loc = Location(name='local', uri=instance_path, default=True)
    db.session.add(loc)
    file_path=os.path.join(os.path.dirname(__file__),'data/weko-logo.png')
    bucket = Bucket(
        id="00000000-0000-0000-0000-000000000000",
        default_location=1,
        default_storage_class="S",
        size=111,
    )
    db.session.add(bucket)
    db.session.commit()

    with patch("invenio_communities.cli.db.session.commit", side_effect=Exception('')):
        runner = CliRunner()
        result = runner.invoke(
            addlogo,
            ["comm1",file_path],
            obj=script_info
        )
        assert result.exit_code == -1
        assert Community.query.filter_by(id="comm1").one().logo_ext == None

    runner = CliRunner()
    result = runner.invoke(
        addlogo,
        ["comm1",file_path],
        obj=script_info
    )
    assert result.exit_code == 0
    assert Community.query.filter_by(id="comm1").one().logo_ext == "png"
    
    # community is not existed
    runner = CliRunner()
    result = runner.invoke(
        addlogo,
        ["not_exist_comm",file_path],
        obj=script_info
    )
    assert result.exit_code == 0
    assert "Community not_exist_comm does not exist." in result.output


# .tox/c1/bin/pytest --cov=invenio_communities tests/test_cli.py::test_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_request(script_info,db_records,communities,mocker):
    mocker.patch("invenio_records.api.before_record_update.send")
    mocker.patch("invenio_records.api.after_record_update.send")
    mocker.patch("invenio_communities.models.inclusion_request_created.send")
    
    community_id = str(communities[0].id)
    record_id = str(db_records[2].id)
    
    # accept is true
    runner = CliRunner()
    mock_index = mocker.patch("invenio_communities.cli.RecordIndexer.index_by_id")
    result = runner.invoke(
        request,
        [community_id,record_id,"--accept"],
        obj=script_info
    )
    args,_=mock_index.call_args
    assert str(args[0]) == record_id
    from invenio_records.models import RecordMetadata
    metadata =RecordMetadata.query.filter_by(id=record_id).one().json
    assert metadata["communities"] == ["comm1"]

    # accept is false
    with patch("invenio_communities.cli.db.session.commit", side_effect=Exception('')):
        community_id = "comm2"
        with patch("invenio_communities.cli.RecordIndexer.index_by_id") as mock_index:
            result = runner.invoke(
                request,
                [community_id,record_id],
                obj=script_info
            )
            # Ensure mock_index is not called
            mock_index.assert_not_called()
            assert InclusionRequest.query.first() == None

    community_id = "comm2"
    mock_index = mocker.patch("invenio_communities.cli.RecordIndexer.index_by_id")
    result = runner.invoke(
        request,
        [community_id,record_id],
        obj=script_info
    )
    args,_=mock_index.call_args
    assert str(args[0]) == record_id
    assert InclusionRequest.query.first().id_community=="comm2"
    
    # Test the branch where RecordIndexer.index_by_id raises an exception and click.secho is called
    with patch("invenio_communities.cli.RecordIndexer") as MockIndexer:
        instance = MockIndexer.return_value
        instance.index_by_id.side_effect = Exception("error")
        with patch("click.secho") as mock_secho:
            result = runner.invoke(
                request,
                [community_id, record_id, "--accept"],
                obj=script_info
            )
            assert mock_secho.called
            called_args, called_kwargs = mock_secho.call_args
            assert str(called_args[0]) == "error"
            assert called_kwargs.get("fg") == "red"

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_cli.py::test_remove -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_remove(script_info,communities,db_records,mocker):
    mocker.patch("invenio_records.api.before_record_update.send")
    mocker.patch("invenio_records.api.after_record_update.send")
    mocker.patch("invenio_communities.models.inclusion_request_created.send")
    
    record_id = str(db_records[2].id)
    comm = Community.query.filter_by(id="comm1").one()
    record = Record.get_record(record_id)
    comm.add_record(record)
    record.commit()
    runner = CliRunner()
    with patch("invenio_communities.cli.db.session.commit", side_effect=Exception('')):
        result = runner.invoke(
            remove,
            [comm.id,record_id],
            obj=script_info
        )
        assert Record.get_record(record_id)

    mock_index = mocker.patch("invenio_communities.cli.RecordIndexer.delete_by_id")
    result = runner.invoke(
        remove,
        [comm.id,record_id],
        obj=script_info
    )
    args,_=mock_index.call_args
    assert str(args[0]) == record_id
