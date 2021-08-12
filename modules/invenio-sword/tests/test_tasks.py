import io

from invenio_sword.schemas import ByReferenceFileDefinition
from sword3common.constants import PackagingFormat

from invenio_sword import tasks
from invenio_sword.api import SWORDDeposit


def test_delete_old_files(api, location, es, task_delay):
    with api.test_request_context():
        record: SWORDDeposit = SWORDDeposit.create({})

        record.set_by_reference_files(
            [
                ByReferenceFileDefinition(
                    url="http://example.com/one",
                    content_disposition="attachment; filename=br-yes.html",
                    content_type="text/html",
                    content_length=100,
                    packaging=PackagingFormat.Binary,
                    dereference=False,
                ),
                ByReferenceFileDefinition(
                    url="http://example.com/two",
                    content_disposition="attachment; filename=br-no.html",
                    content_type="text/html",
                    packaging=PackagingFormat.Binary,
                    dereference=False,
                ),
            ],
            dereference_policy=lambda record, brf: brf.dereference,
            request_url="http://localhost/something",
            replace=False,
        )

        record.ingest_file(
            io.BytesIO(b"data"),
            packaging_name=PackagingFormat.Binary,
            content_type="text/html",
            content_disposition="attachment; filename=direct-yes.html",
            replace=False,
        )
        record.ingest_file(
            io.BytesIO(b"data"),
            packaging_name=PackagingFormat.Binary,
            content_type="text/html",
            content_disposition="attachment; filename=direct-no.html",
            replace=False,
        )

        assert sorted(file.key for file in record.files) == [
            "br-no.html",
            "br-yes.html",
            "direct-no.html",
            "direct-yes.html",
        ]

        tasks.delete_old_objects(
            ["br-yes.html", "direct-yes.html"], bucket_id=record.bucket_id
        )

        assert sorted(file.key for file in record.files) == [
            "br-yes.html",
            "direct-yes.html",
        ]
