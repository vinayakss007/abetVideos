"""Tests for settings manager - file locking, key masking, update validation."""

import json
import tempfile
from pathlib import Path

import pytest

from app.settings_manager import (
    _is_masked,
    get_settings,
    SENSITIVE_KEYS,
    ALL_SETTING_KEYS,
)
from app.json_storage import locked_read, locked_write


class TestKeyMasking:
    def test_is_masked_detects_masked_value(self):
        assert _is_masked("sk-****abcd")

    def test_is_masked_detects_prefix_masked(self):
        assert _is_masked("****abcd")

    def test_is_masked_returns_false_for_clean(self):
        assert not _is_masked("sk-real-key-12345")

    def test_is_masked_empty_string(self):
        assert not _is_masked("")

class TestSensitiveKeys:
    def test_all_sensitive_keys_in_all_keys(self):
        assert SENSITIVE_KEYS.issubset(ALL_SETTING_KEYS)

    def test_get_settings_does_not_expose_values(self):
        from app.settings_manager import get_settings
        result = get_settings()
        for key in SENSITIVE_KEYS:
            assert result.get(key) == "", f"{key} should be empty"
            assert f"{key}_configured" in result


class TestJsonStorage:
    def test_locked_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            data = {"key": "value", "num": 42}
            locked_write(path, data)
            assert path.exists()
            result = locked_read(path)
            assert result == data

    def test_locked_read_nonexistent(self):
        result = locked_read(Path("/nonexistent/path.json"))
        assert result == {}

    def test_locked_write_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            locked_write(path, {"first": "data"})
            locked_write(path, {"second": "data"})
            result = locked_read(path)
            assert result == {"second": "data"}


class TestAppSettings:
    def test_sensitive_keys_have_configured_flag(self):
        from app.settings_manager import get_settings
        result = get_settings()
        for key in SENSITIVE_KEYS:
            configured_key = f"{key}_configured"
            assert configured_key in result
            assert isinstance(result[configured_key], bool)
