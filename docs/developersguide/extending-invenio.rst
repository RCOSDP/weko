.. _extending-invenio:

Extending WEKO3
=================

WEKO3 modules
---------------

Flask Extensions
----------------

.. _entrypoints:

Entry points
------------

Quick word about entry-points: it is a mechanism widely used in WEKO3 3.

WEKO3 is built on top of Flask, so it inherits its mechanisms: it is made of modules that you can add to get new features in your base installation.

In order to extend WEKO3, modules use entry-points. There are a lot of available entry-points, like:

- *bundles* (to use CSS or JavaScript bundle)
- *models* (to store data in the database)
- ...

The complete list of entry points in WEKO3 can be seen running ``invenio instance entrypoints``.

Depending on how your module extends WEKO3, it will be registered on one or several entry points. A module can also add new entry points, thus the *bundles* entry point comes from ``invenio_assets``, and its complete name is ``invenio_assets.bundles``.

The entry-points used by your module are listed in the ``setup.py`` file.


Hooks
-----

Signals
-------
