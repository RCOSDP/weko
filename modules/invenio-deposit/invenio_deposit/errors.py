# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Errors."""

from __future__ import absolute_import, print_function

from invenio_rest.errors import RESTException


class FileAlreadyExists(RESTException):
    """Error file already exists."""

    code = 400
    description = 'Filename already exists.'


class WrongFile(RESTException):
    """Error wrong file."""

    code = 400
    description = 'Wrong file on input.'


class MergeConflict(RESTException):
    """Error on merging a deposit."""

    code = 409
    description = 'Deposit merge conflicts.'
