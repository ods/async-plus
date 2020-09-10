import asyncio
import logging
from time import monotonic
from typing import Awaitable, Optional

from .typing import FloatLike


__all__ = ['impatient']


logger = logging.getLogger(__name__)


async def impatient(
    aw: Awaitable,
    *,
    log_after: Optional[FloatLike],
    # TODO Use `Literal` after dropping support for Python 3.7
    # Literal['never', 'after_long_wait', 'always']
    log_finish: str = 'after_long_wait',
    log_level: int = logging.INFO,
):
    """
    Wait `aw` for completion, log message if it takes too long and/or it
    finishes.

    Possible values for `log_finish`:
        'never'           — don't log on completion
        'after_long_wait' — log on completion only when it took more than
                            `log_after` and corresponding message was logged
        'always'          - log on completion even if took less than
                            `log_after` (`log_after` can be `None` is this
                            case)
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
        logger.log(log_level, f"{aw!r} didn't finish in {log_after} secs")

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

            # TODO Pretty representation for `aw` with source
            # TODO Pretty representation for `elapsed` with flexible precision
            # and units
            logger.log(log_level, f'{aw!r} {status} after {elapsed:.1f} secs')
