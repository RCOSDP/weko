from http import HTTPStatus

from flask import current_app, url_for
from flask import request
from flask import Response
from invenio_records_rest.views import need_record_permission
from invenio_records_rest.views import verify_record_permission

from . import SWORDDepositView

__all__ = ["ServiceDocumentView"]


class ServiceDocumentView(SWORDDepositView):
    view_name = "{}_service_document"

    def get(self):
        """Retrieve the service document

        :see also: https://swordapp.github.io/swordv3/swordv3.html#9.2.
        """
        return {
            # Preamble
            "@type": "ServiceDocument",
            "dc:title": current_app.config["THEME_SITENAME"],
            "root": request.url,
            "acceptDeposits": True,
            "version": "http://purl.org/net/sword/3.0",
            # Capabilities
            "byReferenceDeposit": True,
            "onBehalfOf": False,
            # Size limits (not currently enforced)
            "maxUploadSize": current_app.config["SWORD_MAX_UPLOAD_SIZE"],
            "maxByReferenceSize": current_app.config["SWORD_MAX_BY_REFERENCE_SIZE"],
            # Accepted formats
            "acceptArchiveFormat": ["application/zip"],
            "acceptPackaging": sorted(self.endpoint_options["packaging_formats"]),
            "acceptMetadata": sorted(self.endpoint_options["metadata_formats"]),
            # Segmented uploads
            "staging": url_for("invenio_sword.staging_url"),
            "stagingMaxIdle": current_app.config["SWORD_STAGING_MAX_IDLE"],
            "maxAssembledSize": min(
                current_app.config["FILES_REST_MULTIPART_MAX_PARTS"]
                * current_app.config["FILES_REST_MULTIPART_CHUNKSIZE_MAX"],
                current_app.config["SWORD_MAX_BY_REFERENCE_SIZE"],
            ),
            "maxSegments": current_app.config["FILES_REST_MULTIPART_MAX_PARTS"],
        }

    @need_record_permission("create_permission_factory")
    def post(self, **kwargs):
        """Initiate a SWORD deposit"""
        record = self.create_deposit()

        # Check permissions
        permission_factory = self.create_permission_factory
        if permission_factory:
            verify_record_permission(permission_factory, record)

        self.update_deposit(record, replace=False)

        response = self.make_response(record.get_status_as_jsonld())  # type: Response
        response.status_code = HTTPStatus.CREATED
        response.headers["Location"] = record.sword_status_url
        return response
