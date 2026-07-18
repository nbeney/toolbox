"""Local state tracking for sync detection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

STATE_DIR = Path.home() / ".local" / "state" / "task-tool"
STATE_FILE = STATE_DIR / "state.json"


@dataclass
class SyncState:
    """Tracks last-synced state for change detection."""

    last_local_hash: str = ""
    last_pulled_snapshots: dict[str, str] = field(default_factory=dict)
    # Maps computer_id -> snapshot key of the last pulled snapshot
    last_synced_tasks: dict[str, dict] = field(default_factory=dict)
    # Maps uuid -> task data at last sync point (for conflict detection)

    @classmethod
    def load(cls) -> "SyncState":
        """Load state from disk, or return default if not found."""
        if not STATE_FILE.exists():
            return cls()
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return cls(
                last_local_hash=data.get("last_local_hash", ""),
                last_pulled_snapshots=data.get("last_pulled_snapshots", {}),
                last_synced_tasks=data.get("last_synced_tasks", {}),
            )
        except (json.JSONDecodeError, KeyError):
            return cls()

    def save(self) -> None:
        """Persist state to disk."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "last_local_hash": self.last_local_hash,
            "last_pulled_snapshots": self.last_pulled_snapshots,
            "last_synced_tasks": self.last_synced_tasks,
        }
        STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def update_after_push(self, local_hash: str, tasks: dict[str, dict]) -> None:
        """Update state after a successful push."""
        self.last_local_hash = local_hash
        self.last_synced_tasks = tasks
        self.save()

    def update_after_pull(
        self, computer_id: str, snapshot_key: str, tasks: dict[str, dict]
    ) -> None:
        """Update state after a successful pull."""
        self.last_pulled_snapshots[computer_id] = snapshot_key
        self.last_synced_tasks = tasks
        self.save()

    def update_after_sync(
        self, local_hash: str, pulled: dict[str, str], tasks: dict[str, dict]
    ) -> None:
        """Update state after a full sync (push + pull)."""
        self.last_local_hash = local_hash
        self.last_pulled_snapshots.update(pulled)
        self.last_synced_tasks = tasks
        self.save()
