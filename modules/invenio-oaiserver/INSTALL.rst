..
    This file is part of Invenio.
    Copyright (C) 2016-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Installation
============

Invenio-OAIServer is on PyPI so all you need is:

.. code-block:: console

   $ pip install invenio-oaiserver

Invenio-OAIServer depends on Invenio-Search, Invenio-Records and Celery/Kombu.

**Requirements**

Invenio-OAIServer requires a message queue in addition to the search engine (Invenio-Search) and the database (Invenio-Records). See Kombu documentation for list of supported message queues (e.g. RabbitMQ): http://kombu.readthedocs.io/en/latest/introduction.html#transport-comparison
