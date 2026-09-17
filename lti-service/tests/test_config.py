import json

import pytest

from app.config import _load_platforms


def test_malformed_platform_entry_raises_clear_error(monkeypatch):
    monkeypatch.setenv(
        "LTI_PLATFORMS_JSON",
        json.dumps([{"issuer": "https://canvas.test.instructure.com", "client_id": "abc"}]),
    )

    with pytest.raises(RuntimeError, match="missing required field"):
        _load_platforms()
