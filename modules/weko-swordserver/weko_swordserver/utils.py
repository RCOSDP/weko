# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

import os
import tempfile
import traceback
from copy import deepcopy
from datetime import datetime, timezone
from dateutil import parser
from hashlib import sha256
from zipfile import ZipFile

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from invenio_accounts.models import User
from invenio_oauth2server.models import Token
from weko_accounts.models import ShibbolethUser

from .api import SwordClient, SwordItemTypeMapping
from .errors import WekoSwordserverException, ErrorType


def check_import_file_format(file, packaging):
    """Check inport file format.

    Args:
        file (`FileStorage`): Import file
        packaging (str): Packaging in request header

    Raises:
        WekoSwordserverException: _description_

    Returns:
        str: Import file format
    """
    with ZipFile(file, "r") as zip_ref:
        file_list =  zip_ref.namelist()

    if "SWORDBagIt" in packaging:
        if "metadata/sword.json" in file_list:
            file_format = "JSON"
        else:
            current_app.logger.error(
                "metadate/sword.json is not found in SWORDBagIt."
            )
            raise WekoSwordserverException(
                "SWORDBagIt requires metadate/sword.json.",
                ErrorType.MetadataFormatNotAcceptable
                )
    elif "SimpleZip" in packaging:
        if "ro-crate-metadata.json" in file_list:
            file_format = "JSON"
        elif any(filename.split("/")[1].endswith(".xml")
                for filename in file_list if "/" in filename
            ):
            file_format = "XML"
        elif any(filename.split("/")[1].endswith((".tsv", ".csv"))
                for filename in file_list if "/" in filename
            ):
            file_format = "TSV/CSV"
        else:
            current_app.logger.error(
                "ro-crate-metadata.json or other metadata file is not found."
            )
            raise WekoSwordserverException(
                "SimpleZip requires ro-crate-metadata.json or other metadata file.",
                ErrorType.MetadataFormatNotAcceptable
                )
    else:
        current_app.logger.error(
            f"Not accept packaging format: {packaging}"
        )
        raise WekoSwordserverException(
            f"Not accept packaging format: {packaging}",
            ErrorType.PackagingFormatNotAcceptable
            )

    return file_format

def get_shared_id_from_on_behalf_of(on_behalf_of):
    """Get shared ID from on-behalf-of.

    Get shared ID from on-behalf-of.
    If on-behalf-of is not shared ID, return None.

    Args:
        on_behalf_of (str): On-behalf-of in request
    Returns:
        int: Shared ID
    """
    shared_id = -1
    if on_behalf_of is None:
        return shared_id

    try:
        # get weko user id from email
        user = User.query.filter_by(email=on_behalf_of).one_or_none()
        shared_id = user.id if user is not None else None
        if shared_id is None:
            # get weko user id from personal access token
            token = (
                Token.query
                .filter_by(access_token=on_behalf_of).one_or_none()
            )
            shared_id = token.user_id if token is not None else None
        if shared_id is None:
            # get weko user id from shibboleth user eppn
            shib_user = (
                ShibbolethUser.query
                .filter_by(shib_eppn=on_behalf_of).one_or_none()
            )
            shared_id = shib_user.weko_uid if shib_user is not None else None
    except SQLAlchemyError as ex:
        current_app.logger.error(
            "Somthing went wrong while searching user by On-Behalf-Of.")
        traceback.print_exc()
        raise WekoSwordserverException(
            "An error occurred while searching user by On-Behalf-Of.",
            errorType=ErrorType.ServerError
        ) from ex
    return shared_id

def unpack_zip(file):
    """Unpack zip file.

    Unpack zip file and return extracted files information.

    Args:
        file (FileStorage | str): Zip file object or file path.

    Returns:
        tuple (str, list[str]):
        data_path: Path of extracted files, file_list: List of extracted files.

    """
    data_path = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_SEARCH_UI_IMPORT_TMP_PREFIX")
            + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]
    )

    # Create temp dir for import data
    os.mkdir(data_path)

    # Extract zip file, Extracted files remain.
    with ZipFile(file) as zip_ref:
        file_list = []
        for info in zip_ref.infolist():
            try:
                info.filename = (
                    info.orig_filename.encode("cp437").decode("cp932"))
                # replace backslash to slash
                if os.sep != "/" and os.sep in info.filename:
                    info.filename = info.filename.replace(os.sep, "/")
                file_list.append(info.filename)
            except Exception:
                traceback.print_exc()
                raise
        zip_ref.extractall(path=data_path)

    return data_path, file_list


def is_valid_file_hash(expected_hash, file):
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
    file.seek(0)
    hasher = sha256()
    for chunk in iter(lambda: file.read(4096), b""):
        hasher.update(chunk)
    body_hash = hasher.hexdigest()

    return expected_hash == body_hash


def get_record_by_client_id(client_id):
    """
    Get the SwordClient and SwordItemTypeMapping records associated with client ID.

    Args:
        client_id (str): The ID of the client to get the settings records for.

    Returns:
        tuple (SwordClientModel, SwordItemTypeMappingModel):
            SwordClientModel: The SwordClient record associated with the client ID.
            SwordItemTypeMappingModel: The SwordItemTypeMapping record associated with
            the client ID.
            If the client or mapping is not found, the corresponding
            value in the tuple will be None.
    """
    sword_client = SwordClient.get_client_by_id(client_id)
    mapping_id = sword_client.mapping_id if sword_client is not None else None
    sword_mapping = SwordItemTypeMapping.get_mapping_by_id(mapping_id)
    return sword_client, sword_mapping


def process_json(json_ld):
    """Process json-ld.

    Process RO-Crate metadata json-ld data.
    Pick up necessary data from @graph and resolve links
    in order to map to WEKO item type.

    Args:
        json_ld (dict): Json-ld data.

    Returns:
        dict: Processed json data.
    """
    json = deepcopy(json_ld)

    # transform list which contains @id to dict in @graph
    if "@graph" in json and isinstance(json["@graph"], list):
        new_value = {}
        for v in json["@graph"]:
            if isinstance(v, dict) and "@id" in v:
                new_value[v["@id"]] = v
            else:
                current_app.logger.error("Invalid json-ld format.")
                raise WekoSwordserverException(
                    "Invalid json-ld format.",
                    ErrorType.MetadataFormatNotAcceptable
                )
        json["@graph"] = new_value
    # TODO: support SWORD json-ld format
    else:
        current_app.logger.error("Invalid json-ld format.")
        raise WekoSwordserverException(
            "Invalid json-ld format.",
            ErrorType.MetadataFormatNotAcceptable
        )
    # Remove unnecessary keys
    json = json.get("@graph")

    def _resolve_link(parent, key, value):
        if isinstance(value, dict):
            if len(value) == 1 and "@id" in value and value["@id"] in json:
                parent[key] = json[value["@id"]]
            else:
                for k, v in value.items():
                    _resolve_link(value, k, v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                _resolve_link(value, i, v)

    for key, value in json.items():
        _resolve_link(json, key, value)

    # replace Dataset identifier
    id = current_app.config["WEKO_SWORDSERVER_DATASET_ROOT"].get("")
    enc = current_app.config["WEKO_SWORDSERVER_DATASET_ROOT"].get("enc")
    json.update({enc: json.pop(id)})

    # prepare json for mapper format
    json = {
        "record": {
            "header": {
                "identifier": json.get(enc).get("name"),
                "datestamp": (
                    parser.parse(json.get(enc).pop("datePublished"))
                    .strftime('%Y-%m-%d')
                ),
                "publish_status": json.get(enc).pop("accessMode"),
                "indextree": (
                    int(json.get(enc).get("isPartOf").pop("sameAs", "/").split("/")[-1])
                        if "sameAs" in json.get(enc).get("isPartOf")
                        else None
                )
            },
            "metadata": json
        }
    }

    return json

def get_priority(link_data):
    """Determine the priority of link data based on specific conditions.

    Args:
        link_data (list): A list of dictionaries containing 'sele_id' and 'item_id'.

    Returns:
        int: The priority level (1 to 6) based on the conditions.
    """
    sele_ids = [link['sele_id'] for link in link_data]
    item_ids = [link['item_id'] for link in link_data]

    # Check conditions
    all_is_supplement_to = all(
        sele_id == 'isSupplementTo'
        for sele_id in sele_ids
        )
    all_item_ids_not_numbers = all(
        not item_id.isdigit()
        for item_id in item_ids
        )
    has_item_ids_not_numbers = any(
        not item_id.isdigit()
        for item_id in item_ids
        )
    has_is_supplement_to_with_not_number = any(
        link['sele_id'] == 'isSupplementTo' and not link['item_id'].isdigit()
        for link in link_data
    )
    all_is_supplement_to_item_ids_are_numbers = all(
        link['item_id'].isdigit() for link in link_data
        if link['sele_id'] == 'isSupplementTo'
    )
    all_is_supplemented_by = all(
        sele_id == 'isSupplementedBy'
        for sele_id in sele_ids
        )

    # Determine priority
    if all_is_supplement_to and all_item_ids_not_numbers:
        return 1  # Highest priority
    elif all_is_supplement_to and has_item_ids_not_numbers:
        return 2  # Second priority
    elif has_is_supplement_to_with_not_number:
        return 3  # Third priority
    elif all_is_supplement_to and all_is_supplement_to_item_ids_are_numbers:
        return 4  # Fourth priority
    elif all_is_supplemented_by:
        return 5  # Lowest priority
    else:
        return 6  # Other cases


def update_item_ids(list_record, new_id):
    """Iterate through list_record, check and update item_id.

    Args:
        list_record (list): A list containing multiple ITEMs.
        new_id (str): The new ID used to overwrite item_id.

    Returns:
        list: The updated list_record.

    Raises:
        ValueError: If list_record is not a list.
    """
    if not isinstance(list_record, list):
        raise ValueError("list_record must be a list.")

    # Create a dictionary to map identifiers to their respective items
    identifier_to_item = {}
    for item in list_record:
        if not isinstance(item, dict):
            continue

        metadata = item.get('metadata')
        if not metadata or not hasattr(metadata, 'id'):
            continue  # Skip if metadata is missing or doesn't have 'id'

        current_identifier = getattr(metadata, 'id')
        if current_identifier is not None:  # Skip if identifier is empty
            identifier_to_item[current_identifier] = item

    # Iterate through each ITEM in list_record
    for item in list_record:
        if not isinstance(item, dict):
            continue

        metadata = item.get('metadata')
        if not metadata or not hasattr(metadata, 'link_data'):
            continue  # Skip if metadata is missing or doesn't have 'link_data'

        link_data = getattr(metadata, 'link_data', [])
        if not isinstance(link_data, list):
            continue

        for link_item in link_data:
            if not isinstance(link_item, dict):
                continue

            item_id = link_item.get("item_id")
            sele_id = link_item.get("sele_id")
            if item_id in identifier_to_item and sele_id == "isSupplementedBy":
                # If a match is found, overwrite item_id with new_id
                link_item["item_id"] = new_id
                current_app.logger.info(
                    f"Updated item_id {item_id} to {new_id} "
                    f"in ITEM {item.get('identifier')}"
                )

    return list_record
