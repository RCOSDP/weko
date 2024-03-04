# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Module tests."""
import json
from mock import MagicMock, Mock, patch

from invenio_deposit.serializers import json_serializer, json_files_serializer

def test_json_serializer():
    data = MagicMock()
    data.dumps = MagicMock(return_value={'key': 'value'})
    assert json_serializer(None, data, None)

def test_json_files_serializer():
    json_data = {"id":"id","filename":"filenmae","filesize":"filesize","checksum":"checksum"}
    with patch("invenio_deposit.serializers.file_serializer", return_value=json_data):
        magicmock = MagicMock()
        with patch("invenio_deposit.serializers.make_response", magicmock):
            json_files_serializer([0])
            args, kwargs = magicmock.call_args
            assert json.loads(args[0]) == [json_data]
