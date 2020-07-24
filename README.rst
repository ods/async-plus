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


Change log
----------

See `CHANGELOG <https://github.com/ods/async-plus/blob/master/CHANGELOG.rst>`_.
