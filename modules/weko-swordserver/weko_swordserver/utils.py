# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

import os
import sys
import tempfile
import traceback
from base64 import b64encode
from datetime import datetime, timezone
from hashlib import sha256
from zipfile import ZipFile

from flask import current_app, request
from invenio_oauth2server.provider import get_token

from .errors import WekoSwordserverException, ErrorType
from .models import SwordClient, SwordItemTypeMapping


def check_import_file_format(file, packaging):
    """Check inport file format.

    Args:
        file (str): Import file
        packaging (str): Packaging in request header

    Raises:
        WekoSwordserverException: _description_

    Returns:
        str: Import file format
    """
    if packaging == 'SWORDBagIt':
        file_format = 'SWORD'
    elif packaging == 'SimpleZip':
        file_list = get_file_list_of_zip(file)
        if 'ro-crate-metadata.json' in file_list:
            file_format = 'ROCRATE'
        else:
            file_format = 'OTHERS'
    else:
        current_app.logger.info("No Packing Included")
        raise WekoSwordserverException(
            f"Unsupported packaging format: {packaging}.",
            ErrorType.BadRequest
            )

    return file_format


def get_file_list_of_zip(file):
    """Get file list of zip.

    Args:
        file (_type_): Zip file.

    Returns:
        list: File list
    """
    with ZipFile(file, 'r') as zip_ref:
        file_list =  zip_ref.namelist()

    return file_list


def unpack_zip(file):
    """Unpack zip file.

    Unpack zip file and return extracted files information.

    Args:
        file (FileStorage): Zip file.

    Returns:
        tuple (str, list[ZipInfo]): Extracted files path and file information

    """
    data_path = (
        tempfile.gettempdir()
        + "/"
        + current_app.config["WEKO_SEARCH_UI_IMPORT_TMP_PREFIX"]
        + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    )

    # Create temp dir for import data
    os.mkdir(data_path)

    # Extract zip file, Extracted files remain.
    with ZipFile(file) as zip_ref:
        file_list =  zip_ref.namelist()
        for info in zip_ref.infolist():
            try:
                info.filename = (
                    info.orig_filename.encode("cp437").decode("cp932"))
                # replace backslash to slash
                if os.sep != "/" and os.sep in info.filename:
                    info.filename = info.filename.replace(os.sep, "/")
            except Exception as ex:
                traceback.print_exc(file=sys.stdout)
            zip_ref.extract(info, path=data_path)

    return data_path, file_list


def is_valid_body_hash(digest, body):
    """Validate body hash.

    Validate body hash by comparing to digest in request headers.
    When body hash is valid : return True.
    Else : return False.

    Args:
        digest (): Digest in request headers.
        body (): Request body.

    Returns:
        bool: Check result.
    """
    body_hash = calculate_sha256(body)

    result = False

    if ('SHA-256=' in digest
        and digest.split('SHA-256=')[-1] == body_hash):
        result = True

    return result


def calculate_sha256(file):
    """Calculate SHA-256 of a file.

    Args:
        file (_type_): File to be calculated.

    Returns:
        _type_: Calculate result.
    """
    sha256_hash = sha256()
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.seek(0)

    return sha256_hash.hexdigest()


def check_rocrate_required_files(file_list):
    """Check RO-Crate required files.

    Args:
        file_list (list): FIle list of zip.

    Returns:
        list: List of results.
    """
    list_required_files = current_app.config.get(
        'WEKO_SWORDSERVER_REQUIRED_FILES_ROCRATE'
    )

    return [required_file in file_list
            for required_file in list_required_files]


def check_swordbagit_required_files(file_list):
    """Check SWORDBagIt required files.

    Args:
        file_list (list): FIle list of zip.

    Returns:
        list: List of results.
    """
    list_required_files = current_app.config.get(
        'WEKO_SWORDSERVER_REQUIRED_FILES_SWORD'
    )

    return [required_file in file_list
            for required_file in list_required_files]


def get_record_by_token(access_token):
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
        raise Exception("Token not found.")

    client_id = token.client_id
    sword_client = SwordClient.get_client_by_id(client_id)

    mapping_id = sword_client.mapping_id if sword_client is not None else None
    sword_mapping = SwordItemTypeMapping.get_mapping_by_id(mapping_id)

    return sword_client, sword_mapping
