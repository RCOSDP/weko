..
    This file is part of Invenio.
    Copyright (C) 2015, 2016 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.

======================
 Invenio-OAIHarvester
======================

.. image:: https://img.shields.io/travis/inveniosoftware/invenio-oaiharvester.svg
        :target: https://travis-ci.org/inveniosoftware/invenio-oaiharvester

.. image:: https://img.shields.io/coveralls/inveniosoftware/invenio-oaiharvester.svg
        :target: https://coveralls.io/r/inveniosoftware/invenio-oaiharvester

.. image:: https://img.shields.io/github/tag/inveniosoftware/invenio-oaiharvester.svg
        :target: https://github.com/inveniosoftware/invenio-oaiharvester/releases

.. image:: https://img.shields.io/pypi/dm/invenio-oaiharvester.svg
        :target: https://pypi.python.org/pypi/invenio-oaiharvester

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio-oaiharvester.svg
        :target: https://github.com/inveniosoftware/invenio-oaiharvester/blob/master/LICENSE


Invenio module for OAI-PMH metadata harvesting between repositories.

* Free software: GPLv2 license
* Documentation: https://invenio-oaiharvester.readthedocs.io/

*This is an experimental development preview release.*

About
=====

This module allows you to easily harvest OAI-PMH repositories, thanks to the `Sickle`_ module, and via signals
you can hook the output into your application, or simply to files.

You keep configurations of your OAI-PMH sources via SQLAlchemy models and run or schedule immediate harvesting jobs
via command-line or regularly via `Celery beat`_.

.. _Celery beat: http://celery.readthedocs.io/en/latest/userguide/periodic-tasks.html
.. _Sickle: http://sickle.readthedocs.io/en/latest/
