from __future__ import annotations

from invenio_files_rest.models import ObjectVersion
from sword3common.constants import PackagingFormat

from ..enum import ObjectTagKey
from ..utils import TagManager
from .base import Packaging

__all__ = ["BinaryPackaging"]


class BinaryPackaging(Packaging):
    packaging_name = PackagingFormat.Binary

    def shortcut_unpack(self, object_version: ObjectVersion):
        tags = TagManager(object_version)
        tags[ObjectTagKey.FileSetFile] = "true"
        return []

    def unpack(self, object_version: ObjectVersion):
        return self.shortcut_unpack(object_version)
