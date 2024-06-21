..
    This file is part of Invenio.
    Copyright (C) 2016-2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Installation
============

Invenio-Previewer is on PyPI so all you need is::

    pip install invenio-previewer

Invenio-Previewer depends on Invenio-Assets for assets bundling and Invenio-PidStore and Invenio-Records-UI for record
integration.

You will normally use it in combination with files. You can install the extra Invenio modules Invenio-Files-REST
and Invenio-Records-Files by specifying the ``files`` key in extras::

    pip install invenio-previewer[files]
