# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

import pytest
from click.testing import CliRunner
from flask.cli import ScriptInfo

from invenio_queues.cli import queues
from invenio_queues.proxies import current_queues


def queues_exist(names, exist=True):
    """Test if the provided queues exist."""
    result = [current_queues.queues[name].exists
              for name in names]
    if exist:
        all(result)
    else:
        not any(result)


@pytest.mark.parametrize("declared", [
    (['queue0', 'queue1']),
    # no queue specified => declare all of them
    ([]),
])
def test_declare(app, test_queues_entrypoints, declared):
    """Test the "declare" CLI."""
    with app.app_context():
        configured = [conf['name'] for conf in test_queues_entrypoints]
        expected = declared or configured
        queues_exist(configured, False)
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(
            queues, ['declare'] + declared, obj=script_info)
        assert result.exit_code == 0
        queues_exist(expected)
        queues_exist([name for name in configured if
                      name not in expected], False)


@pytest.mark.parametrize("purged", [
    (['queue0', 'queue1']),
    # no queue specified => purge all of them
    ([]),
])
def test_purge(app, test_queues, purged):
    """Test the "purge" CLI."""
    with app.app_context():
        configured = [conf['name'] for conf in test_queues]
        expected = purged or configured
        data = [1, 2, 3]
        for conf in test_queues:
            current_queues.queues[conf['name']].publish(data)
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(
            queues, ['purge'] + purged, obj=script_info)
        assert result.exit_code == 0
        for conf in test_queues:
            if conf['name'] in expected:
                assert len(list(
                    current_queues._queues[conf['name']].consume())) == 0
            else:
                assert list(
                    current_queues.queues[conf['name']].consume()) == data


@pytest.mark.parametrize("deleted", [
    (['queue0', 'queue1']),
    # no queue specified => delete all of them
    ([]),
])
def test_delete(app, test_queues, deleted):
    """Test the "delete" CLI."""
    with app.app_context():
        configured = [conf['name'] for conf in test_queues]
        expected = deleted or configured
        queues_exist(configured, True)
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(
            queues, ['delete'] + deleted, obj=script_info)
        assert result.exit_code == 0
        queues_exist(expected, False)
        queues_exist([name for name in configured if
                      name not in expected], True)


def test_list(app, test_queues):
    """Test the "list" CLI"""
    with app.app_context():
        # Test listing all queues
        configured = [conf['name'] for conf in test_queues]
        configured.sort()
        deleted = configured[0:2]
        declared = configured[2:]
        current_queues.delete(queues=deleted)
        runner = CliRunner()
        script_info = ScriptInfo(create_app=lambda info: app)
        result = runner.invoke(
            queues, ['list'], obj=script_info)
        assert result.exit_code == 0
        assert result.output.split('\n')[0:-1] == configured
        # Test listing only undeclared queues
        result = runner.invoke(
            queues, ['list', '--undeclared'], obj=script_info)
        assert result.exit_code == 0
        assert result.output.split('\n')[0:-1] == deleted
        # Test listing only declared queues
        result = runner.invoke(
            queues, ['list', '--declared'], obj=script_info)
        assert result.exit_code == 0
        assert result.output.split('\n')[0:-1] == declared
