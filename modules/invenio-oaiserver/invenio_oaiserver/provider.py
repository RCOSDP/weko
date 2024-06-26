# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAI-PMH ID provider."""

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.base import BaseProvider


class OAIIDProvider(BaseProvider):
    """OAI-PMH identifier provider."""

    pid_type = "oai"
    """Type of persistent identifier."""

    pid_provider = "oai"
    """Provider name."""

    default_status = PIDStatus.RESERVED
    """OAI IDs are by default registered when object is known."""

    @classmethod
    def create(cls, object_type=None, object_uuid=None, **kwargs):
        """Create a new record identifier.

        :param object_type: The object type. (Default: ``None``)
        :param object_uuid: The object UUID. (Default: ``None``)
        """
        assert "pid_value" in kwargs

        kwargs.setdefault("status", cls.default_status)
        if object_type and object_uuid:
            kwargs["status"] = PIDStatus.REGISTERED

        return super(OAIIDProvider, cls).create(
            object_type=object_type, object_uuid=object_uuid, **kwargs
        )
