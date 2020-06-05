# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helper tests."""

from __future__ import absolute_import, print_function

import pytest
from six.moves.urllib.parse import quote_plus

from invenio_app.helpers import get_safe_redirect_target


@pytest.mark.parametrize("test_input,expected", [
    ('https://example.org/search?page=1&q=&keywords=taxonomy&keywords=animali',
     '/search?page=1&q=&keywords=taxonomy&keywords=animali'),
    ('/search?page=1&size=20',
     '/search?page=1&size=20'),
    ('https://localhost/search?page=1',
     'https://localhost/search?page=1'),
])
def test_get_safe_redirect_target(app, test_input, expected):
    """Test that only "localhost" is a trusted absolute redirect target."""
    with app.test_request_context(
            '/?next={0}'.format(quote_plus(test_input))):
        assert get_safe_redirect_target() == expected
