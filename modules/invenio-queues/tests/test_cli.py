# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

import pytest
from click.testing import CliRunner
from flask.cli import ScriptInfo

from invenio_queues.cli import queues
from invenio_queues.proxies import current_queues


def queues_exist(names):
    """Test if the provided queues exist."""
    result = [current_queues.queues[name].exists for name in names]
    return all(result)


@pytest.mark.parametrize(
    "declared",
    [
        (["queue0", "queue1"]),
        # no queue specified => declare all of them
        ([]),
    ],
)
def test_declare(app, test_queues_entrypoints, declared):
    """Test the "declare" CLI."""
    with app.app_context():
        configured = [conf["name"] for conf in test_queues_entrypoints]
        expected = declared or configured
        assert not queues_exist(configured)
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(queues, ["declare"] + declared, obj=script_info)
        assert result.exit_code == 0
        assert queues_exist(expected)
        other = [name for name in configured if name not in expected]
        if other:
            assert not queues_exist(other)


@pytest.mark.parametrize(
    "purged",
    [
        (["queue0", "queue1"]),
        # no queue specified => purge all of them
        ([]),
    ],
)
def test_purge(app, test_queues, purged):
    """Test the "purge" CLI."""
    with app.app_context():
        configured = [conf["name"] for conf in test_queues]
        expected = purged or configured
        data = [1, 2, 3]
        for conf in test_queues:
            current_queues.queues[conf["name"]].publish(data)
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(queues, ["purge"] + purged, obj=script_info)
        assert result.exit_code == 0
        for conf in test_queues:
            if conf["name"] in expected:
                assert len(list(current_queues._queues[conf["name"]].consume())) == 0
            else:
                assert list(current_queues.queues[conf["name"]].consume()) == data


@pytest.mark.parametrize(
    "deleted",
    [
        (["queue0", "queue1"]),
        # no queue specified => delete all of them
        ([]),
    ],
)
def test_delete(app, test_queues, deleted):
    """Test the "delete" CLI."""
    with app.app_context():
        configured = [conf["name"] for conf in test_queues]
        expected = deleted or configured
        assert queues_exist(configured)
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(queues, ["delete"] + deleted, obj=script_info)
        assert result.exit_code == 0
        assert not queues_exist(expected)
        other = [name for name in configured if name not in expected]
        if other:
            assert queues_exist(other)


def test_list(app, test_queues):
    """Test the "list" CLI"""
    with app.app_context():
        # Test listing all queues
        configured = [conf["name"] for conf in test_queues]
        configured.sort()
        deleted = configured[0:2]
        declared = configured[2:]
        current_queues.delete(queues=deleted)
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(queues, ["list"], obj=script_info)
        assert result.exit_code == 0
        assert result.output.split("\n")[0:-1] == configured
        # Test listing only undeclared queues
        result = runner.invoke(queues, ["list", "--undeclared"], obj=script_info)
        assert result.exit_code == 0
        assert result.output.split("\n")[0:-1] == deleted
        # Test listing only declared queues
        result = runner.invoke(queues, ["list", "--declared"], obj=script_info)
        assert result.exit_code == 0
        assert result.output.split("\n")[0:-1] == declared


def test_declare_existing(app, test_queues_entrypoints):
    """Test the scenario of declaring a tasks that already exists."""
    with app.app_context():
        configured = [conf["name"] for conf in test_queues_entrypoints]
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        # Declare all the configured queues
        result = runner.invoke(queues, ["declare"] + configured, obj=script_info)
        assert result.exit_code == 0
        # Declare configured queues again without deletion
        result = runner.invoke(queues, ["declare"] + configured, obj=script_info)
        assert result.exit_code == 0


def test_delete_without_queues(app, test_queues):
    """Test delete without any queue declared."""
    with app.app_context():
        deleted = [conf["name"] for conf in test_queues]
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        # Delete a first time
        result = runner.invoke(queues, ["delete"] + deleted, obj=script_info)
        assert result.exit_code == 0
        # Delete without any queue declared
        result = runner.invoke(queues, ["delete"] + deleted, obj=script_info)
        assert result.exit_code == 0


def test_purge_force(app, test_queues):
    """Test purge function with the --force option."""
    with app.app_context():
        purged = [conf["name"] for conf in test_queues]
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(queues, ["delete"] + purged, obj=script_info)
        # Test with regular call
        result = runner.invoke(queues, ["purge"] + purged, obj=script_info)
        assert not result.exit_code == 0
        # Test with the --force
        result = runner.invoke(queues, ["purge", "--force"] + purged, obj=script_info)
        assert result.exit_code == 0
