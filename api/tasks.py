import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from file import migrate_all
from file.protocols import LoadResult

logger = logging.getLogger(__name__)


@dataclass
class TaskEntry:
    status: str  # running | completed | failed
    result: list[LoadResult] | None = None
    error: str | None = None


_tasks: dict[str, TaskEntry] = {}


async def run_migration(
    source: str,
    target: str,
    tables: list[str],
    source_config: dict[str, Any],
    target_config: dict[str, Any],
) -> str:
    task_id = str(uuid.uuid4())
    _tasks[task_id] = TaskEntry(status="running")
    logger.info("Task %s: migration started %s -> %s tables=%s", task_id[:8], source, target, tables)

    async def _execute():
        try:
            results = await migrate_all(
                source_name=source,
                target_name=target,
                tables=tables,
                source_kwargs=source_config,
                target_kwargs=target_config,
            )
            _tasks[task_id].status = "completed"
            _tasks[task_id].result = results
            logger.info("Task %s: migration completed successfully", task_id[:8])
        except Exception as e:
            _tasks[task_id].status = "failed"
            _tasks[task_id].error = str(e)
            logger.error("Task %s: migration failed: %s", task_id[:8], e)

    asyncio.create_task(_execute())
    return task_id


def get_task(task_id: str) -> TaskEntry | None:
    return _tasks.get(task_id)
