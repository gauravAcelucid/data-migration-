from file._registry import create_source, create_target, list_sources, list_targets, migrate_all

import file.postgresql
import file.mongodb
import file.sql
import file.s3
import file.file_upload

__all__ = [
    "create_source",
    "create_target",
    "list_sources",
    "list_targets",
    "migrate_all",
]
