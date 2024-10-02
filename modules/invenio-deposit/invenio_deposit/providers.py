# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Deposit identifier provider."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.base import BaseProvider


class DepositProvider(BaseProvider):
    """Deposit identifier provider."""

    pid_type = 'depid'
    """Type of persistent identifier."""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of deposit ids.
    """

    default_status = PIDStatus.REGISTERED
    """Deposit IDs are by default registered immediately."""

    @classmethod
    def create(cls, object_type=None, object_uuid=None, **kwargs):
        """Create a new deposit identifier.

        :param object_type: The object type (Default: ``None``)
        :param object_uuid: The object UUID (Default: ``None``)
        :param kwargs: It contains the pid value.
        """
        assert 'pid_value' in kwargs
        kwargs.setdefault('status', cls.default_status)
        return super(DepositProvider, cls).create(
            object_type=object_type, object_uuid=object_uuid, **kwargs)
