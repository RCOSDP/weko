from http import HTTPStatus

from flask import request
from flask import Response
from invenio_db import db
from invenio_records_rest.views import need_record_permission
from invenio_records_rest.views import pass_record

from . import SWORDDepositView
from ..api import SWORDDeposit

__all__ = ["DepositFilesetView"]


class DepositFilesetView(SWORDDepositView):
    view_name = "{}_fileset"

    @pass_record
    @need_record_permission("update_permission_factory")
    def post(self, pid, record: SWORDDeposit):
        self.ingest_file(
            record,
            request.stream
            if (request.content_type or request.content_length)
            else None,
            replace=False,
        )
        record.commit()
        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)

    @pass_record
    @need_record_permission("update_permission_factory")
    def put(self, pid, record: SWORDDeposit):
        self.ingest_file(
            record,
            request.stream
            if (request.content_type or request.content_length)
            else None,
        )
        record.commit()
        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)

    @pass_record
    @need_record_permission("update_permission_factory")
    def delete(self, pid, record: SWORDDeposit):
        self.ingest_file(
            record, None,
        )
        record.commit()
        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)
