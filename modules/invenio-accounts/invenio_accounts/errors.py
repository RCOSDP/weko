# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Exception classes."""


class JWTExtendedException(Exception):
    """Base exception for all JWT errors."""


class JWTDecodeError(JWTExtendedException):
    """Exception raised when decoding is failed."""


class JWTExpiredToken(JWTExtendedException):
    """Exception raised when JWT is expired."""
