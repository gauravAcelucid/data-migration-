from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Protocol

from .batch import Batch
from .config import BaseConfig


@dataclass
class LoadResult:
    destination_type: str
    table_name: str
    rows_loaded: int
    batch_count: int
    errors: list[str]


@dataclass
class TargetCapabilities:
    supports_batch_write: bool
    supports_parallel_uploads: bool
    max_batch_size: int


class TargetConnector(Protocol):
    @abstractmethod
    async def connect(self, config: BaseConfig) -> None:
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        ...

    @abstractmethod
    async def load(
        self,
        batches: AsyncIterator[Batch],
        table_name: str,
    ) -> LoadResult:
        ...

    @abstractmethod
    def get_capabilities(self) -> TargetCapabilities:
        ...
