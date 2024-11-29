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
from copy import deepcopy
from datetime import datetime, timezone
from dateutil import parser
from hashlib import sha256
from zipfile import ZipFile

from flask import current_app
from invenio_oauth2server.models import Token

from .api import SwordClient, SwordItemTypeMapping
from .errors import WekoSwordserverException, ErrorType
from .decorators import check_digest

@check_digest()
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
    if "SWORDBagIt" in packaging:
        file_list = get_file_list_of_zip(file)
        if "metadata/sword.json" in file_list:
            file_format = "JSON"
        else:
            raise WekoSwordserverException(
                "SWORDBagIt requires metadate/sword.json.",
                ErrorType.MetadataFormatNotAcceptable
                )
    elif "SimpleZip" in packaging:
        file_list = get_file_list_of_zip(file)
        if "ro-crate-metadata.json" in file_list:
            file_format = "JSON"
        else:
            file_format = "OTHERS"
    else:
        raise WekoSwordserverException(
            f"Not accept packaging format: {packaging}",
            ErrorType.PackagingFormatNotAcceptable
            )

    return file_format


def get_file_list_of_zip(file):
    """Get file list of zip.

    Args:
        file (_type_): Zip file.

    Returns:
        list: File list
    """
    with ZipFile(file, "r") as zip_ref:
        file_list =  zip_ref.namelist()

    return file_list


def unpack_zip(file):
    """Unpack zip file.

    Unpack zip file and return extracted files information.

    Args:
        file (FileStorage | str): Zip file object or file path.

    Returns:
        tuple (str, list[str]):
        data_path: Path of extracted files, file_list: List of extracted files.

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
    sha256_hash = sha256()
    for byte_block in iter(lambda: body.read(4096), b""):
        sha256_hash.update(byte_block)
    body.seek(0)
    body_hash = sha256_hash.hexdigest()

    result = False
    if (digest is not None and "SHA-256=" in digest
        and digest.split("SHA-256=")[-1] == body_hash):
        result = True

    return result


def get_record_by_token(access_token):
    """Get mapping by token.

    Get mapping for RO-Crate matadata by access token.

    Args:
        access_token (str): Access token.

    Returns:
        SwordItemTypeMapping: Mapping for RO-Crate matadata.
    """
    token = Token.query.filter_by(access_token=access_token).first()
    if token is None:
        current_app.logger.error(f"Accesstoken not found.")
        raise Exception("Accesstoken not found.")

    client_id = token.client_id
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

    # transform list that contains @id to dict in @graph
    if "@graph" in json and isinstance(json["@graph"], list):
        new_value = {}
        for v in json["@graph"]:
            if isinstance(v, dict) and "@id" in v:
                new_value[v["@id"]] = v
            else:
                new_value = value
                break
        json["@graph"] = new_value
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
