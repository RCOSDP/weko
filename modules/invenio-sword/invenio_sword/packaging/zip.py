from __future__ import annotations

import mimetypes
import shutil
import tempfile
import uuid
import zipfile

from invenio_files_rest.models import ObjectVersion
from sword3common.constants import PackagingFormat
from sword3common.exceptions import ContentMalformed
from sword3common.exceptions import ContentTypeNotAcceptable

from ..enum import ObjectTagKey
from ..utils import TagManager
from .base import Packaging


__all__ = ["SimpleZipPackaging"]


class SimpleZipPackaging(Packaging):
    content_type = "application/zip"
    packaging_name = PackagingFormat.SimpleZip

    def get_original_deposit_filename(
        self, filename: str = None, media_type: str = None
    ) -> str:
        return self.record.original_deposit_key_prefix + "simple-zip-{}.zip".format(
            uuid.uuid4()
        )

    def unpack(self, object_version: ObjectVersion):
        if object_version.mimetype != self.content_type:
            raise ContentTypeNotAcceptable(
                "Content-Type must be {}".format(self.content_type)
            )

        try:
            with tempfile.TemporaryFile() as f:
                with object_version.file.storage().open() as stream:
                    shutil.copyfileobj(stream, f)
                f.seek(0)

                with zipfile.ZipFile(f) as zip:
                    names = set(zip.namelist())

                    for name in names:
                        archive_object_version = ObjectVersion.create(
                            self.record.bucket,
                            name,
                            mimetype=mimetypes.guess_type(name)[0],
                            stream=zip.open(name),
                        )

                        tags = TagManager(archive_object_version)
                        tags.update(
                            {
                                ObjectTagKey.FileSetFile: "true",
                                ObjectTagKey.DerivedFrom: object_version.key,
                            }
                        )
                return names
        except zipfile.BadZipFile as e:
            raise ContentMalformed("Bad ZIP file") from e
