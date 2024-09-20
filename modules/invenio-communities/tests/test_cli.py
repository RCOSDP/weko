# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


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
        mock_index = patch("invenio_communities.cli.RecordIndexer.index_by_id")
        result = runner.invoke(
            request,
            [community_id,record_id],
            obj=script_info
        )
        args,_=mock_index.call_args
        assert InclusionRequest.query.first()==None

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



# .tox/c1/bin/pytest --cov=invenio_communities tests/no_test_cli.py::test_remove -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
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
