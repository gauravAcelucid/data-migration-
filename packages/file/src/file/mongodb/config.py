from typing import Literal

from file.protocols.config import BaseConfig


class MongoDBConfig(BaseConfig):
    source_type: Literal["mongodb"] = "mongodb"

    connection_string: str
    database: str
    collection: str

    max_pool_size: int = 100
    min_pool_size: int = 10

    batch_size: int = 20_000

    incremental_field: str | None = None
    last_checkpoint: dict | None = None
    checkpoint_file: str | None = None

    read_preference: Literal["primary", "secondary", "nearest"] = "primary"
