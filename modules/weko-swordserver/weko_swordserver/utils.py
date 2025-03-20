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
                "SWORDBagIt requires metadate/sword.json."
            )
            raise WekoSwordserverException(
                "SWORDBagIt requires metadate/sword.json.",
                ErrorType.MetadataFormatNotAcceptable
                )
    elif "SimpleZip" in packaging:
        if "ro-crate-metadata.json" in file_list:
            file_format = "JSON"
        else:
            file_format = "OTHERS"
    else:
        current_app.logger.error(
            f"Not accept packaging format: {packaging}"
        )
        raise WekoSwordserverException(
            f"Not accept packaging format: {packaging}",
            ErrorType.PackagingFormatNotAcceptable
            )

    return file_format


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
            A tuple containing the SwordClient object and the SwordItemTypeMapping
            object. If the client or mapping is not found, the corresponding
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
