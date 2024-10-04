# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test CLI."""

import uuid

import amqp
import pytest
from celery.messaging import establish_connection
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records import Record
from invenio_search import current_search, current_search_client
from kombu import Queue

from invenio_indexer import cli
from invenio_indexer.api import RecordIndexer
from invenio_indexer.proxies import current_indexer_registry


def test_run(app):
    """Test run."""
    runner = app.test_cli_runner()
    res = runner.invoke(cli.run, [])
    assert 0 == res.exit_code

    runner = app.test_cli_runner()
    res = runner.invoke(cli.run, ["-d", "-c", "2"])
    assert 0 == res.exit_code
    assert "Starting 2 tasks" in res.output


def test_reindex(app):
    """Test reindex."""
    # load records
    with app.test_request_context():
        runner = app.test_cli_runner()

        id1 = uuid.uuid4()
        id2 = uuid.uuid4()
        record1 = Record.create(dict(title="Test 1", recid=1), id_=id1)
        record2 = Record.create(dict(title="Test 2", recid=2), id_=id2)
        PersistentIdentifier.create(
            pid_type="recid",
            pid_value=1,
            object_type="rec",
            object_uuid=id1,
            status=PIDStatus.REGISTERED,
        )
        PersistentIdentifier.create(
            pid_type="recid",
            pid_value=2,
            object_type="rec",
            object_uuid=id2,
            status=PIDStatus.REGISTERED,
        )
        db.session.commit()
        indexer = RecordIndexer()
        index = indexer.record_to_index(record1)

        # Make sure the index doesn't exist at the beginning (it was not
        # preserved by accident from some other tests)
        assert current_search_client.indices.exists(index) is False

        # Initialize queue
        res = runner.invoke(cli.queue, ["init", "purge"])
        
        print(f"Command exit code: {res.exit_code}")
        print(f"Command output: {res.output}")
        print(f"Command exception: {res.exception}")
        
        if res.exception:
            print(f"Exception traceback: {res.exc_info}")
        
        assert res.exit_code == 0, f"Command failed with exit code {res.exit_code}"
        assert "Indexing queue has been initialized." in res.output
        assert "Indexing queue has been purged." in res.output


        
        res = runner.invoke(cli.reindex, ["--yes-i-know", "-t", "recid"])
        assert 0 == res.exit_code
        res = runner.invoke(cli.run, [])
        assert 0 == res.exit_code
        current_search.flush_and_refresh(index)

        # Both records should be indexed
        res = current_search_client.search(index=index)
        assert len(res["hits"]["hits"]) == 2

        # Delete one of the records
        record2 = Record.get_record(id2)
        record2.delete()
        db.session.commit()
        # Destroy the index and reindex
        list(current_search.delete(ignore=[404]))
        res = runner.invoke(cli.reindex, ["--yes-i-know", "-t", "recid"])
        assert 0 == res.exit_code
        res = runner.invoke(cli.run, [])
        assert 0 == res.exit_code
        current_search.flush_and_refresh(index)

        # Check that the deleted record is not indexed
        res = current_search_client.search(index=index)
        assert len(res["hits"]["hits"]) == 1
        assert res["hits"]["hits"][0]["_source"]["title"] == "Test 1"

        # Destroy queue and the index
        res = runner.invoke(cli.queue, ["delete"])
        assert 0 == res.exit_code
        list(current_search.delete(ignore=[404]))


def test_queues_options(app):
    """Test queue sub-command options."""

    cli_runner = app.test_cli_runner()

    users_indexer = RecordIndexer(
        queue=Queue(
            "users",
            exchange=app.config["INDEXER_MQ_EXCHANGE"],
            routing_key="users",
        ),
        routing_key="users",
    )
    files_indexer = RecordIndexer(
        queue=Queue(
            "files",
            exchange=app.config["INDEXER_MQ_EXCHANGE"],
            routing_key="files",
        ),
        routing_key="files",
    )
    current_indexer_registry.register(users_indexer, "users")
    current_indexer_registry.register(files_indexer, "files")
    queues = {
        "default": app.config["INDEXER_MQ_QUEUE"],
        "users": users_indexer.mq_queue,
        "files": files_indexer.mq_queue,
    }

    # Initialize all queues
    res = cli_runner.invoke(cli.queue, ["--all-queues", "init"])
    assert 0 == res.exit_code

    with establish_connection() as c:
        for queue in queues.values():
            assert queue(c).queue_declare(passive=True)

    # Delete all queues
    res = cli_runner.invoke(cli.queue, ["--all-queues", "delete"])
    assert 0 == res.exit_code

    with establish_connection() as c:
        for queue in queues.values():
            with pytest.raises(amqp.exceptions.NotFound):
                queue(c).queue_declare(passive=True)

    # Initialize users queue
    res = cli_runner.invoke(cli.queue, ["--queue", "users", "init"])
    assert 0 == res.exit_code

    with establish_connection() as c:
        assert queues["users"](c).queue_declare(passive=True)

    users_indexer.bulk_index(["123", "456"])
    files_indexer.bulk_index(["file1", "file2", "file3"])

    with establish_connection() as c:
        assert queues["users"](c).queue_declare(passive=True).message_count == 2
        assert queues["files"](c).queue_declare(passive=True).message_count == 3
        assert queues["default"](c).queue_declare(passive=True).message_count == 0

    # Purge files queue
    res = cli_runner.invoke(cli.queue, ["--queue", "files", "purge"])
    assert 0 == res.exit_code

    with establish_connection() as c:
        assert queues["users"](c).queue_declare(passive=True).message_count == 2
        assert queues["files"](c).queue_declare(passive=True).message_count == 0
        assert queues["default"](c).queue_declare(passive=True).message_count == 0

    # Delete files and default queue
    res = cli_runner.invoke(cli.queue, ["--queue", "files", "delete"])
    assert 0 == res.exit_code

    with establish_connection() as c:
        assert queues["users"](c).queue_declare(passive=True).message_count == 2
        with pytest.raises(amqp.exceptions.NotFound):
            queues["files"](c).queue_declare(passive=True)
        with pytest.raises(amqp.exceptions.NotFound):
            queues["default"](c).queue_declare(passive=True)
