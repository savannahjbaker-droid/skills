import pytest

from app import store


@pytest.fixture(autouse=True)
def clean_store():
    """Reset in-memory repositories between tests."""
    store.reset()
    yield
    store.reset()
