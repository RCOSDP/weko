# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

from __future__ import absolute_import, print_function

from datetime import datetime, timedelta
import shutil

import sword3common
from flask import Blueprint, current_app, jsonify, request, url_for
from flask_login import current_user
from invenio_deposit.scopes import write_scope
from invenio_oauth2server.ext import verify_oauth_token_and_set_current_user
from invenio_oauth2server.provider import oauth2
from sword3common import ServiceDocument, StatusDocument, constants
from sword3common.lib.seamless import SeamlessException
from weko_admin.api import TempDirInfo
from weko_records_ui.utils import get_record_permalink, soft_delete
from weko_search_ui.utils import check_import_items, import_items_to_system
from werkzeug.http import parse_options_header
from invenio_db import db

from invenio_oaiserver.api import OaiIdentify
from weko_workflow.utils import get_site_info_name

from .decorators import *
from .errors import *


class SwordState:
    accepted = "http://purl.org/net/sword/3.0/state/accepted"
    inProgress = "http://purl.org/net/sword/3.0/state/inProgress"
    inWorkflow ="http://purl.org/net/sword/3.0/state/inWorkflow"
    ingested = "http://purl.org/net/sword/3.0/state/ingested"
    rejected = "http://purl.org/net/sword/3.0/state/rejected"
    deleted = "http://purl.org/net/sword/3.0/state/deleted"


blueprint = Blueprint(
    'weko_swordserver',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/sword',
)
blueprint.before_request(verify_oauth_token_and_set_current_user)

@blueprint.route("/service-document", methods=['GET'])
@oauth2.require_oauth()
@check_on_behalf_of()
def get_service_document():
    """
    Request from the server a list of the Service-URLs that the client can deposit to.
    A Service-URL allows the server to support multiple different deposit conditions - each URL may have its own set of rules/workflows behind it;
    for example, Service-URLs may be subject-specific, organisational-specific, or process-specific.
    It is up to the client to determine which is the suitable URL for its deposit, based on the information provided by the server.
    The list of Service-URLs may vary depending on the authentication credentials supplied by the client.

    This request can be made against a root Service-URL, which will describe the capabilities of the entire server,
    for information about the full list of Service-URLs, or can be made against an individual Service-URL for information just about that service.
    """
    
    """
    Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
    """
    
    """
    Response Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST only list Service-URLs in the Service Document for which a deposit request would be permitted
        * MUST respond with a valid Service Document or a suitable error response
    """

    """
    Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
    """
    
    """
    Set raw data to ServiceDocument
    """
    repositoryName, site_name_ja = get_site_info_name()
    if repositoryName is None or len(repositoryName) == 0:
        identify = OaiIdentify.get_all()
        repositoryName = current_app.config['THEME_SITENAME']
        if identify is not None:
            repositoryName = identify.repositoryName

    raw_data = {
        "@context": constants.JSON_LD_CONTEXT,
        "@type": constants.DocumentType.ServiceDocument,
        "@id": request.url,
        "root": request.url,
        "dc:title": repositoryName,
        "version": current_app.config['WEKO_SWORDSERVER_SWORD_VERSION'],
        "accept": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT'],
        "digest": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_DIGEST'],
        "acceptArchiveFormat": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT'],
        "acceptDeposits": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_DEPOSITS'],
        "acceptMetadata": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_METADATA'],
        "acceptPackaging": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING'],
        "authentication": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_AUTHENTICATION'],
        "byReferenceDeposit": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_BY_REFERENCE_DEPOSIT'],
        "collectionPolicy": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_COLLECTION_POLICY'],
        "dcterms:abstract": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ABSTRACT'],
        "maxAssembledSize": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_ASSEMBLED_SIZE'],
        "maxByReferenceSize": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_BY_REFERENCE_SIZE'],
        "maxSegments": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_SEGMENTS'],
        "maxUploadSize": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE'],
        "onBehalfOf": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF'],
        "services": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_SERVICES'],
        "staging": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_STAGING'],
        "stagingMaxIdle": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_STAGING_MAX_IDLE'],
        "treatment": current_app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_TREATMENT'],
    }
    serviceDocument = ServiceDocument(raw=raw_data)

    return jsonify(serviceDocument.data)


@blueprint.route("/service-document", methods=['POST'])
@oauth2.require_oauth(write_scope.id)
@check_on_behalf_of()
@check_package_contents()
def post_service_document():
    """
    Create a new Object on the server, sending a single Binary File.
    The Binary File itself is specified as Packaged Content, which the server may understand how to unpack.
    """

    """
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
    """

    """
    Response Requirements
        * MUST include ETag header if implementing concurrency control
        * MUST include one or more File-URLs for the deposited content in the Status document. The behaviour of these File-URLs may vary depending on the type of content deposited (e.g. ByReference and Segmented Uploads do not need to be immediately retrievable)
        * MUST respond with a Location header, containing the Object-URL
        * MUST respond with a valid Status Document or a suitable error response
        * Status Document MUST be available on GET to the Object-URL in the Location header immediately (irrespective of whether this is a 201 or 202 response)
        * MUST respond with a 201 if the item was created immediately, a 202 if the item was queued for import, or raise an error.
    """

    """
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
    """
    
    """
    Check content-disposition
        Request format:
            Content-Disposition	attachment; filename=[filename]
    """
    content_disposition, content_disposition_options = parse_options_header(
            request.headers.get("Content-Disposition") or ""
        )
    if content_disposition != "attachment" or not content_disposition_options.get('filename'):
        raise WekoSwordserverException("Cannot get filename by Content-Disposition.", ErrorType.BadRequest)
    filename = content_disposition_options.get('filename')

    # Check import item
    file = None
    for key, value in request.files.items():
        if value.filename == filename:
            file = value
    if file is None:
        raise WekoSwordserverException("Not found {0} in request body.".format(filename), ErrorType.BadRequest)

    check_result = check_import_items(file, False)
    item = check_result.get('list_record')[0] if check_result.get('list_record') else None
    if check_result.get('error') or not item or item.get('errors'):
        errorType = None
        check_result_msg = ''
        if check_result.get('error'):
            errorType = ErrorType.ServerError
            check_result_msg = check_result.get('error')
        elif item and item.get('errors'):
            errorType = ErrorType.ContentMalformed
            check_result_msg = ', '.join(item.get('errors'))
        else:
            errorType = ErrorType.ContentMalformed
            check_result_msg = 'item_missing'
        raise WekoSwordserverException('Error in check_import_items: {0}'.format(check_result_msg), errorType)
    if item.get('status') != 'new':
        raise WekoSwordserverException('This item is already registered: {0]'.format(item.get('item_title')), ErrorType.BadRequest)

    data_path = check_result.get("data_path","")
    expire = datetime.now() + timedelta(days=1)
    TempDirInfo().set(data_path, {"expire": expire.strftime("%Y-%m-%d %H:%M:%S")})
    item["root_path"] = data_path+"/data"
    
    # import item
    owner = -1
    if current_user.is_authenticated:
        owner = current_user.id
    request_info = {
            "remote_addr": request.remote_addr,
            "referrer": request.referrer,
            "hostname": request.host,
            "user_id": owner,
            "action": "IMPORT"
    }
    import_result = import_items_to_system(item, request_info=request_info)
    if not import_result.get('success'):
        raise WekoSwordserverException('Error in import_items_to_system: {0}'.format(item.get('error_id')), ErrorType.ServerError)
    
    shutil.rmtree(data_path)
    TempDirInfo().delete(data_path)
    
    recid = import_result.get('recid')

    return jsonify(_get_status_document(recid))


@blueprint.route("/deposit/<recid>", methods=['GET'])
@oauth2.require_oauth()
@check_on_behalf_of()
def get_status_document(recid):
    """
    For an Object where you have an Object-URL, you may request information about the current state of that resource,
    and receive the Status document in response.
    """

    """
    Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
    """

    """
    Response Requirements
        * MUST respond with a valid Status Document or a suitable error response
        * MUST include ETag header if implementing concurrency control
    """

    """
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
    record_class = import_string('weko_deposit.api:WekoRecord')
    try:
        resolver = Resolver(pid_type='recid', object_type='rec',
                        getter=record_class.get_record)
        pid, record = resolver.resolve(recid)
    except Exception:
        raise WekoSwordserverException("Item not found. (recid={})".format(recid), ErrorType.NotFound)

    # Get record uri
    record_uri = '{}records/{}'.format(request.url_root, recid)
    permalink = get_record_permalink(record)
    if not permalink and \
        record.get('system_identifier_doi') and \
        record.get('system_identifier_doi').get(
            'attribute_value_mlt')[0]:
        permalink = record['system_identifier_doi'][
            'attribute_value_mlt'][0][
            'subitem_systemidt_identifier']
    
    """
    Set raw data to StatusDocument
    
    The following fields are set by sword3common
        # "@context"
        # "@type"
    """
    raw_data = {
        "@context": constants.JSON_LD_CONTEXT,
        "@type": constants.DocumentType.Status[0],
        "@id" : url_for('weko_swordserver.get_status_document', recid=recid, _external=True),
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
        "eTag" : str(record.revision_id),
        "fileSet" : {
            # "@id" : "",
            # "eTag" : ""
        },
        "metadata" : {
            # "@id" : "",
            # "eTag" : ""
        },
        "service" : url_for('weko_swordserver.get_service_document'),
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
        raw_data['links'].append({
                "@id" : permalink,
                "rel" : ["alternate"],
                "contentType" : "text/html"
            })

    statusDocument = StatusDocument(raw=raw_data)

    return statusDocument.data

@blueprint.route("/deposit/<recid>", methods=['DELETE'])
@oauth2.require_oauth()
@check_on_behalf_of()
def delete_item(recid):
    """ Delete the Object in its entirety from the server, along with all Metadata and Files. """
    
    """
    Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
        * MUST verify that the content matches the Digest header
        * MUST verify that the supplied content matches the Content-Length if this is provided
    """

    """
    Response Requirements
        * MUST respond with a 204 if the delete is successful, 202 if the delete is queued for processing, or raise an error
    """

    """
    Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
    """
    try:
        # delete item 
        soft_delete(recid)
        current_app.logger.debug("item deleted by sword (recid={})".format(recid))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
    return ('', 204)

def _create_error_document(type, error):
    
    class Error(sword3common.Error):
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
    current_app.logger.error(ex.message)
    return jsonify(_create_error_document(ex.errorType.type, ex.message)), ex.errorType.code

@blueprint.teardown_request
def dbsession_clean(exception):
    db.session.remove()
