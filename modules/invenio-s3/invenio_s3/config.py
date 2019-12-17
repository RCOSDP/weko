# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""S3 file storage support for Invenio."""

S3_ENDPOINT_URL = None
"""S3 server URL endpoint.

If using Amazon AWS S3 service this config variable can be set to None as the
underlining library, `boto3 <https://boto3.readthedocs.io/en/latest/>`_,
will automatically construct the appropriate URL to use when communicating with
a service.

If set to a value (including the "http/https" scheme) it will be passed as
``endpoint_url`` to boto3`client
<https://boto3.readthedocs.io/en/latest/reference/core/session.html#boto3.session.Session.client>`_.
"""

S3_ACCCESS_KEY_ID = None
"""The access key to use when creating the client.

This is entirely optional, and if not provided, the credentials configured for
the session will automatically be used.
See `Configuring Credentials
<https://boto3.readthedocs.io/en/latest/guide/configuration.html#credentials>`_.
for more information.
"""

S3_SECRECT_ACCESS_KEY = None
"""The secret key to use when creating the client.

This is entirely optional, and if not provided, the credentials configured for
the session will automatically be used.
See `Configuring Credentials
<https://boto3.readthedocs.io/en/latest/guide/configuration.html#credentials>`_.
for more information.
"""

S3_SEND_FILE_DIRECTLY = True
"""The flag to use when send file to the client.

If this flag is false, system will redirects the file to the client.
When redirecting, S3_ENDPOINT_URL need to be set except for US region.
"""
