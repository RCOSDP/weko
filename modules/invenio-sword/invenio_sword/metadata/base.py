from __future__ import annotations

import json
import typing
import uuid

import rdflib
from rdflib.namespace import DC

from ..typing import BytesReader

if typing.TYPE_CHECKING:  # pragma: nocover
    from invenio_sword.api import SWORDDeposit


class Metadata:
    content_type: str
    filename: str
    metadata_format: str

    @classmethod
    def from_document(
        cls, document: BytesReader, content_type: str, encoding: str = "utf_8"
    ) -> Metadata:
        raise NotImplementedError  # pragma: nocover

    def to_sword_metadata(self) -> dict:
        raise NotImplementedError  # pragma: nocover

    def update_record_metadata(self, record: SWORDDeposit):
        graph = rdflib.Graph()
        subject = rdflib.URIRef("urn:uuid:" + str(uuid.uuid4()))

        data = {
            **self.to_sword_metadata(),
            "@id": str(subject),
        }
        graph.parse(data=json.dumps(data), format="json-ld")

        predicates = set(graph.predicates(subject=subject))

        if "metadata" not in record:
            record["metadata"] = {}

        if DC.title in predicates:
            if "title_statement" not in record["metadata"]:
                record["metadata"]["title_statement"] = {}
            record["metadata"]["title_statement"]["title"] = str(
                graph.value(subject, DC.title)
            )
        elif "title" in record["metadata"].get("title_statement", {}):
            del record["metadata"]["title_statement"]["title"]

    def __bytes__(self):
        raise NotImplementedError  # pragma: nocover

    def __add__(self, other):
        return NotImplemented  # pragma: nocover


class JSONMetadata(Metadata):
    @classmethod
    def from_document(
        cls,
        document: typing.Union[BytesReader, dict],
        content_type: str,
        encoding: str = "utf_8",
    ) -> Metadata:
        raise NotImplementedError
