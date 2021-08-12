import datetime
import json
import typing
from copy import deepcopy
from functools import partial
from http import HTTPStatus

import marshmallow.exceptions
from flask import Blueprint
from flask import Response

import sword3common
from invenio_deposit.search import DepositSearch
from invenio_deposit.views.rest import create_error_handlers
from invenio_records_rest.utils import obj_or_import_string

from . import (
    DepositFilesetView,
    DepositFileView,
    DepositMetadataView,
    DepositStatusView,
    ServiceDocumentView,
    StagingURLView,
    TemporaryURLView,
)

from .. import serializers
from ..api import SWORDDeposit
from ..typing import SwordEndpointDefinition

__all__ = ["create_blueprint"]


def create_blueprint(config) -> Blueprint:
    """
    Create an Invenio-SWORD blueprint

    This takes a list of endpoint definitions and returns a SWORD blueprint for use in Invenio. You shouldn't need to
    use this directly, as it's called by :class:`invenio_sword.ext.InvenioSword`.

    See: :data:`invenio_sword.config.SWORD_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """

    endpoints: typing.Dict[str, SwordEndpointDefinition] = config["SWORD_ENDPOINTS"]

    blueprint = Blueprint("invenio_sword", __name__, url_prefix="",)
    create_error_handlers(blueprint)

    for endpoint, options in (endpoints or {}).items():
        options = deepcopy(options)

        options.setdefault("search_class", DepositSearch)
        search_class = obj_or_import_string(options["search_class"])

        # records rest endpoints will use the deposit class as record class
        options.setdefault("record_class", SWORDDeposit)
        record_class = obj_or_import_string(options["record_class"])

        # backward compatibility for indexer class
        options.setdefault("indexer_class", None)

        search_class_kwargs = {}
        if options.get("search_index"):
            search_class_kwargs["index"] = options["search_index"]

        if options.get("search_type"):
            search_class_kwargs["doc_type"] = options["search_type"]

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get("read_permission_factory_imp")
            ),
            create_permission_factory=obj_or_import_string(
                options.get("create_permission_factory_imp")
            ),
            update_permission_factory=obj_or_import_string(
                options.get("update_permission_factory_imp")
            ),
            delete_permission_factory=obj_or_import_string(
                options.get("delete_permission_factory_imp")
            ),
            record_class=record_class,
            search_class=partial(search_class, **search_class_kwargs),
            default_media_type=options.get("default_media_type"),
            pid_type=endpoint,
        )

        blueprint.add_url_rule(
            options["service_document_route"],
            endpoint=ServiceDocumentView.view_name.format(endpoint),
            view_func=ServiceDocumentView.as_view(
                "service",
                serializers={"application/ld+json": serializers.jsonld_serializer,},
                ctx=ctx,
            ),
        )

        blueprint.add_url_rule(
            options["item_route"],
            endpoint=DepositStatusView.view_name.format(endpoint),
            view_func=DepositStatusView.as_view(
                "item",
                serializers={"application/ld+json": serializers.jsonld_serializer,},
                ctx=ctx,
            ),
        )
        blueprint.add_url_rule(
            options["metadata_route"],
            endpoint=DepositMetadataView.view_name.format(endpoint),
            view_func=DepositMetadataView.as_view(
                "metadata",
                serializers={"application/ld+json": serializers.jsonld_serializer,},
                ctx=ctx,
            ),
        )
        blueprint.add_url_rule(
            options["fileset_route"],
            endpoint=DepositFilesetView.view_name.format(endpoint),
            view_func=DepositFilesetView.as_view(
                "fileset",
                serializers={"application/ld+json": serializers.jsonld_serializer,},
                ctx=ctx,
            ),
        )
        blueprint.add_url_rule(
            options["file_route"],
            endpoint=DepositFileView.view_name.format(endpoint),
            view_func=DepositFileView.as_view(
                name="file",
                serializers={
                    "*/*": lambda *args, **kwargs: Response(
                        status=HTTPStatus.NO_CONTENT
                    )
                },
            ),
        )

    blueprint.add_url_rule(
        config["SWORD_STAGING_URL_ROUTE"],
        endpoint=StagingURLView.view_name,
        view_func=StagingURLView.as_view(
            "staging-url",
            serializers={"application/ld+json": serializers.jsonld_serializer,},
            ctx=config["SWORD_SEGMENTED_UPLOAD_CONTEXT"],
        ),
    )

    blueprint.add_url_rule(
        config["SWORD_TEMPORARY_URL_ROUTE"],
        endpoint=TemporaryURLView.view_name,
        view_func=TemporaryURLView.as_view(
            "temporary-url",
            serializers={"application/ld+json": serializers.jsonld_serializer,},
            ctx=config["SWORD_SEGMENTED_UPLOAD_CONTEXT"],
        ),
    )

    @blueprint.errorhandler(sword3common.exceptions.SwordException)
    def sword_exception_handler(exc):
        return Response(
            json.dumps(
                {
                    "@context": sword3common.constants.JSON_LD_CONTEXT,
                    "@type": exc.name,
                    "error": exc.reason,
                    "log": exc.message,
                    "timestamp": exc.timestamp.isoformat(),
                }
            ),
            content_type="application/ld+json",
            status=exc.status_code,
        )

    @blueprint.errorhandler(marshmallow.exceptions.ValidationError)
    def marshmallow_exception_handler(exc):
        return Response(
            json.dumps(
                {
                    "@context": sword3common.constants.JSON_LD_CONTEXT,
                    "@type": sword3common.exceptions.ValidationFailed.name,
                    "error": sword3common.exceptions.ValidationFailed.reason,
                    "timestamp": datetime.datetime.now(
                        tz=datetime.timezone.utc
                    ).isoformat(),
                    "errors": exc.messages,
                }
            ),
            content_type="application/ld+json",
            status=sword3common.exceptions.ValidationFailed.status_code,
        )

    return blueprint
