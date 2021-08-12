from __future__ import annotations

import json
import typing

from sword3common.constants import MetadataFormat
from sword3common.exceptions import ContentMalformed
from sword3common.exceptions import ContentTypeNotAcceptable

from .base import JSONMetadata
from invenio_sword.typing import BytesReader

__all__ = ["SWORDMetadata"]


class SWORDMetadata(JSONMetadata):
    content_type = "application/ld+json"
    filename = "sword.jsonld"
    metadata_format = MetadataFormat.Sword

    def __init__(self, data):
        self.data = data

    @classmethod
    def from_document(
        cls,
        document: typing.Union[BytesReader, dict],
        content_type: str,
        encoding: str = "utf_8",
    ) -> SWORDMetadata:
        if content_type not in (cls.content_type, "application/json"):
            raise ContentTypeNotAcceptable(
                "Content-Type must be {}".format(cls.content_type)
            )
        if isinstance(document, BytesReader):
            if encoding not in ('U8', 'UTF', 'utf8', 'utf_8', 'utf-8', 'cp65001'):
                raise ValueError("encoding must be utf_8 or an alias thereof")
            try:
                data = json.load(document)
            except json.JSONDecodeError as e:
                raise ContentMalformed("Unable to parse JSON") from e
        else:
            data = document
        data.pop("@id", None)
        return cls(data)

    def to_sword_metadata(self) -> dict:
        # Record the full SWORD metadata without the '@id' key
        return {k: self.data[k] for k in self.data if k != "@id"}

    def __add__(self, other):
        if not isinstance(other, SWORDMetadata):
            return NotImplemented
        return type(self)({**self.data, **other.data})

    def __bytes__(self):
        return json.dumps(self.data, indent=2).encode("utf-8")
