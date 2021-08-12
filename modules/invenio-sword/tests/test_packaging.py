import io
import secrets
from typing import Type

import pytest
from invenio_files_rest.models import ObjectVersion

from invenio_sword.api import SWORDDeposit
from invenio_sword.packaging import BinaryPackaging
from invenio_sword.packaging import Packaging
from invenio_sword.packaging import SimpleZipPackaging
from invenio_sword.packaging import SWORDBagItPackaging


def test_get_original_deposit_filename(api, es, location):
    with api.test_request_context():
        record: SWORDDeposit = SWORDDeposit.create({})
        packaging = BinaryPackaging(record)

        filename = secrets.token_hex(16)
        assert (
            packaging.get_original_deposit_filename(filename, media_type="text/plain")
            == filename
        )

        assert packaging.get_original_deposit_filename(
            media_type="text/plain"
        ).endswith(".txt")

        assert packaging.get_original_deposit_filename().endswith(".bin")


@pytest.mark.parametrize("packaging_cls", [SimpleZipPackaging, SWORDBagItPackaging])
def test_non_binary_doesnt_shortcut_unpack(
    api, location, es, packaging_cls: Type[Packaging]
):
    with api.test_request_context():
        record = SWORDDeposit.create({})
        object_version = ObjectVersion.create(
            bucket=record.bucket, key="some-file.txt", stream=io.BytesIO(b"data")
        )
        packaging = packaging_cls(record)
        assert packaging.shortcut_unpack(object_version) == NotImplemented
