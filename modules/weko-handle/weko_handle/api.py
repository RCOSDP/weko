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

import sys
import traceback
import requests
import os

from b2handle.clientcredentials import PIDClientCredentials
from b2handle.handleclient import EUDATHandleClient
from b2handle.handleexceptions import CredentialsFormatError, \
    GenericHandleError, HandleAuthenticationError, \
    HandleAlreadyExistsException
from flask import current_app, jsonify

from invenio_pidstore.models import PersistentIdentifier
from weko_handle.config import BASE_ARK_ID_FOR_MINTER_USE, WEKO_SERVER_CNRI_HOST_LINK


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

    def get_ark_identifier_from_ark_server(self, location, record=None, index=None, useArkIdentifier=False):
        """Get ARK identifier using record metadata"""
        current_app.logger.debug(
            "location:{0} hdl:{1}".format(location, 'ark'))
        try:
            who = ''
            what = ''
            when = ''
            target = ''

            if record:
                who = record.get('_oai', {}).get('id')
                what = record.get('item_title')
                when = record.get('publish_date')
                target = str(location)
            elif index:
                who = index.get('ezid_who')
                what = index.get('ezid_what')
                when = index.get('ezid_when')
                target = str(location)
            
            headers_post = {
                'Content-Type': 'text/plain',
            }

            params = {
                '_profile': 'erc',
                'erc.who': who,
                'erc.what': what,
                'erc.when': when,
                '_target': target,
                '_export': 'yes'
            }
            os.environ['NO_PROXY'] = '127.0.0.1'
            url_post = f'http://host.docker.internal:8000/id/ark:/99999/{BASE_ARK_ID_FOR_MINTER_USE}'
            response_post = requests.post(url_post, json=params, headers=headers_post)
            ark_identifier = None

            if response_post.text:
                ark_identifier = response_post.text.split(':')
                ark_identifier = ark_identifier[-1]
                ark_identifier = f"id/ark:{ark_identifier}"

            if useArkIdentifier and ark_identifier:
                current_app.logger.info(
                    f'EZID ARK identifier successfully generated pid:{ark_identifier}'
                )
                return ark_identifier
            else:
                return None
            
        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(e)
            return None


    def get_cnri_identifier_from_cnri_server(self, index_id=None):
        """Get CNRI identifier using index information"""
        current_app.logger.debug(
            f"index_id:{index_id} hdl:cnri"
        )

        try:
            # In case json header will be needed
            headers_application_json = {
                'Content-Type': 'application/json',
            }

            # This prefix is from modules/resources/handle_creds.json
            prefix = "20.500.12345"

            url_post = f'{WEKO_SERVER_CNRI_HOST_LINK}/{prefix}/{index_id}'
            response_post = requests.post(url_post)
            cnri_identifier = None

            # TODO This snippet will be edited once CNRI handle server is usable
            if response_post.text:
                cnri_identifier = response_post.text

            if response_post:
                current_app.logger.info(
                    f'CNRI identifier successfully generated: {cnri_identifier}'
                )
                return cnri_identifier
            else:
                return None
            
        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(e)
            return None



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

    def get_prefix(self):
        """Get Handle prefix."""
        return PIDClientCredentials.load_from_JSON(self.credential_path).get_prefix()
