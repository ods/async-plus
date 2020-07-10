import asyncio


def pytest_collection_modifyitems(items):
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker('asyncio')
