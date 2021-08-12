from http import HTTPStatus

from flask import request
from flask import Response
from invenio_db import db
from invenio_records_rest.views import need_record_permission
from invenio_records_rest.views import pass_record

from . import SWORDDepositView
from ..api import SWORDDeposit

__all__ = ["DepositMetadataView"]


class DepositMetadataView(SWORDDepositView):
    view_name = "{}_metadata"

    @pass_record
    @need_record_permission("read_permission_factory")
    def get(self, pid, record: SWORDDeposit):
        """
        Retrieve the deposit's SWORD metadata as a JSON-LD document

        This will return the empty document with a 200 status if no metadata is available
        """
        return {
            "@id": record.sword_status_url,
            **record.get("swordMetadata", {}),
        }

    @pass_record
    @need_record_permission("update_permission_factory")
    def post(self, pid, record: SWORDDeposit):
        """
        Extend the metadata with new metadata from the request body

        :param pid: The persistent identifier for the deposit
        :param record: The SWORDDeposit object
        :raises Conflict: if there is existing metadata that doesn't support the ``+`` operation
        :return: a 204 No Content response
        """
        record.set_metadata(
            request.stream, self.metadata_class, request.content_type, replace=False
        )
        record.commit()
        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)

    @pass_record
    @need_record_permission("update_permission_factory")
    def put(self, pid, record: SWORDDeposit):
        """
        Set the metadata with new metadata from the request body

        :param pid: The persistent identifier for the deposit
        :param record: The SWORDDeposit object
        :return: a 204 No Content response
        """
        record.set_metadata(request.stream, self.metadata_class, request.content_type)
        record.commit()
        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)

    @pass_record
    @need_record_permission("delete_permission_factory")
    def delete(self, pid, record: SWORDDeposit):
        """
        Delete ny existing metadata of the format given by the Metadata-Format header

        :param pid: The persistent identifier for the deposit
        :param record: The SWORDDeposit object
        :return: a 204 No Content response
        """
        record.set_metadata(None, self.metadata_class)
        record.commit()
        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)
