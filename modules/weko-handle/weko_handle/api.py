# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Handle is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""WEKO3 module docstring."""

from b2handle.clientcredentials import PIDClientCredentials
from b2handle.handleclient import EUDATHandleClient
from b2handle.handleexceptions import CredentialsFormatError, \
    GenericHandleError, HandleAuthenticationError
from flask import current_app, jsonify

from .config import WEKO_HANDLE_CREDS_JSON_PATH


class Handle(object):
    """Operated on the Flow."""

    def __init__(self):
        """Bind to current bucket."""
        self.credential_path = WEKO_HANDLE_CREDS_JSON_PATH

    def retrieve_handle(self, handle):
        """Retrieve a handle."""
        try:
            credential = PIDClientCredentials.load_from_JSON(
                self.credential_path)
            client = EUDATHandleClient.instantiate_with_credentials(credential)
            handle_record_json = client.retrieve_handle_record_json(handle)
            return jsonify(handle_record_json)
        except (CredentialsFormatError, FileNotFoundError) as e:
            current_app.logger.error(
                '{} in HandleClient.retrieve_handle_record_json({})'.format(
                    e, handle))

    def register_handle(self, location):
        """Register a handle."""
        pid = ''
        try:
            credential = PIDClientCredentials.load_from_JSON(
                self.credential_path)
            client = EUDATHandleClient.instantiate_with_credentials(credential)
            pid = credential.get_prefix() + '/' \
                + "{:010d}".format(int(location.split('/records/')[1]))
            handle = client.register_handle(pid, location)
            current_app.logger.info(
                'Registered successfully handle {}'.format(pid))
            return handle
        except (FileNotFoundError, CredentialsFormatError,
                HandleAuthenticationError, GenericHandleError) as e:
            current_app.logger.error(
                'Registration failed of handle {}. {} in '
                'HandleClient.register_handle'.format(pid, e))
            return None
        except AttributeError:
            current_app.logger.error('Missing Private Key!')
            return None
        except Exception as e:
            current_app.logger.error(e)
            return None
