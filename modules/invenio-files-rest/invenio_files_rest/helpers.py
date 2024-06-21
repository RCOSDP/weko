# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""File serving helpers for Files REST API."""

import hashlib
import mimetypes
import os
import unicodedata
import warnings
from time import time
from urllib.parse import urlsplit

from flask import current_app, make_response, request
from werkzeug.datastructures import Headers
from werkzeug.urls import url_quote
from werkzeug.wsgi import FileWrapper

MIMETYPE_TEXTFILES = {"readme"}

MIMETYPE_WHITELIST = {
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "text/plain",
}
"""List of whitelisted MIME types.

.. warning::

   Do not add new types to this list unless you know what you are doing. You
   could potentially open up for XSS attacks.
"""

MIMETYPE_PLAINTEXT = {
    "application/javascript",
    "application/json",
    "application/xhtml+xml",
    "application/xml",
    "text/css",
    "text/csv",
    "text/html",
    "image/svg+xml",
}


def chunk_size_or_default(chunk_size):
    """Use default chunksize if not configured."""
    return chunk_size or 5 * 1024 * 1024  # 5MiB


def send_stream(
    stream,
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
    trusted=False,
):
    """Send the contents of a file to the client.

    .. warning::

        It is very easy to be exposed to Cross-Site Scripting (XSS) attacks if
        you serve user uploaded files. Here are some recommendations:

            1. Serve user uploaded files from a separate domain
               (not a subdomain). This way a malicious file can only attack
               other user uploaded files.
            2. Prevent the browser from rendering and executing HTML files (by
               setting ``trusted=False``).
            3. Force the browser to download the file as an attachment
               (``as_attachment=True``).

    :param stream: The file stream to send.
    :param filename: The file name.
    :param size: The file size.
    :param mtime: A Unix timestamp that represents last modified time (UTC).
    :param mimetype: The file mimetype. If ``None``, the module will try to
        guess. (Default: ``None``)
    :param restricted: If the file is not restricted, the module will set the
        cache-control. (Default: ``True``)
    :param as_attachment: If the file is an attachment. (Default: ``False``)
    :param etag: If defined, it will be set as HTTP E-Tag.
    :param content_md5: If defined, a HTTP Content-MD5 header will be set.
    :param chunk_size: The chunk size.
    :param conditional: Make the response conditional to the request.
        (Default: ``True``)
    :param trusted: Do not enable this option unless you know what you are
        doing. By default this function will send HTTP headers and MIME types
        that prevents your browser from rendering e.g. a HTML file which could
        contain a malicious script tag.
        (Default: ``False``)
    :returns: A Flask response instance.
    """
    chunk_size = chunk_size_or_default(chunk_size)

    # Guess mimetype from filename if not provided.
    if mimetype is None and filename:
        mimetype = mimetypes.guess_type(filename)[0]
    if mimetype is None:
        mimetype = "application/octet-stream"

    # Construct headers
    headers = Headers()
    headers["Content-Length"] = size
    if content_md5:
        headers["Content-MD5"] = content_md5

    if not trusted:
        # Sanitize MIME type
        mimetype = sanitize_mimetype(mimetype, filename=filename)
        # See https://www.owasp.org/index.php/OWASP_Secure_Headers_Project
        # Prevent JavaScript execution
        headers["Content-Security-Policy"] = "default-src 'none';"
        # Prevent MIME type sniffing for browser.
        headers["X-Content-Type-Options"] = "nosniff"
        # Prevent opening of downloaded file by IE
        headers["X-Download-Options"] = "noopen"
        # Prevent cross domain requests from Flash/Acrobat.
        headers["X-Permitted-Cross-Domain-Policies"] = "none"
        # Prevent files from being embedded in frame, iframe and object tags.
        headers["X-Frame-Options"] = "deny"
        # Enable XSS protection (IE, Chrome, Safari)
        headers["X-XSS-Protection"] = "1; mode=block"

    # Force Content-Disposition for application/octet-stream to prevent
    # Content-Type sniffing.
    if as_attachment or mimetype == "application/octet-stream":
        # See https://github.com/pallets/flask/commit/0049922f2e690a6d
        try:
            filenames = {"filename": filename.encode("latin-1")}
        except UnicodeEncodeError:
            filenames = {"filename*": "UTF-8''%s" % url_quote(filename)}
            encoded_filename = unicodedata.normalize("NFKD", filename).encode(
                "latin-1", "ignore"
            )
            if encoded_filename:
                filenames["filename"] = encoded_filename
        headers.add("Content-Disposition", "attachment", **filenames)
    else:
        headers.add("Content-Disposition", "inline")

    # Construct response object.
    rv = current_app.response_class(
        FileWrapper(stream, buffer_size=chunk_size),
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


def sanitize_mimetype(mimetype, filename=None):
    """Sanitize a MIME type so the browser does not render the file."""
    # Allow some few mime type like plain text, images and audio.
    if mimetype in MIMETYPE_WHITELIST:
        return mimetype
    # Rewrite HTML, JavaScript, CSS etc to text/plain.
    if mimetype in MIMETYPE_PLAINTEXT or (
        filename and filename.lower() in MIMETYPE_TEXTFILES
    ):
        return "text/plain"
    # Default
    return "application/octet-stream"


def make_path(base_uri, path, filename, path_dimensions, split_length):
    """Generate a path as base location for file instance.

    :param base_uri: The base URI.
    :param path: The relative path.
    :param path_dimensions: Number of chunks the path should be split into.
    :param split_length: The length of any chunk.
    :returns: A string representing the full path.
    """
    assert len(path) > path_dimensions * split_length

    uri_parts = []
    for i in range(path_dimensions):
        uri_parts.append(path[0:split_length])
        path = path[split_length:]
    uri_parts.append(path)
    uri_parts.append(filename)

    return os.path.join(base_uri, *uri_parts)


def compute_md5_checksum(stream, **kwargs):
    """Get helper method to compute MD5 checksum from a stream.

    :param stream: The input stream.
    :returns: The MD5 checksum.
    """
    return compute_checksum(stream, "md5", hashlib.md5(), **kwargs)


def compute_checksum(
    stream, algo, message_digest, chunk_size=None, progress_callback=None
):
    """Get helper method to compute checksum from a stream.

    :param stream: File-like object.
    :param algo: Identifier for checksum algorithm.
    :param messsage_digest: A message digest instance.
    :param chunk_size: Read at most size bytes from the file at a time.
    :param progress_callback: Function accepting one argument with number
        of bytes read. (Default: ``None``)
    :returns: The checksum.
    """
    chunk_size = chunk_size_or_default(chunk_size)

    bytes_read = 0
    while 1:
        chunk = stream.read(chunk_size)
        if not chunk:
            if progress_callback:
                progress_callback(bytes_read)
            break
        message_digest.update(chunk)
        bytes_read += len(chunk)
        if progress_callback:
            progress_callback(bytes_read)
    return "{0}:{1}".format(algo, message_digest.hexdigest())


def populate_from_path(bucket, source, checksum=True, key_prefix="", chunk_size=None):
    """Populate a ``bucket`` from all files in path.

    :param bucket: The bucket (instance or id) to create the object in.
    :param source: The file or directory path.
    :param checksum: If ``True`` then a MD5 checksum will be computed for each
        file. (Default: ``True``)
    :param key_prefix: The key prefix for the bucket.
    :param chunk_size: Chunk size to read from file.
    :returns: A iterator for all
        :class:`invenio_files_rest.models.ObjectVersion` instances.
    """
    from .models import FileInstance, ObjectVersion

    def create_file(key, path):
        """Create new ``ObjectVersion`` from path or existing ``FileInstance``.

        It checks MD5 checksum and size of existing ``FileInstance``s.
        """
        key = key_prefix + key

        if checksum:
            file_checksum = compute_md5_checksum(
                open(path, "rb"), chunk_size=chunk_size
            )
            file_instance = FileInstance.query.filter_by(
                checksum=file_checksum, size=os.path.getsize(path)
            ).first()
            if file_instance:
                return ObjectVersion.create(bucket, key, _file_id=file_instance.id)
        return ObjectVersion.create(bucket, key, stream=open(path, "rb"))

    if os.path.isfile(source):
        yield create_file(os.path.basename(source), source)
    else:
        for root, dirs, files in os.walk(source, topdown=False):
            for name in files:
                filename = os.path.join(root, name)
                assert filename.startswith(source)
                parts = [p for p in filename[len(source) :].split(os.sep) if p]
                yield create_file("/".join(parts), os.path.join(root, name))


def create_file_streaming_redirect_response(obj):
    """Redirect response generating function."""
    warnings.warn("This streaming does not support multiple storage backends.")
    response = make_response()
    redirect_url_base = "/user_files/"
    redirect_url_key = urlsplit(obj.file.uri).path
    response.headers["X-Accel-Redirect"] = redirect_url_base + redirect_url_key[1:]
    return response
