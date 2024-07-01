# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Minimal Flask application example for development.

SPHINX-START

This example requires that you have a search server (ES/OS) running
on localost:9200.
WARNING: This will remove all data from your search server.

You should also have the `Redis` running on your machine. To know how to
install and run `redis`, please refer to the
`redis website <https://redis.io/>`_.

First install Invenio-stats, setup the application and load fixture data by
running:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ export FLASK_APP=app.py
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Next, start the development server:

.. code-block:: console

   $ flask run -p 5000

You can now query the generated statistics.

Request a histogram of the number of downloads for a file:

.. code-block:: console

    $ curl -XPOST localhost:5000/stats -H "Content-Type: application/json"
    -d '{
        "mystat":{
            "stat": "bucket-file-download-histogram",
            "params": {
                "start_date":"2016-12-18",
                "end_date":"2016-12-19",
                "interval": "day",
                "bucket_id": 20,
                "file_key": "file1.txt"
            }
        }
    }'

Request a histogram of the number of downloads for a file:

.. code-block:: console

    $ curl -v -XPOST localhost:5000/stats -H "Content-Type: application/json"
    -d '{
        "mystat": {
            "stat": "bucket-file-download-total",
            "params": {
                "start_date":"2016-12-18",
                "end_date":"2016-12-19",
                "bucket_id": 20
            }
        }
    }'

To remove the example application data run:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END
"""

import os.path
import random
from datetime import datetime, timedelta

from flask import Flask
from invenio_queues import InvenioQueues
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, current_search_client

from invenio_stats import InvenioStats
from invenio_stats.proxies import current_stats
from invenio_stats.tasks import aggregate_events, process_events
from invenio_stats.views import blueprint

# Create Flask application
app = Flask(__name__)
app.config.update(
    {
        "BROKER_URL": "redis://",
        "CELERY_RESULT_BACKEND": "redis://",
        "DATADIR": os.path.join(os.path.dirname(__file__), "data"),
        "FILES_REST_MULTIPART_CHUNKSIZE_MIN": 4,
        "REST_ENABLE_CORS": True,
        "SECRET_KEY": "CHANGEME",
        "SQLALCHEMY_ECHO": False,
        "SQLALCHEMY_DATABASE_URI": os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": True,
    }
)

InvenioREST(app)
InvenioStats(app)
InvenioQueues(app)
InvenioSearch(app)

app.register_blueprint(blueprint)


@app.cli.group()
def fixtures():
    """Command for working with test data."""


def publish_filedownload(nb_events, user_id, file_key, file_id, bucket_id, date):
    current_stats.publish(
        "file-download",
        [
            {
                # When:
                "timestamp": (date + timedelta(minutes=idx)).isoformat(),
                # What:
                "bucket_id": str(bucket_id),
                "file_key": file_key,
                "file_id": file_id,
                # Who:
                "user_id": str(user_id),
            }
            for idx in range(nb_events)
        ],
    )


@fixtures.command()
def events():
    # Create events
    nb_days = 20
    day = datetime(2016, 12, 1, 0, 0, 0)
    max_events = 10
    random.seed(42)
    for _ in range(nb_days):
        publish_filedownload(
            random.randrange(1, max_events), 1, "file1.txt", 1, 20, day
        )
        publish_filedownload(
            random.randrange(1, max_events), 1, "file2.txt", 2, 20, day
        )
        day = day + timedelta(days=1)

    process_events(["file-download"])
    # flush search indices so that the events become searchable
    current_search_client.indices.flush(index="*")


@fixtures.command()
def aggregations():
    aggregate_events(["file-download-agg"])
    # flush search indices so that the aggregations become searchable
    current_search_client.indices.flush(index="*")
