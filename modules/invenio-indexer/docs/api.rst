..
    This file is part of Invenio.
    Copyright (C) 2016-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

API Docs
========

Record Indexer
--------------

.. automodule:: invenio_indexer.api
   :members:


Flask Extension
---------------

.. automodule:: invenio_indexer.ext
   :members:


Celery tasks
------------

.. automodule:: invenio_indexer.tasks
   :members:
.. autotask:: invenio_indexer.tasks.process_bulk_queue(version_type)
.. autotask:: invenio_indexer.tasks.index_record(record_uuid)
.. autotask:: invenio_indexer.tasks.delete_record(record_uuid)


Signals
-------

.. automodule:: invenio_indexer.signals
   :members:
