# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Error."""


class OAIBadMetadataFormatError(Exception):
    """Metadata format required doesn't exist."""


class OAISetSpecUpdateError(Exception):
    """Spec attribute cannot be updated.

    The correct way is to delete the set and create a new one.
    """


class OAINoRecordsMatchError(Exception):
    """No records match the query.

    The combination of the values of the from, until, and set arguments
    results in an empty list.
    """
