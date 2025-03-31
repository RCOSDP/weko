# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, 2019, 2020 Esteban J. G. Gabancho.
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
``endpoint_url`` to boto3 `client
<https://boto3.readthedocs.io/en/latest/reference/core/session.html#boto3.session.Session.client>`_.
"""

S3_REGION_NAME = None
"""S3 region name

This is entirely optional, and if not provided, the region name will be
automatically set to 'us-east-1'.

If set to a value it will be passed as ``region_name`` to boto3 `client
<https://boto3.readthedocs.io/en/latest/reference/core/session.html#boto3.session.Session.client>`_.
"""

S3_ACCESS_KEY_ID = None
"""The access key to use when creating the client.

This is entirely optional, and if not provided, the credentials configured for
the session will automatically be used.
See `Configuring Credentials
<https://boto3.readthedocs.io/en/latest/guide/configuration.html#credentials>`_.
for more information.
"""

S3_SECRET_ACCESS_KEY = None
"""The secret key to use when creating the client.

This is entirely optional, and if not provided, the credentials configured for
the session will automatically be used.
See `Configuring Credentials
<https://boto3.readthedocs.io/en/latest/guide/configuration.html#credentials>`_.
for more information.
"""

S3_URL_EXPIRATION = 60
"""Number of seconds the file serving URL will be valid.

See `Amazon Boto3 documentation on presigned URLs
<https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.generate_presigned_url>`_
for more information.
"""

S3_SIGNATURE_VERSION = 's3v4'
"""Version of the S3 signature algorithm. Can be 's3' (v2) or 's3v4' (v4).
See `Amazon Boto3 documentation on configuration variables
<https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#configuration-file>`_
for more information.
"""

S3_MAXIMUM_NUMBER_OF_PARTS = 10000
"""Maximum number of parts to be used.
See `AWS Multipart Upload Overview
<https://docs.aws.amazon.com/AmazonS3/latest/dev/mpuoverview.html>`_ for more
information.
"""

S3_DEFAULT_BLOCK_SIZE = 5 * 2**20
"""Default block size value used to send multi-part uploads to S3.
Typically 5Mb is minimum allowed by the API."""
