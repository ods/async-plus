import asyncio
from contextlib import asynccontextmanager
import functools
import logging


__all__ = ['try_gather', 'launch_watched', 'task_scope']


logger = logging.getLogger(__name__)


async def try_gather(*futures_or_coroutines):
    """Safe version of gather that doesn't leak tasks."""
    futs = [asyncio.ensure_future(fut) for fut in futures_or_coroutines]
    try:
        return await asyncio.gather(*futs)
    finally:
        for fut in futs:
            if not fut.done():
                fut.cancel()
        # TODO Limit time and log warning when timed out?
        await asyncio.wait(futs)


def _task_done_callback(task, on_exception=None):
    if task.cancelled():
        return

    exc = task.exception()
    if exc is None:
        return

    if on_exception is None:
        logger.exception(f'Exception in {task!r}:', exc_info=exc)
    else:
        try:
            on_exception(task, exc)
        except:
            logger.exception(
                f'Exception when handling error for {task!r}:',
            )


def set_task_name(task, name):
    # For compatibility with Python <3.8
    if name is not None:
        try:
            set_name = task.set_name
        except AttributeError:
            pass
        else:
            set_name(name)


def launch_watched(coro, name=None, on_exception=None):
    task = asyncio.create_task(coro)
    set_task_name(task, name)
    task.add_done_callback(
        functools.partial(_task_done_callback, on_exception=on_exception)
    )
    return task


@asynccontextmanager
async def task_scope(on_exception=None):
    """Isolated scope of tasks.  All tasks launched in the scope are cancelled
    on exit.

    Usage example:

        async with task_scope() as scope:
            scope.launch(coro1)
            scope.launch(coro2)
            await scope.wait()
    """
    scope = _TaskScope(on_exception)
    try:
        yield scope
    finally:
        scope.cancel()
        # Wait cancelation to take effect
        if scope:
            await scope.wait(return_when=asyncio.ALL_COMPLETED)


class _TaskScope:

    def __init__(self, on_exception=None):
        self.tasks = set()
        self.default_on_exception = on_exception

    def __len__(self):
        return len(self.tasks)

    def launch(self, coro, on_exception=None, **kwargs):
        if on_exception is None:
            on_exception = self.default_on_exception
        task = launch_watched(coro, on_exception=on_exception, **kwargs)
        self.tasks.add(task)
        return task

    def cancel(self):
        for task in self.tasks:
            # Calling `cancel()` for task with exception would clear the
            # `_log_traceback` flag, so we have to exclude them
            if not task.done():
                task.cancel()

    async def wait(self, timeout=None, return_when=asyncio.FIRST_EXCEPTION):
        await asyncio.wait_for(
            asyncio.wait(self.tasks, return_when=return_when),
            timeout=timeout,
        )
