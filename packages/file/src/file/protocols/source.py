from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

from .batch import Batch
from .config import BaseConfig


@dataclass
class ExtractResult:
    batches: AsyncIterator[Batch]
    total_rows: int | None = None
    schema: Any | None = None


class SourceConnector(Protocol):
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
    async def get_schema(self, table_name: str) -> Any:
        ...

    @abstractmethod
    async def extract(
        self,
        table_name: str,
        config: BaseConfig,
        columns: list[str] | None = None,
        filter_predicate: str | None = None,
    ) -> ExtractResult:
        ...

    @abstractmethod
    async def get_checkpoint(self, table_name: str) -> dict | None:
        ...

    @abstractmethod
    async def list_tables(self, config: BaseConfig) -> list[str]:
        ...

    @abstractmethod
    async def list_databases(self, config: BaseConfig) -> list[str]:
        ...

    @abstractmethod
    def supports_incremental(self) -> bool:
        ...
