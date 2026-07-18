"""TaskWarrior data file parsing and writing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Task:
    """A single TaskWarrior task."""

    uuid: str
    source_file: str  # "pending" or "completed"
    data: dict  # full JSON object

    def description(self) -> str:
        return self.data.get("description", "(no description)")


@dataclass
class TaskStore:
    """Collection of tasks indexed by uuid."""

    tasks: dict[str, Task] = field(default_factory=dict)

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> "TaskStore":
        """Load tasks from pending.data and completed.data."""
        store = cls()
        store._load_file(data_dir / "pending.data", "pending")
        store._load_file(data_dir / "completed.data", "completed")
        return store

    @classmethod
    def from_files(cls, pending_content: str, completed_content: str) -> "TaskStore":
        """Load tasks from file content strings."""
        store = cls()
        store._parse_content(pending_content, "pending")
        store._parse_content(completed_content, "completed")
        return store

    def _load_file(self, path: Path, source: str) -> None:
        if not path.exists():
            return
        content = path.read_text(encoding="utf-8")
        self._parse_content(content, source)

    def _parse_content(self, content: str, source: str) -> None:
        for line in content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            uuid = obj.get("uuid")
            if uuid:
                self.tasks[uuid] = Task(uuid=uuid, source_file=source, data=obj)

    def get_pending_tasks(self) -> list[Task]:
        return [t for t in self.tasks.values() if t.source_file == "pending"]

    def get_completed_tasks(self) -> list[Task]:
        return [t for t in self.tasks.values() if t.source_file == "completed"]

    def write_to_dir(self, data_dir: Path) -> None:
        """Write tasks back to pending.data and completed.data."""
        pending_lines = []
        completed_lines = []

        for task in self.tasks.values():
            line = json.dumps(task.data, separators=(",", ":"))
            if task.source_file == "pending":
                pending_lines.append(line)
            else:
                completed_lines.append(line)

        (data_dir / "pending.data").write_text(
            "\n".join(pending_lines) + "\n" if pending_lines else "",
            encoding="utf-8",
        )
        (data_dir / "completed.data").write_text(
            "\n".join(completed_lines) + "\n" if completed_lines else "",
            encoding="utf-8",
        )


def compute_data_hash(data_dir: Path) -> str:
    """Compute a stable hash of pending.data + completed.data content."""
    h = hashlib.sha256()
    for filename in ("pending.data", "completed.data"):
        path = data_dir / filename
        if path.exists():
            h.update(path.read_bytes())
        else:
            h.update(b"")
    return h.hexdigest()
