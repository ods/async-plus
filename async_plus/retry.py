import asyncio
import itertools
from random import random
import time
from typing import Optional, Sequence, Union

from .typing import FloatLike


__all__ = ['RetryDelayer']


class RetryDelayer:
    """Usage example:

        retry_delayer = async_plus.RetryDelayer()
        while True:
            try:
                await run_service_x()
            # In Python <3.8 it inherits from Exception
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception('Error in service X:')
                await retry_delayer.sleep()

    Classic exponential backoff with first retry without delay:

        retry_delayer = async_plus.RetryDelayer(
            delays = [0] + [2 ** n for n in range(10)]
        )
        ...
    """

    def __init__(
        self,
        delays: Sequence[FloatLike] = (0, 1, 10, 60),
        random_shift: FloatLike = 0,
        reset_after: Optional[FloatLike] = None,
    ):
        self.delays = delays
        self.random_shift = random_shift

        if reset_after is None:
            reset_after = delays[-1]
        self.reset_after = reset_after

        self.reset()

    def reset(self):
        self._iter_delays = itertools.chain(
            self.delays, itertools.cycle(self.delays[-1:]),
        )
        self._last_time = time.monotonic()

    async def sleep(self):
        if time.monotonic() - self._last_time > self.reset_after:
            self.reset()

        delay = next(self._iter_delays)
        if self.random_shift:
            delay += self.random_shift * random()
        await asyncio.sleep(delay)

        self._last_time = time.monotonic()
