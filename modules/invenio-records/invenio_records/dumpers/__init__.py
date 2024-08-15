# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Dumpers used for producing versions of records that can be persisted.

**A simple example**

You can for instance use a dumper to produce the body of the document to be
indexed for the search engine:

.. code-block:: python

    dump = Record({...}).dumps(dumper=SearchDumper())

A dump can be loaded by the dumper as well:

.. code-block:: python

    record = Record.loads(dump, loader=SearchDumper())

**Data harmonization**

Invenio can read records from the database, search engine and data files. The
master copy is always the database, however for performance reasons, it's not
efficient to always use the master version of a record. For instance, during
searches it would come with a big performance impact if we had to read each
record in a search result from the database.

The problem is however that a secondary copy of a record (e.g. in the
search index) is not identical to the master copy. For instance, usage
statistics may have been cached in the search engine version whereas we don't
persist it in the database. This is again for performance reasons and allows
e.g. also having a "sort by most viewed" while not overloading the database
with usage statistics updates.

Because the master and secondary copies might not be identical, this causes
troubles for other Invenio modules who would have to "massage" the record
depending on where it comes form. Overall, this eventually leads to a confusing
data flow in the application.

The dumpers fixes this issue by harmonizing data access to a record from
multiple different data sources. This way, other Invenio modules always have a
standardized version of a record independently of where it was loaded from.
"""

from .base import Dumper
from .search import SearchDumper, SearchDumperExt

__all__ = (
    "Dumper",
    "SearchDumper",
    "SearchDumperExt",
)
