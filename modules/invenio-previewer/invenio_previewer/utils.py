# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2024 CERN.
# Copyright (C) 2023 Northwestern University.
# Copyright (C) 2023 California Institute of Technology.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Previewer Utilities."""


import charset_normalizer
from flask import current_app


def detect_encoding(fp, default=None):
    """Detect the character encoding of a file.

    :param fp: Open Python file pointer.
    :param default: Fallback encoding to use.
    :returns: The detected encoding.

    .. note:: The file pointer is returned at its original read position.
    """
    init_pos = fp.tell()
    try:
        chardet_size = current_app.config.get("PREVIEWER_CHARDET_BYTES", 1024)
        threshold = current_app.config.get("PREVIEWER_CHARDET_CONFIDENCE", 0.9)

        sample = fp.read(chardet_size)

        # Result contains 'confidence' and 'encoding'
        result = charset_normalizer.detect(sample)
        confidence = result.get("confidence", 0) or 0
        encoding = result.get("encoding", default) or default

        # if low confidence or ascii, override to default (usually utf8 which is
        # better in case of unicode beyond checked range)
        if confidence <= threshold or encoding == "ascii":
            encoding = default

        return encoding
    except Exception:
        current_app.logger.warning("Encoding detection failed.", exc_info=True)
        return default
    finally:
        fp.seek(init_pos)


def dotted_exts(file_extensions):
    """Guarantee passed file extensions are prefixed with '.' .

    :param file_extensions: file extensions
    :type file_extensions: List[str]
    :return: dot-prefixed file extensions
    :rtype: List[str]
    """
    return ["." + ext.lstrip(".") for ext in file_extensions]
