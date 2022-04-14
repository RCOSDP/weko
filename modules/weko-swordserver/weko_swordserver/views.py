# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function
from fileinput import filename

from flask import Blueprint, current_app, jsonify, abort, request, url_for
from flask_babelex import gettext as _

from sword3common import ServiceDocument, StatusDocument, constants
from sword3common.lib.seamless import SeamlessException
from weko_search_ui.utils import check_import_items, import_items_to_system
from weko_records_ui.utils import get_record_permalink, soft_delete
from werkzeug.http import parse_options_header

blueprint = Blueprint(
    'weko_swordserver',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/sword',
)


@blueprint.route("/service-document", methods=['GET'])
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
    TODO: Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
    """
    
    """
    TODO: Response Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST only list Service-URLs in the Service Document for which a deposit request would be permitted
        * MUST respond with a valid Service Document or a suitable error response
    """

    """
    TODO: Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
    """

    try:
        """
        Set raw data to ServiceDocument
        
        The following fields are set by sword3common
            # "@context"
            # "@type"
        """
        raw_data = {
            "@context": constants.JSON_LD_CONTEXT,
            "@type": constants.DocumentType.ServiceDocument,
            "@id": request.url,
            "root": request.url,
            "dc:title": current_app.config['THEME_SITENAME'],
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
    
    except SeamlessException as ex:
        current_app.logger.error(ex.message)
        abort(500)

    except Exception as ex:
        current_app.logger.error(ex)
        abort(500)


@blueprint.route("/service-document", methods=['POST'])
def post_service_document():
    """
    Create a new Object on the server, sending a single Binary File.
    The Binary File itself is specified as Packaged Content, which the server may understand how to unpack.
    """

    """
    TODO: Server Requirements
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
    TODO: Response Requirements
        * MUST include ETag header if implementing concurrency control
        * MUST include one or more File-URLs for the deposited content in the Status document. The behaviour of these File-URLs may vary depending on the type of content deposited (e.g. ByReference and Segmented Uploads do not need to be immediately retrievable)
        * MUST respond with a Location header, containing the Object-URL
        * MUST respond with a valid Status Document or a suitable error response
        * Status Document MUST be available on GET to the Object-URL in the Location header immediately (irrespective of whether this is a 201 or 202 response)
        * MUST respond with a 201 if the item was created immediately, a 202 if the item was queued for import, or raise an error.
    """

    """
    TODO: Error Responses
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
    try:
        # TODO: Check file and metadata
        # file = request.get_data()
        # form = request.form

        # zipfile = request.files.get('file')

        """
        Check content-disposition
            Request format:
                Content-Disposition	attachment; filename=[filename]
        """
        content_disposition, content_disposition_options = parse_options_header(
                request.headers.get("Content-Disposition") or ""
            )
        if content_disposition != "attachment" or not content_disposition_options.get('filename'):
            abort(500)
        filename = content_disposition_options.get('filename')

        # Check files
        file = None
        for key, value in request.files.items():
            if value.filename == filename:
                file = value
        
        check_result = check_import_items(file, False)
        item = check_result.get('list_record')[0] if check_result.get('list_record') else None

        print("================")
        print(item)
        print("================")

        if check_result.get('error') or not item or item.get('errors'):
            if check_result.get('error'):
                current_app.logger.error('check_import_items', check_result.get('error'))
            elif item.get('errors'):
                current_app.logger.error('check_import_items', item.get('errors'))
            else:
                current_app.logger.error('check_import_items', 'item_missing')
            abort(500)
        
        import_result = import_items_to_system(item, None)
        if not import_result.get('success'):
            current_app.logger.error('import_items_to_system', item.get('error_id'))
            abort(500)
        
        recid = import_result.get('recid')

        return jsonify(_get_status_document(recid))

    
    except SeamlessException as ex:
        current_app.logger.error(ex.message)
        abort(500)

    except Exception as ex:
        current_app.logger.error(ex)
        abort(500)


@blueprint.route("/deposit/<recid>", methods=['GET'])
def get_status_document(recid):
    """
    For an Object where you have an Object-URL, you may request information about the current state of that resource,
    and receive the Status document in response.
    """

    """
    TODO: Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
    """

    """
    TODO: Response Requirements
        * MUST respond with a valid Status Document or a suitable error response
        * MUST include ETag header if implementing concurrency control
    """

    """
    TODO: Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
    """
    try:
        # Get status document
        status_document = _get_status_document(recid)

        return jsonify(status_document)
    
    except SeamlessException as ex:
        current_app.logger.error(ex.message)
        abort(500)

    except Exception as ex:
        current_app.logger.error(ex)
        raise ex
        #abort(500)

def _get_status_document(recid):
    """
    :param recid: Record Identifier.
    :returns: A :class:`sword3common.StatusDocument` instance.
    """

    # Get record
    from invenio_pidstore.resolver import Resolver
    from werkzeug.utils import import_string
    record_class = import_string('weko_deposit.api:WekoRecord')
    resolver = Resolver(pid_type='recid', object_type='rec',
                    getter=record_class.get_record)
    pid, record = resolver.resolve(recid)

    print("=============")
    print(pid)
    print(record)
    print("=============")

    record_uri = None
    permalink = get_record_permalink(record)
    if not permalink:
        if record.get('system_identifier_doi') and \
            record.get('system_identifier_doi').get(
                'attribute_value_mlt')[0]:
            record['permalink_uri'] = \
                record['system_identifier_doi'][
                    'attribute_value_mlt'][0][
                    'subitem_systemidt_identifier']
        else:
            record_uri = '{}records/{}'.format(request.url_root, recid)
    else:
        record_uri = permalink

    """
    Set raw data to StatusDocument
    
    The following fields are set by sword3common
        # "@context"
        # "@type"
    """
    raw_data = {
        "@context": constants.JSON_LD_CONTEXT,
        "@type": constants.DocumentType.Status[0],
        "@id" : request.url,
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
            # TODO: other links
        ]
    }
    statusDocument = StatusDocument(raw=raw_data)

    return statusDocument.data

@blueprint.route("/deposit/<recid>", methods=['DELETE'])
def delete_item(recid):
    """ Delete the Object in its entirety from the server, along with all Metadata and Files. """
    
    """
    TODO: Server Requirements
        * If Authorization (and optionally On-Behalf-Of) headers are provided, MUST authenticate the request
        * MUST verify that the content matches the Digest header
        * MUST verify that the supplied content matches the Content-Length if this is provided
    """

    """
    TODO: Response Requirements
        * MUST respond with a 204 if the delete is successful, 202 if the delete is queued for processing, or raise an error
    """

    """
    TODO: Error Responses
        * If no authentication credentials were supplied, but were expected, MUST respond with a 401 (AuthenticationRequired)
        * If authentication fails with supplied credentials, MUST respond with a 403 (AuthenticationFailed)
        * If the server does not allow this method in this context at this time, MAY respond with a 405 (MethodNotAllowed)
        * If the server does not support On-Behalf-Of deposit and the On-Behalf-Of header has been provided, MAY respond with a 412 (OnBehalfOfNotAllowed)
    """
    try:
        # TODO: Request header check
        
        # TODO: recidに該当するレコードがない場合の挙動の確認。Exceptionがraiseされる？
        soft_delete(recid)
        return jsonify({'recid':recid})
    
    except SeamlessException as ex:
        current_app.logger.error(ex.message)
        abort(500)

    except Exception as ex:
        current_app.logger.error(ex)
        abort(500)

class SwordState:
    accepted = "http://purl.org/net/sword/3.0/state/accepted"
    inProgress = "http://purl.org/net/sword/3.0/state/inProgress"
    inWorkflow ="http://purl.org/net/sword/3.0/state/inWorkflow"
    ingested = "http://purl.org/net/sword/3.0/state/ingested"
    rejected = "http://purl.org/net/sword/3.0/state/rejected"
    deleted = "http://purl.org/net/sword/3.0/state/deleted"
