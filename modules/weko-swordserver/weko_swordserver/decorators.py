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
from invenio_oauth2server.decorators import (
    require_api_auth, require_oauth_scopes
)

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
                    raise WekoSwordserverException(
                        "Authentication is failed.",
                        ErrorType.AuthenticationFailed
                    )

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
            allowOnBehalfOf = current_app.config.get(
                "WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF"
            )
            onBehalfOf = request.headers.get("On-Behalf-Of", "")
            if not allowOnBehalfOf and onBehalfOf:
                current_app.logger.error(
                    "Not support On-Behalf-Of but request has it.")
                raise WekoSwordserverException(
                    "Not support On-Behalf-Of.", ErrorType.OnBehalfOfNotAllowed
                )

            return f(*args, **kwargs)
        return decorated
    return wrapper

def check_package_contents():
    """Decorator to check Content-Length header."""
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'file' not in request.files:
                current_app.logger.error("No file part.")
                raise WekoSwordserverException(
                    "No file part.", ErrorType.ContentMalformed
                )
            file = request.files['file']
            if file.filename == '':
                current_app.logger.error("No selected file.")
                raise WekoSwordserverException(
                    "No selected file.", ErrorType.ContentMalformed
                )

            # Check Content-Length
            max_upload_size = current_app.config.get(
                "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE"
            )
            content_length = request.headers.get("Content-Length")

            file.seek(0, os.SEEK_END)
            content_size = file.tell()
            file.seek(0, 0)

            if int(content_length or content_size) > max_upload_size:
                current_app.logger.error(
                    "Content size is too large. "
                    f"(request:{content_length}, maxUploadSize:{max_upload_size})"
                )
                raise WekoSwordserverException(
                    "Content size is too large. "
                    f"(request:{content_length}, maxUploadSize:{max_upload_size})",
                    ErrorType.MaxUploadSizeExceeded
                )

            # Check Content-Type
            accept_archive_format = current_app.config.get(
                "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT"
            )
            req_content_type = request.headers.get("Content-Type", None)
            if req_content_type and (';' in req_content_type):
                req_content_type = req_content_type.split(';')[0]

            files_content_type = file.headers.get('Content-Type', None)
            if files_content_type and (';' in files_content_type):
                files_content_type = files_content_type.split(';')[0]

            failed_content_type = None
            if req_content_type not in accept_archive_format:
                failed_content_type = req_content_type
                if files_content_type not in accept_archive_format:
                    failed_content_type = files_content_type
            if failed_content_type is not None:
                current_app.logger.error(
                    f"Not accept Content-Type: {failed_content_type}"
                )
                raise WekoSwordserverException(
                    f"Not accept Content-Type: {failed_content_type}",
                    ErrorType.ContentTypeNotAcceptable
                )

            # Check Packaging
            packaging = request.headers.get("Packaging", None)
            accept_packaging = current_app.config.get(
                "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING"
            )
            if '*' not in accept_packaging:
                if packaging not in accept_packaging:
                    current_app.logger.error(f"Not accept packaging: {packaging}")
                    raise WekoSwordserverException(
                        f"Not accept packaging: {packaging}",
                        ErrorType.PackagingFormatNotAcceptable
                    )
            elif packaging is None:
                current_app.logger.error(
                    "Packaging is required, but not contained in request headers."
                )
                raise WekoSwordserverException(
                    "Packaging is required.",
                    ErrorType.PackagingFormatNotAcceptable
                )

            return f(*args, **kwargs)
        return decorated
    return wrapper

