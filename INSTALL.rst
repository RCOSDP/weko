Installation
============

The best way to get an Weko demo instance up and running immediately is by
using Docker or Vagrant, for example:

.. code-block:: console

   $ docker-compose build
   $ docker-compose up -d
   $ docker-compose run --rm web ./scripts/populate-instance.sh
   $ firefox http://127.0.0.1/records/1

This will start an Weko demo instance containing several example records and
all the needed services such as PostgreSQL, Elasticsearch, Redis, RabbitMQ.

For a detailed walk-through on how to set up your Weko instance, please see
our `installation documentation
<http://weko.readthedocs.io/en/latest/installation/index.html>`_.
