# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Test CLI."""

import os

from invenio_files_rest.cli import files as cmd


def test_simple_workflow(app, db, tmpdir):
    """Run simple workflow."""
    runner = app.test_cli_runner()

    source = os.path.join(os.path.dirname(__file__), "fixtures", "source")

    # Create a location to use
    result = runner.invoke(
        cmd, ["location", "create", "tmp", "file://" + tmpdir.strpath, "--default"]
    )
    assert 0 == result.exit_code

    # Create the same location (check idempotent)
    result = runner.invoke(
        cmd, ["location", "create", "tmp", "file://" + tmpdir.strpath, "--default"]
    )
    assert 0 == result.exit_code
    assert "already exists" in result.output

    # Passing no subcommand should use default command 'create' (idempotent)
    result = runner.invoke(
        cmd, ["location", "tmp", "file://" + tmpdir.strpath, "--default"]
    )
    assert 0 == result.exit_code
    assert "already exists" in result.output

    # Create a second one as default to check tmp is not default anymore
    result = runner.invoke(
        cmd, ["location", "create", "aux", "file://" + tmpdir.strpath, "--default"]
    )
    assert 0 == result.exit_code

    # List locations and check the default is correct
    result = runner.invoke(cmd, ["location", "list"])
    assert 0 == result.exit_code

    created_locations = result.output.split("\n")

    # tmp is not default
    assert "tmp" in created_locations[0]
    assert "as default False" in created_locations[0]
    # aux is default
    assert "aux" in created_locations[1]
    assert "as default True" in created_locations[1]

    # Set tmp back as default
    result = runner.invoke(cmd, ["location", "set-default", "tmp"])
    assert 0 == result.exit_code

    # List locations and check the default is correct
    result = runner.invoke(cmd, ["location", "list"])
    assert 0 == result.exit_code

    created_locations = result.output.split("\n")
    # tmp is default
    assert "tmp" in created_locations[0]
    assert "as default True" in created_locations[0]
    # aux is not default
    assert "aux" in created_locations[1]
    assert "as default False" in created_locations[1]

    ##
    # Buckets
    ##

    result = runner.invoke(cmd, ["bucket", "touch"])
    assert 0 == result.exit_code
    bucket_id = result.output.split("\n")[0]

    # Specify a directory where 2 files have same content.
    result = runner.invoke(cmd, ["bucket", "cp", source, bucket_id, "--checksum"])
    assert 0 == result.exit_code

    # Specify a file.
    result = runner.invoke(cmd, ["bucket", "cp", __file__, bucket_id])
    assert 0 == result.exit_code
    prev_num_files = len(tmpdir.listdir())

    # No new file should be created.
    result = runner.invoke(cmd, ["bucket", "cp", __file__, bucket_id, "--checksum"])
    assert 0 == result.exit_code
    assert len(tmpdir.listdir()) == prev_num_files
