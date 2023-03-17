# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""File serving helpers for S3 files."""

import mimetypes
import unicodedata
from time import time
from flask import current_app, request
from invenio_files_rest.helpers import chunk_size_or_default, sanitize_mimetype
from werkzeug.datastructures import Headers
from werkzeug.urls import url_quote


def redirect_stream(url,
                    filename,
                    size,
                    mtime,
                    mimetype=None,
                    restricted=True,
                    as_attachment=False,
                    etag=None,
                    content_md5=None,
                    chunk_size=None,
                    conditional=True,
                    trusted=False):
    """Redirect to URL to serve the file directly from there.

    :param url: redirection URL

    :return: Flaks response.
    """
    chunk_size = chunk_size_or_default(chunk_size)

    # Guess mimetype from filename if not provided.
    if mimetype is None and filename:
        mimetype = mimetypes.guess_type(filename)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'

    # Construct headers
    headers = Headers()
    headers['Content-Length'] = size
    if content_md5:
        headers['Content-MD5'] = content_md5
    # Add redirect url as localtion
    headers['Location'] = url

    if not trusted:
        # Sanitize MIME type
        mimetype = sanitize_mimetype(mimetype, filename=filename)
        # See https://www.owasp.org/index.php/OWASP_Secure_Headers_Project
        # Prevent JavaScript execution
        headers['Content-Security-Policy'] = "default-src 'none';"
        # Prevent MIME type sniffing for browser.
        headers['X-Content-Type-Options'] = 'nosniff'
        # Prevent opening of downloaded file by IE
        headers['X-Download-Options'] = 'noopen'
        # Prevent cross domain requests from Flash/Acrobat.
        headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        # Prevent files from being embedded in frame, iframe and object tags.
        headers['X-Frame-Options'] = 'deny'
        # Enable XSS protection (IE, Chrome, Safari)
        headers['X-XSS-Protection'] = '1; mode=block'

    # Force Content-Disposition for application/octet-stream to prevent
    # Content-Type sniffing.
    if as_attachment or mimetype == 'application/octet-stream':
        # See https://github.com/pallets/flask/commit/0049922f2e690a6d
        try:
            filenames = {'filename': filename.encode('latin-1')}
        except UnicodeEncodeError:
            filenames = {'filename*': "UTF-8''%s" % url_quote(filename)}
            encoded_filename = (unicodedata.normalize('NFKD', filename).encode(
                'latin-1', 'ignore'))
            if encoded_filename:
                filenames['filename'] = encoded_filename
        headers.add('Content-Disposition', 'attachment', **filenames)
    else:
        headers.add('Content-Disposition', 'inline')

    # Construct response object.
    rv = current_app.response_class(
        url,
        status=302,
        mimetype=mimetype,
        headers=headers,
        direct_passthrough=True,
    )

    # Set etag if defined
    if etag:
        rv.set_etag(etag)

    # Set last modified time
    if mtime is not None:
        rv.last_modified = int(mtime)

    # Set cache-control
    if not restricted:
        rv.cache_control.public = True
        cache_timeout = current_app.get_send_file_max_age(filename)
        if cache_timeout is not None:
            rv.cache_control.max_age = cache_timeout
            rv.expires = int(time() + cache_timeout)

    if conditional:
        rv = rv.make_conditional(request)

    return rv
