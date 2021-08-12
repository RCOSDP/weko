from flask_login import current_user
from invenio_deposit.scopes import write_scope
from invenio_deposit.utils import check_oauth2_scope
from invenio_oauth2server import require_api_auth

from invenio_sword.api import SWORDDeposit


def is_record_owner(record: SWORDDeposit):
    return current_user.id in record["_deposit"]["owners"]


check_has_write_scope = check_oauth2_scope(lambda record: True, write_scope.id)

check_has_write_scope_and_is_record_owner = check_oauth2_scope(
    is_record_owner, write_scope.id
)


class CheckIsRecordOwner:
    def __init__(self, record):
        self.record = record

    @require_api_auth
    def can(self):
        return is_record_owner(self.record)


check_is_record_owner = CheckIsRecordOwner
