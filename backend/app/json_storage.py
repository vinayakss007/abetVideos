"""Thread-safe JSON file storage with file locking."""

import fcntl
import json
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def locked_read(path: Path) -> dict[str, Any] | list[Any]:
    """Read a JSON file with a shared (read) lock."""
    if not path.exists():
        return {} if path.suffix == ".json" else []
    try:
        with open(path) as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            data = json.load(f)
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read %s: %s", path, e)
        return {} if path.suffix == ".json" else []


def locked_write(path: Path, data: Any) -> None:
    """Write a JSON file with an exclusive (write) lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(data, f, indent=2)
            f.flush()
        shutil.move(str(tmp), str(path))
    except OSError as e:
        logger.warning("Failed to write %s: %s", path, e)
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
