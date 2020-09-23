async_plus
==========

Async-related stuff you miss in standard library

..  Original (unscaled) picture:
    https://upload.wikimedia.org/wikipedia/commons/f/fe/The_Hanging_by_Jacques_Callot.jpg
    :align:, :figwidth: directives appear not working for figure, so just scale
    it with Wikimedia capabilities and put under description.

.. figure:: https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/The_Hanging_by_Jacques_Callot.jpg/500px-The_Hanging_by_Jacques_Callot.jpg

    *“The horrors of hanging tasks when using asyncio” by Jacques Callot*


Safely run coroutines concurrently
----------------------------------

The ``asyncio.gather()`` function has an
`issue <https://bugs.python.org/issue31452>`_: in case of error in one of
coroutines the rest coroutines are left running detached.  This might cause
hard to detect problems.  On the contrary, the ``async_plus.try_gather()``
insures all tasks are cancelled on error:

.. code-block:: python

    result1, result2 = await async_plus.try_gather(
        coroutine_func1(...),
        coroutine_func2(...),
    )


Fire-and-forget task
--------------------

With ``create_task()`` it's your responsibility to retrieve exception.
Usually this causes that exception is not seen until process finishes or
even is not seen at all if process is killed.  With ``launch_watched()``
exception is logged immediately when it's raised.

.. code-block:: python

    async_plus.launch_watched(your_coroutine_func(...))


Structuring groups of tasks
---------------------------

.. code-block:: python

    async with async_plus.task_scope() as scope:
        scope.launch(coroutine_func1(...))
        scope.launch(coroutine_func2(...))
        await scope.wait()

By default, ``wait()`` call returns when all tasks finish or first exception
occurs.  In all cases all unfinished tasks are cancelled at the end of
``async with`` block.


Increase delay between attempts in supervisor
---------------------------------------------

.. code-block:: python

    retry_delayer = async_plus.RetryDelayer([0, 10, 60], random_shift=1)
    while True:
        try:
            await run_service_x()
        # In Python <3.8 it inherits from Exception
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('Error in service X:')
            await retry_delayer.sleep()


Log long waits
--------------

Does your program hang and you don't know what it's waiting for?  Wrap
suspicious coroutines with ``impatient()`` to see bottlenecks:

.. code-block:: python

    await async_plus.impatient(asyncio.sleep(10), log_after=5)

Or just log the time it took:

.. code-block:: python

    await async_plus.impatient(asyncio.sleep(10), log_completion='always')


Change log
----------

..  Absolute link is needed for correct description on PyPI.
    See https://github.com/pypa/readme_renderer/issues/163

See `CHANGELOG <https://github.com/ods/async-plus/blob/master/CHANGELOG.rst>`_.
