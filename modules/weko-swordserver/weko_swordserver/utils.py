# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
import traceback
from zipfile import ZipFile
from flask import current_app
from invenio_oauth2server.provider import get_token

from .errors import WekoSwordserverException, ErrorType
from .models import SwordClient, SwordItemTypeMapping


def unpack_zip(file):
    data_path = (
        tempfile.gettempdir()
        + "/"
        + current_app.config["WEKO_SEARCH_UI_IMPORT_TMP_PREFIX"]
        + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    )

    try:
        # Create temp dir for import data
        os.mkdir(data_path)

        # Extract zip file
        with ZipFile(file) as z:
            for info in z.infolist():
                try:
                    info.filename = info.orig_filename.encode("cp437").decode("cp932")
                    # replace backslash to slash
                    if os.sep != "/" and os.sep in info.filename:
                        info.filename = info.filename.replace(os.sep, "/")
                except Exception:
                    traceback.print_exc(file=sys.stdout)
                z.extract(info, path=data_path)

    except Exception as e:
        current_app.logger.error(f'An error occured while extraction the zip file')
        traceback.print_exc()
        return None

    return data_path

def get_mapping_by_token(access_token):
    """Get mapping by token.

    Get mapping for RO-Crate matadata by access token.

    Args:
        access_token (str): Access token.

    Returns:
        SwordItemTypeMapping: Mapping for RO-Crate matadata.
    """
    token = get_token(access_token=access_token)
    if token is None:
        current_app.logger.error(f"Token not found.")
        raise WekoSwordserverException(
            "Token not found.", errorType=ErrorType.ServerError
        )

    client_id = token.client_id
    sword_client = SwordClient.get_client_by_id(client_id)

    mapping_id = sword_client.mapping_id if sword_client is not None else None
    mapping = SwordItemTypeMapping.get_mapping_by_id(mapping_id)

    return mapping



def check_bagit_import_items(file, header, file_format):
    check_result = {}

    if isinstance(file, str):
        filename = file.split("/")[-1]
    else:
        filename = file.filename

    # TODO: extension zip in tmporary directory
    data_path = unpack_zip(file)

    # TODO: check request header

    sword_mapping = get_mapping_by_token(header["access_token"])
    if sword_mapping is None:
        current_app.logger.error(f"Mapping not found by your token.")
        raise WekoSwordserverException(
            "Mapping not found by your token.",
            errorType=ErrorType.MappingNotFound
        )

    mapping = json.loads(sword_mapping.mapping)
    register_format = sword_mapping.registration_type

    # TODO: validate mapping

    # TODO: make check_result

    return check_result, register_format


