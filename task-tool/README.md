# task-tool

A CLI tool for backing up and syncing TaskWarrior 2.x data across multiple machines via
an S3 bucket, with Fernet encryption applied before anything leaves the machine.

Designed for use on Linux and ChromeOS/Crostini without requiring a Taskserver (taskd).

## Installation

### Global install (run from anywhere)

```bash
uv tool install /path/to/toolbox/task-tool
```

This puts `task-tool` on your PATH. After code changes, reinstall with:

```bash
uv tool install /path/to/toolbox/task-tool --reinstall
```

### Local development (run from project directory)

```bash
cd task-tool
uv sync
uv run task-tool init
```

## First-time setup

```bash
task-tool init
```

## Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TASKTOOL_S3_BUCKET` | Target S3 bucket name | (required) |
| `TASKTOOL_S3_REGION` | AWS region for the bucket | (required) |
| `TASKTOOL_COMPUTER_ID` | Stable ID for this machine (e.g. `laptop`, `chromebook`) | (required) |
| `TASKTOOL_FERNET_KEY` | Base64 Fernet key for encryption | (required) |
| `TASKTOOL_TASK_DATA_DIR` | Path to TaskWarrior data directory | `~/.task` |
| `TASKTOOL_KEEP_SNAPSHOTS` | Snapshots to retain per computer during pruning | `10` |
| `TASKTOOL_LOCK_TIMEOUT` | Lock timeout in seconds | `300` |

AWS credentials are handled via the standard AWS credential chain (`~/.aws/credentials`,
env vars, or SSO profile). The tool itself does not manage AWS auth.

## Generating a Fernet Key

```bash
uv run task-tool init
# Follow the prompt to generate a key, then export it:
export TASKTOOL_FERNET_KEY='your-generated-key-here'
```

Or generate one manually:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Store this key securely (e.g. in a password manager or a shell profile not committed to
version control). Use the **same key** on all machines.

## Commands

### `task-tool init`

Interactive first-time setup. Checks environment variables, offers to generate a Fernet
key, validates S3 bucket access, and creates the local state directory.

### `task-tool sync`

The main command. Detects whether a push and/or pull is needed:
- If local data changed since last sync → pushes.
- If a remote computer has newer snapshots → pulls and merges.
- Prompts interactively on true field-level conflicts.

```bash
task-tool sync
task-tool sync --dry-run   # preview only
```

### `task-tool push`

Force-push local data to S3, regardless of change detection.

```bash
task-tool push
task-tool push --dry-run
```

### `task-tool pull`

Force-pull the latest remote snapshot(s) and merge into local data.

```bash
task-tool pull
task-tool pull --dry-run
```

### `task-tool status`

Show current sync status: local changes, available remote snapshots, lock state.

```bash
task-tool status
```

### `task-tool list-backups`

List available snapshots in S3.

```bash
task-tool list-backups
task-tool list-backups --computer laptop
```

### `task-tool restore <snapshot>`

Restore local data from a specific snapshot (by key or index from `list-backups`).
Creates `.bak` files before overwriting. Works on fresh machines where `~/.task` doesn't
exist yet.

```bash
task-tool restore 0                          # by index
task-tool restore taskwarrior-2026-07-18T14-32-05Z-laptop  # by key
```

## How It Works

1. **Snapshots**: Local `pending.data` + `completed.data` are tarred and encrypted with
   Fernet before upload. Each snapshot is named with a timestamp and computer ID.

2. **Locking**: A lock object in S3 prevents concurrent access. Locks expire after 5
   minutes (configurable via `TASKTOOL_LOCK_TIMEOUT`).

3. **Merge**: Three-way field-level merge using the last-synced state as the common
   base. Auto-merges when only one side changed a field; prompts on true conflicts.

4. **State**: A local JSON file (`~/.local/state/task-tool/state.json`) tracks the hash
   of local data and the last-pulled snapshot per remote computer.

## Safety

- Local `.bak` files are always created before any overwrite.
- `--dry-run` flag available on sync/push/pull.
- No secrets are ever written to disk by this tool.
- Clear error messages on missing env vars, auth failures, lock contention, and
  decryption failures.

## Design Decisions

- **Lock timeout** defaults to 5 minutes (configurable via `TASKTOOL_LOCK_TIMEOUT` env
  var). This handles cases where a process crashes without releasing the lock.
- **`restore`** works on a completely fresh machine (creates `~/.task` if needed),
  making it suitable for bootstrapping a new installation.
