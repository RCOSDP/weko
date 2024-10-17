# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

import bagit
import json
from flask import current_app

from weko_records.api import ItemTypes
from .errors import ErrorType, WekoSwordserverException
from .utils import (
    check_rocrate_required_files,
    check_swordbagit_required_files,
    get_mapping_by_token,
    unpack_zip)


def check_import_items(file, is_change_identifier: bool = False):
    pass



def check_bagit_import_items(file, header_info, file_format):
    """Check bagit import items.

    Check that the actual file contents match the recorded hashes stored
    in the manifest files and mapping metadata to the item type.

    Args:
        file (FileStorage | str): File object or file path.
        header_info (dict):
            Request header information. It should contain "access_token".
        file_format (str): File format. "ROCRATE" or "SWORD".

    Returns:
        dict: Result of mapping to item type
        str: Registration type "Direct" or "Workflow"

    """
    check_result = {}

    if isinstance(file["file"], str):
        filename = file["file"].split("/")[-1]
    else:
        filename = file["file"].filename

    # TODO: extension zip in tmporary directory
    data_path, file_list = unpack_zip(file)
    check_result.update({"data_path": data_path})

    # TODO: check request header
    # Check if all required files are contained
    if file_format == 'ROCRATE':
        all_file_contained = all(check_rocrate_required_files(file_list))
    elif file_format == 'SWORD':
        all_file_contained = all(check_swordbagit_required_files(file_list))

    if not all_file_contained:
        raise ValueError(
            'Metadata JSON File Or "manifest-sha-256.txt" Is Lacking')

    # Check if the bag is valid
    try:
        bag = bagit.Bag(data_path)
        bag.validate()
    except bagit.BagValidationError as ex:
        current_app.logger.error(ex)
        raise WekoSwordserverException(
            "Bag validation failed.", errorType=ErrorType.BadRequest
        )

    sword_mapping = get_mapping_by_token(header_info["access_token"])
    if sword_mapping is None:
        current_app.logger.error(f"Mapping not found by your token.")
        raise WekoSwordserverException(
            "Mapping not found by your token.",
            errorType=ErrorType.MappingNotFound
        )

    register_format = sword_mapping.registration_type
    mapping = json.loads(sword_mapping.mapping)
    item_type = ItemTypes.get_by_id(sword_mapping.item_type_id)

    # TODO: validate mapping

    item_type_name = item_type.item_type_name

    # TODO: make check_result

    return check_result, register_format
