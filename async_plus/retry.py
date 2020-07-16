import asyncio
import itertools
import time


__all__ = ['RetryDelayer']


class RetryDelayer:
    """
    Usage example:

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
    """

    def __init__(self, delays=(0, 10, 60), reset_after=None):
        self.delays = delays
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
        await asyncio.sleep(delay)
        self._last_time = time.monotonic()
