"""Snapshot creation and extraction (tar + encrypt/decrypt)."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

from . import crypto


def create_snapshot(data_dir: Path, fernet_key: str) -> bytes:
    """Create an encrypted tarball of pending.data + completed.data.

    Returns the Fernet-encrypted bytes ready for S3 upload.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for filename in ("pending.data", "completed.data"):
            filepath = data_dir / filename
            if filepath.exists():
                tar.add(str(filepath), arcname=filename)
            else:
                # Add an empty file so the snapshot is always complete
                info = tarfile.TarInfo(name=filename)
                info.size = 0
                tar.addfile(info, io.BytesIO(b""))

    return crypto.encrypt(buf.getvalue(), fernet_key)


def extract_snapshot(encrypted_data: bytes, fernet_key: str) -> dict[str, str]:
    """Decrypt and extract a snapshot.

    Returns dict mapping filename -> file content string.
    """
    decrypted = crypto.decrypt(encrypted_data, fernet_key)
    buf = io.BytesIO(decrypted)
    result = {}

    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.name in ("pending.data", "completed.data"):
                f = tar.extractfile(member)
                if f:
                    result[member.name] = f.read().decode("utf-8")
                else:
                    result[member.name] = ""

    return result
