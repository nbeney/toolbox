"""S3 operations: upload, download, list, lock management."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from .config import Config

LOCK_KEY = "taskwarrior/.lock"
SNAPSHOT_PREFIX = "taskwarrior-"


def get_client(config: "Config"):
    """Create an S3 client."""
    return boto3.client("s3", region_name=config.s3_region)


def acquire_lock(config: "Config", client=None) -> None:
    """Acquire the sync lock. Exits if another computer holds it."""
    if client is None:
        client = get_client(config)

    try:
        response = client.get_object(Bucket=config.s3_bucket, Key=LOCK_KEY)
        lock_data = json.loads(response["Body"].read().decode())
        acquired_at = datetime.fromisoformat(lock_data["acquired_at"])
        age_seconds = (datetime.now(timezone.utc) - acquired_at).total_seconds()

        if age_seconds < config.lock_timeout_seconds:
            owner = lock_data.get("computer_id", "unknown")
            print(
                f"Error: lock held by '{owner}' (acquired {int(age_seconds)}s ago). "
                f"Timeout is {config.lock_timeout_seconds}s. Aborting.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        # Lock is stale — override it
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchKey":
            raise

    # Write lock
    lock_data = {
        "computer_id": config.computer_id,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    }
    client.put_object(
        Bucket=config.s3_bucket,
        Key=LOCK_KEY,
        Body=json.dumps(lock_data).encode(),
    )


def release_lock(config: "Config", client=None) -> None:
    """Release the sync lock."""
    if client is None:
        client = get_client(config)
    try:
        client.delete_object(Bucket=config.s3_bucket, Key=LOCK_KEY)
    except ClientError:
        pass  # best effort


def get_lock_status(config: "Config", client=None) -> dict | None:
    """Return lock info or None if no lock exists."""
    if client is None:
        client = get_client(config)
    try:
        response = client.get_object(Bucket=config.s3_bucket, Key=LOCK_KEY)
        return json.loads(response["Body"].read().decode())
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise


def upload_snapshot(config: "Config", encrypted_data: bytes, client=None) -> str:
    """Upload an encrypted snapshot to S3. Returns the object key."""
    if client is None:
        client = get_client(config)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    key = f"{SNAPSHOT_PREFIX}{timestamp}-{config.computer_id}"

    client.put_object(
        Bucket=config.s3_bucket,
        Key=key,
        Body=encrypted_data,
    )
    return key


def list_snapshots(
    config: "Config", computer_id: str | None = None, client=None
) -> list[dict]:
    """List snapshot objects in S3, optionally filtered by computer_id.

    Returns list of dicts with keys: key, timestamp, computer_id, size.
    """
    if client is None:
        client = get_client(config)

    paginator = client.get_paginator("list_objects_v2")
    results = []

    for page in paginator.paginate(Bucket=config.s3_bucket, Prefix=SNAPSHOT_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            parsed = _parse_snapshot_key(key)
            if parsed is None:
                continue
            if computer_id and parsed["computer_id"] != computer_id:
                continue
            results.append(
                {
                    "key": key,
                    "timestamp": parsed["timestamp"],
                    "computer_id": parsed["computer_id"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                }
            )

    results.sort(key=lambda x: x["key"], reverse=True)
    return results


def download_snapshot(config: "Config", key: str, client=None) -> bytes:
    """Download a snapshot's encrypted content from S3."""
    if client is None:
        client = get_client(config)
    response = client.get_object(Bucket=config.s3_bucket, Key=key)
    return response["Body"].read()


def prune_snapshots(config: "Config", client=None) -> list[str]:
    """Delete old snapshots for this computer, keeping the most recent N.

    Returns list of deleted keys.
    """
    if client is None:
        client = get_client(config)

    snapshots = list_snapshots(config, computer_id=config.computer_id, client=client)
    # Already sorted newest-first
    to_delete = snapshots[config.keep_snapshots :]
    deleted = []

    for snap in to_delete:
        client.delete_object(Bucket=config.s3_bucket, Key=snap["key"])
        deleted.append(snap["key"])

    return deleted


def check_bucket_access(config: "Config", client=None) -> bool:
    """Check if we have access to the configured S3 bucket."""
    if client is None:
        client = get_client(config)
    try:
        client.head_bucket(Bucket=config.s3_bucket)
        return True
    except ClientError:
        return False


def _parse_snapshot_key(key: str) -> dict | None:
    """Parse a snapshot key into its components.

    Expected format: taskwarrior-<ISO8601-timestamp>-<computer_id>
    e.g. taskwarrior-2026-07-18T14-32-05Z-laptop
    """
    if not key.startswith(SNAPSHOT_PREFIX):
        return None

    rest = key[len(SNAPSHOT_PREFIX) :]
    # Timestamp format: YYYY-MM-DDTHH-MM-SSZ (20 chars)
    # Then a '-' separator, then computer_id
    if len(rest) < 22:  # 20 for timestamp + 1 dash + at least 1 char id
        return None

    timestamp_str = rest[:20]
    computer_id = rest[21:]  # skip the separating '-'

    if not computer_id:
        return None

    return {
        "timestamp": timestamp_str,
        "computer_id": computer_id,
    }
