import typing

import sword3common.constants
import sword3common.exceptions
from flask import current_app
from flask import request
from invenio_db import db
from invenio_rest import ContentNegotiatedMethodView
from werkzeug.exceptions import Conflict
from werkzeug.http import parse_options_header
from werkzeug.utils import cached_property

from ..api import SWORDDeposit
from ..metadata import Metadata
from ..schemas import ByReferenceSchema
from ..typing import BytesReader

__all__ = ["SWORDDepositView"]


class SWORDDepositView(ContentNegotiatedMethodView):
    """
    Base class for all SWORD views

    The properties and methods defined on this class are used by subclasses to SWORD operations with common
    implementations across different SWORD views.
    """

    view_name: str
    record_class: typing.Type[SWORDDeposit]
    pid_type: str

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(SWORDDepositView, self).__init__(
            serializers,
            default_media_type=ctx.get("default_media_type"),
            *args,
            **kwargs,
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @cached_property
    def endpoint_options(self) -> typing.Dict[str, typing.Any]:
        """Configuration endpoints for this view's SWORD endpoint"""
        return current_app.config["SWORD_ENDPOINTS"][self.pid_type]

    @cached_property
    def metadata_format(self) -> str:
        """The ``Metadata-Format`` header, or its default per config"""
        return request.headers.get(
            "Metadata-Format", self.endpoint_options["default_metadata_format"]
        )

    @cached_property
    def metadata_class(self) -> typing.Type[Metadata]:
        """The Metadata subclass associated with the request.

        :raises NotImplemented: if the ``Metadata-Format`` is not supported
        """
        try:
            return self.endpoint_options["metadata_formats"][self.metadata_format]
        except KeyError as e:
            raise sword3common.exceptions.MetadataFormatNotAcceptable from e

    @cached_property
    def packaging_name(self) -> str:
        """The Packaging subclass associated with the request.

        :raises NotImplemented: if the ``Packaging`` is not supported
        """
        packaging = request.headers.get(
            "Packaging", self.endpoint_options["default_packaging_format"]
        )
        if packaging not in self.endpoint_options["packaging_formats"]:
            raise sword3common.exceptions.PackagingFormatNotAcceptable
        return packaging

    @cached_property
    def in_progress(self) -> bool:
        """Whether the request declares that the deposit is still in progress, via the ``In-Progress`` header"""
        return request.headers.get("In-Progress") == "true"

    def update_deposit_status(self, record: SWORDDeposit) -> None:
        """Updates a deposit status from the In-Progress header

        """
        if self.in_progress:
            if record["_deposit"]["status"] == "published":
                raise Conflict(
                    "Deposit has status {}; cannot subsequently be made In-Progress".format(
                        record["_deposit"]["status"]
                    )
                )
        elif record["_deposit"]["status"] == "draft":
            record["_deposit"]["status"] = "published"

    def create_deposit(self) -> SWORDDeposit:
        """Create an empty deposit record"""
        return SWORDDeposit.create({"metadata": {}})

    def update_deposit(self, record: SWORDDeposit, replace: bool = True):
        """Update a deposit according to the request data

        :param replace: If ``True``, all previous data on the deposit is removed. If ``False``, the request augments
            data already provided.
        """

        content_disposition, content_disposition_options = parse_options_header(
            request.headers.get("Content-Disposition", "")
        )

        metadata_deposit = content_disposition_options.get("metadata") == "true"
        by_reference_deposit = content_disposition_options.get("by-reference") == "true"

        if metadata_deposit:
            if by_reference_deposit:  # pragma: nocover
                record.set_metadata(
                    request.json["metadata"], self.metadata_class, replace=replace,
                )
            else:
                record.set_metadata(
                    request.stream,
                    self.metadata_class,
                    request.content_type,
                    replace=replace,
                )
        elif replace:
            record.set_metadata(None, self.metadata_class, replace=replace)

        if by_reference_deposit:
            by_reference_schema = ByReferenceSchema(
                context={"url_adapter": current_app.create_url_adapter(request)},
            )
            if metadata_deposit:
                by_reference = by_reference_schema.load(request.json["by-reference"])
            else:
                by_reference = by_reference_schema.load(request.json)
            record.set_by_reference_files(
                by_reference["files"],
                dereference_policy=self.endpoint_options["dereference_policy"],
                request_url=request.url,
                replace=replace,
            )
        elif replace:
            record.set_by_reference_files(
                [],
                dereference_policy=self.endpoint_options["dereference_policy"],
                request_url=request.url,
                replace=replace,
            )

        if not (metadata_deposit or by_reference_deposit) and (
            request.content_type or request.content_length
        ):
            self.ingest_file(record, request.stream, replace=replace)
        elif replace:
            self.ingest_file(record, None, replace=replace)

        self.update_deposit_status(record)

        record.commit()
        db.session.commit()

    def ingest_file(
        self, record: SWORDDeposit, stream: typing.Optional[BytesReader], replace=True
    ):
        """
        Sets or adds to a deposit fileset using a bytestream and request headers

        This method wraps ``record.set_fileset_from_stream()`` with appropriate arguments.

        :param record: The SWORDDeposit record to modify
        :param stream: A bytestream of the file or package to be deposited
        :param replace: Whether to replace or add to the deposit
        :return: an IngestResult
        """
        return record.ingest_file(
            stream if (request.content_type or request.content_length) else None,
            packaging_name=self.packaging_name,
            content_disposition=request.headers.get("Content-Disposition"),
            content_type=request.content_type,
            replace=replace,
        )
