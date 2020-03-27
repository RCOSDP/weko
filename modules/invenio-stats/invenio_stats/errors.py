# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Errors used in Invenio-Stats."""

from __future__ import absolute_import, print_function

from invenio_rest.errors import RESTException

##
#  Events errors
##


class DuplicateEventError(Exception):
    """Error raised when a duplicate event is detected."""


class UnknownEventError(Exception):
    """Error raised when an unknown event is detected."""


class UnknownAggregationError(Exception):
    """Error raised when an unknown  is detected."""


class DuplicateAggregationError(Exception):
    """Error raised when a duplicate aggregation is detected."""


class DuplicateQueryError(Exception):
    """Error raised when a duplicate aggregation is detected."""

##
#  Aggregation errors
##


class NotSupportedInterval(Exception):
    """Error raised for an unsupported aggregation interval."""


##
#  Query errors
##

class InvalidRequestInputError(RESTException):
    """Error raised when the request input is invalid."""

    code = 400

    def __init__(self, description, **kwargs):
        """Initialize exception."""
        super(RESTException, self).__init__(**kwargs)
        self.description = description


class UnknownQueryError(RESTException):
    """Error raised when the request input is invalid."""

    def __init__(self, query_name):
        """Constructor.

        :param query_name: name of the unknown query.
        """
        super(RESTException, self).__init__()
        self.query_name = query_name
        self.description = 'Unknown statistic \'{}\''.format(query_name)
    code = 400
