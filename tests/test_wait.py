import asyncio
import logging
import sys

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


@pytest.mark.parametrize('log_completion', ['never', 'after_long_wait', 'bad'])
@pytest.mark.filterwarnings(
    'ignore:coroutine .* was never awaited:RuntimeWarning'
)
async def test_unsound_usage(log_completion):
    with pytest.raises(ValueError):
        await async_plus.impatient(
            delayed(0, None), log_completion=log_completion,
        )


async def test_no_log_after_success(caplog):
    with caplog.at_level(logging.INFO):
        result = await async_plus.impatient(
            delayed(0, RESULT), log_completion='always',
        )

    assert result is RESULT
    [rec] = caplog.matching(name='async_plus')
    assert 'returned after' in rec.message
    assert 'tests/test_wait.py' in rec.message


async def test_no_log_after_exception(caplog):
    with caplog.at_level(logging.INFO), pytest.raises(CustomException):
        await async_plus.impatient(
            delayed(0, CustomException()), log_completion='always',
        )

    [rec] = caplog.matching(name='async_plus')
    assert 'raised CustomException after' in rec.message
    assert 'tests/test_wait.py' in rec.message


@pytest.mark.parametrize('log_completion', ['after_long_wait', 'always'])
async def test_long_wait_success(caplog, log_completion):
    with caplog.at_level(logging.INFO):
        result = await async_plus.impatient(
            delayed(0.2, RESULT), log_after=0.1, log_completion=log_completion,
        )

    assert result is RESULT
    rec1, rec2 = caplog.matching(name='async_plus')
    assert 'Still wating for' in rec1.message
    assert 'returned after' in rec2.message
    assert 'tests/test_wait.py' in rec1.message
    assert 'tests/test_wait.py' in rec2.message


@pytest.mark.parametrize('log_completion', ['after_long_wait', 'always'])
async def test_long_wait_exception(caplog, log_completion):
    with caplog.at_level(logging.INFO), pytest.raises(CustomException):
        await async_plus.impatient(
            delayed(0.2, CustomException()), log_after=0.1,
            log_completion=log_completion,
        )

    rec1, rec2 = caplog.matching(name='async_plus')
    assert 'Still wating for' in rec1.message
    assert 'raised CustomException after' in rec2.message
    assert 'tests/test_wait.py' in rec1.message
    if sys.version_info >= (3, 9, 0):
        assert 'tests/test_wait.py' in rec2.message


@pytest.mark.parametrize('log_completion', ['never', 'after_long_wait'])
async def test_not_long_wait_success(caplog, log_completion):
    with caplog.at_level(logging.INFO):
        result = await async_plus.impatient(
            delayed(0, RESULT), log_after=0.1, log_completion=log_completion,
        )

    assert result is RESULT
    recs = caplog.matching(name='async_plus')
    assert not recs


@pytest.mark.parametrize('log_completion', ['never', 'after_long_wait'])
async def test_not_long_wait_exception(caplog, log_completion):
    with caplog.at_level(logging.INFO), pytest.raises(CustomException):
        await async_plus.impatient(
            delayed(0, CustomException()), log_after=0.1,
            log_completion=log_completion,
        )

    recs = caplog.matching(name='async_plus')
    assert not recs
