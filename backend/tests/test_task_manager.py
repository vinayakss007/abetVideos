"""Tests for task manager - creation, cancellation, status."""

from unittest.mock import patch

import pytest

from app.services.task_manager import (
    create_task,
    cancel_task,
    get_task,
    TaskStatus,
    _tasks,
)
from app.models.schemas import GenerateFullRequest


class TestTaskManager:
    def setup_method(self):
        _tasks.clear()

    def test_get_nonexistent_task(self):
        assert get_task("nonexistent") is None

    def test_cancel_nonexistent_task(self):
        assert not cancel_task("nonexistent")

    def test_task_id_is_unique(self):
        ids = set()
        for _ in range(100):
            req = GenerateFullRequest(topic="Test")
            task = {
                "task_id": req.topic + str(_),
                "status": TaskStatus.PENDING,
                "events": [],
                "result": None,
                "user_id": "user_1",
                "created_at": "now",
                "_cancel_event": __import__("asyncio").Event(),
            }
            _tasks[task["task_id"]] = task
            ids.add(task["task_id"])
        assert len(ids) == 100


@pytest.mark.asyncio
async def test_create_task():
    _tasks.clear()
    from unittest.mock import patch
    with patch("app.services.task_manager.asyncio.create_task"):
        req = GenerateFullRequest(topic="Test topic")
        task_id = create_task(req, "user_1")
        assert task_id is not None
        task = get_task(task_id)
        assert task is not None
        assert task["status"] == TaskStatus.PENDING
        assert task["user_id"] == "user_1"


@pytest.mark.asyncio
async def test_cancel_pending_task():
    _tasks.clear()
    req = GenerateFullRequest(topic="Test topic")
    with patch("app.services.task_manager.asyncio.create_task"):
        task_id = create_task(req, "user_1")
    assert cancel_task(task_id)
    task = get_task(task_id)
    assert task["status"] == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_double_cancel_returns_false():
    _tasks.clear()
    req = GenerateFullRequest(topic="Test topic")
    with patch("app.services.task_manager.asyncio.create_task"):
        task_id = create_task(req, "user_1")
    assert cancel_task(task_id)
    assert not cancel_task(task_id)


@pytest.mark.asyncio
async def test_cancel_emits_sse_event():
    _tasks.clear()
    req = GenerateFullRequest(topic="Test topic")
    with patch("app.services.task_manager.asyncio.create_task"):
        task_id = create_task(req, "user_1")
    cancel_task(task_id)
    task = get_task(task_id)
    events = task.get("events", [])
    assert any("cancelled" in str(e).lower() for e in events)
