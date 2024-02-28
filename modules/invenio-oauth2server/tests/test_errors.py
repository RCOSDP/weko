# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test settings views."""
import json
from mock import MagicMock, Mock, patch

from invenio_oauth2server.errors import JWTExtendedException

def test_JWTExtendedException_get_body():
    json_data = {"status":"code","message":"description","errors":"errors"}
    self = MagicMock()
    self.code = 'code'
    self.description = 'description'
    self.get_errors = MagicMock(return_value='errors')
    ret = JWTExtendedException.get_body(self)
    assert json.loads(ret) == json_data
    assert type(ret) == str
