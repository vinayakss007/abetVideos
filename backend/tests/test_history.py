"""Tests for history service - CRUD, file cleanup."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.history_service import (
    get_history,
    add_to_history,
    delete_from_history,
    clear_history,
    HISTORY_DIR,
    MAX_HISTORY,
)


@pytest.fixture(autouse=True)
def temp_history_dir(tmp_path):
    """Redirect HISTORY_DIR to a temp directory for test isolation."""
    with patch("app.services.history_service.HISTORY_DIR", tmp_path):
        with patch("app.services.history_service._history_path",
                   lambda uid: tmp_path / f"{uid}_history.json"):
            yield tmp_path


class TestHistoryReadWrite:
    def test_empty_history(self):
        assert get_history("user_1") == []

    def test_add_entry(self):
        add_to_history("user_1", "vid_1", "Test Video", "topic", 60.0, 5, "landscape")
        history = get_history("user_1")
        assert len(history) == 1
        assert history[0]["title"] == "Test Video"
        assert history[0]["video_id"] == "vid_1"
        assert history[0]["scenes_count"] == 5

    def test_max_history_limit(self):
        for i in range(MAX_HISTORY + 5):
            add_to_history("user_2", f"vid_{i}", f"Video {i}", "topic", 30.0, 3, "landscape")
        history = get_history("user_2")
        assert len(history) == MAX_HISTORY

    def test_add_multiple_entries(self):
        add_to_history("user_3", "vid_a", "First", "topic", 10.0, 1, "landscape")
        add_to_history("user_3", "vid_b", "Second", "topic", 20.0, 2, "shorts")
        history = get_history("user_3")
        assert len(history) == 2
        assert history[0]["title"] == "Second"
        assert history[1]["title"] == "First"

    def test_users_isolated(self):
        add_to_history("user_a", "vid_a", "A", "topic", 10.0, 1, "landscape")
        add_to_history("user_b", "vid_b", "B", "topic", 20.0, 2, "shorts")
        assert len(get_history("user_a")) == 1
        assert len(get_history("user_b")) == 1


class TestHistoryDelete:
    def test_delete_existing_entry(self):
        add_to_history("user_1", "vid_1", "Test", "topic", 60.0, 5, "landscape")
        add_to_history("user_1", "vid_2", "Test 2", "topic", 30.0, 3, "shorts")
        history = get_history("user_1")
        entry_id = history[0]["id"]
        assert delete_from_history("user_1", entry_id)
        remaining = get_history("user_1")
        assert len(remaining) == 1
        assert remaining[0]["video_id"] == "vid_1"

    def test_delete_nonexistent_entry(self):
        add_to_history("user_1", "vid_1", "Test", "topic", 60.0, 5, "landscape")
        assert not delete_from_history("user_1", "nonexistent_id")

    def test_clear_all_history(self):
        add_to_history("user_1", "vid_1", "Test", "topic", 30.0, 3, "landscape")
        add_to_history("user_1", "vid_2", "Test 2", "topic", 30.0, 3, "shorts")
        clear_history("user_1")
        assert get_history("user_1") == []
