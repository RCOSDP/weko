from invenio_records_files.views import RecordObjectResource

__all__ = ["DepositFileView"]


class DepositFileView(RecordObjectResource):
    view_name = "{}_file"
