# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Useful decorators for checking request headers."""
import os
from functools import wraps

from flask import current_app, request
from invenio_oauth2server.decorators import require_api_auth, require_oauth_scopes

from .errors import ErrorType, WekoSwordserverException


def check_oauth(*scopes):
    """Decorator to check header.

    :param \*scopes: List of scopes required.
    """
    def wrapper(f):
        """Wrap function with oauth require decorator."""
        f_require_api_auth = require_oauth_scopes(*scopes)(require_api_auth()(f))

        @wraps(f)
        def decorated(*args, **kwargs):
            # Check oauth authorization
            authorization = request.headers.get("Authorization", None)
            if authorization is not None:
                if not hasattr(request, 'oauth'):
                    raise WekoSwordserverException('Authentication is failed.', ErrorType.AuthenticationFailed)

            if scopes:
                return f_require_api_auth(*args, **kwargs)
            else:
                return f(*args, **kwargs)
        return decorated
    return wrapper

def check_on_behalf_of():
    """Decorator to check onBehalfOf header."""
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check onBehalfOf
            allowOnBehalfOf = current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF']
            onBehalfOf = request.headers.get("On-Behalf-Of", "")
            if allowOnBehalfOf == False and onBehalfOf != "":
                raise WekoSwordserverException("Not support On-Behalf-Of.", ErrorType.OnBehalfOfNotAllowed)

            return f(*args, **kwargs)
        return decorated
    return wrapper

def check_package_contents():
    """Decorator to check Content-Length header."""
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'file' not in request.files:
                raise WekoSwordserverException("No file part.", ErrorType.ContentMalformed)
            file = request.files['file']
            if file.filename == '':
                raise WekoSwordserverException("No selected file.", ErrorType.ContentMalformed)

            # Check Content-Length
            maxUploadSize = current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE']
            contentLength = request.headers.get("Content-Length", None)
            if contentLength is None:
                # Get length by file
                file.seek(0, os.SEEK_END)
                contentLength = file.tell()
                file.seek(0, 0)
            if int(contentLength or '0') > maxUploadSize:
                raise WekoSwordserverException(
                    "Content size is too large. (request:{}, maxUploadSize:{})".format(
                        contentLength, maxUploadSize), ErrorType.MaxUploadSizeExceeded)

            # Check Content-Type
            acceptArchiveFormat = current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT']
            reqContentType = request.headers.get("Content-Type", None)
            filesContentType = file.headers.get('Content-Type', None)
            failedContentType = None
            if reqContentType not in acceptArchiveFormat:
                failedContentType = reqContentType
                if filesContentType is not None:
                    failedContentType = filesContentType
                    if filesContentType in acceptArchiveFormat:
                        failedContentType = None
            if failedContentType is not None:
                raise WekoSwordserverException("Not accept Content-Type: {0}".format(failedContentType), ErrorType.ContentTypeNotAcceptable)

            # Check Packaging
            packaging = request.headers.get("Packaging", None)
            acceptPackaging = current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING']
            if '*' not in acceptPackaging:
                if packaging not in acceptPackaging:
                    raise WekoSwordserverException("Not accept packaging: {0}".format(packaging), ErrorType.PackagingFormatNotAcceptable)

            return f(*args, **kwargs)
        return decorated
    return wrapper

