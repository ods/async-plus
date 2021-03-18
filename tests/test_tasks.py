import asyncio
import inspect
import logging
from unittest.mock import Mock

import pytest

import async_plus


class CustomException(Exception):

    # Needed for `Mock.assert_called_once_with`
    def __eq__(self, other):
        return type(self) is type(other) and self.args == other.args


async def eternal():
    await asyncio.Future()

async def instant():
    pass

async def falling():
    raise CustomException('FALLING_TASK')

async def delayed(delay, result=None):
    await asyncio.sleep(delay)
    return result


async def test_try_gather_is_useful():
    # Not an actual test, but a demonstration that `asyncio.gather()` has
    # problems and `try_gather` is actually useful
    eternal_fut = eternal()
    eternal_task = asyncio.create_task(eternal_fut)
    falling_fut = falling()
    with pytest.raises(CustomException):
        await asyncio.gather(eternal_task, falling_fut)
    assert not eternal_task.cancelled()
    assert inspect.getcoroutinestate(eternal_fut) != inspect.CORO_CLOSED
    eternal_task.cancel()


@pytest.mark.parametrize('delay1, delay2', [(0, 0.001), (0.001, 0)])
async def test_try_gather_results(delay1, delay2):
    expected1 = object()
    expected2 = object()
    assert expected1 != expected2
    result1, result2 = await async_plus.try_gather(
        delayed(delay1, result=expected1),
        delayed(delay2, result=expected2),
    )
    assert result1 == expected1
    assert result2 == expected2


@pytest.mark.parametrize('wrapper', [lambda x: x, asyncio.create_task])
async def test_try_gather_falling(wrapper):
    eternal_fut = eternal()
    falling_fut = falling()
    with pytest.raises(CustomException):
        await async_plus.try_gather(
            wrapper(eternal_fut), wrapper(falling_fut),
        )
    assert inspect.getcoroutinestate(eternal_fut) == inspect.CORO_CLOSED


@pytest.mark.parametrize('task_name', [None, 'TASK_NAME'])
async def test_launch_watched_success(caplog, task_name):
    func_was_here = False

    async def func():
        nonlocal func_was_here
        func_was_here = True

    task = async_plus.launch_watched(func(), name=task_name)
    await asyncio.sleep(0.001)
    assert task.done()
    assert func_was_here

    if task_name is not None and hasattr(asyncio.Task, 'get_name'):
        assert task.get_name() == task_name


async def test_launch_watched_exception(caplog):
    with caplog.at_level(logging.ERROR):
        async_plus.launch_watched(falling())
        await asyncio.sleep(0.001)

    [rec] = caplog.matching(name='async_plus')
    assert rec.exc_info is not None
    assert 'FALLING_TASK' in rec.exc_text


async def test_launch_watched_custom_on_exception():
    on_exception = Mock()

    task = async_plus.launch_watched(falling(), on_exception=on_exception)
    await asyncio.sleep(0.001)

    on_exception.assert_called_once_with(task, CustomException('FALLING_TASK'))


async def test_launch_watched_bad_on_exception(caplog):

    def on_exception(task, exc):
        raise RuntimeError('Oops!')

    with caplog.at_level(logging.ERROR):
        async_plus.launch_watched(falling(), on_exception=on_exception)
        await asyncio.sleep(0.001)

    [rec] = caplog.matching(name='async_plus')
    assert rec.exc_info is not None
    assert rec.exc_info[0] is RuntimeError


async def test_empty():
    async with async_plus.task_scope():
        pass


async def test_coroutine_scope_no_wait():
    async with async_plus.task_scope() as scope:
        eternal_task = scope.launch(eternal())
        instant_task = scope.launch(instant())
        # Needed to start tasks
        await asyncio.sleep(0)

    assert eternal_task.cancelled()
    assert instant_task.done() and not instant_task.cancelled()


@pytest.mark.parametrize('return_when', [
    asyncio.FIRST_EXCEPTION,
    asyncio.FIRST_COMPLETED,
])
async def test_coroutine_scope_exception(caplog, return_when):
    async with async_plus.task_scope() as scope:
        eternal_task = scope.launch(eternal())
        falling_task = scope.launch(falling())
        with caplog.at_level(logging.ERROR):
            await scope.wait(return_when=return_when)

    [rec] = caplog.matching(name='async_plus')
    assert rec.exc_info is not None
    assert 'FALLING_TASK' in rec.exc_text

    assert eternal_task.cancelled()
    assert falling_task.done() and not falling_task.cancelled()


async def test_coroutine_scope_first_completed():
    async with async_plus.task_scope() as scope:
        eternal_task = scope.launch(eternal())
        instant_task = scope.launch(instant())
        await scope.wait(return_when=asyncio.FIRST_COMPLETED)

    assert eternal_task.cancelled()
    assert instant_task.done() and not instant_task.cancelled()


async def test_coroutine_scope_first_exception_no_exception():
    async with async_plus.task_scope() as scope:
        eternal_task = scope.launch(eternal())
        instant_task = scope.launch(instant())
        with pytest.raises(asyncio.TimeoutError):
            await scope.wait(timeout=0.001)

        # task_scope.wait() musn't cancel tasks on timeout
        await asyncio.sleep(0)
        assert not eternal_task.cancelled()

    assert eternal_task.cancelled()
    assert instant_task.done() and not instant_task.cancelled()


async def test_coroutine_scope_custom_on_exception(caplog):
    on_exception = Mock()

    async with async_plus.task_scope(on_exception=on_exception) as scope:
        task = scope.launch(falling())
        with caplog.at_level(logging.ERROR):
            await scope.wait()

    on_exception.assert_called_once_with(task, CustomException('FALLING_TASK'))


async def test_coroutine_scope_launch_custom_on_exception(caplog):
    on_exception = Mock()

    async with async_plus.task_scope() as scope:
        task = scope.launch(falling(), on_exception=on_exception)
        with caplog.at_level(logging.ERROR):
            await scope.wait()

    on_exception.assert_called_once_with(task, CustomException('FALLING_TASK'))
