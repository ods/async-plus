async_plus
==========

Async-related stuff you miss in standard library


Fire-and-forget task
--------------------

With ``create_task()`` it's your responsibility to retrieve exception.
Usually this causes that exception is not seen until process finishes or
even is not seen at all if process is killed.  With ``launch_watched()``
excpetion is logged immediately when it's raised.

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


Increase delay between attempts in superviser
---------------------------------------------

.. code-block:: python

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


Change log
----------

..  Absolute link is needed for correct description on PyPI.
    See https://github.com/pypa/readme_renderer/issues/163

See `CHANGELOG <https://github.com/ods/async-plus/blob/master/CHANGELOG.rst>`_.
