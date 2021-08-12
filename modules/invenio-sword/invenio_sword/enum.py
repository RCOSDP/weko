import enum


class ObjectTagKey(enum.Enum):
    OriginalDeposit = "invenio_sword.originalDeposit"
    DerivedFrom = "invenio_sword.derivedFrom"
    FileSetFile = "invenio_sword.fileSetFile"
    Packaging = "invenio_sword.packaging"
    MetadataFormat = "invenio_sword.metadataFormat"
    FileState = "invenio_sword.fileState"
    ByReferenceURL = "invenio_sword.byReferenceURL"
    ByReferenceTemporaryID = "invenio_sword.byReferenceTemporaryID"
    ByReferenceDereference = "invenio_sword.byReferenceDereference"
    ByReferenceTTL = "invenio_sword.byReferenceTTL"
    ByReferenceContentLength = "invenio_sword.byReferenceContentLength"
    # Used to mark an object version as extent, even though it's not got a file.
    ByReferenceNotDeleted = "invenio_sword.byReferenceNotDeleted"


class FileState(enum.Enum):
    Pending = "http://purl.org/net/sword/3.0/filestate/pending"
    Downloading = "http://purl.org/net/sword/3.0/filestate/downloading"
    Unpacking = "http://purl.org/net/sword/3.0/filestate/unpacking"
    Error = "http://purl.org/net/sword/3.0/filestate/error"
    Ingested = "http://purl.org/net/sword/3.0/filestate/ingested"
