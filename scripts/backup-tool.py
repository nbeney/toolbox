#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "boto3>=1.42.30",
#   "rich>=14.2.0",
#   "typer>=0.21.1",
# ]
# ///

"""
Encrypted S3 Backup Tool

A tool for creating encrypted backups of directories and storing them in AWS S3.
"""

import os
import sys
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional
import subprocess

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Encrypted S3 Backup Tool")
console = Console()


class BackupConfig:
    """Configuration for backup operations."""

    def __init__(
        self,
        s3_bucket: str = "your-backup-bucket",
        s3_prefix: str = "backups",
        encryption_key_file: Optional[Path] = None,
    ):
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.encryption_key_file = encryption_key_file or Path.home() / ".backup_key"


class EncryptionManager:
    """Handles encryption and decryption operations."""

    def __init__(self, key_file: Path):
        self.key_file = key_file

    def ensure_key_exists(self) -> None:
        """Generate encryption key if it doesn't exist."""
        if not self.key_file.exists():
            console.print("[yellow]Generating new encryption key...[/yellow]")
            result = subprocess.run(
                ["openssl", "rand", "-base64", "32"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.key_file.write_text(result.stdout)
            self.key_file.chmod(0o600)
            console.print(f"[green]Key generated and saved to {self.key_file}[/green]")
            console.print("[yellow]⚠️  Keep this key safe! You'll need it to restore backups.[/yellow]")

    def encrypt_file(self, input_file: Path, output_file: Path) -> None:
        """Encrypt a file using AES-256-CBC."""
        subprocess.run(
            [
                "openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2",
                "-in", str(input_file),
                "-out", str(output_file),
                "-pass", f"file:{self.key_file}",
            ],
            check=True,
        )

    def decrypt_file(self, input_file: Path, output_file: Path) -> None:
        """Decrypt a file using AES-256-CBC."""
        subprocess.run(
            [
                "openssl", "enc", "-aes-256-cbc", "-d", "-pbkdf2",
                "-in", str(input_file),
                "-out", str(output_file),
                "-pass", f"file:{self.key_file}",
            ],
            check=True,
        )


class ArchiveManager:
    """Handles archive creation and extraction."""

    @staticmethod
    def create_archive(source_dir: Path, output_file: Path) -> None:
        """Create a tar.gz archive of a directory."""
        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)

    @staticmethod
    def extract_archive(archive_file: Path, destination: Path) -> None:
        """Extract a tar.gz archive to a destination."""
        with tarfile.open(archive_file, "r:gz") as tar:
            tar.extractall(destination)


class S3Manager:
    """Handles S3 operations."""

    def __init__(self, bucket: str, prefix: str):
        self.bucket = bucket
        self.prefix = prefix

    def get_s3_path(self, filename: str) -> str:
        """Get full S3 path for a file."""
        return f"s3://{self.bucket}/{self.prefix}/{filename}"

    def upload_file(self, local_file: Path, remote_filename: str) -> None:
        """Upload a file to S3."""
        s3_path = self.get_s3_path(remote_filename)
        subprocess.run(
            ["aws", "s3", "cp", str(local_file), s3_path],
            check=True,
        )

    def download_file(self, remote_filename: str, local_file: Path) -> None:
        """Download a file from S3."""
        s3_path = self.get_s3_path(remote_filename)
        subprocess.run(
            ["aws", "s3", "cp", s3_path, str(local_file)],
            check=True,
        )

    def list_backups(self) -> list[dict]:
        """List all backups in S3."""
        s3_path = f"s3://{self.bucket}/{self.prefix}/"
        result = subprocess.run(
            ["aws", "s3", "ls", s3_path, "--recursive"],
            capture_output=True,
            text=True,
            check=True,
        )

        backups = []
        for line in result.stdout.strip().split("\n"):
            if not line or not line.endswith(".tar.gz.enc"):
                continue

            parts = line.split()
            if len(parts) >= 4:
                date = parts[0]
                time = parts[1]
                size = int(parts[2])
                filename = parts[3].split("/")[-1]

                backups.append({
                    "date": date,
                    "time": time,
                    "size": size,
                    "filename": filename,
                })

        return backups


class BackupService:
    """Main service for backup operations."""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.encryption_manager = EncryptionManager(config.encryption_key_file)
        self.archive_manager = ArchiveManager()
        self.s3_manager = S3Manager(config.s3_bucket, config.s3_prefix)

    def backup(self, source_dir: Path) -> str:
        """Create and upload an encrypted backup."""
        if not source_dir.is_dir():
            raise ValueError(f"Directory not found: {source_dir}")

        self.encryption_manager.ensure_key_exists()

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_dir.name}_{timestamp}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            tar_file = tmp_path / f"{backup_name}.tar.gz"
            encrypted_file = tmp_path / f"{backup_name}.tar.gz.enc"

            console.print(f"[cyan]Creating archive of {source_dir}...[/cyan]")
            self.archive_manager.create_archive(source_dir, tar_file)

            console.print("[cyan]Encrypting archive with AES-256-CBC...[/cyan]")
            self.encryption_manager.encrypt_file(tar_file, encrypted_file)

            console.print(f"[cyan]Uploading to S3...[/cyan]")
            remote_filename = f"{backup_name}.tar.gz.enc"
            self.s3_manager.upload_file(encrypted_file, remote_filename)

            console.print(f"[green]✓ Backup completed: {remote_filename}[/green]")
            return remote_filename

    def restore(self, backup_name: str, destination: Path) -> None:
        """Download and restore an encrypted backup."""
        self.encryption_manager.ensure_key_exists()

        # Add extension if not provided
        if not backup_name.endswith(".tar.gz.enc"):
            backup_name = f"{backup_name}.tar.gz.enc"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            encrypted_file = tmp_path / backup_name
            tar_file = tmp_path / backup_name.replace(".enc", "")

            console.print(f"[cyan]Downloading from S3...[/cyan]")
            self.s3_manager.download_file(backup_name, encrypted_file)

            console.print("[cyan]Decrypting archive...[/cyan]")
            self.encryption_manager.decrypt_file(encrypted_file, tar_file)

            console.print(f"[cyan]Extracting to {destination}...[/cyan]")
            self.archive_manager.extract_archive(tar_file, destination)

            console.print("[green]✓ Restore completed successfully[/green]")

    def list_backups(self) -> list[dict]:
        """List all available backups."""
        return self.s3_manager.list_backups()


# CLI Commands

@app.command()
def backup(
    directory: Path = typer.Argument(..., help="Directory to backup"),
    bucket: str = typer.Option("your-backup-bucket", "--bucket", "-b", help="S3 bucket name"),
    prefix: str = typer.Option("backups", "--prefix", "-p", help="S3 prefix/folder"),
):
    """Create and upload an encrypted backup of a directory."""
    try:
        config = BackupConfig(s3_bucket=bucket, s3_prefix=prefix)
        service = BackupService(config)
        service.backup(directory)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def restore(
    backup_name: str = typer.Argument(..., help="Name of backup to restore"),
    destination: Path = typer.Option(".", "--dest", "-d", help="Destination directory"),
    bucket: str = typer.Option("your-backup-bucket", "--bucket", "-b", help="S3 bucket name"),
    prefix: str = typer.Option("backups", "--prefix", "-p", help="S3 prefix/folder"),
):
    """Download and restore an encrypted backup."""
    try:
        config = BackupConfig(s3_bucket=bucket, s3_prefix=prefix)
        service = BackupService(config)
        service.restore(backup_name, destination)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def list(
    bucket: str = typer.Option("your-backup-bucket", "--bucket", "-b", help="S3 bucket name"),
    prefix: str = typer.Option("backups", "--prefix", "-p", help="S3 prefix/folder"),
):
    """List all backups in S3."""
    try:
        config = BackupConfig(s3_bucket=bucket, s3_prefix=prefix)
        service = BackupService(config)
        backups = service.list_backups()

        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            return

        table = Table(title=f"Backups in s3://{bucket}/{prefix}/")
        table.add_column("Date", style="cyan")
        table.add_column("Time", style="cyan")
        table.add_column("Size", style="green")
        table.add_column("Filename", style="yellow")

        for backup in backups:
            size_mb = backup["size"] / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{backup['size'] / 1024:.2f} KB"
            table.add_row(
                backup["date"],
                backup["time"],
                size_str,
                backup["filename"],
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
