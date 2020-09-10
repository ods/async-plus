import asyncio
import logging

import pytest

import async_plus


RESULT = object()

class CustomException(Exception):
    pass

async def delayed(delay, result):
    await asyncio.sleep(delay)
    if isinstance(result, BaseException):
        raise result
    else:
        return result


async def test_long_success(caplog):
    with caplog.at_level(logging.INFO):
        result = await async_plus.impatient(
            delayed(0.2, RESULT), log_after=0.1,
        )

    assert result is RESULT
    rec1, rec2 = caplog.pop_matching(name='async_plus')
    assert "didn't finish in 0.1 secs" in rec1.message
    assert 'returned after 0.2 secs' in rec2.message


async def test_long_exception(caplog):
    with caplog.at_level(logging.INFO), pytest.raises(CustomException):
        await async_plus.impatient(
            delayed(0.2, CustomException()), log_after=0.1,
        )

    rec1, rec2 = caplog.pop_matching(name='async_plus')
    assert "didn't finish in 0.1 secs" in rec1.message
    assert 'raised CustomException after 0.2 secs' in rec2.message
