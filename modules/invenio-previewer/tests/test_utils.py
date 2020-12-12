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

"""Test of utilities module."""

from __future__ import absolute_import, print_function

import pytest
from mock import patch
from six import BytesIO

from invenio_previewer import current_previewer
from invenio_previewer.utils import detect_encoding


def test_default_file_reader(app, record_with_file, testfile):
    """Test view by default."""
    file_ = current_previewer.record_file_factory(
        None, record_with_file, testfile.key)
    assert file_.version_id == testfile.version_id


@pytest.mark.parametrize('string, confidence, encoding, detect', [
    (u'Γκρήκ Στρίνγκ'.encode('utf-8'), 0.99000, 'UTF-8', 'UTF-8'),
    (u'dhǾk: kjd köd, ddȪj@dd.k'.encode('utf-8'), 0.87625, 'UTF-8', None),
    (u'क्या हाल तुम या कर रहे हो?'.encode('utf-8'), 0.99000, 'UTF-8', 'UTF-8'),
    (u'石原氏 移転は「既定路線」'.encode('euc-jp'), 0.46666, 'EUC-JP', None),
    (u'Hi bye sigh die'.encode('utf-8'), 1.00000, 'UTF-8', 'UTF-8'),
    (u'Monkey donkey cow crow'.encode('euc-jp'), 0.00000, 'ASCII', None),
    (u'Monkey donkey cow crow'.encode('euc-jp'), 0.90000, 'EUC-JP', None),
    (u'Monkey donkey cow crow'.encode('euc-jp'), 0.90001, 'EUC-JP', 'EUC-JP'),
    (u'Monkey donkey cow crow'.encode('euc-jp'), 0.50000, 'UTF-8', None),
])
def test_detect_encoding(app, string, confidence, encoding, detect):
    """Test encoding detection."""

    f = BytesIO(string)
    initial_position = f.tell()

    with patch('cchardet.detect') as mock_detect:
        mock_detect.return_value = {'encoding': encoding,
                                    'confidence': confidence}
        assert detect_encoding(f) is detect
        assert f.tell() == initial_position


def test_detect_encoding_exception(app):
    f = BytesIO(u'Γκρήκ Στρίνγκ'.encode('utf-8'))

    with patch('cchardet.detect', Exception):
        assert detect_encoding(f) is None
