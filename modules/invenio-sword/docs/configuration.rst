Configuration
=============

By default, invenio-sword's configuration mirrors the default configuration for invenio-deposit. It's possible to have
multiple SWORD endpoints, each depositing using a different ``pid_type``. The default ``pid_type`` is ``"depid"``.

.. code:: python

   _PID = 'pid(depid,record_class="invenio_sword.api:SWORDDeposit")'

   SWORD_ENDPOINTS = {
       name: {
           **options,
           "packaging_formats": {
               ep.name: ep.load()
               for ep in pkg_resources.iter_entry_points("invenio_sword.packaging")
           },
           "metadata_formats": {
               ep.name: ep.load()
               for ep in pkg_resources.iter_entry_points("invenio_sword.metadata")
           },
           "default_packaging_format": "http://purl.org/net/sword/3.0/package/Binary",
           "default_metadata_format": "http://purl.org/net/sword/3.0/types/Metadata",
           "record_class": "invenio_sword.api:Deposit",
           "default_media_type": "application/ld+json",
           # Permissions
           "create_permission_factory_imp": permissions.check_has_write_scope,
           "read_permission_factory_imp": permissions.check_is_record_owner,
           "update_permission_factory_imp": permissions.check_has_write_scope_and_is_record_owner,
           "delete_permission_factory_imp": permissions.check_has_write_scope_and_is_record_owner,
           "service_document_route": "/sword/service-document",
           "item_route": "/sword/deposit/<{}:pid_value>".format(_PID),
           "metadata_route": "/sword/deposit/<{}:pid_value>/metadata".format(_PID),
           "fileset_route": "/sword/deposit/<{}:pid_value>/fileset".format(_PID),
           "file_route": "/sword/deposit/<{}:pid_value>/file/<path:key>".format(_PID),
       }
       for name, options in DEPOSIT_REST_ENDPOINTS.items()
   }


Permissions configuration
-------------------------

You currently need to configure invenio-files-rest to allow all access to files:

.. code:: python

   # This allows access to files across all of invenio-files-rest
   FILES_REST_PERMISSION_FACTORY = lambda *a, **kw: type(
       "Allow", (object,), {"can": lambda self: True}
   )()

This needs a better solution in invenio-sword.
