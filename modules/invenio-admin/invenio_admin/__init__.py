# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Administration interface for Invenio applications.

Invenio-Admin is an optional component of Invenio, responsible for registering
and customizing the administration panel for model views and user-defined
admin pages. The module uses standard Flask-Admin features and assumes very
little about other components installed within a given Invenio instance.

Quick start
-----------
This section presents a minimal working example of the Invenio-Admin.

First, let us create a new Flask application:

>>> from flask import Flask
>>> app = Flask('DinerApp')

and load the Invenio-DB and Invenio-Admin extensions:

>>> from invenio_db import InvenioDB
>>> from invenio_admin import InvenioAdmin
>>> ext_db = InvenioDB(app)
>>> ext_admin = InvenioAdmin(app, view_class_factory=lambda x: x)

.. warning::

    We use the ``view_class_factory`` parameter above to disable the
    authentication to the admin panel, in order to simplify this tutorial.
    Do not use this for production systems, as you will grant access to the
    admin panel to anonymous users!

    In full application with an authentication system in place, it is
    sufficient to instantiate the extension like:

    ``ext_admin = InvenioAdmin(app)``


Let's now define a simple model with a model view, and one base view:

>>> from invenio_db import db
>>> from flask_admin.contrib.sqla import ModelView
>>> from flask_admin.base import BaseView, expose
>>> class Lunch(db.Model):
...     __tablename__ = 'diner_lunch'
...     id = db.Column(db.Integer, primary_key=True)
...     meal_name = db.Column(db.String(255), nullable=False)
...     is_vegetarian = db.Column(db.Boolean(name='is_v'), default=False)
...
>>> class LunchModelView(ModelView):
...     can_create = True
...     can_edit = True
...
>>> class MenuCard(BaseView):
...     @expose('/')
...     def index(self):
...         return "HelloMenuCard!"

and register them in the admin extension:

>>> ext_admin.register_view(LunchModelView, Lunch, db.session)
>>> ext_admin.register_view(MenuCard)

Finally, initialize the database and run the development server:

>>> from sqlalchemy_utils.functions import create_database
>>> app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///test.db',
...     SECRET_KEY='SECRET')
...
>>> with app.app_context():
...     create_database(db.engine.url)
...     db.create_all()
>>> app.run() # doctest: +SKIP

You should now be able to access the admin panel `http://localhost:5000/admin
<http://localhost:5000/admin>`_.

Adding admin views from Invenio module
--------------------------------------
In real-world scenarios you will most likley want to add an admin view for
your custom models from within the Invenio module or an Invenio overlay
application. Instead of registering it directly on the application as in the
example above, you can use entry points to register those automatically.

Defining admin views
~~~~~~~~~~~~~~~~~~~~
Let us start with defining the ``admin.py`` file inside your module or overlay,
which will contain all admin-related classes and functions.
For example, assuming a ``Invenio-Diner`` module, the file could reside in:

``invenio-diner/invenio_diner/admin.py``.

In this example we will define two model views for two database models and one
separate base view for statistics page. The content of the file is as follows:

.. code-block:: python

    # invenio-diner/invenio_diner/admin.py
    from flask_admin.base import BaseView, expose
    from flask_admin.contrib.sqla import ModelView
    from invenio_db import db
    from .models import Snack, Breakfast

    class SnackModelView(ModelView):
        can_create = True
        can_edit = True
        can_view_details = True
        column_list = ('id', 'name', 'price', )

    class BreakfastModelView(ModelView):
        can_create = False
        can_edit = False
        can_view_details = True
        column_searchable_list = ('id', 'toast', 'eggs', 'bacon' )

    class DinerStats(BaseView):
        @expose('/')
        def index(self):
            return "Welcome to the Invenio-Diner statistics page!"

        @expose('/sales/')
        def sales(self):
            return "You have served 0 meals!"

    snack_adminview = {
        'view_class': Snack,
        'args': [SnackModelView, db.session],
        'kwargs': {'category': 'Diner'},
    }

    breakfast_adminview = {
        'view_class': Breakfast,
        'args': [BreakfastModelView, db.session],
        'kwargs': {'category': 'Diner'},
    }

    stats_adminview = {
        'view_class': DinerStats,
        'kwargs': {'name': 'Invenio Diner Stats'},
    }

    __all__ = (
        'snack_adminview',
        'breakfast_adminview',
        'stats_adminview',
    )

.. note::

    You have to define a dictionary for each BaseView and Model-ModelView pairs
    (see ``stats_adminview``, ``snack_adminview`` and ``breakfast_adminview``
    above) in order to have the admin views automatically registered via
    entry points (see next section).

    The ``args`` and ``kwargs`` keys in the dictionaries are passed to the
    constructor of the view class once it is intialized.

Registering the entry point
~~~~~~~~~~~~~~~~~~~~~~~~~~~
The default way of adding admin views to the admin panel is though
setuptools' entry point discovery. To do that, a newly created module has to
register an entry point under the group ``invenio_admin.views`` inside its
``setup.py`` as follows:

.. code-block:: python

    # invenio-diner/setup.py
    setup(
      entry_points={
        'invenio_admin.views': [
          'invenio_diner_snack = invenio_diner.admin.snack_adminview',
          'invenio_diner_breakfast = invenio_diner.admin.breakfast_adminview',
          'invenio_diner_stats = invenio_diner.admin.stats_adminview',
        ],
      },
    )


Authentication and authorization
--------------------------------
By default Invenio-Admin protects the admin views from unauthenticated users
with Flask-Login and restricts the access on a per-permission basis using
Flask-Security. In order to login to a Invenio-Admin panel the user
needs to be authenticated using Flask-Login and have a Flask-Security
identity which provides the ``ActionNeed('admin-access')``.

.. note::

    If you want to use a custom permission rule, you can easily specify
    your own permission factory in the configuration variable
    :data:`invenio_admin.config.ADMIN_PERMISSION_FACTORY`.

    For more information, see the default factory:
    :func:`invenio_admin.permissions.admin_permission_factory`
    and how the the view is using it:
    :func:`invenio_admin.views.protected_adminview_factory`


Styling
-------
At core, Invenio-Admin uses Flask-Admin for rendering the admin panel
and all of its views. All of the features for defining the ModelViews
and BaseViews can be found in the official Flask-Admin documentation.
Nonetheless, we will mention some of the ones that were already made easy to
use directly in Invenio-Admin.

Custom database type filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Non-basic data types can be made easier to search for and filter using type
filters. This way, fields of certain type that is not searchable by default
can be extended with that functionality. For example see a built-in UUID
filter :class:`invenio_admin.filters.UUIDEqualFilter`. You can enable the
custom fields filters, by setting a variable ``filter_converter`` on the
ModelView class. See an example of a custom filter converter in
:class:`invenio_admin.filters.FilterConverter`.

Assuming that the ``id`` field in ``Snack`` model from the example above is a
UUID-type field, you could enable the UUID filtering on this model as follows:

.. code::

    from invenio_admin.filters import FilterConverter

    class SnackModelView(ModelView):
        filter_converter = FilterConverter()  # Add filter converter
        can_create = True
        can_edit = True
        can_view_details = True
        column_list = ('id', 'name', 'price', )

Base template
~~~~~~~~~~~~~
Styling of the administration interface can be changed via the configuration
variable ``ADMIN_BASE_TEMPLATE``.

If Invenio-Theme is installed,
``ADMIN_BASE_TEMPLATE`` is automatically set to use the
`AdminLTE <https://almsaeedstudio.com/themes/AdminLTE/index2.html>`_ theme
which provides an extra configuration variable ``ADMIN_UI_SKIN`` which controls
the AdminLTE skin (e.g. ``skin-blue`` or ``skin-black``). See AdminLTE
documentation for details on supported skins.

If Invenio-Theme is not installed the default Flask-Admin templates will be
used (based on Bootstrap).

View template mode
~~~~~~~~~~~~~~~~~~
Flask-Admin view templates (forms etc.) can either use Bootstap 2 or 3. By
default the template mode is set to Bootstrap 3 but can be controlled through
``ADMIN_TEMPLATE_MODE`` configuration variable.
"""

from __future__ import absolute_import, print_function

from .ext import InvenioAdmin
from .proxies import current_admin
from .version import __version__

__all__ = ('__version__', 'InvenioAdmin', 'current_admin')
