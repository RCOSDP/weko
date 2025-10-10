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

import traceback

from b2handle.clientcredentials import PIDClientCredentials
from b2handle.handleclient import EUDATHandleClient
from b2handle.handleexceptions import CredentialsFormatError, \
    GenericHandleError, HandleAuthenticationError, \
    HandleAlreadyExistsException, HandleNotFoundException
from flask import current_app, jsonify


class Handle(object):
    """Operated on the Flow."""

    def __init__(self):
        """Bind to current bucket."""
        self.credential_path = current_app.config.get(
            'WEKO_HANDLE_CREDS_JSON_PATH')

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

    def register_handle(self, location, hdl="", overwrite=False):
        """Register a handle."""
        current_app.logger.debug(
            "location:{0} hdl:{1}".format(location, hdl))
        pid = hdl
        try:
            credential = PIDClientCredentials.load_from_JSON(
                self.credential_path)
            client = EUDATHandleClient.instantiate_with_credentials(credential)
            if pid == '' and location:
                pid = credential.get_prefix() + '/' + \
                    "{:010d}".format(int(location.split('/records/')[1]))
            current_app.logger.debug(
                'call register_handle({0}, {1})'.format(pid, location))
            handle = client.register_handle(pid, location, overwrite=overwrite)
            current_app.logger.info(
                'Registered successfully handle pid:{0} handle:{1}'.format(pid, handle))
            return handle
        except (FileNotFoundError, CredentialsFormatError,
                HandleAuthenticationError, GenericHandleError) as e:
            current_app.logger.error(
                'Registration failed of handle {0}. {1} in '
                'HandleClient.register_handle'.format(pid, e))
            current_app.logger.error(traceback.format_exc())
            return None
        except HandleAlreadyExistsException as e:
            current_app.logger.error(
                'Handle: {0} already exists.'.format(pid))
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(e)
            return None
        except AttributeError:
            current_app.logger.error('Missing Private Key!')
            current_app.logger.error(traceback.format_exc())
            return None
        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(e)
            return None

    def delete_handle(self, hdl):
        """Delete a handle."""
        current_app.logger.debug("hdl:{0}".format(hdl))
        try:
            credential = PIDClientCredentials.load_from_JSON(
                self.credential_path)
            client = EUDATHandleClient.instantiate_with_credentials(credential)

            current_app.logger.debug(
                'call delete_handle({0})'.format(hdl))
            client.delete_handle(hdl)
            current_app.logger.info(
                'Delete successfully handle:{0}'.format(hdl))
            return hdl
        except (FileNotFoundError, CredentialsFormatError,
                HandleAuthenticationError, GenericHandleError) as e:
            current_app.logger.error(
                'Delete failed of handle {0}. {1} in '
                'HandleClient.delete_handle'.format(hdl, e))
            current_app.logger.error(traceback.format_exc())
            return None
        except HandleNotFoundException:
            """The deleted handle is returned to the caller, and the Notfound also works correctly."""
            current_app.logger.debug(
                'Handle: {0} is not exists.'.format(hdl))
            return hdl
        except AttributeError:
            current_app.logger.error('Missing Private Key!')
            current_app.logger.error(traceback.format_exc())
            return None
        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(e)
            return None

    def get_prefix(self):
        """Get Handle prefix."""
        return PIDClientCredentials.load_from_JSON(self.credential_path).get_prefix()
