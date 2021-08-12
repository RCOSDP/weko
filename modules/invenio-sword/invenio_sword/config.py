from typing import Dict

import pkg_resources
from invenio_deposit.config import DEPOSIT_REST_ENDPOINTS
from sword3common.constants import MetadataFormat
from sword3common.constants import PackagingFormat

from . import permissions
from .typing import SwordEndpointDefinition

SWORD_MAX_UPLOAD_SIZE = 1024 ** 3  # 1 GiB
SWORD_MAX_BY_REFERENCE_SIZE = 10 * 1024 ** 3  # 10 GiB

_PID = 'pid(depid,record_class="invenio_sword.api:SWORDDeposit")'

SWORD_ENDPOINTS: Dict[str, SwordEndpointDefinition] = {
    name: {
        "packaging_formats": {
            ep.name: ep.load()
            for ep in pkg_resources.iter_entry_points("invenio_sword.packaging")
        },
        "metadata_formats": {
            ep.name: ep.load()
            for ep in pkg_resources.iter_entry_points("invenio_sword.metadata")
        },
        "default_packaging_format": PackagingFormat.Binary,
        "default_metadata_format": MetadataFormat.Sword,
        "record_class": "invenio_sword.api:Deposit",
        "default_media_type": "application/ld+json",
        # Permissions
        "create_permission_factory_imp": permissions.check_has_write_scope,
        "read_permission_factory_imp": permissions.check_is_record_owner,
        "update_permission_factory_imp": permissions.check_has_write_scope_and_is_record_owner,
        "delete_permission_factory_imp": permissions.check_has_write_scope_and_is_record_owner,
        # Routes
        "service_document_route": "/sword/service-document",
        "item_route": "/sword/deposit/<{}:pid_value>".format(_PID),
        "metadata_route": "/sword/deposit/<{}:pid_value>/metadata".format(_PID),
        "fileset_route": "/sword/deposit/<{}:pid_value>/fileset".format(_PID),
        "file_route": "/sword/deposit/<{}:pid_value>/file/<path:key>".format(_PID),
        # Search
        "search_class": "invenio_deposit.search:DepositSearch",
        "indexer_class": None,
        "search_index": None,
        "search_type": None,
        # By-reference
        "dereference_policy": (
            lambda object_version, by_reference_file: by_reference_file.dereference
        ),
    }
    for name, options in DEPOSIT_REST_ENDPOINTS.items()
}


_SEGMENTED_UPLOAD_PID = (
    'pid(stagingid,record_class="invenio_sword.api:SegmentedUploadRecord")'
)

SWORD_STAGING_MAX_IDLE = 3600
SWORD_STAGING_PID_TYPE = "stagingid"
SWORD_STAGING_URL_ROUTE = "/sword/staging"
SWORD_TEMPORARY_URL_ROUTE = "/sword/staging/<uuid:temporary_id>"
SWORD_SEGMENTED_UPLOAD_CONTEXT = {
    "create_permission_factory": permissions.check_has_write_scope,
    "read_permission_factory": permissions.check_is_record_owner,
    "update_permission_factory": permissions.check_has_write_scope_and_is_record_owner,
    "delete_permission_factory": permissions.check_has_write_scope_and_is_record_owner,
}
