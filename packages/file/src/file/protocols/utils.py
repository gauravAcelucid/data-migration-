import asyncio
from collections.abc import Callable
from concurrent.futures import Executor
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def run_sync_in_executor(
    func: Callable[P, R],
    executor: Executor | None = None,
) -> Callable[P, asyncio.Future]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
    return wrapper


class SyncToAsync:
    def __init__(self, max_workers: int = 4):
        self._executor = None
        self._max_workers = max_workers

    @property
    def executor(self):
        if self._executor is None:
            from concurrent.futures import ThreadPoolExecutor
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        return self._executor

    async def run_sync(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, lambda: func(*args, **kwargs))

    async def close(self):
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
