from __future__ import annotations

import mimetypes
import typing
import uuid
from typing import Any
from typing import Collection
from typing import Union

from flask import current_app
from invenio_files_rest.models import ObjectVersion

if typing.TYPE_CHECKING:  # pragma: nocover
    from ..api import SWORDDeposit


class Packaging:
    packaging_name: str

    def __init__(self, record: SWORDDeposit):
        self.record = record

    def get_original_deposit_filename(
        self, filename: str = None, media_type: str = None
    ) -> str:
        if filename:
            return filename
        elif media_type and mimetypes.guess_extension(media_type):
            return "{}{}".format(uuid.uuid4(), mimetypes.guess_extension(media_type))
        else:
            return "{}.bin".format(uuid.uuid4())

    @classmethod
    def for_record_and_name(cls, record: SWORDDeposit, packaging_name: str):
        packaging_class = current_app.config["SWORD_ENDPOINTS"][record.pid.pid_type][
            "packaging_formats"
        ][packaging_name]
        return packaging_class(record)

    def shortcut_unpack(
        self, object_version: ObjectVersion
    ) -> Union[Any, Collection[str]]:
        """Override this to shortcut task-based unpacking"""
        return NotImplemented

    def unpack(self, object_version: ObjectVersion) -> Collection[str]:
        raise NotImplementedError  # pragma: nocover
