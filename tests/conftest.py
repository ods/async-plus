import asyncio
import functools

import pytest
from _pytest.logging import LogCaptureFixture


def pytest_collection_modifyitems(items):
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker('asyncio')


class AdvancedLogCaptureFixture(LogCaptureFixture):

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

    @functools.wraps(matching)
    def pop_matching(self, *args, **kwargs):
        result = self.matching(*args, **kwargs)

        if result:
            all_records = list(self.handler.records) # copy
            self.clear()
            # Re-emit not matching
            for record in all_records:
                if not any(record is match for match in result):
                    self.handler.emit(record)

        return result


@pytest.fixture
def caplog(request):
    result = AdvancedLogCaptureFixture(request.node)
    yield result
    result._finalize()
