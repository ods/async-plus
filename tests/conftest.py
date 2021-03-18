import asyncio
import re

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker('asyncio')


class LogCaptureFixtureWrapper:

    def __init__(self, orig):
        self._orig = orig

    def __getattr__(self, name):
        return getattr(self._orig, name)

    def matching(self, _func=None, *, name=None, message=None):
        filters = []
        if _func is not None:
            filters.append(_func)
        if name is not None:
            def _filter(record):
                if callable(name):
                    return name(record.name)
                else:
                    # The same behavior as for `logging.Filter(name=...)`
                    return (
                        record.name == name or
                        record.name.startswith(name + '.')
                    )
            filters.append(_filter)
        if message is not None:
            def _filter(record):
                if callable(message):
                    return message(record.getMessage())
                else:
                    return re.search(message, record.getMessage())
            filters.append(_filter)

        result = []
        for record in self.handler.records:
            if all(matches(record) for matches in filters):
                result.append(record)
        return result


@pytest.fixture
def caplog(caplog):
    return LogCaptureFixtureWrapper(caplog)
