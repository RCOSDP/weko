# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest

from weko_notifications.utils import inbox_url, rfc3339

# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace

# def inbox_url():
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_utils.py::test_inbox_url -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_inbox_url(app):
    with app.app_context():
        assert inbox_url() == "http://inbox:8080/inbox"
        assert inbox_url(_external=True) == f"{app.config['THEME_SITEURL']}/inbox"
