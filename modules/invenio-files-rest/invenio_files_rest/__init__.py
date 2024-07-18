# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2024 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


r"""Invenio-Files-REST module.

This guide will show you how to get started with
Invenio-Files-REST. It assumes that you already have knowledge of
Flask applications and Invenio modules.

It will then explain key topics and concepts of this module.

Getting started
---------------

You will learn how to create a new Location, a Bucket and an ObjectVersion
using the programmatic APIs of Invenio-Files-REST.

First, you will have to setup your virtualenv environment and install
this module along with all it's dependencies.

After that, start a Python shell and execute the following commands:

>>> from flask import Flask
>>> app = Flask('myapp')

This is the initial configuration needed to have things running:

>>> app.config['BROKER_URL'] = 'redis://'
>>> app.config['CELERY_RESULT_BACKEND'] = 'redis://'
>>> app.config['DATADIR'] = 'data'
>>> app.config['FILES_REST_MULTIPART_CHUNKSIZE_MIN'] = 4
>>> app.config['REST_ENABLE_CORS'] = True
>>> app.config['SECRET_KEY'] = 'CHANGEME'
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
>>> app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

>>> allow_all = lambda *args, **kwargs: \
... type('Allow', (), {'can': lambda self: True})()
>>> app.config['FILES_REST_PERMISSION_FACTORY'] = allow_all

Relevant configuration variables will be explained later on.
Now let's initialize all required Invenio extensions:

>>> import shutil
>>> from os import makedirs
>>> from os.path import dirname, exists, join
>>> from pprint import pprint
>>> import json

>>> from invenio_i18n import Babel, InvenioI18N
>>> from flask_menu import Menu
>>> from invenio_db import InvenioDB, db
>>> from invenio_rest import InvenioREST
>>> from invenio_admin import InvenioAdmin
>>> from invenio_accounts import InvenioAccounts
>>> from invenio_access import InvenioAccess
>>> from invenio_accounts.views import blueprint as accounts_blueprint
>>> from invenio_celery import InvenioCelery
>>> from invenio_files_rest import InvenioFilesREST
>>> from invenio_files_rest.views import blueprint

>>> ext_babel = Babel(app)
>>> ext_menu = Menu(app)
>>> ext_db = InvenioDB(app)
>>> ext_rest = InvenioREST(app)
>>> ext_admin = InvenioAdmin(app)
>>> ext_accounts = InvenioAccounts(app)
>>> ext_access = InvenioAccess(app)
>>> ext_i18n = InvenioI18N(app)

You can now initialize  Invenio-Files-REST. When using Invenio-Files-REST as
dependency of an Invenio applicaton, the REST views are automatically
registered via entry points. For this example, you will have to register
them manually and push a Flask application context:

>>> ext_rest = InvenioFilesREST(app)

>>> app.register_blueprint(accounts_blueprint)
>>> app.register_blueprint(blueprint)

>>> app.app_context().push()

Let's create the database and tables, using an in-memory SQLite database:

>>> db.create_all()

When you setup Invenio-Files-REST for the first time, you will have to define
a default Location. It can be local or remote and it will be accessed via
its URI.

.. _usage-create-location:

Create a location
^^^^^^^^^^^^^^^^^
For this example, you will use a temporary directory:

>>> from invenio_files_rest.models import Location
>>> d = app.config['DATADIR']  # folder `data`
>>> if exists(d): shutil.rmtree(d)
>>> makedirs(d)
>>> loc = Location(name='local', uri=d, default=True)
>>> db.session.add(loc)
>>> db.session.commit()

Create a bucket
^^^^^^^^^^^^^^^
In order to create, modify or delete files, you have to create a files
container first, the Bucket.

>>> from invenio_files_rest.models import Bucket
>>> b1 = Bucket.create(loc)
>>> db.session.commit()

Create objects
^^^^^^^^^^^^^^
Files are represented by ObjectVersions. After creating a bucket, you can now
add files to it, for example:

>>> from io import BytesIO
>>> from invenio_files_rest.models import ObjectVersion
>>> a_file = BytesIO(b"my file contents")
>>> f = ObjectVersion.create(b1, "thesis.pdf", stream=a_file)
>>> db.session.commit()

Retrieve objects
^^^^^^^^^^^^^^^^
You can now retrieve objects. Retrieve the bucket object:

>>> b = Bucket.get(b1.id)

Retrieve all ObjectVersions contained in a bucket:

>>> file_names = [ov.key for ov in ObjectVersion.get_by_bucket(b1.id)]

Retrieve a specific ObjectVersion by filename:

>>> f = ObjectVersion.get(b1.id, "thesis.pdf")

Data model
----------

This is a more in-depth explanation of the concepts introduced in the
:doc:`overview` section.

Buckets
^^^^^^^

A bucket is a container of objects. It is uniquely identified by an ID.
Buckets have a default Location and Storage class.
Individual objects in the bucket can however have different
Locations and Storage classes.

The :code:`size` field stores the current size of the bucket. When a new
object is added or completely removed, its size is updated.

Buckets can have constraints on the maximum amount of objects that they can
contain. It is controlled by the function
:py:func:`invenio_files_rest.limiters.file_size_limiters`:
by default, a new object can be added to the bucket if the maximum
size of the file is lower than
:py:data:`invenio_files_rest.config.FILES_REST_DEFAULT_MAX_FILE_SIZE`
and if the total quota (the sum of sizes of all files) is lower than
:py:data:`invenio_files_rest.config.FILES_REST_DEFAULT_QUOTA_SIZE`.

Buckets can be marked as :code:`locked`. When a bucket is locked, objects
can be retrieved but no object can be added and deleted.

Similarly to objects, bucket can be logically marked as :code:`deleted`
without affecting the actual content. When it is deleted, it simply means
that no objects can be retrieved or added via APIs.

Finally, buckets provide ways to create or synchronize copies: the
:code:`snapshot` operation creates a new copy of a bucket with all
the latest versions of the object it contains, without duplicating files
on disk.
The :code:`sync` operation mirrors objects contained in the source bucket
to the destination bucket.


ObjectVersion
^^^^^^^^^^^^^

ObjectVersions are objects that represent a specific version of a file at
a given point in time. ObjectVersions are uniquely identified by its ID.
They are always contained in an existing Bucket by having the reference
:code:`bucket_id` to it.

An ObjectVersion describes the file (:code:`FileInstance`) that references
with the attribute :code:`file_id`. It also stores some metadata of the file:
the file name, stored in the :code:`key` attribute and the version, stored in
:code:`version_id` attribute. The triplet (bucket_id, key, version_id) is
unique.

For a given :code:`key` in a Bucket, normally the latest version in history
is marked as the :code:`head`.

The :code:`key` has a maximum length defined via
:py:data:`invenio_files_rest.config.FILES_REST_OBJECT_KEY_MAX_LEN`.

ObjectVersion can be marked as deleted by removing its reference to the
file it represents: from the user perspective, deleting a file normally
means adding a new ObjectVersion, which will be the new :code:`head`,
without :code:`file_id`.


FileInstance
^^^^^^^^^^^^

A file instance represents a file on disk. A file instance may be linked
from many objects, while an object can have one and only one file instance.

The file on disk can be retrieved by the file instance :code:`uri`, which
is an absolute path/URI generated when adding the file: the base path is
retrieved from the :code:`Location` used for this file, and the relative
path is assigned by the file's :code:`Storage`. It is responsibility of the
Storage, which is aware of the file system that is managing, to generate
a unique final path for the file. You can modify how the path is generated
with the default storage
:py:func:`invenio_files_rest.storage.pyfs_storage_factory`
by changing
:py:data:`invenio_files_rest.config.FILES_REST_STORAGE_PATH_SPLIT_LENGTH` or
:py:data:`invenio_files_rest.config.FILES_REST_STORAGE_PATH_DIMENSIONS`.

A file instance may not be ready to be accessed, for example in case of
multipart uploads: the attribute :code:`readable` marks it. It can also be
marked as not :code:`writable` if it cannot be deleted or replaced, for
safety reasons.

:code:`checksum`, :code:`last_check_at` and :code:`last_check` are
attributes used to store information about integrity checks.

You can find the documentation of each API in the :doc:`api`.

.. _usage-rest-apis:

REST APIs
---------
REST APIs allow you to perform most of the operations needed when
manipulating files.

By design, Locations cannot be created using REST APIs.
This is because they depend on your physical file storage infrastructure.
You will have to create them in advance when setting up your Invenio
instance.

To be able to run each of the next steps, you can instantiate and start an
Invenio instance as described `here
<https://invenio.readthedocs.io/en/latest/quickstart/quickstart.html#create-an-invenio-instance>`_.

Create a bucket
^^^^^^^^^^^^^^^
A bucket can be created by a POST request to :code:`/files`.
The response will contain the unique ID of the bucket.

.. code-block:: console

   $ curl -X POST http://localhost:5000/api/files

.. code-block:: json

    {
        "max_file_size": null,
        "updated": "2019-05-16T13:07:21.595398+00:00",
        "locked": false,
        "links": {
            "self": "http://localhost:5000/api/files/
                     cb8d0fa7-2349-484b-89cb-16573d57f09e",
            "uploads": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e?uploads",
            "versions": "http://localhost:5000/api/files/
                         cb8d0fa7-2349-484b-89cb-16573d57f09e?versions"
        },
        "created": "2019-05-16T13:07:21.595391+00:00",
        "quota_size": null,
        "id": "cb8d0fa7-2349-484b-89cb-16573d57f09e",
        "size": 0
    }


Uploading Files
^^^^^^^^^^^^^^^
You can upload, download and modify single files via REST APIs.
A file is uniquely identified within a bucket by its name and version.
Each file can have multiple versions.

Let's upload a file called :code:`my_file.txt` inside the bucket that
was just created.

.. code-block:: console

   $ BUCKET=cb8d0fa7-2349-484b-89cb-16573d57f09e

   $ echo "my file content" > my_file.txt

   $ curl -i -X PUT --data-binary @my_file.txt \
     "http://localhost:5000/api/files/$BUCKET/my_file.txt"

.. code-block:: json

    {
        "mimetype": "text/plain",
        "updated": "2019-05-16T13:10:22.621533+00:00",
        "links": {
            "self": "http://localhost:5000/api/files/
                     cb8d0fa7-2349-484b-89cb-16573d57f09e/my_file.txt",

            "version": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e/my_file.txt?
                        versionId=7f62676d-0b8e-4d77-9687-8465dc506ca8",
            "uploads": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e/
                        my_file.txt?uploads"
        },
        "is_head": true,
        "tags": {},
        "checksum": "md5:d7d02c7125bdcdd857eb70cb5f19aecc",
        "created": "2019-05-16T13:10:22.617714+00:00",
        "version_id": "7f62676d-0b8e-4d77-9687-8465dc506ca8",
        "delete_marker": false,
        "key": "my_file.txt",
        "size": 14
    }

If you have a new version of the file, you can upload it to the same bucket
using the same filename. In this case, a new ObjectVersion will be created.

.. code-block:: console

   $ echo "my file content version 2" > my_filev2.txt

   $ curl -i -X PUT --data-binary @my_filev2.txt \
     "http://localhost:5000/api/files/$BUCKET/my_file.txt"

.. code-block:: json

    {
        "mimetype": "text/plain",
        "updated": "2019-05-16T13:11:22.621533+00:00",
        "links": {
            "self": "http://localhost:5000/api/files/
                     cb8d0fa7-2349-484b-89cb-16573d57f09e/my_file.txt",

            "version": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e/my_file.txt?
                        versionId=24bf075f-09f4-42f8-9fbe-3f00b8aac3e8",
            "uploads": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e/
                        my_file.txt?uploads"
        },
        "is_head": true,
        "tags": {},
        "checksum": "md5:fe76512703258a894e56bac89d2e8dec",
        "created": "2019-05-16T13:11:22.617714+00:00",
        "version_id": "24bf075f-09f4-42f8-9fbe-3f00b8aac3e8",
        "delete_marker": false,
        "key": "my_file.txt",
        "size": 13
    }

When integrating the REST APIs to upload files via a web application, you
might use JavaScript to improve user experience. Invenio-Files-REST provides
out of the box integration with JavaScript uploaders. See the
:ref:`usage-js-uploaders` section for more information.

Invenio-Files-REST also provides different ways to upload large files. See
the :ref:`usage-multipart-upload` and :ref:`usage-large-files` sections
for more information.

Serving files
^^^^^^^^^^^^^

To serve and allow download of files, you can perform a GET request
specifying the bucket and the filename used to upload the file.

.. code-block:: console

   $ curl -i -X GET "http://localhost:5000/api/files/$BUCKET/my_file.txt"

You can also list files or download specific versions of files. See the REST
APIs reference documentation below for more information.

Be aware that there are security implications to take into account when
serving files. See the :ref:`usage-security` for more information.

Invenio-Files-Rest provides also the functionality to serve your files directly
from your external storage. This is achieved by attaching the
`X-Accel-Redirect
<https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/>`_
header to the response, which will then be redirected by
your Web Proxy (e.g. NGINX, Apache) to your external storage, finally streaming
the file directly to the user.
To use this feature you will need to configure your Web Proxy accordingly and
then enable the
:py:data:`invenio_files_rest.config.FILES_REST_XSENDFILE_ENABLED`.

API Reference
^^^^^^^^^^^^^

Default Location
++++++++++++++++

Create a bucket:

.. code-block:: console

    POST /files/

Buckets
+++++++

Check if bucket exists, returning either a 200 or 404:

.. code-block:: console

    HEAD /files/<bucket_id>

Retrieve the latest version of all objects in bucket:

.. code-block:: console

    GET /files/<bucket_id>

Retrieve all versions of files in a bucket:

.. code-block:: console

    GET /files/<bucket_id>?versions

Return list of multipart uploads:

.. code-block:: console

    GET /files/<bucket_id>?uploads

ObjectVersions
++++++++++++++

Initiate multipart upload (see :ref:`usage-multipart-upload`):

.. code-block:: console

    POST /files/<bucket_id>/<file_name>?
         uploads&size=<total_size>&partSize=<part_size>

Finalize multipart upload:

.. code-block:: console

    POST /files/<bucket_id>/<file_name>?uploadId=<upload_id>

Upload a file to a bucket:

.. code-block:: console

    PUT /files/<bucket_id>/<file_name>

Upload part of in-progress multipart upload to a bucket:

.. code-block:: console

    PUT /files/<bucket_id>/<file_name>?uploadId=<upload_id>&part=<part_number>

Retrieve the latest version of a given file. By default, the file is returned
with the header :code:`'Content-Disposition': 'inline'`. Be aware that the
browser will try to preview it.

.. code-block:: console

    GET /files/<bucket_id>/<file_name>

Download the latest version of a given file. It will return the same response
as the request above but with the response header
:code:`'Content-Disposition': 'attachment'` to instruct the browser
trigger a download.

.. code-block:: console

    GET /files/<bucket_id>/<file_name>?download

Retrieve a specific version of a given file:

.. code-block:: console

    GET /files/<bucket_id>/<file_name>?versionId=<version_id>

Retrieve the list of parts of a multipart upload:

.. code-block:: console

    GET /files/<bucket_id>/<file_name>?uploadId=<id_number>

Mark an object as deleted (see :ref:`usage-deleting-files`):

.. code-block:: console

    DELETE /files/<bucket_id>/<file_name>

Permanently erase an object and the physical file on disk:

.. code-block:: console

    DELETE /files/<bucket_id>/<file_name>?versionId=<version_id>

Abort multipart upload:

.. code-block:: console

    DELETE /files/<bucket_id>/<file_name>?uploadId=<upload_id>


.. _usage-deleting-files:

Deleting files
--------------
A delete operation can be of two types:

1. mark an object as deleted, allowing the possibility of restoring
   a deleted file (also called delete marker or soft deletion).
2. permanently remove any trace of an object and referenced file
   on disk (also called hard deletion).

Soft deletion
^^^^^^^^^^^^^
Technically, it creates a new ObjectVersion, that becomes the new :code:`head`,
with no reference to a FileInstance. It is possible to revert it
by getting the previous version.

This operation will not access to the file on disk and it will leave it
untouched.

You can soft delete using REST APIs:

.. code-block:: console

   DELETE /files/<bucket_id>/<file_name>

Hard deletion
^^^^^^^^^^^^^
Given a specific object version, it will delete the ObjectVersion,
the referenced FileInstance and the file on disk. If the deleted version
was the :code:`head`, it will then set the previous object
as the new head.

The deletion of files on disk will not happen immediately. This is because
it is done via an asynchronous task to ensure that the FileInstance is
safely removed from the database in case the low level operation of file
removal on disk fails for any unexpected reason.

You can hard delete a file using REST APIs:

.. code-block:: console

   DELETE /files/<bucket_id>/<file_name>?versionId=<version_id>

REST APIs do not allow to perform delete operations that can affect multiple
objects at the same time. For advanced use cases, you will to use the
Invenio-Files-REST APIs programmatically.

.. note::
    For safety reasons, the deletion will fail if the file that you want
    to delete is referenced by multiple ObjectVersions, for example
    in case of Buckets snapshots.

Authorization
-------------
Invenio-Files-REST relies on `Invenio-Access
<https://invenio-access.readthedocs.io>`_ to implement files authorization.
The following documentation assumes that you already have knowledge of how
authorization works on Invenio.

Invenio-Files-REST defines a set of actions for operations on Bucket and
ObjectVersions that can be used to implement authorization as you need:

    - files-rest-location-update
    - files-rest-bucket-read
    - files-rest-bucket-read-versions
    - files-rest-bucket-update
    - files-rest-bucket-listmultiparts
    - files-rest-object-read
    - files-rest-object-read-version
    - files-rest-object-delete
    - files-rest-object-delete-version
    - files-rest-multipart-read
    - files-rest-multipart-delete

Response codes
^^^^^^^^^^^^^^
If the authorization for an action fails, Invenio-Files-REST normally returns
a :code:`403` response code for authenticated users, :code:`401` otherwise.
For security reasons, when trying to retrieve an unauthorized file, it will
return a :code:`404` instead to hide the existence or
non-existence of the file.

Authorization definition
^^^^^^^^^^^^^^^^^^^^^^^^
The default permission factory
:py:data:`invenio_files_rest.permissions.permission_factory` will authorize
users that has :code:`Needs` that fulfill the actions listed above. This means
that by default no user will be authorized (with the exception of
any :code:`superuser`).

Depending on how you are planning to integrate Invenio-Files-REST in your
Invenio application, you might want to decide how to give permissions for
operations on files.

If you plan to give authorization to specific users or roles, you can use the
default permission factory and assign user or roles to the actions listed
above as described in the Invenio-Access documentation.

If instead you want to define permissions based on other object, for example
on records to which the files are attached to, then you will have to
define your own permission factory and used via the configuration variable
:py:data:`invenio_files_rest.config.FILES_REST_PERMISSION_FACTORY`.

See :mod:`invenio_files_rest.permissions` for more documentation.


.. _usage-security:

Security
--------
When serving files, you will have to take into account any security
implications. Here you can find some recommendations to mitigate possible
vulnerabilities, such as Cross-Site Scripting (XSS):

1. If possible, serve user uploaded files from a separate domain
   (not a subdomain).

2. By default, Invenio-Files-REST sets some response headers to prevent
   the browser from rendering and executing HTML files.
   See :py:func:`invenio_files_rest.helpers.send_stream` for more information.

3. Prefer file download instead of allowing the browser to preview any file,
   by adding the :code:`?download` URL query argument


.. _usage-signals:

Signals
-------
Invenio-Files-REST supports signals that can be used to react to events.

Events are sent whenever a file is downloaded, uploaded or deleted.

As an example, let's listen to the file download event:

.. code-block:: python

    from invenio_files_rest.signals import file_downloaded

    def after_file_downloaded(event, sender_app, obj=None, **kwargs):
        print("File downloaded {0}".format(obj))

    listener = file_downloaded.connect(after_file_downloaded)
    # Request to download a file for the event to trigger

See :mod:`invenio_files_rest.signals` for more documentation.


.. _usage-integrity:

Integrity
^^^^^^^^^
Invenio-Files-REST computes and stores checksums when files are uploaded and it
allows you to set up periodic tasks to regularly re-validate files integrity.

By default, it uses :code:`MD5` to compute checksums. You can override this
by subclassing :py:class:`invenio_files_rest.storage.FileStorage`.

You can use the tasks :py:func:`invenio_files_rest.tasks.verify_checksum` and
:py:func:`invenio_files_rest.tasks.schedule_checksum_verification` to set up
periodic tasks to perform checksum verifications on single files or batches
and provide reports.

Let's create a periodic task to compute checksums:

.. code-block:: python

    CELERY_BEAT_SCHEDULE = {
        'file-checks': {
           'task': 'invenio_files_rest.tasks.schedule_checksum_verification',
           'schedule': timedelta(hours=1),
        }
    }

By default, :py:func:`invenio_files_rest.tasks.schedule_checksum_verification`
will generate batches of files to check using some predefined constraints,
in order to throttle the execution rate of the checks.
It will then spawn a celery task
:py:func:`invenio_files_rest.tasks.verify_checksum` for each of the file in
the set.

You can customize most of these parameters by passing the method arguments
to the schedule definition.

Keep in mind that you need to have :code:`celerybeat` running.


.. _usage-storage-backends:

Storage Backends
----------------
Invenio-Files-REST provides a default implementation of storage factory
:py:class:`invenio_files_rest.storage.PyFSFileStorage`
used when performing operation on files in the defined locations.
The :code:`PyFSFileStorage` class uses
`PyFilesystem <https://www.pyfilesystem.org/>`_ to access the file system.


Build your own Storage Backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In order to use a different storage backend, you can implement the
:py:class:`invenio_files_rest.storage.FileStorage` interface.

Mandatory methods to implement:

* :code:`initialize`
* :code:`open`
* :code:`save`
* :code:`update`
* :code:`delete`

Optional methods to implement:

* :code:`send_file`
* :code:`checksum`
* :code:`copy`
* :code:`_init_hash`
* :code:`_compute_checksum`
* :code:`_write_stream`

Then, you will have to re-implement a storage factory in a similar way as the
default :py:func:`invenio_files_rest.storage.pyfs_storage_factory` and
set configuration variable
:py:data:`invenio_files_rest.config.FILES_REST_STORAGE_FACTORY`.


.. _usage-js-uploaders:

JS Uploaders
------------
Some JS uploaders do not allow you to customize the HTTP request that is
sent to the REST APIs when uploading a file. If the default implementation
provided by Invenio-Files-REST is not compatible, you will have to
implement your own custom factory to adapt the JS uploader request to
Invenio-Files-REST.

When using the AngularJS uploader
`ng-file-upload <https://github.com/danialfarid/ng-file-upload>`_,
Invenio-Files-REST already provides a compatible factory,
:py:func:`invenio_files_rest.views.ngfileupload_uploadfactory`.

If you have to create a new custom factory, you have to:

1. Create your own factory similar to
   :py:func:`invenio_files_rest.views.ngfileupload_uploadfactory`.

2. Instruct Invenio-Files-REST to use it by setting the configuration variables
:py:data:`invenio_files_rest.config.FILES_REST_MULTIPART_PART_FACTORIES` and
:py:data:`invenio_files_rest.config.FILES_REST_UPLOAD_FACTORIES`


.. _usage-multipart-upload:

Multipart Upload
----------------
You might want to optimize upload in case of large files.
Invenio-Files-REST allows you to upload parts of the same file in parallel
via multiparts uploads.

A multipart upload requires that each part of the file has the
same size, except for the last one that can be smaller.
Each part can be uploaded at the same
time and at the end of the process all parts are merged into one single file.

In case of failure when uploading one of the parts, the operation is completely
aborted and all parts are deleted.

With Invenio-Files-REST, the multipart upload consists of 3 actions:

* An initial request to initiate the upload and obtain an :code:`id`
  to be used for each part upload.

* A series of requests to upload of each part specifying
  the part number to correctly merge the file at the end.

* A final request to to merge all parts together.

Let's see an example. Let's create an 11 MB file which will then be split
into 2 chunks using the linux :code:`split` command:

.. code-block:: console

   $ dd if=/dev/urandom of=my_file.txt bs=1048576 count=11

   $ split -b6291456 my_file.txt segment_

Create a new bucket:

.. code-block:: console

   $ curl -X POST http://localhost:5000/api/files

Response:

.. code-block:: json

    {
       "max_file_size":null,
       "updated":"2019-05-17T06:52:52.897378+00:00",
       "locked":false,
       "links":{
          "self":"http://localhost:5000/api/files/
                  c896d17b-0e7d-44b3-beba-7e43b0b1a7a4",
          "uploads":"http://localhost:5000/api/files/
                     c896d17b-0e7d-44b3-beba-7e43b0b1a7a4?uploads",
          "versions":"http://localhost:5000/api/files/
                      c896d17b-0e7d-44b3-beba-7e43b0b1a7a4?versions"
       },
       "created":"2019-05-17T06:52:52.897373+00:00",
       "quota_size":null,
       "id":"c896d17b-0e7d-44b3-beba-7e43b0b1a7a4",
       "size":0
    }

Now, let's initiate the multipart upload. Notice the URL query argument
that specify total size and each part size:

.. code-block:: console

   $ B=c896d17b-0e7d-44b3-beba-7e43b0b1a7a4

   $ curl -i -X POST \
     "http://localhost:5000/api/files/$B/my_file.txt?
      uploads&size=11534336&partSize=6291456"

Notice the upload :code:`id` in the response:

.. code-block:: json

    {
       "updated":"2019-05-17T07:07:22.219002+00:00",
       "links":{
          "self":"http://localhost:5000/api/files/
                  c896d17b-0e7d-44b3-beba-7e43b0b1a7a4/my_file.txt?
                  uploadId=a85b1cbd-4080-4c81-a95c-b4df5d1b615f",

          "object":"http://localhost:5000/api/files/
                    c896d17b-0e7d-44b3-beba-7e43b0b1a7a4/my_file.txt",

          "bucket":"http://localhost:5000/api/files/
                    c896d17b-0e7d-44b3-beba-7e43b0b1a7a4"
       },
       "last_part_size":5242880,
       "created":"2019-05-17T07:07:22.218998+00:00",
       "bucket":"c896d17b-0e7d-44b3-beba-7e43b0b1a7a4",
       "completed":false,
       "part_size":6291456,
       "key":"my_file.txt",
       "last_part_number":1,
       "id":"a85b1cbd-4080-4c81-a95c-b4df5d1b615f",
       "size":11534336
    }

Now, let's upload each part in parallel. Notice the :code:`uploadId` and
:code:`partNumber` URL query arguments:

.. code-block:: console

   $ U=a85b1cbd-4080-4c81-a95c-b4df5d1b615f

   $ curl -i -X PUT --data-binary @segment_aa \
     "http://localhost:5000/api/files/$B/my_file.txt?uploadId=$U&partNumber=0"

   $ curl -i -X PUT --data-binary @segment_ab \
     "http://localhost:5000/api/files/$B/my_file.txt?uploadId=$U&partNumber=1"

Complete the multipart upload:

.. code-block:: console

   $ curl -i -X POST \
     "http://localhost:5000/api/files/$B/my_file.txt?uploadId=$U"

You can also abort a multipart upload (and delete all uploaded parts):

.. code-block:: console

   $ curl -i -X DELETE \
     "http://localhost:5000/api/files/$B/my_file.txt?uploadId=$U"

Multiparts uploads limits can be controlled via configuration variables:

* Set :py:data:`invenio_files_rest.config.FILES_REST_MULTIPART_MAX_PARTS`
  to limit the maximum number of parts for a single multipart upload.

* Set :py:data:`invenio_files_rest.config.FILES_REST_MULTIPART_CHUNKSIZE_MIN`
  to define the minimum size of each part.

* Set :py:data:`invenio_files_rest.config.FILES_REST_MULTIPART_CHUNKSIZE_MAX`
  to define the maximum size of each part.

* Set :py:data:`invenio_files_rest.config.FILES_REST_MULTIPART_EXPIRES`
  to define the maximum number of days for which a multipart upload is
  considered valid and accepts new part uploads.


.. _usage-large-files:

Large Files
-----------
By default, Flask and your web server have a limit on the maximum size of the
upload files. Normally, when the max size is exceeded, the server will return
a response code :code:`413 (Request Entity Too Large)`.

You can adjust these configurations according to your needs.

For Flask, specify :code:`MAX_CONTENT_LENGTH` configuration variable.
Be aware that if the request does not specify a :code:`CONTENT_LENGTH`,
no data will be read. To change the max size, you can for example:

.. code-block:: console

    $ app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

Here is an example for Nginx web server. If you are using another web server,
please check the related documentation.

.. code-block:: console

    http {
        ...
        client_max_body_size 25M;
    }


.. _usage-data-migration:

Data Migration
--------------
When you already have an instance running with a certain amount of uploaded
data, you might have the need to migrate the data to a different, larger or
more efficient physical location. It can involve your entire set of files or
just a part of it.

Note that files migration can be performed with no downtime and in a
completely transparent way for the user.

The steps to perform a complete migration are the followings:

1. Create the new :code:`Location` in the database with the URI of your
   new location and set it to :code:`default = True`. In this way, new
   :code:`Buckets` will use the new default location.
2. Change all existing buckets locations in the database to the new one.
   By doing this, any new file uploaded to the existing bucket will be stored
   in the new location.
3. For each :code:`FileInstance`, run the asynchronous task
   :py:func:`invenio_files_rest.tasks.migrate_file` passing the new location.

The asynchronous task :py:func:`invenio_files_rest.tasks.migrate_file`
will create a new :code:`FileInstance` and copy the file content to the
new location. It will then change each :code:`ObjectVersion` that have
a reference to the old :code:`FileInstance` to reference the new
:code:`FileInstance` and eventually run an integrity check.
"""

from .ext import InvenioFilesREST
from .proxies import current_files_rest

__version__ = "2.2.0"

__all__ = (
    "__version__",
    "current_files_rest",
    "InvenioFilesREST",
)
