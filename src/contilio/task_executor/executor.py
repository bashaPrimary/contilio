import asyncio
import logging
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from functools import wraps
from typing import cast, Callable, Awaitable, Any, TypeVar, Optional

from strawberry.types import Info as GraphQLResolveInfo

logger = logging.getLogger(__name__)


def get_task_executor(max_workers: int = 4) -> Executor:
    return ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="db",
        initializer=lambda: logger.info("Spawning a Worker in an Executor Pool"),
    )


def executor_from_request_context(info: Optional[GraphQLResolveInfo]) -> Optional[Executor]:
    """A helper function that knows how to retrieve an application-level thread pool
    from contextual data assigned to Starlette/FastAPI request.
    """
    if info is None:
        return None
    if not info.context:
        raise ValueError("Context needs to be present")
    return cast(Executor, info.context["request"].app.extra["task_executor"])


T = TypeVar("T")


def make_awaitable(
    info: Optional[GraphQLResolveInfo] = None,
) -> Callable[[Callable[[], T]], Awaitable[T]]:
    """Produce a function that is capable of running blocking functions concurrently. If a
    ResolveInfo is supplied then the executor is taken from the request context.
    """
    task_executor = executor_from_request_context(info) or ThreadPoolExecutor(
        thread_name_prefix="concurrently"
    )
    loop = asyncio.get_event_loop()

    def run(f: Callable[..., T]) -> Awaitable[T]:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            # TODO: Trace this:
            return f(*args, **kwargs)

        return loop.run_in_executor(task_executor, wrapped)

    return run
