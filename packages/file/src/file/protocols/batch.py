from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pyarrow as pa

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class BatchMetadata:
    source_name: str
    table_name: str
    batch_id: str
    row_count: int
    byte_size: int
    schema: pa.Schema
    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    checkpoint: dict | None = None
    partition_values: dict = field(default_factory=dict)


@dataclass
class Batch:
    data: pa.Table
    metadata: BatchMetadata

    def to_pandas(self) -> "pd.DataFrame":
        return self.data.to_pandas()

    def to_parquet(self, path: str, **kwargs) -> None:
        import pyarrow.parquet as pq
        pq.write_table(self.data, path, **kwargs)
