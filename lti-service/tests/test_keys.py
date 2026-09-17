import pytest

from app import keys
from app.config import settings


def test_tool_jwks_raises_clear_error_when_public_key_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "tool_public_key_pem", "")

    with pytest.raises(RuntimeError, match="not configured"):
        keys.tool_jwks()
