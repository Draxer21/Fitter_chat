import pytest


@pytest.fixture(autouse=True)
def _set_secret_key(monkeypatch):
    """Ensure SECRET_KEY is always defined for every test that creates the app."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-not-for-production")
