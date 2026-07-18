# Build Prompt: `task-tool` — TaskWarrior S3 Backup & Sync CLI

## Context

I use TaskWarrior 2.x on two computers (Linux and ChromeOS/Crostini). I don't run a
Taskserver (taskd). I want a standalone CLI tool that backs up and syncs my TaskWarrior
data across both machines via an S3 bucket, with everything encrypted before it leaves
the machine. The code will live in a **public GitHub repo**, so no secrets, bucket
names, or credentials may ever be hardcoded — everything sensitive/environment-specific
comes from environment variables.

## Tech stack

- Python, packaged/run with **uv**
- CLI framework: **Typer**
- AWS access: **boto3** (assume standard AWS credential chain — `~/.aws/credentials`,
  env vars, or SSO profile; the tool itself does not manage AWS auth, only S3 bucket
  operations)
- Encryption: **`cryptography`** library's **Fernet** (symmetric, authenticated
  encryption) — no external binaries (no `age`/`gpg`), so behavior is identical on
  Linux and ChromeOS/Crostini
- Config/secrets: **environment variables only** (no config files, no OS keychain
  dependency)

## Command name

`task-tool`

## Environment variables (all required unless noted)

- `TASKTOOL_S3_BUCKET` — target bucket name
- `TASKTOOL_S3_REGION` — AWS region
- `TASKTOOL_COMPUTER_ID` — a stable identifier for this machine (e.g. `laptop`,
  `chromebook`) — used in S3 object naming and lock ownership
- `TASKTOOL_FERNET_KEY` — base64 Fernet key used to encrypt/decrypt snapshots
- `TASKTOOL_TASK_DATA_DIR` — path to the TaskWarrior data directory (default:
  `~/.task` if unset)
- `TASKTOOL_KEEP_SNAPSHOTS` — number of snapshots to retain per computer during
  pruning (default: `10` if unset)

Provide a `task-tool init` command (see below) that helps generate/validate these
(e.g. can generate a new Fernet key), but the tool must never write secrets to disk —
only print instructions/values for the user to export or store themselves.

## Data model

TaskWarrior stores tasks as JSON-lines files. This tool only needs to read/write:

- `pending.data` — active/incomplete tasks
- `completed.data` — completed/deleted tasks

(`undo.data` and `backlog.data` are TaskWarrior's own local bookkeeping and are out of
scope — do not sync them.)

Each line in these files is a JSON object with a `uuid` field. Build an internal
representation that indexes all tasks (from both files, tagged with which file they
came from) by `uuid`.

## S3 object naming & layout

- Snapshot objects: `taskwarrior-<ISO8601-timestamp>-<computer_id>` (e.g.
  `taskwarrior-2026-07-18T14-32-05Z-laptop`), stored as Fernet-encrypted tarballs
  containing `pending.data` + `completed.data` as they existed on that computer at
  push time.
- Lock object: a single well-known key (e.g. `taskwarrior/.lock`) containing JSON
  `{"computer_id": ..., "acquired_at": ...}`. Before push/pull, check for this object;
  if present and younger than a timeout (e.g. 5 minutes), abort with a clear message
  naming which computer holds the lock. Remove the lock object when done (including
  on error, via try/finally).

## Sync algorithm

### Detecting "necessary"

Maintain a local state file (e.g. `~/.local/state/task-tool/state.json` — this is
non-secret bookkeeping, not credentials, so it's fine as a plain file) recording:
- the hash of the local task data as of the last successful sync
- the S3 object key of the last snapshot successfully pulled from each other computer

`sync` should:
1. Compute the current local data hash. If it differs from the last-synced hash →
   a push is needed.
2. List snapshot objects in S3 for *other* `computer_id` values. If there's a newer
   one than what was last pulled → a pull is needed.
3. Skip push and/or pull entirely if neither is needed (print a "nothing to do"
   message).

### Merge logic (structured, uuid-keyed, field-level)

When a pull brings in a remote snapshot:
1. Parse remote and local tasks into uuid-indexed dicts (per file: pending/completed).
2. For each uuid, compare field-by-field against the last common synced state (from
   the state file) to classify each side's changes:
   - Only remote changed → apply remote's value.
   - Only local changed → keep local's value (no action needed).
   - Both changed **the same field to the same value** → no conflict.
   - Both changed **the same field to different values** → **true conflict**: prompt
     the user interactively, showing the task description/uuid, the field, and both
     values, with options to keep local / keep remote / skip (leave unresolved for
     next sync).
   - Both changed **different fields** on the same task → auto-merge, no prompt.
   - New tasks (uuid not seen before) on either side → include them (no conflict
     possible).
   - Tasks that moved between `pending.data` and `completed.data` (e.g. completed
     locally) → treat file membership itself as a field to merge the same way.
3. Write the merged result back to local `pending.data`/`completed.data` (take a
   local backup copy before overwriting, e.g. `pending.data.bak`).
4. Update the local state file with the new last-synced hash and pulled snapshot
   pointers.

### Push

1. Compute current local data.
2. Tar + Fernet-encrypt `pending.data` + `completed.data`.
3. Upload as a new timestamped object under this computer's `computer_id`.
4. Prune old snapshots for this `computer_id`, keeping the most recent
   `TASKTOOL_KEEP_SNAPSHOTS` (delete older ones).
5. Update local state file.

## Subcommands

- `task-tool init` — interactive first-time setup: checks/creates the local state
  directory, offers to generate a Fernet key (printed for the user to store as an
  env var — never written to disk), validates S3 bucket access, and reports which
  required env vars are missing.
- `task-tool sync` — the main command: does the "necessary" push/pull described
  above, prompting on real conflicts.
- `task-tool push` — force a push regardless of the "necessary" check.
- `task-tool pull` — force a pull regardless of the "necessary" check.
- `task-tool status` — show: local changes since last sync (yes/no), available
  remote snapshots per computer, whether a pull is pending, lock status.
- `task-tool restore <snapshot-key-or-index>` — decrypt and restore local
  `pending.data`/`completed.data` from a specific past snapshot (with a
  confirmation prompt and a local backup taken first, since this overwrites
  current data).
- `task-tool list-backups [--computer <id>]` — list available snapshots in S3
  (timestamp, computer, size), optionally filtered by computer.

## Safety / UX requirements

- Always take a local `.bak` copy of `pending.data`/`completed.data` before any
  overwrite (merge apply, restore).
- Never write `TASKTOOL_FERNET_KEY` or AWS credentials to disk anywhere.
- Clear, human-readable conflict prompts — show task description, not just uuid,
  wherever the description field itself isn't the conflicting field.
- `--dry-run` flag on `sync`/`push`/`pull` to preview what would happen without
  making changes.
- Exit non-zero with a clear error message on: missing required env vars, S3 auth
  failures, lock contention, decryption failures (e.g. wrong key).

## Deliverable

A `uv`-managed Python project:
- `pyproject.toml` with dependencies (`typer`, `boto3`, `cryptography`)
- Source laid out for a `task-tool` console-script entry point
- Reasonably organized into modules (e.g. `cli.py`, `s3.py`, `crypto.py`, `merge.py`,
  `taskdata.py`, `state.py`) rather than one giant file
- A `README.md` explaining setup: required env vars, how to generate a Fernet key,
  first-run (`init`) instructions, and basic usage examples for each subcommand

## Open points the builder should flag if they seem wrong

- Lock timeout duration (suggested default: 5 minutes) — configurable via env var?
- Whether `restore` should also support restoring to a totally clean environment
  (i.e. work even if `~/.task` doesn't exist yet on a brand-new machine)
