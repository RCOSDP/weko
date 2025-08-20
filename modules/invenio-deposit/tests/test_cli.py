# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test CLI."""

from __future__ import absolute_import, print_function

import uuid

from click.testing import CliRunner
from flask import current_app
from flask.cli import with_appcontext
from invenio_deposit import cli
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_db import db
from invenio_records import Record
# from invenio_search import current_search, current_search_client

# .tox/c1/bin/pytest --cov=invenio_deposit tests/test_cli.py::test_reindex -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-deposit/.tox/c1/tmp
def test_reindex(app, script_info):
    """Test reindex."""
    # load records
    with app.test_request_context():
        runner = CliRunner()

        id1 = uuid.uuid4()
        record1 = Record.create(dict(title='Test 1', recid=1), id_=id1)
        PersistentIdentifier.create(
            pid_type='recid',
            pid_value=1,
            object_type='rec',
            object_uuid=id1,
            status=PIDStatus.REGISTERED,
        )
        db.session.commit()

        res = runner.invoke(cli.reindex,
                            ['-r',id1],
                            obj=script_info)
        assert 0 == res.exit_code
        
        # res = current_search_client.get(index=app.config.get("INDEXER_DEFAULT_INDEX"),doc_type=app.config.get("INDEXER_DEFAULT_DOC_TYPE"),id=id1)
        # assert res
        # assert res['_id'] == str(id1)