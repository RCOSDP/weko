# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module of weko-swordserver."""


WEKO_SWORDSERVER_DEFAULT_VALUE = "foobar"
"""Default value for the application."""

WEKO_SWORDSERVER_BASE_TEMPLATE = "weko_swordserver/base.html"
"""Default base template for the demo page."""

WEKO_SWORDSERVER_SWORD_VERSION = "http://purl.org/net/sword/3.0"
""" The version of the SWORD protocol this server supports """

WEKO_SWORDSERVER_SERVICEDOCUMENT_ABSTRACT = ""
""" A description of the service """

WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT = ["*/*"]
""" List of Content Types which are acceptable to the server. """

WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT = [
    'application/zip', 'multipart/form-data'
]
""" List of Archive Formats that the server can unpack. If the server sends
a package using a different format, the server MAY treat it as a Binary File
"""

WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_DEPOSITS = True
""" Does the Service accept deposits? """

WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_METADATA = [
    "https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd",
    "https://w3id.org/ro/crate/1.1/",
]
""" List of Metadata Formats which are acceptable to the server. """

WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING = [
    "http://purl.org/net/sword/3.0/package/SimpleZip",
    "http://purl.org/net/sword/3.0/package/SWORDBagIt",
]
""" List of Packaging Formats which are acceptable to the server.

    ["*"] or List of Packaging Formats URI
        - http://purl.org/net/sword/3.0/package/Binary
        - http://purl.org/net/sword/3.0/package/SimpleZip
        - http://purl.org/net/sword/3.0/package/SWORDBagIt
"""

WEKO_SWORDSERVER_SERVICEDOCUMENT_COLLECTION_POLICY = {}
""" URL and description of the server’s collection policy.
example:
    {
        "@id" : "http://www.myorg.ac.uk/collectionpolicy",
        "description" : "...."
    }
"""
WEKO_SWORDSERVER_SERVICEDOCUMENT_TREATMENT = {}
""" URL and description of the treatment content can expect during deposit.
example:
    {
        "@id" : "http://www.myorg.ac.uk/treatment",
        "description" : "..."
    }
"""
WEKO_SWORDSERVER_SERVICEDOCUMENT_STAGING = ""
""" The URL where clients may stage content prior to deposit, in particular for segmented upload """

WEKO_SWORDSERVER_SERVICEDOCUMENT_STAGING_MAX_IDLE = 3600
""" What is the minimum time a server will hold on to an incomplete Segmented
File Upload since it last received any content before deleting it.
"""

WEKO_SWORDSERVER_SERVICEDOCUMENT_BY_REFERENCE_DEPOSIT = False
""" Does the server support By-Reference deposit? """

WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF = True
""" Does the server support deposit on behalf of other users (mediation) """

WEKO_SWORDSERVER_SERVICEDOCUMENT_DIGEST = ["SHA-256"]
""" The list of digest formats that the server will accept. """

WEKO_SWORDSERVER_SERVICEDOCUMENT_AUTHENTICATION = ["OAuth"]
""" List of authentication schemes supported by the server. """

WEKO_SWORDSERVER_SERVICEDOCUMENT_SERVICES = []
""" List of Services contained within the parent service """

WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE = 16777216000
""" Maximum size in bytes as an integer for files being uploaded. """

WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_BY_REFERENCE_SIZE = 30000000000000000
""" Maximum size in bytes as an integer for files uploaded by reference. """

WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_ASSEMBLED_SIZE = 30000000000000
""" Maximum size in bytes as an integer for the total size of an assembled segmented upload """

WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_SEGMENTS = 1000
""" Maximum number of segments that the server will accept for a single
segmented upload, if segmented upload is supported.
"""

WEKO_SWORDSERVER_DIGEST_VERIFICATION = True
""" Does the server require the client to send a digest? """

WEKO_SWORDSERVER_DEPOSIT_ROLE_ENABLE = [
    "System Administrator",
    "Repository Administrator"
]
""" Roles that can deposit items with token authentication. """
