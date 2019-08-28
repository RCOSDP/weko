# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO3 module docstring."""

import uuid
from datetime import datetime

from flask import current_app, request, session, url_for, jsonify, current_app
from flask_login import current_user
from b2handle.clientcredentials import PIDClientCredentials
from b2handle.handleclient import EUDATHandleClient

from .config import WEKO_HANDLE_CREDS_JSON_PATH


class Handle(object):
    """Operated on the Flow."""
    credential_path = WEKO_HANDLE_CREDS_JSON_PATH

    def retrieve_handle(self, handle):
        """Retrieve a handle."""
        try:
            credential = PIDClientCredentials.load_from_JSON(
                self.credential_path)
            client = EUDATHandleClient.instantiate_with_credentials(credential)
            handle_record_json = client.retrieve_handle_record_json(handle)
            return handle_record_json
        except Exception as e:
            current_app.logger.error('Unexpected error: ', e)

    def register_handle(self, location):
        """Register a handle."""
        try:
            credential = PIDClientCredentials.load_from_JSON(
                self.credential_path)
            client = EUDATHandleClient.instantiate_with_credentials(credential)
            pid = client.generate_PID_name(credential.get_prefix())
            new_handle = pid
            handle = client.register_handle(new_handle, location)
            return jsonify(handle)
        except Exception as e:
            current_app.logger.error('Unexpected error: ', e)
