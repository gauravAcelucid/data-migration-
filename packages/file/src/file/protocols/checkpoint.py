import json
from pathlib import Path
from typing import Any


class CheckpointFile:
    def __init__(self, path: str | None = None):
        self._path = Path(path) if path else None
        self._data: dict[str, Any] = {}
        if self._path and self._path.exists():
            with self._path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)

    def get(self, table: str) -> Any | None:
        return self._data.get(table)

    def set(self, table: str, value: Any) -> None:
        self._data[table] = value
        if self._path:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, default=str)

    def contains(self, table: str) -> bool:
        return table in self._data
