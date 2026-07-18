"""Configuration loading from environment variables."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_ENV_VARS = [
    "TASKTOOL_S3_BUCKET",
    "TASKTOOL_S3_REGION",
    "TASKTOOL_COMPUTER_ID",
    "TASKTOOL_FERNET_KEY",
]


@dataclass(frozen=True)
class Config:
    """All configuration values loaded from environment variables."""

    s3_bucket: str
    s3_region: str
    computer_id: str
    fernet_key: str
    task_data_dir: Path
    keep_snapshots: int
    lock_timeout_seconds: int

    @classmethod
    def from_env(cls, require_all: bool = True) -> "Config":
        """Load config from environment variables.

        If require_all is True, exits with an error listing missing vars.
        If False, missing values default to empty strings (used by init/status).
        """
        missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]

        if require_all and missing:
            print("Error: missing required environment variables:", file=sys.stderr)
            for var in missing:
                print(f"  - {var}", file=sys.stderr)
            raise SystemExit(1)

        task_data_dir = os.environ.get("TASKTOOL_TASK_DATA_DIR", "")
        if not task_data_dir:
            task_data_dir = str(Path.home() / ".task")

        keep_snapshots = int(os.environ.get("TASKTOOL_KEEP_SNAPSHOTS", "10"))
        lock_timeout = int(os.environ.get("TASKTOOL_LOCK_TIMEOUT", "300"))

        return cls(
            s3_bucket=os.environ.get("TASKTOOL_S3_BUCKET", ""),
            s3_region=os.environ.get("TASKTOOL_S3_REGION", ""),
            computer_id=os.environ.get("TASKTOOL_COMPUTER_ID", ""),
            fernet_key=os.environ.get("TASKTOOL_FERNET_KEY", ""),
            task_data_dir=Path(task_data_dir),
            keep_snapshots=keep_snapshots,
            lock_timeout_seconds=lock_timeout,
        )

    def get_missing_vars(self) -> list[str]:
        """Return list of required env vars that are not set."""
        return [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
