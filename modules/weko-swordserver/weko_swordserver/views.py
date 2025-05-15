# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

from __future__ import absolute_import, print_function

import os
import shutil
from datetime import datetime, timedelta
import traceback

from flask import Blueprint, current_app, jsonify, request, url_for, abort, Response
from flask_login import current_user
from flask_limiter.errors import RateLimitExceeded
from sword3common import (
    ServiceDocument, StatusDocument, constants, Error as sword3commonError
)
from sword3common.lib.seamless import SeamlessException
from werkzeug.http import parse_options_header

from invenio_db import db
from invenio_deposit.scopes import write_scope, actions_scope
from invenio_files_rest.permissions import has_update_version_role
from invenio_oaiserver.api import OaiIdentify
from invenio_oauth2server.decorators import require_oauth_scopes
from invenio_oauth2server.ext import verify_oauth_token_and_set_current_user
from invenio_oauth2server.provider import oauth2

from weko_accounts.utils import roles_required
from weko_admin.api import TempDirInfo
from weko_deposit.api import WekoRecord
from weko_items_ui.scopes import item_create_scope, item_update_scope, item_delete_scope
from weko_items_ui.utils import send_mail_direct_registered, send_mail_item_deleted
from weko_notifications.utils import notify_item_imported, notify_item_deleted
from weko_records.api import JsonldMapping
from weko_records_ui.utils import get_record_permalink, soft_delete
from weko_search_ui.utils import (
    import_items_to_system, import_items_to_activity,
    delete_items_with_activity
)
from weko_workflow.utils import get_site_info_name
from weko_workflow.scopes import activity_scope

from .config import WEKO_SWORDSERVER_DEPOSIT_ROLE_ENABLE
from .decorators import check_on_behalf_of, check_package_contents
from .errors import ErrorType, WekoSwordserverException
from .utils import (
    check_import_file_format,
    is_valid_file_hash,
    check_import_items,
    get_deletion_type,
    update_item_ids,
    get_shared_id_from_on_behalf_of
)
from weko_accounts.utils import limiter


class SwordState:
    accepted = "http://purl.org/net/sword/3.0/state/accepted"
    inProgress = "http://purl.org/net/sword/3.0/state/inProgress"
    inWorkflow ="http://purl.org/net/sword/3.0/state/inWorkflow"
    ingested = "http://purl.org/net/sword/3.0/state/ingested"
    rejected = "http://purl.org/net/sword/3.0/state/rejected"
    deleted = "http://purl.org/net/sword/3.0/state/deleted"


blueprint = Blueprint(
    "weko_swordserver",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/sword",
)
blueprint.before_request(verify_oauth_token_and_set_current_user)


@blueprint.route("/service-document", methods=["GET"])
@oauth2.require_oauth()
@limiter.limit("")
@check_on_behalf_of()
def get_service_document():
    """Retrieve the Service Document

    https://swordapp.github.io/swordv3/swordv3-behaviours.html#1

    Request from the server a list of the Service-URLs that the client can deposit
    to. A Service-URL allows the server to support multiple different deposit
    conditions - each URL may have its own set of rules/workflows behind it;
    for example, Service-URLs may be subject-specific, organizational-specific,
    or process-specific. It is up to the client to determine which is the suitable
    URL for its deposit, based on the information provided by the server.
    The list of Service-URLs may vary depending on the authentication credentials
    supplied by the client.

    This request can be made against a root Service-URL, which will describe the
    capabilities of the entire server, for information about the full list of
    Service-URLs, or can be made against an individual Service-URL for information
    just about that service.

    Protocol Operation
        * GET Service-URL: https://swordapp.github.io/swordv3/swordv3.html#7.3.1

    Request Requirements
        * MAY specify Authorization and On-Behalf-Of headers (i.e. if authenticating this request)

    Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request

    Response Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST only list Service-URLs in the Service Document for which a deposit request would be permitted
        * MUST respond with a valid Service Document or a suitable error response

    Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)

    Set raw data to ServiceDocument
    """
    repositoryName, site_name_ja = get_site_info_name()
    if repositoryName is None or len(repositoryName) == 0:
        identify = OaiIdentify.get_all()
        repositoryName = current_app.config["THEME_SITENAME"]
        if identify is not None:
            repositoryName = identify.repositoryName

    raw_data = {
        "@context": constants.JSON_LD_CONTEXT,
        "@type": constants.DocumentType.ServiceDocument,
        "@id": request.url,
        "root": request.url,
        "dc:title": repositoryName,
        "version": current_app.config["WEKO_SWORDSERVER_SWORD_VERSION"],
        "accept": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT"],
        "digest": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_DIGEST"],
        "acceptArchiveFormat": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT"],
        "acceptDeposits": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_DEPOSITS"],
        "acceptMetadata": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_METADATA"],
        "acceptPackaging": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING"],
        "authentication": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_AUTHENTICATION"],
        "byReferenceDeposit": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_BY_REFERENCE_DEPOSIT"],
        "collectionPolicy": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_COLLECTION_POLICY"],
        "dcterms:abstract": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ABSTRACT"],
        "maxAssembledSize": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_ASSEMBLED_SIZE"],
        "maxByReferenceSize": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_BY_REFERENCE_SIZE"],
        "maxSegments": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_SEGMENTS"],
        "maxUploadSize": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE"],
        "onBehalfOf": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF"],
        "services": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_SERVICES"],
        "staging": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_STAGING"],
        "stagingMaxIdle": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_STAGING_MAX_IDLE"],
        "treatment": current_app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_TREATMENT"],
    }
    serviceDocument = ServiceDocument(raw=raw_data)

    return jsonify(serviceDocument.data)


@blueprint.route("/service-document", methods=["POST"])
@oauth2.require_oauth()
@limiter.limit("")
@require_oauth_scopes(write_scope.id, actions_scope.id)
@require_oauth_scopes(item_create_scope.id)
@roles_required(WEKO_SWORDSERVER_DEPOSIT_ROLE_ENABLE)
@check_on_behalf_of()
@check_package_contents()
def post_service_document():
    """Creating Objects with Packaged Content

    https://swordapp.github.io/swordv3/swordv3-behaviours.html#2.6

    Create a new Object on the server, sending a single Binary File.
    The Binary File itself is specified as Packaged Content, which the server
    may understand how to unpack.

    Protocol Operation
        * POST Service-URL: https://swordapp.github.io/swordv3/swordv3.html#7.3.2

    Request Requirements
        * MAY specify Authorization and On-Behalf-Of headers (i.e. if authenticating this request)
        * MUST provide the Content-Disposition header, with the appropriate value for the request
        * MUST provide the Digest header
        * SHOULD provide the Content-Length
        * MUST provide the Content-Type header
        * MUST provide the Packaging header
        * MUST provide Packaged Content in the request body
        * MAY provide the Slug header
        * MAY provide the In-Progress header

    Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
        * MUST verify that the content matches the Digest header
        * MUST verify that the supplied content matches the Content-Length if this is provided
        * If all preconditions are met, MUST either accept the deposit request immediately, queue the request for processing, or respond with an error
        * If accepting the request MUST attach the supplied file to the Object as an originalDeposit
        * The server MAY attempt to unpack the file, and create derivedResources from it.
        * If a Slug header is provided, MAY use this as the identifier for the newly created Object.
        * If accepting the request MUST create a new Object
        * If no In-Progress header is provided, MUST assume that it is false
        * If In-Progress is false, SHOULD expect further updates to the item, and not progress it through any ingest workflows yet.

    Response Requirements
        * MUST include ETag header if implementing concurrency control
        * MUST include one or more File-URLs for the deposited content in the Status document. The behavior of these File-URLs may vary depending on the type of content deposited (e.g. ByReference and Segmented Uploads do not need to be immediately retrievable)
        * MUST respond with a Location header, containing the Object-URL
        * MUST respond with a valid Status Document or a suitable error response
        * Status Document MUST be available on GET to the Object-URL in the Location header immediately (irrespective of whether this is a 201 or 202 response)
        * MUST respond with a 201 if the item was created immediately, a 202 if the item was queued for import, or raise an error.

    Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
        * If one or more of the digests provided by the client that the server checked did not match, MAY respond with 412 (DigestMismatch). Note that servers MAY NOT check digests in real-time.
        * If the body content could not be read correctly, MAY return a 400 (ContentMalformed)
        * If the Content-Type header contains a format that the server cannot accept, MUST respond with 415 (ContentTypeNotAcceptable)
        * If the body content is larger than the maximum allowed by the server, MAY return 413 (MaxUploadSizeExceeded)
        * If the server does not accept packages in the format identified in the Packaging header, MUST respond with a 415 (PackagingFormatNotAcceptable)
        * If the Packaging header does not match the format found in the body content, SHOULD return 415 (FormatHeaderMismatch). Note that the server may not be able to inspect the package during the request-response, so MAY NOT return this response.

    Check content-disposition
        Request format:
            Content-Disposition	attachment; filename=[filename]
    """
    content_disposition, content_disposition_options = parse_options_header(
        request.headers.get("Content-Disposition") or ""
    )

    filename = content_disposition_options.get("filename")
    if (content_disposition != "attachment" or filename is None):
        current_app.logger.error("Cannot get filename by Content-Disposition.")
        raise WekoSwordserverException(
            "Cannot get filename by Content-Disposition.",
            ErrorType.BadRequest
        )

    # Check import item
    file = None
    for _, value in request.files.items():
        if value.filename == filename:
            file = value
    if file is None:
        current_app.logger.error(f"Not found {filename} in request body.")
        raise WekoSwordserverException(
            f"Not found {filename} in request body.", ErrorType.BadRequest
        )

    # check packaging, "SimpleZip" or "SWORDBagIt"
    packaging = request.headers.get("Packaging")
    file_format = check_import_file_format(file, packaging)

    on_behalf_of = request.headers.get("On-Behalf-Of")
    shared_id = get_shared_id_from_on_behalf_of(on_behalf_of)
    client_id = request.oauth.client.client_id

    digest = request.headers.get("Digest")
    if current_app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"]:
        if (
            not isinstance(digest, str)
            or not digest.startswith("SHA-256=")
            or not is_valid_file_hash(digest.split("SHA-256=")[-1], file)
        ):
            current_app.logger.error(
                "Request body and digest verification failed."
            )
            raise WekoSwordserverException(
                "Request body and digest verification failed.",
                ErrorType.DigestMismatch
            )

    check_result = check_import_items(
        file, file_format, shared_id=shared_id,
        packaging=packaging, client_id=client_id
    )

    data_path = check_result.get("data_path","")
    expire = datetime.now() + timedelta(days=1)
    TempDirInfo().set(
        data_path,
        {"expire": expire.strftime("%Y-%m-%d %H:%M:%S")}
    )

    register_type = check_result.get("register_type")
    if register_type == "Workflow":
        # activity scope check
        required_scopes = set([activity_scope.id])
        token_scopes = set(request.oauth.access_token.scopes)
        if not required_scopes.issubset(token_scopes):
            abort(403)

    if check_result.get("error"):
        current_app.logger.error(
            f"Error in item to import: {check_result.get('error')}"
        )
        raise WekoSwordserverException(
            f"Item check error: {check_result.get('error')}",
            ErrorType.ContentMalformed
        )

    # Validate items in the check result
    for item in check_result.get("list_record") or [{}]:
        if not item or item.get("errors"):
            error_msg = (
                ", ".join(item.get("errors"))
                if item and item.get("errors") else "item_missing"
            )
            current_app.logger.error(f"Error in check_import_items: {error_msg}")
            raise WekoSwordserverException(
                f"Item check error: {error_msg}",
                ErrorType.ContentMalformed
            )

        if item.get("status") != "new":
            current_app.logger.error(
                f"This item is already registered: {item.get('item_title')}"
            )
            raise WekoSwordserverException(
                f"This item is already registered: {item.get('item_title')}.",
                ErrorType.BadRequest,
            )

        if check_result.get("duplicate_check", False):
            from weko_items_ui.utils import check_duplicate
            result, list_id, list_url = check_duplicate(item["metadata"], is_item=True)
            if result:
                current_app.logger.error(
                    f"New item appears to be a duplicate: {list_id}"
                )
                raise WekoSwordserverException(
                    f"Some similar items are already registered: {list_url}.",
                    ErrorType.BadRequest,
                )

    # Prepare request information
    owner = -1
    if current_user.is_authenticated:
        owner = current_user.id
    request_info = {
        "remote_addr": request.remote_addr,
        "referrer": request.referrer,
        "hostname": request.host,
        "user_id": owner,
        "action": "IMPORT",
        "workflow_id": check_result.get("workflow_id"),
    }

    # Define a nested function to process a single item
    def process_item(item, request_info):
        """Process a single item for import.

        Args:
            item (dict): The item to process.
            request_info (dict): Information about the request.

        Returns:
            tuple: A tuple containing the response and the record ID.
        """
        activity_id, recid, error = None, None, None
        if register_type == "Direct":
            import_result = import_items_to_system(
                item, request_info=request_info
            )
            if not import_result.get("success"):
                current_app.logger.error(
                    f"Error in import_items_to_system: {item.get('error_id')}"
                )
                error = str(item.get('error_id'))
            else:
                recid = str(import_result.get("recid"))
                notify_item_imported(
                    current_user.id, recid, current_user.id, shared_id=shared_id
                )
                send_mail_direct_registered(recid, current_user.id)

        elif register_type == "Workflow":
            url, recid, _ , error = import_items_to_activity(
                item, request_info=request_info
            )
            activity_id = str(url.split("/")[-1])

        return activity_id, recid, error

    response = {}
    warns = []
    activity_id = None
    recid = None
    # Process and register items
    for item in check_result["list_record"]:
        item["root_path"] = os.path.join(data_path, "data")
        try:
            activity_id, recid, error = process_item(item, request_info)
            if error:
                warns.append((error, activity_id, recid))
            if file_format == "JSON":
                update_item_ids(
                    check_result["list_record"], recid, item.get("_id"))
        except Exception as ex:
            current_app.logger.error(f"Unexpected error: {ex}")
            traceback.print_exc()
            warns.append(("Unexpected error: {ex}", activity_id, recid))
            continue  # Skip to the next iteration

    # Clean up temporary directory
    if os.path.exists(data_path):
        shutil.rmtree(data_path)
        TempDirInfo().delete(data_path)

    current_app.logger.info(
        f"Items imported via SWORD api by {request.oauth.client.name} (recid={recid})"
    )
    if len(warns) > 0:
        if register_type == "Direct":
            raise WekoSwordserverException(
                "Failed to import item.", ErrorType.ServerError)
        else:
            error_messages = "; ".join(
                [
                    "{error} Please open the following URL to continue "
                    "with the remaining operations.{url}: Item id: {recid}."
                    .format(
                        error=error,
                        url=url_for(
                            "weko_workflow.display_activity",
                            activity_id=activity_id, _external=True
                        ),
                        recid=recid
                    )
                    for error, activity_id, recid in warns
                ]
            )

        response = jsonify(
            _create_error_document(
                ErrorType.ContentMalformed.type, error_messages
            )
        )
    else:
        if register_type == "Direct":
            response = jsonify(_get_status_document(recid))
        elif register_type == "Workflow":
            response = jsonify(_get_status_workflow_document(activity_id,recid))

    return response

@blueprint.route("/deposit/<recid>", methods=["PUT"])
@oauth2.require_oauth()
@limiter.limit("")
@require_oauth_scopes(write_scope.id, actions_scope.id)
@require_oauth_scopes(item_update_scope.id)
@roles_required(WEKO_SWORDSERVER_DEPOSIT_ROLE_ENABLE)
@check_on_behalf_of()
@check_package_contents()
def put_object(recid):
    """Replacing an Object with Packaged Content

    https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.12

    Replace in its entirety the Object, including all Metadata and Files, with
    the Metadata and Files contained in the Packaged Content. All previous files
    and metadata will be removed, and new ones will replace them. The server may
    or may not keep old versions of the content available.

    Args:
        recid (str): Record Identifier.

    Protocol Operation
        * PUT Object-URL: https://swordapp.github.io/swordv3/swordv3.html#7.3.5

    Request Requirements
        * MAY specify Authorization and On-Behalf-Of headers (i.e. if authenticating this request)
        * MUST provide the Content-Disposition header, with the appropriate value for the request
        * MUST provide the Digest header
        * SHOULD provide the Content-Length
        * MUST provide the Content-Type header
        * MUST provide the Packaging header
        * MUST provide Packaged Content in the request body
        * MUST include the If-Match header, if the server implements concurrency control
        * MAY provide the In-Progress header

    Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
        * MUST verify that the content matches the Digest header
        * MUST verify that the supplied content matches the Content-Length if this is provided
        * If all preconditions are met, MUST either accept the deposit request immediately, queue the request for processing, or respond with an error
        * If accepting the request MUST attach the supplied file to the Object as an originalDeposit
        * The server MAY attempt to unpack the file, and create derivedResources from it.
        * MUST reject the request if the If-Match header does not match the current ETag of the resource
        * If no In-Progress header is provided, MUST assume that it is false
        * If accepting the new File, MUST remove all existing Files from the Object and replace with the new File. The new File should be marked as an originalDeposit. The server MUST also remove all Metadata, so the Metadata Resource contains no fields.

    Response Requirements
        * MUST include ETag header if implementing concurrency control
        * MUST include one or more File-URLs for the deposited content in the Status document. The behaviour of these File-URLs may vary depending on the type of content deposited (e.g. ByReference and Segmented Uploads do not need to be immediately retrievable)
        * MUST respond with a valid Status Document or a suitable error response
        * MUST include ETag header if implementing concurrency control
        * MUST respond with a 200 if the request was accepted immediately, a 202 if the request was queued for processing, or raise an error.

    Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
        * If one or more of the digests provided by the client that the server checked did not match, MAY respond with 412 (DigestMismatch). Note that servers MAY NOT check digests in real-time.
        * If the body content could not be read correctly, MAY return a 400 (ContentMalformed)
        * If the Content-Type header contains a format that the server cannot accept, MUST respond with 415 (ContentTypeNotAcceptable)
        * If the body content is larger than the maximum allowed by the server, MAY return 413 (MaxUploadSizeExceeded)
        * If the server does not accept packages in the format identified in the Packaging header, MUST respond with a 415 (PackagingFormatNotAcceptable)
        * If the Packaging header does not match the format found in the body content, SHOULD return 415 (FormatHeaderMismatch). Note that the server may not be able to inspect the package during the request-response, so MAY NOT return this response.
        * For servers implementing concurrency control, if the If-Match header does not match the current ETag, MUST respond with 412 (ETagNotMatched)
        * For servers implementing concurrency control, if no If-Match header is provided, MUST respond with 412 (ETagRequired)

    Check content-disposition
        Request format:
            Content-Disposition	attachment; filename=[filename]
    """
    content_disposition, content_disposition_options = parse_options_header(
        request.headers.get("Content-Disposition") or ""
    )

    filename = content_disposition_options.get("filename")
    if content_disposition != "attachment" or filename is None:
        current_app.logger.error("Cannot get filename by Content-Disposition.")
        raise WekoSwordserverException(
            "Cannot get filename by Content-Disposition.",
            ErrorType.BadRequest
        )

    # Check import item
    file = None
    for _, value in request.files.items():
        if value.filename == filename:
            file = value
    if file is None:
        current_app.logger.error(f"Not found {filename} in request body.")
        raise WekoSwordserverException(
            f"Not found {filename} in request body.", ErrorType.BadRequest
        )

    # check packaging, "SimpleZip" or "SWORDBagIt"
    packaging = request.headers.get("Packaging")
    file_format = check_import_file_format(file, packaging)

    on_behalf_of = request.headers.get("On-Behalf-Of")
    shared_id = get_shared_id_from_on_behalf_of(on_behalf_of)
    client_id = request.oauth.client.client_id

    digest = request.headers.get("Digest")
    if current_app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"]:
        if (
            not isinstance(digest, str)
            or not digest.startswith("SHA-256=")
            or not is_valid_file_hash(digest.split("SHA-256=")[-1], file)
        ):
            current_app.logger.error(
                "Request body and digest verification failed."
            )
            raise WekoSwordserverException(
                "Request body and digest verification failed.",
                ErrorType.DigestMismatch
            )

    check_result = check_import_items(
        file, file_format, shared_id=shared_id,
        packaging=packaging, client_id=client_id
    )

    data_path = check_result.get("data_path","")
    expire = datetime.now() + timedelta(days=1)
    TempDirInfo().set(
        data_path,
        {"expire": expire.strftime("%Y-%m-%d %H:%M:%S")}
    )

    register_type = check_result.get("register_type")
    if register_type == "Workflow":
        # activity scope check
        required_scopes = set([activity_scope.id])
        token_scopes = set(request.oauth.access_token.scopes)
        if not required_scopes.issubset(token_scopes):
            abort(403)

    if check_result.get("error"):
        current_app.logger.error(
            f"Error in check_import_items: {check_result.get('error')}"
        )
        raise WekoSwordserverException(
            f"Item check error: {check_result.get('error')}",
            ErrorType.ContentMalformed
        )

    # only first item
    item = (check_result.get("list_record") or [{}])[0]
    if not item or item.get("errors"):
        error_msg = (
            ", ".join(item.get("errors"))
            if item and item.get("errors") else "item_missing"
        )
        current_app.logger.error(f"Error in check_import_items: {error_msg}")
        raise WekoSwordserverException(
            f"Item check error: {error_msg}",
            ErrorType.ContentMalformed
        )

    if item.get("status") == "new":
        current_app.logger.error(
            f"This item is not registered yet: {item.get('item_title')}"
        )
        raise WekoSwordserverException(
            f"This item is not registered yet: {item.get('item_title')}",
            ErrorType.BadRequest,
        )
    if item.get("id") != recid:
        current_app.logger.error(
            f"Item id does not match. item: {item.get('id')}, request: {recid}"
        )
        raise WekoSwordserverException(
            f"Item id does not match. item: {item.get('id')}, request: {recid}",
            ErrorType.BadRequest,
        )
    if check_result.get("duplicate_check", False):
        from weko_items_ui.utils import check_duplicate
        result, list_id, list_url = check_duplicate(item["metadata"], is_item=True)
        if result:
            current_app.logger.error(
                f"New item appears to be a duplicate: {list_id}"
            )
            raise WekoSwordserverException(
                f"Some similar items are already registered: {list_url}.",
                ErrorType.BadRequest,
            )

    item["root_path"] = os.path.join(data_path, "data")

    # Prepare request information
    owner = -1
    if current_user.is_authenticated:
        owner = current_user.id
    request_info = {
        "remote_addr": request.remote_addr,
        "referrer": request.referrer,
        "hostname": request.host,
        "user_id": owner,
        "action": "UPDATE",
        "workflow_id": check_result.get("workflow_id"),
    }
    response = {}
    if register_type == "Direct":
        import_result = import_items_to_system(item, request_info=request_info)
        if not import_result.get("success"):
            current_app.logger.error(
                f"Error in import_items_to_system: {item.get('error_id')}"
            )
            raise WekoSwordserverException(
                f"Item import error:: {import_result.get('error_id')}",
                ErrorType.ServerError
            )
        send_mail_direct_registered(recid, current_user.id)
        notify_item_imported(
            current_user.id, recid, current_user.id, shared_id=shared_id
        )
        response = jsonify(_get_status_document(recid))

    elif register_type == "Workflow":
        url, _, _, error = import_items_to_activity(
            item, request_info=request_info
        )
        activity_id = url.split("/")[-1]

        if error and url:
            raise WekoSwordserverException(
                "Error: {error}. Please open the following URL to continue "
                "with the remaining operations.{url}: Item id: {recid}."
                .format(error=error, url=url, recid=recid),
                ErrorType.BadRequest
            )
        if error:
            raise WekoSwordserverException(
                f"Unexpected error: {error}.", ErrorType.ServerError
            )
        response = jsonify(_get_status_workflow_document(activity_id, recid))
    else:
        if os.path.exists(data_path):
            shutil.rmtree(data_path)
            TempDirInfo().delete(data_path)
        raise WekoSwordserverException(
            "Invalid register format has been set for admin setting",
            ErrorType.ServerError
        )

    if os.path.exists(data_path):
        shutil.rmtree(data_path)
        TempDirInfo().delete(data_path)

    current_app.logger.info(
        f"Item updated via SWORD api by {request.oauth.client.name} (recid={recid})"
    )

    return response

@blueprint.route("/deposit/<recid>", methods=["GET"])
@oauth2.require_oauth()
@check_on_behalf_of()
def get_status_document(recid):
    """Retrieving an Object's Status

    https://swordapp.github.io/swordv3/swordv3-behaviours.html#3.1

    For an Object where you have an Object-URL, you may request information about
    the current state of that resource, and receive the Status document in response.

    Args:
        recid (str): Record Identifier.

    Protocol Operation
        * GET Object-URL: https://swordapp.github.io/swordv3/swordv3.html#7.3.3

    Request Requirements
        * MAY specify Authorization and On-Behalf-Of headers (i.e. if authenticating this request)

    Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request

    Response Requirements
        * MUST respond with a valid Status Document or a suitable error response
        * MUST include ETag header if implementing concurrency control

    Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
    """
    # Get status document
    status_document = _get_status_document(recid)

    return jsonify(status_document)

def _get_status_document(recid):
    """
    :param recid: Record Identifier.
    :returns: A :class:`sword3common.StatusDocument` instance.
    """

    # Get record
    from invenio_pidstore.resolver import Resolver
    from werkzeug.utils import import_string
    record_class = import_string("weko_deposit.api:WekoRecord")
    try:
        resolver = Resolver(pid_type="recid", object_type="rec",
                        getter=record_class.get_record)
        pid, record = resolver.resolve(recid)
    except Exception:
        raise WekoSwordserverException("Item not found. (recid={})".format(recid), ErrorType.NotFound)

    # Get record uri
    record_uri = "{}records/{}".format(request.url_root, recid)
    permalink = get_record_permalink(record)
    if (
        not permalink
        and record.get("system_identifier_doi")
        and record.get("system_identifier_doi").get("attribute_value_mlt")[0]
    ):
        permalink = record["system_identifier_doi"][
            "attribute_value_mlt"][0][
            "subitem_systemidt_identifier"]

    """
    Set raw data to StatusDocument

    The following fields are set by sword3common
        # "@context"
        # "@type"
    """
    raw_data = {
        "@context": constants.JSON_LD_CONTEXT,
        "@type": constants.DocumentType.Status[0],
        "@id" : url_for("weko_swordserver.get_status_document", recid=recid, _external=True),
        "actions" : {
            "getMetadata" : False,      # Not implemented
            "getFiles" : False,         # Not implemented
            "appendMetadata" : False,   # Not implemented
            "appendFiles" : False,      # Not implemented
            "replaceMetadata" : False,  # Not implemented
            "replaceFiles" : False,     # Not implemented
            "deleteMetadata" : False,   # Not implemented
            "deleteFiles" : False,      # Not implemented
            "deleteObject" : True,
        },
        "eTag" : str(record.revision_id),
        "fileSet" : {
            # "@id" : "",
            # "eTag" : ""
        },
        "metadata" : {
            # "@id" : "",
            # "eTag" : ""
        },
        "service" : url_for("weko_swordserver.get_service_document"),
        "state" : [
            {
                "@id" : SwordState.ingested,
                "description" : ""
            }
        ],
        "links" : [
            {
                "@id" : record_uri,
                "rel" : ["alternate"],
                "contentType" : "text/html"
            },
        ]
    }
    if permalink:
        raw_data["links"].append({
                "@id" : permalink,
                "rel" : ["alternate"],
                "contentType" : "text/html"
            })

    statusDocument = StatusDocument(raw=raw_data)

    return statusDocument.data

def _get_status_workflow_document(activity_id, recid):
    """
    :param recid: Record Identifier.
    :returns: A :class:`sword3common.StatusDocument` instance.
    """

    """
    Set raw data to StatusDocument

    The following fields are set by sword3common
        # "@context"
        # "@type"
    """
    if not activity_id:
        raise WekoSwordserverException("Activity created, but not found.", ErrorType.NotFound)

    # Get record uri
    record_url = ""
    if recid:
        record_url = url_for("weko_swordserver.get_status_document", recid=recid, _external=True)

    raw_data = {
        "@id": record_url,
        "@context": constants.JSON_LD_CONTEXT,
        "@type": constants.DocumentType.ServiceDocument,
        "actions" : {
            "getMetadata" : False,      # Not implimented
            "getFiles" : False,         # Not implimented
            "appendMetadata" : False,   # Not implimented
            "appendFiles" : False,      # Not implimented
            "replaceMetadata" : False,  # Not implimented
            "replaceFiles" : False,     # Not implimented
            "deleteMetadata" : False,   # Not implimented
            "deleteFiles" : False,      # Not implimented
            "deleteObject" : True,
        },
        "fileSet" : {
            # "@id" : "",
            # "eTag" : ""
        },
        "metadata" : {
            # "@id" : "",
            # "eTag" : ""
        },
        "service" : url_for("weko_swordserver.get_service_document", _external=False),
        "state" : [
            {
                "@id" : SwordState.inWorkflow,
                "description" : ""
            }
        ],
        "links" : [
            {
                "@id" : url_for("weko_workflow.display_activity", activity_id=activity_id, _external=True),
                "rel" : ["alternate"],
                "contentType" : "text/html"
            },
        ]
    }

    statusDocument = StatusDocument(raw=raw_data)

    return statusDocument.data

@blueprint.route("/deposit/<recid>", methods=["DELETE"])
@oauth2.require_oauth()
@limiter.limit("")
@require_oauth_scopes(write_scope.id, actions_scope.id)
@require_oauth_scopes(item_delete_scope.id)
@roles_required(WEKO_SWORDSERVER_DEPOSIT_ROLE_ENABLE)
@check_on_behalf_of()
def delete_object(recid):
    """Deleting the entire Object

    Delete the Object in its entirety from the server, along with all Metadata and Files.

    Args:
        recid (str): Record Identifier.

    Protocol Operation
        * DELETE Object-URL: https://swordapp.github.io/swordv3/swordv3.html#7.3.6

    Request Requirements
        * MAY specify Authorization and On-Behalf-Of headers (i.e. if authenticating this request)

    Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
        * MUST verify that the content matches the Digest header
        * MUST verify that the supplied content matches the Content-Length if this is provided

    Response Requirements
        * MUST respond with a 204 if the delete is successful, 202 if the delete is queued for processing, or raise an error

    Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
    """
    # check if the item exists
    _ = _get_status_document(recid)
    has_update_version_role(current_user)
    record = WekoRecord.get_record_by_pid(recid)
    if record.pid_doi:
        current_app.logger.error(f"Cannot delete item with DOI; item id {recid}")
        raise WekoSwordserverException(
            "Cannot delete item with DOI.", ErrorType.BadRequest
        )

    on_behalf_of = request.headers.get("On-Behalf-Of")
    shared_id = get_shared_id_from_on_behalf_of(on_behalf_of)
    client_id = request.oauth.client.client_id
    check_result = get_deletion_type(client_id)

    deletion_type = check_result.get("deletion_type")

    owner = -1
    if current_user.is_authenticated:
        owner = current_user.id
    request_info = {
        "remote_addr": request.remote_addr,
        "referrer": request.referrer,
        "hostname": request.host,
        "user_id": owner,
        "shared_id": shared_id,
        "action": "DELETE"
    }

    response = {}
    if deletion_type == "Workflow":
        required_scopes = set([activity_scope.id])
        token_scopes = set(request.oauth.access_token.scopes)
        if not required_scopes.issubset(token_scopes):
            abort(403)

        try:
            url, current_action = delete_items_with_activity(
                recid, request_info=request_info
            )
        except Exception as ex:
            current_app.logger.error(
                f"Failed to delete item with activity: {str(ex)}"
            )
            raise WekoSwordserverException(
                f"Failed to delete item: {str(ex)}",
                ErrorType.BadRequest
            )

        if current_action == "approval":
            response = Response(status=202, headers={"Location": url})
        else:
            response = jsonify(status=204)
    else:
        soft_delete(recid)
        notify_item_deleted(
            current_user.id, recid, current_user.id, shared_id=shared_id
        )
        send_mail_item_deleted(recid, record, current_user.id)
        current_app.logger.info(
            f"Item deleted by sword from {request.oauth.client.name} (recid={recid})"
        )
        response = Response(status=204)

    return response


@blueprint.route("/all_mappings", methods=["GET"])
def all_mappings():
    """Get all SwordItemTypeMapping list.

    Returns:
        SwordItemTypeMappingModel: All SwordItemTypeMapping list.
    """
    def convert(item):
        return {
            "id": item.id,
            "name": item.name,
            "item_type_id": item.item_type_id,
        }
    mappings = list(map(convert, JsonldMapping.get_all()))
    return jsonify(mappings)


def _create_error_document(type, error):
    class Error(sword3commonError):
        # fix to timestamp coerce function not defined
        __SEAMLESS_STRUCT__ = {
            "fields": {
                "@context": {"coerce": "unicode"},
                "@type": {"coerce": "unicode"},
                "timestamp": {"coerce": "datetime"},
                "error": {"coerce": "unicode"},
                "log": {"coerce": "unicode"},
            }
        }

        @property
        def data(self):
            return self.__seamless__.data

    raw_data = {
        "@context": constants.JSON_LD_CONTEXT,
        "@type": type,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "error": error,
        # "log": "",
    }
    return Error(raw_data).data


@blueprint.errorhandler(401)
def handle_unauthorized(ex):
    msg = "Authentication is required."
    current_app.logger.error(msg)
    return jsonify(_create_error_document(ErrorType.AuthenticationRequired.type, msg)), ErrorType.AuthenticationRequired.code

@blueprint.errorhandler(403)
def handle_forbidden(ex):
    msg = "Not allowed operation in your token scope."
    current_app.logger.error(msg)
    return jsonify(_create_error_document(ErrorType.Forbidden.type, msg)), ErrorType.Forbidden.code

@blueprint.errorhandler(RateLimitExceeded)
def handle_ratelimit(ex):
    current_app.logger.error(ex)
    return jsonify(_create_error_document(ErrorType.TooManyRequests.type, "Too many requests.")), ErrorType.TooManyRequests.code

@blueprint.errorhandler(SeamlessException)
def handle_seamless_exception(ex):
    current_app.logger.error(ex.message)
    return jsonify(_create_error_document(ErrorType.ServerError.type, ex.message)), ErrorType.ServerError.code

@blueprint.errorhandler(Exception)
def handle_exception(ex):
    current_app.logger.error(str(ex), exc_info=True)
    return jsonify(_create_error_document(ErrorType.ServerError.type, "Internal Server Error")), ErrorType.ServerError.code

@blueprint.errorhandler(WekoSwordserverException)
def handle_weko_swordserver_exception(ex):
    return jsonify(_create_error_document(ex.errorType.type, ex.message)), ex.errorType.code

@blueprint.teardown_request
def dbsession_clean(exception):
    db.session.remove()
