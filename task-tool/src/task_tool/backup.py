"""Local backup utilities for safety before overwrites."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer


def backup_local_data(data_dir: Path) -> list[Path]:
    """Create .bak copies of pending.data and completed.data.

    Returns list of backup file paths created.
    """
    backups = []
    for filename in ("pending.data", "completed.data"):
        src = data_dir / filename
        if src.exists():
            dst = data_dir / f"{filename}.bak"
            shutil.copy2(str(src), str(dst))
            backups.append(dst)
    return backups


def confirm_overwrite(data_dir: Path) -> bool:
    """Ask user to confirm before overwriting local data."""
    typer.echo(f"This will overwrite data in: {data_dir}")
    return typer.confirm("Proceed?", default=False)
