# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module contains the serialization of communities."""

from __future__ import absolute_import, print_function

from .response import community_responsify
from .schemas.community import CommunitySchemaV1

community_response = community_responsify(
    CommunitySchemaV1, 'application/json')
