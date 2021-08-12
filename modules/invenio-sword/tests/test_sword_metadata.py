import json

import pytest
from sword3common.exceptions import ContentTypeNotAcceptable

from invenio_sword.api import SWORDDeposit
from invenio_sword.metadata import Metadata
from invenio_sword.metadata import SWORDMetadata


class OtherMetadata(Metadata):
    pass


def test_parse_document(metadata_document):
    sword_metadata = SWORDMetadata.from_document(
        metadata_document, content_type="application/ld+json"
    )
    assert "@id" not in sword_metadata.data
    assert sword_metadata.data == {
        "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
        "@type": "Metadata",
        "dc:title": "The title",
        "dcterms:abstract": "This is my abstract",
        "dc:contributor": "A.N. Other",
    }


def test_parse_document_with_wrong_content_type(metadata_document):
    with pytest.raises(ContentTypeNotAcceptable):
        SWORDMetadata.from_document(metadata_document, content_type="text/yaml")


def test_update_record(metadata_document):
    sword_metadata = SWORDMetadata.from_document(
        metadata_document, content_type="application/ld+json"
    )
    record = SWORDDeposit(data={"metadata": {}})
    sword_metadata.update_record_metadata(record)
    assert record["metadata"]["title_statement"]["title"] == "The title"


def test_metadata_bytes_roundtrip(metadata_document):
    sword_metadata = SWORDMetadata.from_document(
        metadata_document, content_type="application/ld+json"
    )
    assert json.loads(bytes(sword_metadata)) == sword_metadata.data


def test_construct_from_dict(metadata_document):
    data = json.load(metadata_document)
    sword_metadata = SWORDMetadata(data)
    assert sword_metadata.data == data


def test_cant_add_to_other_metadata(metadata_document):
    sword_metadata = SWORDMetadata.from_document(
        metadata_document, content_type="application/ld+json"
    )
    other_metadata = OtherMetadata()

    with pytest.raises(TypeError):
        sword_metadata + other_metadata

    with pytest.raises(TypeError):
        other_metadata + sword_metadata

    assert sword_metadata.__add__(other_metadata) == NotImplemented
