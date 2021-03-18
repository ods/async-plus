import asyncio
import sys
import time
from unittest import mock

import pytest

import async_plus


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason='author is too lazy to backport test',
)
@pytest.mark.parametrize('reset_after', [None, 10])
async def test_full_cycle(reset_after):
    delayer = async_plus.RetryDelayer([0, 1, 5], reset_after=reset_after)
    if reset_after is None:
        reset_after = 5

    with mock.patch.object(time, 'monotonic') as monotonic_mock:
        monotonic_mock.return_value = 0

        def shift_monotonic(secs):
            monotonic_mock.return_value += secs

        for shift, expected_sleep in [
            (0              , 0), # 1st
            (reset_after + 1, 0), # reset + 1st
            (reset_after - 1, 1), # 2nd
            (reset_after + 1, 0), # reset + 1st
            (reset_after - 1, 1), # 2nd
            (reset_after - 1, 5), # 3rd
            (reset_after - 1, 5), # last repeated
            (reset_after + 1, 0), # reset + 1st
        ]:
            shift_monotonic(shift)
            with mock.patch.object(
                asyncio, 'sleep', side_effect=shift_monotonic,
            ) as sleep_mock:
                await delayer.sleep()
                sleep_mock.assert_awaited_once_with(expected_sleep)


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason='author is too lazy to backport test',
)
async def test_random_shift():
    delayer = async_plus.RetryDelayer([3], random_shift=2)

    def shift_monotonic(secs):
        monotonic_mock.return_value += secs

    with mock.patch.object(time, 'monotonic') as monotonic_mock, \
            mock.patch.object(
                asyncio, 'sleep', side_effect=shift_monotonic,
            ) as sleep_mock:
        monotonic_mock.return_value = 0

        COUNT = 1_000
        shifts = 0
        for i in range(COUNT):
            await delayer.sleep()
            assert sleep_mock.await_count == i + 1
            (delay,) = sleep_mock.await_args.args  # type: ignore
            assert 3 <= delay < 5
            shifts += delay - 3

        avg_shift = shifts / COUNT
        assert 0.9 < avg_shift < 1.1
