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


class AlreadyLinkedError(Exception):
    """Signifies that an account was already linked to another account."""

    def __init__(self, user, external_id):
        """Initialize exception."""
        self.user = user
        self.external_id = external_id
