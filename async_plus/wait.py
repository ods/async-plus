import asyncio
import logging
import math
import sys
from time import monotonic
from typing import Awaitable, Optional

from .typing import FloatLike


__all__ = ['impatient']


logger = logging.getLogger(__name__)


def _describe_caller(stacklevel=1):
    frame = sys._getframe(stacklevel)
    return f'at {frame.f_code.co_filename}:{frame.f_lineno}'


def _pprint_float(value, significant_digits=2):
    precision = max(0, math.ceil(-math.log(value) / math.log(10)) + 1)
    return f'{value:.{precision}f}'


async def impatient(
    aw: Awaitable,
    *,
    log_after: Optional[FloatLike],
    # TODO Use `Literal` after dropping support for Python 3.7
    # Literal['never', 'after_long_wait', 'always']
    log_finish: str = 'after_long_wait',
    log_level: int = logging.INFO,
):
    """Wait `aw` for completion, log message if it takes too long and/or it
    finishes.

    Possible values for `log_finish`:
        'never'
            don't log on completion
        'after_long_wait'
            log on completion only when it took more than `log_after` and
            corresponding message was logged
        'always'
            log on completion even if took less than `log_after` (`log_after`
            may be `None` is this case)
    """
    if log_finish in ('never', 'after_long_wait'):
        if log_after is None:
            raise ValueError(
                f"log_after can't be None for log_finish={log_finish!r}"
            )
    elif log_finish != 'always':
        raise ValueError(f'Invalid value for log_after: {log_after!r}')

    fut = asyncio.ensure_future(aw)
    long_wait = False
    started = monotonic()

    done, _ = await asyncio.wait({fut}, timeout=log_after)

    if not done and log_after is not None:
        long_wait = True
        message = (
            f'Still wating for {aw!r} {_describe_caller()} after '
            f'{log_after} secs'
        )
        logger.log(log_level, message)

    try:
        return await fut
    finally:
        if (
            log_finish == 'always' or
            (log_finish == 'after_long_wait' and long_wait)
        ):
            exc = fut.exception()
            if exc is None:
                status = 'returned'
            else:
                status = f'raised {type(exc).__name__}'

            elapsed = monotonic() - started

            message = (
                f'{aw!r} {_describe_caller()} {status} after '
                f'{_pprint_float(elapsed)} secs'
            )
            logger.log(log_level, message)
