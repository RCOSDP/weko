from http import HTTPStatus

from flask import Response
from invenio_db import db
from invenio_records_rest.views import need_record_permission
from invenio_records_rest.views import pass_record

from . import SWORDDepositView
from ..api import SWORDDeposit

__all__ = ["DepositStatusView"]


class DepositStatusView(SWORDDepositView):
    view_name = "{}_item"

    @pass_record
    @need_record_permission("read_permission_factory")
    def get(self, pid, record: SWORDDeposit):
        """Retrieve a SWORD status document for a deposit record

        :see also: https://swordapp.github.io/swordv3/swordv3.html#9.6.
        """
        return record.get_status_as_jsonld()

    @pass_record
    @need_record_permission("update_permission_factory")
    def post(self, pid, record: SWORDDeposit):
        """Augment a SWORD deposit with either metadata or files"""
        self.update_deposit(record, replace=False)
        return record.get_status_as_jsonld()

    @pass_record
    @need_record_permission("update_permission_factory")
    def put(self, pid, record: SWORDDeposit):
        """Replace a SWORD deposit with either metadata or files"""
        self.update_deposit(record)
        return record.get_status_as_jsonld()

    @pass_record
    @need_record_permission("update_permission_factory")
    def delete(self, pid, record: SWORDDeposit):
        """Delete a SWORD deposit"""
        record.delete()
        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)
