"""Structured uuid-keyed, field-level merge logic."""

from __future__ import annotations

from dataclasses import dataclass

import typer

from .taskdata import Task, TaskStore


@dataclass
class MergeResult:
    """Result of merging remote tasks into local tasks."""

    merged_store: TaskStore
    conflicts_resolved: int
    conflicts_skipped: int
    tasks_added: int
    tasks_updated: int


def merge_stores(
    local: TaskStore,
    remote: TaskStore,
    base: dict[str, dict],
    interactive: bool = True,
) -> MergeResult:
    """Merge remote TaskStore into local TaskStore using three-way merge.

    Args:
        local: Current local task store.
        remote: Remote task store from pulled snapshot.
        base: Last-synced task data (uuid -> full task dict) for conflict detection.
        interactive: If True, prompt user on true conflicts. If False, keep local.

    Returns:
        MergeResult with the merged store and statistics.
    """
    merged = TaskStore()
    conflicts_resolved = 0
    conflicts_skipped = 0
    tasks_added = 0
    tasks_updated = 0

    all_uuids = set(local.tasks.keys()) | set(remote.tasks.keys())

    for uuid in sorted(all_uuids):
        local_task = local.tasks.get(uuid)
        remote_task = remote.tasks.get(uuid)
        base_data = base.get(uuid)

        if local_task and not remote_task:
            # Only exists locally — keep it
            merged.tasks[uuid] = local_task
            continue

        if remote_task and not local_task:
            # Only exists remotely — add it
            merged.tasks[uuid] = remote_task
            tasks_added += 1
            continue

        # Both exist — merge field by field
        assert local_task is not None and remote_task is not None

        merged_data, merged_source, result = _merge_task(
            local_task, remote_task, base_data, interactive
        )

        if result == "conflict_resolved":
            conflicts_resolved += 1
        elif result == "conflict_skipped":
            conflicts_skipped += 1
        elif result == "updated":
            tasks_updated += 1

        merged.tasks[uuid] = Task(
            uuid=uuid, source_file=merged_source, data=merged_data
        )

    return MergeResult(
        merged_store=merged,
        conflicts_resolved=conflicts_resolved,
        conflicts_skipped=conflicts_skipped,
        tasks_added=tasks_added,
        tasks_updated=tasks_updated,
    )


def _merge_task(
    local_task: Task,
    remote_task: Task,
    base_data: dict | None,
    interactive: bool,
) -> tuple[dict, str, str]:
    """Merge a single task. Returns (merged_data, source_file, result_type).

    result_type is one of: "unchanged", "updated", "conflict_resolved", "conflict_skipped"
    """
    local_data = local_task.data
    remote_data = remote_task.data

    # If no base, treat remote as authoritative for new fields only
    if base_data is None:
        base_data = {}

    # Merge source_file (pending vs completed) as a virtual field
    merged_source = _merge_source_file(
        local_task.source_file,
        remote_task.source_file,
        base_data.get("_source_file", local_task.source_file),
    )

    all_fields = set(local_data.keys()) | set(remote_data.keys()) | set(
        base_data.keys()
    )
    all_fields.discard("_source_file")

    merged_data = {}
    had_conflict = False
    conflict_skipped = False

    for field_name in sorted(all_fields):
        local_val = local_data.get(field_name)
        remote_val = remote_data.get(field_name)
        base_val = base_data.get(field_name)

        if local_val == remote_val:
            # No divergence
            if local_val is not None:
                merged_data[field_name] = local_val
            continue

        # Check which side changed from base
        local_changed = local_val != base_val
        remote_changed = remote_val != base_val

        if remote_changed and not local_changed:
            # Only remote changed — apply remote
            if remote_val is not None:
                merged_data[field_name] = remote_val
        elif local_changed and not remote_changed:
            # Only local changed — keep local
            if local_val is not None:
                merged_data[field_name] = local_val
        else:
            # Both changed to different values — true conflict
            if interactive:
                resolution = _prompt_conflict(
                    local_task, field_name, local_val, remote_val
                )
                if resolution == "local":
                    if local_val is not None:
                        merged_data[field_name] = local_val
                    had_conflict = True
                elif resolution == "remote":
                    if remote_val is not None:
                        merged_data[field_name] = remote_val
                    had_conflict = True
                else:  # skip
                    # Keep local value, mark as skipped
                    if local_val is not None:
                        merged_data[field_name] = local_val
                    conflict_skipped = True
            else:
                # Non-interactive: keep local
                if local_val is not None:
                    merged_data[field_name] = local_val

    if conflict_skipped:
        result = "conflict_skipped"
    elif had_conflict:
        result = "conflict_resolved"
    elif merged_data != local_data or merged_source != local_task.source_file:
        result = "updated"
    else:
        result = "unchanged"

    return merged_data, merged_source, result


def _merge_source_file(local_source: str, remote_source: str, base_source: str) -> str:
    """Merge the file membership (pending/completed) like any other field."""
    if local_source == remote_source:
        return local_source

    local_changed = local_source != base_source
    remote_changed = remote_source != base_source

    if remote_changed and not local_changed:
        return remote_source
    # In all other cases (local changed, or both changed), prefer local
    return local_source


def _prompt_conflict(
    task: Task, field_name: str, local_val, remote_val
) -> str:
    """Prompt user to resolve a conflict. Returns 'local', 'remote', or 'skip'."""
    desc = task.description()
    typer.echo(f"\n{'='*60}")
    typer.echo(f"CONFLICT in task: {desc}")
    typer.echo(f"  UUID: {task.uuid}")
    typer.echo(f"  Field: {field_name}")
    typer.echo(f"  Local value:  {local_val}")
    typer.echo(f"  Remote value: {remote_val}")
    typer.echo(f"{'='*60}")

    while True:
        choice = typer.prompt(
            "Keep [l]ocal / [r]emote / [s]kip?",
            default="s",
        ).lower()
        if choice in ("l", "local"):
            return "local"
        elif choice in ("r", "remote"):
            return "remote"
        elif choice in ("s", "skip"):
            return "skip"
        typer.echo("Please enter 'l', 'r', or 's'.")
