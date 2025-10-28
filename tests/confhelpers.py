"""Helper utilities for testing."""

import asyncio
import pytest


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def await_sync(coroutine):
    """Run async function synchronously."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)


# Register helper with pytest
pytest.helpers = type("Helpers", (), {
    "await_sync": await_sync
})