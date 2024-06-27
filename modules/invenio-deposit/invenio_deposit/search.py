# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Configuration for deposit search."""

from elasticsearch_dsl import Q, TermsFacet
from flask import has_request_context
from flask_login import current_user
from invenio_search import RecordsSearch
from invenio_search.api import DefaultFilter

from .permissions import admin_permission_factory


def deposits_filter():
    """Filter list of deposits.

    Permit to the user to see all if:

    * The user is an admin (see
        func:`invenio_deposit.permissions:admin_permission_factory`).

    * It's called outside of a request.

    Otherwise, it filters out any deposit where user is not the owner.
    """
    if not has_request_context() or admin_permission_factory().can():
        return Q()
    else:
        return Q(
            'match', **{'_deposit.owners': getattr(current_user, 'id', 0)}
        )


class DepositSearch(RecordsSearch):
    """Default search class."""

    class Meta:
        """Configuration for deposit search."""

        index = 'deposits'
        doc_types = None
        fields = ('*', )
        facets = {
            'status': TermsFacet(field='_deposit.status'),
        }
        default_filter = DefaultFilter(deposits_filter)
