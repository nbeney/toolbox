"""CLI entry point and subcommand definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .backup import backup_local_data, confirm_overwrite
from .config import Config
from .crypto import generate_fernet_key
from .merge import merge_stores
from .s3 import (
    acquire_lock,
    check_bucket_access,
    download_snapshot,
    get_lock_status,
    list_snapshots,
    prune_snapshots,
    release_lock,
    upload_snapshot,
)
from .snapshot import create_snapshot, extract_snapshot
from .state import SyncState
from .taskdata import TaskStore, compute_data_hash

app = typer.Typer(
    name="task-tool",
    help="TaskWarrior S3 backup & sync CLI with Fernet encryption.",
    no_args_is_help=True,
)


def app_entry():
    """Entry point for console script."""
    app()


@app.command()
def init():
    """Interactive first-time setup: validate env vars, generate keys, check S3."""
    typer.echo("=== task-tool init ===\n")

    config = Config.from_env(require_all=False)
    missing = config.get_missing_vars()

    if missing:
        typer.echo("Missing required environment variables:")
        for var in missing:
            typer.echo(f"  ✗ {var}")
    else:
        typer.echo("All required environment variables are set. ✓")

    typer.echo()

    # Offer to generate a Fernet key
    if typer.confirm("Generate a new Fernet key?", default=False):
        key = generate_fernet_key()
        typer.echo(f"\nGenerated Fernet key (store this securely, never commit it):")
        typer.echo(f"\n  export TASKTOOL_FERNET_KEY='{key}'\n")

    # Check state directory
    from .state import STATE_DIR

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    typer.echo(f"State directory: {STATE_DIR} ✓")

    # Check task data dir
    task_dir = config.task_data_dir
    if task_dir.exists():
        typer.echo(f"Task data directory: {task_dir} ✓")
    else:
        typer.echo(f"Task data directory: {task_dir} (does not exist yet)")

    # Check S3 access
    if config.s3_bucket and config.s3_region:
        typer.echo(f"\nChecking S3 bucket access: {config.s3_bucket} ...")
        if check_bucket_access(config):
            typer.echo("  S3 bucket accessible. ✓")
        else:
            typer.echo("  ✗ Cannot access S3 bucket. Check credentials and bucket name.")
    else:
        typer.echo("\nSkipping S3 check (bucket/region not configured).")

    typer.echo("\nSetup check complete.")


@app.command()
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without changes."),
):
    """Sync local TaskWarrior data with S3 (push and/or pull as needed)."""
    config = Config.from_env()
    state = SyncState.load()

    current_hash = compute_data_hash(config.task_data_dir)
    push_needed = current_hash != state.last_local_hash

    # Check for remote snapshots from other computers
    remote_snapshots = list_snapshots(config)
    pull_needed = False
    pull_from: dict[str, dict] = {}  # computer_id -> snapshot info

    for snap in remote_snapshots:
        cid = snap["computer_id"]
        if cid == config.computer_id:
            continue
        last_pulled = state.last_pulled_snapshots.get(cid)
        if last_pulled != snap["key"]:
            pull_needed = True
            if cid not in pull_from:
                pull_from[cid] = snap

    if not push_needed and not pull_needed:
        typer.echo("Nothing to do — local and remote are in sync.")
        return

    if dry_run:
        if push_needed:
            typer.echo("[dry-run] Would push local changes to S3.")
        if pull_needed:
            for cid, snap in pull_from.items():
                typer.echo(f"[dry-run] Would pull snapshot from '{cid}': {snap['key']}")
        return

    # Acquire lock
    acquire_lock(config)
    try:
        pulled_snapshots: dict[str, str] = {}

        # Pull first (so we merge before pushing)
        if pull_needed:
            for cid, snap in pull_from.items():
                typer.echo(f"Pulling snapshot from '{cid}': {snap['key']}")
                encrypted = download_snapshot(config, snap["key"])
                files = extract_snapshot(encrypted, config.fernet_key)

                remote_store = TaskStore.from_files(
                    files.get("pending.data", ""),
                    files.get("completed.data", ""),
                )
                local_store = TaskStore.from_data_dir(config.task_data_dir)

                result = merge_stores(
                    local_store, remote_store, state.last_synced_tasks
                )

                typer.echo(
                    f"  Merged: {result.tasks_added} added, "
                    f"{result.tasks_updated} updated, "
                    f"{result.conflicts_resolved} conflicts resolved, "
                    f"{result.conflicts_skipped} conflicts skipped."
                )

                backup_local_data(config.task_data_dir)
                result.merged_store.write_to_dir(config.task_data_dir)
                pulled_snapshots[cid] = snap["key"]

            # Recompute hash after merge
            current_hash = compute_data_hash(config.task_data_dir)
            push_needed = True  # Always push after a merge

        # Push
        if push_needed:
            typer.echo("Pushing local data to S3...")
            encrypted = create_snapshot(config.task_data_dir, config.fernet_key)
            key = upload_snapshot(config, encrypted)
            typer.echo(f"  Uploaded: {key}")

            deleted = prune_snapshots(config)
            if deleted:
                typer.echo(f"  Pruned {len(deleted)} old snapshot(s).")

        # Update state
        local_store = TaskStore.from_data_dir(config.task_data_dir)
        synced_tasks = _store_to_state_dict(local_store)
        state.update_after_sync(current_hash, pulled_snapshots, synced_tasks)

        typer.echo("Sync complete. ✓")

    finally:
        release_lock(config)


@app.command()
def push(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without changes."),
):
    """Force push local data to S3 regardless of sync state."""
    config = Config.from_env()

    if dry_run:
        typer.echo("[dry-run] Would push local data to S3.")
        return

    acquire_lock(config)
    try:
        typer.echo("Pushing local data to S3...")
        encrypted = create_snapshot(config.task_data_dir, config.fernet_key)
        key = upload_snapshot(config, encrypted)
        typer.echo(f"  Uploaded: {key}")

        deleted = prune_snapshots(config)
        if deleted:
            typer.echo(f"  Pruned {len(deleted)} old snapshot(s).")

        # Update state
        state = SyncState.load()
        local_store = TaskStore.from_data_dir(config.task_data_dir)
        current_hash = compute_data_hash(config.task_data_dir)
        state.update_after_push(current_hash, _store_to_state_dict(local_store))

        typer.echo("Push complete. ✓")
    finally:
        release_lock(config)


@app.command()
def pull(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without changes."),
):
    """Force pull latest remote snapshot and merge into local data."""
    config = Config.from_env()

    remote_snapshots = list_snapshots(config)
    pull_from: dict[str, dict] = {}

    for snap in remote_snapshots:
        cid = snap["computer_id"]
        if cid == config.computer_id:
            continue
        if cid not in pull_from:
            pull_from[cid] = snap

    if not pull_from:
        typer.echo("No remote snapshots from other computers found.")
        return

    if dry_run:
        for cid, snap in pull_from.items():
            typer.echo(f"[dry-run] Would pull snapshot from '{cid}': {snap['key']}")
        return

    acquire_lock(config)
    try:
        state = SyncState.load()

        for cid, snap in pull_from.items():
            typer.echo(f"Pulling snapshot from '{cid}': {snap['key']}")
            encrypted = download_snapshot(config, snap["key"])
            files = extract_snapshot(encrypted, config.fernet_key)

            remote_store = TaskStore.from_files(
                files.get("pending.data", ""),
                files.get("completed.data", ""),
            )
            local_store = TaskStore.from_data_dir(config.task_data_dir)

            result = merge_stores(local_store, remote_store, state.last_synced_tasks)

            typer.echo(
                f"  Merged: {result.tasks_added} added, "
                f"{result.tasks_updated} updated, "
                f"{result.conflicts_resolved} conflicts resolved, "
                f"{result.conflicts_skipped} conflicts skipped."
            )

            backup_local_data(config.task_data_dir)
            result.merged_store.write_to_dir(config.task_data_dir)

            # Update state
            local_store = TaskStore.from_data_dir(config.task_data_dir)
            synced_tasks = _store_to_state_dict(local_store)
            state.update_after_pull(cid, snap["key"], synced_tasks)

        typer.echo("Pull complete. ✓")
    finally:
        release_lock(config)


@app.command()
def status():
    """Show sync status: local changes, remote snapshots, lock state."""
    config = Config.from_env(require_all=False)

    missing = config.get_missing_vars()
    if missing:
        typer.echo("Warning: some env vars are missing — limited functionality.")
        for var in missing:
            typer.echo(f"  ✗ {var}")
        typer.echo()

    # Local change detection
    state = SyncState.load()
    if config.task_data_dir.exists():
        current_hash = compute_data_hash(config.task_data_dir)
        if state.last_local_hash:
            changed = current_hash != state.last_local_hash
            typer.echo(f"Local changes since last sync: {'yes' if changed else 'no'}")
        else:
            typer.echo("Local changes since last sync: unknown (no previous sync)")
    else:
        typer.echo(f"Task data dir does not exist: {config.task_data_dir}")

    # Remote snapshots
    if config.s3_bucket and config.s3_region:
        typer.echo("\nRemote snapshots:")
        try:
            snapshots = list_snapshots(config)
            if not snapshots:
                typer.echo("  (none)")
            else:
                # Group by computer
                by_computer: dict[str, list] = {}
                for snap in snapshots:
                    by_computer.setdefault(snap["computer_id"], []).append(snap)
                for cid, snaps in sorted(by_computer.items()):
                    marker = " (this computer)" if cid == config.computer_id else ""
                    typer.echo(f"  {cid}{marker}: {len(snaps)} snapshot(s)")
                    latest = snaps[0]
                    typer.echo(f"    latest: {latest['key']}")
                    last_pulled = state.last_pulled_snapshots.get(cid)
                    if cid != config.computer_id:
                        if last_pulled == latest["key"]:
                            typer.echo("    status: up to date")
                        else:
                            typer.echo("    status: pull available")
        except Exception as e:
            typer.echo(f"  Error listing snapshots: {e}")

        # Lock status
        typer.echo("\nLock status:")
        try:
            lock = get_lock_status(config)
            if lock:
                typer.echo(f"  Held by: {lock.get('computer_id', 'unknown')}")
                typer.echo(f"  Acquired at: {lock.get('acquired_at', 'unknown')}")
            else:
                typer.echo("  No lock held. ✓")
        except Exception as e:
            typer.echo(f"  Error checking lock: {e}")
    else:
        typer.echo("\nS3 not configured — cannot check remote status.")


@app.command()
def restore(
    snapshot: str = typer.Argument(
        help="Snapshot key or index (from list-backups) to restore."
    ),
):
    """Restore local data from a specific S3 snapshot."""
    config = Config.from_env()

    # If snapshot looks like an integer, treat it as an index
    snapshots = list_snapshots(config)
    key: str

    if snapshot.isdigit():
        idx = int(snapshot)
        if idx < 0 or idx >= len(snapshots):
            typer.echo(f"Error: index {idx} out of range (0-{len(snapshots)-1}).")
            raise SystemExit(1)
        key = snapshots[idx]["key"]
    else:
        key = snapshot

    typer.echo(f"Restoring from snapshot: {key}")

    if not confirm_overwrite(config.task_data_dir):
        typer.echo("Aborted.")
        return

    # Ensure data dir exists (support restore to fresh machine)
    config.task_data_dir.mkdir(parents=True, exist_ok=True)

    # Backup existing data if present
    if (config.task_data_dir / "pending.data").exists():
        backup_local_data(config.task_data_dir)
        typer.echo("  Local backup created (.bak files).")

    encrypted = download_snapshot(config, key)
    files = extract_snapshot(encrypted, config.fernet_key)

    (config.task_data_dir / "pending.data").write_text(
        files.get("pending.data", ""), encoding="utf-8"
    )
    (config.task_data_dir / "completed.data").write_text(
        files.get("completed.data", ""), encoding="utf-8"
    )

    # Update state
    state = SyncState.load()
    local_store = TaskStore.from_data_dir(config.task_data_dir)
    current_hash = compute_data_hash(config.task_data_dir)
    state.update_after_push(current_hash, _store_to_state_dict(local_store))

    typer.echo("Restore complete. ✓")


@app.command("list-backups")
def list_backups(
    computer: Optional[str] = typer.Option(
        None, "--computer", "-c", help="Filter by computer ID."
    ),
):
    """List available snapshots in S3."""
    config = Config.from_env()

    snapshots = list_snapshots(config, computer_id=computer)

    if not snapshots:
        typer.echo("No snapshots found.")
        return

    typer.echo(f"{'Idx':<4} {'Timestamp':<22} {'Computer':<15} {'Size':>10}")
    typer.echo("-" * 55)

    for i, snap in enumerate(snapshots):
        size_kb = snap["size"] / 1024
        typer.echo(
            f"{i:<4} {snap['timestamp']:<22} {snap['computer_id']:<15} "
            f"{size_kb:>8.1f} KB"
        )


def _store_to_state_dict(store: TaskStore) -> dict[str, dict]:
    """Convert a TaskStore to a dict suitable for state persistence."""
    result = {}
    for uuid, task in store.tasks.items():
        data = dict(task.data)
        data["_source_file"] = task.source_file
        result[uuid] = data
    return result
