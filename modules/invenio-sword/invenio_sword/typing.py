from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING
from typing import Type
from typing import Union

import sys


if TYPE_CHECKING:  # pragma: nocover
    from invenio_files_rest.models import ObjectVersion
    from invenio_sword.metadata import Metadata
    from invenio_sword.packaging import Packaging
    from invenio_sword.schemas import ByReferenceFileDefinition
    from invenio_deposit.search import DepositSearch
    from invenio_sword.api import SWORDDeposit

if sys.version_info >= (3, 8):  # pragma: nocover
    from typing import Protocol
    from typing import runtime_checkable
    from typing import TypedDict
else:  # pragma: nocover
    from typing_extensions import Protocol  # type: ignore
    from typing_extensions import runtime_checkable
    from typing_extensions import TypedDict


@runtime_checkable
class BytesReader(Protocol):
    def read(self, amount: int = -1) -> bytes:
        ...  # pragma: nocover


class SwordEndpointDefinition(TypedDict):
    packaging_formats: Dict[str, Type[Packaging]]
    metadata_formats: Dict[str, Type[Metadata]]
    default_packaging_format: str
    default_metadata_format: str

    record_class: Optional[Union[Type[SWORDDeposit], str]]
    search_class: Optional[Union[Type[DepositSearch], str]]
    search_index: Optional[str]
    search_type: Optional[Any]
    indexer_class: Any

    create_permission_factory_imp: Callable
    read_permission_factory_imp: Callable
    update_permission_factory_imp: Callable
    delete_permission_factory_imp: Callable

    service_document_route: str
    item_route: str
    metadata_route: str
    fileset_route: str
    file_route: str

    default_media_type: str

    dereference_policy: Callable[[ObjectVersion, ByReferenceFileDefinition], bool]
