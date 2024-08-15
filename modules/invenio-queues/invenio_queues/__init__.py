# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


r"""Invenio module for managing queues.

This guide will show you how to get started with Invenio-Queues. It assumes
that you already have knowledge of Flask applications and Invenio modules.

It will then explain key topics and concepts of this module.

Getting started
---------------

You will learn how to register queues and to interact with it. To begin with,
we assume that you already have setup your virtual environment and install
the module:

You now need an application to work with, that can be created with the
following commands in a Python shell:

.. code-block:: python

   from flask import Flask
   app = Flask('myapp')

You can then initialize the module:

.. code-block:: python

   from invenio_queues.ext import InvenioQueues
   ext_queues = InvenioQueues(app)
   app.app_context().push()

In our example, we are using RabbitMQ as a broker, which can be configured
as follow::

    app.config['QUEUES_BROKER_URL'] = 'amqp://localhost:5672'

Register queues
^^^^^^^^^^^^^^^

To register queues, need to add it to the configuration.

.. code-block:: python

   from kombu import Exchange

   app.config['QUEUES_DEFINITIONS'] = [[
       {
           'name': 'notifications',
           'exchange': Exchange(
               'example',
               type='direct',
               delivery_mode='transient',  # in-memory queue
           ),
       },
   ]]

For more information about how to set an Exchange:
(https://docs.celeryproject.org/projects/kombu/en/stable/reference/kombu.html#exchange)

Create queues
^^^^^^^^^^^^^

Now that the queues are configured, you can create them::

    ext_queues.declare()

If you want to delete them, this can be done in the same way::

    ext_queues.delete()

Access queues
^^^^^^^^^^^^^

You can list the available queues by using::

    ext_queues.queues

Suppose you have a queue with name "notifications" you can directly access it
by name::

    notifications_queue = ext_queues.queues["notifications"]


Publish events
^^^^^^^^^^^^^^

After we have defined and instantiated (declare) our Queue we can start using
it.
This operation pushes an event or events to the queue:

.. code-block:: python

    events = [
        {
            'user_id': 123,
            'type': 'record-published',
            'record_id': '1234-5678'
        }
    ]

    notifications_queue.publish(events)


Comsume events
^^^^^^^^^^^^^^

After you have published some events in your queue, you can consume them.
The consume method of the queue will return a generator for the events:

.. code-block:: python

    queue_gen = notifications_queue.consume()
    list(queue_gen)

You can as well add this in a task like:

.. code-block:: python

   for msg in notifications_queue.consume():
       if msg['type'] == 'record-published':
           user = fetch_user(msg['user_id'])
           send_email(
               user.email, "New record {record_id} was published".format(**msg)
            )

"""

from .ext import InvenioQueues
from .proxies import current_queues

__version__ = "1.0.1"

__all__ = (
    "__version__",
    "current_queues",
    "InvenioQueues",
)
