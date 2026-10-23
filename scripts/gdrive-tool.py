#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "google-api-python-client>=2.149.0",
#   "google-auth>=2.35.0",
#   "rich>=14.0.0",
#   "typer>=0.26.7",
# ]
# ///

"""
Google Drive Manager

Manage files in your Google Drive from the command line.

Commands:
  list      - List files/folders in Drive.
  download  - Download a file by id (or name) to a local path.
  upload    - Upload a local file to Drive.
  delete    - Delete a file by id (or name) from Drive.

Authentication
--------------
This tool uses Application Default Credentials (ADC) via gcloud. Run this
once to grant the Drive scope (the default ADC login does NOT include Drive):

    gcloud auth application-default login \\
        --scopes=https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/cloud-platform

The Google Drive API must also be enabled for the project:

    gcloud services enable drive.googleapis.com --project=restic-eb4d68a6
"""

from __future__ import annotations

import io
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TransferSpeedColumn,
)
from rich.prompt import Confirm
from rich.table import Table

app = typer.Typer(
    help="Manage files in your Google Drive.",
    no_args_is_help=True,
)
console = Console()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PROJECT = "restic-eb4d68a6"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"

# Google Workspace native types need an export mime-type to download.
EXPORT_MAP: dict[str, tuple[str, str]] = {
    "application/vnd.google-apps.document": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
    ),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
    "application/vnd.google-apps.drawing": ("image/png", ".png"),
}


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OrderBy(str, Enum):
    name = "name"
    modified = "modifiedTime desc"
    created = "createdTime desc"
    size = "quotaBytesUsed desc"


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------


class State:
    project: str = DEFAULT_PROJECT


state = State()


@app.callback()
def main(
    project: Annotated[
        str,
        typer.Option("--project", "-p", help="Google Cloud project id."),
    ] = DEFAULT_PROJECT,
) -> None:
    state.project = project


# ---------------------------------------------------------------------------
# Drive service
# ---------------------------------------------------------------------------


def get_service():
    """Build an authenticated Drive API client using ADC."""
    try:
        import google.auth
        from google.auth.exceptions import DefaultCredentialsError
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - dependency issue
        console.print(f"[red]Missing dependency:[/red] {exc}")
        raise typer.Exit(code=1)

    try:
        credentials, _ = google.auth.default(scopes=DRIVE_SCOPES)
    except DefaultCredentialsError:
        _auth_help()
        raise typer.Exit(code=1)

    try:
        return build("drive", "v3", credentials=credentials, cache_discovery=False)
    except Exception as exc:  # pragma: no cover - network/auth issue
        console.print(f"[red]Failed to build Drive client:[/red] {escape(str(exc))}")
        _auth_help()
        raise typer.Exit(code=1)


def _auth_help() -> None:
    console.print(
        "\n[yellow]Google Drive credentials are not set up.[/yellow]\n"
        "Run this once to grant the Drive scope:\n\n"
        "  [cyan]gcloud auth application-default login \\\n"
        "      --scopes=https://www.googleapis.com/auth/drive,"
        "https://www.googleapis.com/auth/cloud-platform[/cyan]\n\n"
        "And make sure the Drive API is enabled:\n\n"
        f"  [cyan]gcloud services enable drive.googleapis.com "
        f"--project={state.project}[/cyan]\n"
    )


def _api_error(exc: Exception) -> "typer.Exit":
    """Print a friendly message for a Google API error and return an Exit."""
    from googleapiclient.errors import HttpError

    if isinstance(exc, HttpError):
        status = exc.resp.status if exc.resp else "?"
        console.print(f"[red]Drive API error ({status}):[/red] {escape(exc._get_reason() or '')}")
        if status in (401, 403):
            _auth_help()
    else:
        console.print(f"[red]Error:[/red] {escape(str(exc))}")
    return typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _human_size(num: Optional[int | str]) -> str:
    if num is None:
        return "-"
    try:
        size = float(num)
    except (TypeError, ValueError):
        return "-"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _resolve_file(service, identifier: str) -> dict:
    """Resolve a file by id first, then fall back to an exact name match.

    Returns the file metadata dict. Exits if nothing (or multiple) match.
    """
    from googleapiclient.errors import HttpError

    fields = "id, name, mimeType, size, modifiedTime"

    # Try as an id first.
    try:
        return (
            service.files()
            .get(fileId=identifier, fields=fields, supportsAllDrives=True)
            .execute()
        )
    except HttpError as exc:
        if exc.resp is None or exc.resp.status != 404:
            raise _api_error(exc)

    # Fall back to a name lookup.
    safe = identifier.replace("'", "\\'")
    try:
        result = (
            service.files()
            .list(
                q=f"name = '{safe}' and trashed = false",
                fields=f"files({fields})",
                pageSize=10,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as exc:
        raise _api_error(exc)

    matches = result.get("files", [])
    if not matches:
        console.print(f"[red]No file found with id or name:[/red] {escape(identifier)}")
        raise typer.Exit(code=1)
    if len(matches) > 1:
        console.print(
            f"[yellow]Multiple files named[/yellow] '{escape(identifier)}'. "
            "Use the id instead:"
        )
        for m in matches:
            console.print(f"  [cyan]{m['id']}[/cyan]  {escape(m['name'])}")
        raise typer.Exit(code=1)
    return matches[0]


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


@app.command("list")
def list_files(
    query: Annotated[
        Optional[str],
        typer.Option(
            "--query",
            "-q",
            help="Raw Drive query string (overrides --name/--folder).",
        ),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Filter by name substring."),
    ] = None,
    folder: Annotated[
        Optional[str],
        typer.Option("--folder", "-f", help="Parent folder id to list within."),
    ] = None,
    order: Annotated[
        OrderBy,
        typer.Option("--order", "-o", help="Sort order."),
    ] = OrderBy.name,
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Maximum number of files to show."),
    ] = 100,
) -> None:
    """List files and folders in Drive."""
    from googleapiclient.errors import HttpError

    service = get_service()

    clauses = ["trashed = false"]
    if query:
        clauses = [query]
    else:
        if name:
            safe = name.replace("'", "\\'")
            clauses.append(f"name contains '{safe}'")
        if folder:
            safe = folder.replace("'", "\\'")
            clauses.append(f"'{safe}' in parents")
    q = " and ".join(clauses)

    files: list[dict] = []
    page_token: Optional[str] = None
    try:
        while len(files) < limit:
            result = (
                service.files()
                .list(
                    q=q,
                    orderBy=order.value,
                    pageSize=min(100, limit - len(files)),
                    pageToken=page_token,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                )
                .execute()
            )
            files.extend(result.get("files", []))
            page_token = result.get("nextPageToken")
            if not page_token:
                break
    except HttpError as exc:
        raise _api_error(exc)

    if not files:
        console.print("[dim]No files found.[/dim]")
        return

    table = Table(title="Google Drive files")
    table.add_column("Id", style="bright_black", header_style="white")
    table.add_column("Name", style="bright_cyan", header_style="white")
    table.add_column("Type", style="bright_green", header_style="white")
    table.add_column("Size", style="bright_white", header_style="white", justify="right")
    table.add_column("Modified", style="bright_white", header_style="white")

    for f in files:
        is_folder = f.get("mimeType") == FOLDER_MIME
        type_label = "folder" if is_folder else f.get("mimeType", "").split(".")[-1]
        name_cell = f"📁 {f['name']}" if is_folder else f["name"]
        table.add_row(
            f["id"],
            escape(name_cell),
            escape(type_label),
            "-" if is_folder else _human_size(f.get("size")),
            (f.get("modifiedTime") or "-").replace("T", " ").replace("Z", ""),
        )

    console.print(table)
    console.print(f"[dim]{len(files)} file(s).[/dim]")


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------


@app.command("download")
def download(
    identifier: Annotated[
        str,
        typer.Argument(help="File id (preferred) or exact file name."),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Local output path. Defaults to the file name."),
    ] = None,
) -> None:
    """Download a file from Drive to a local path."""
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload

    service = get_service()
    meta = _resolve_file(service, identifier)

    file_id = meta["id"]
    mime = meta.get("mimeType", "")

    if mime == FOLDER_MIME:
        console.print(f"[red]'{escape(meta['name'])}' is a folder — cannot download.[/red]")
        raise typer.Exit(code=1)

    dest = output or Path(meta["name"])
    export_mime: Optional[str] = None

    if mime in EXPORT_MAP:
        export_mime, suffix = EXPORT_MAP[mime]
        if output is None and dest.suffix != suffix:
            dest = dest.with_suffix(suffix)
        console.print(f"[dim]Exporting Google-native file as {export_mime}[/dim]")

    if dest.exists():
        if not Confirm.ask(f"[yellow]{dest}[/yellow] exists. Overwrite?"):
            console.print("Aborted.")
            raise typer.Exit(code=0)

    try:
        if export_mime:
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        else:
            request = service.files().get_media(fileId=file_id, supportsAllDrives=True)

        total = int(meta.get("size", 0)) or None
        with open(dest, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024)
            with Progress(
                TextColumn("[cyan]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(f"Downloading {meta['name']}", total=total)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status and total:
                        progress.update(task, completed=int(status.resumable_progress))
                progress.update(task, completed=total or progress.tasks[task].completed)
    except HttpError as exc:
        dest.unlink(missing_ok=True)
        raise _api_error(exc)

    size = dest.stat().st_size
    console.print(
        f"[bold green]✓ Downloaded[/bold green] [cyan]{dest}[/cyan] ({_human_size(size)})"
    )


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------


@app.command("upload")
def upload(
    file: Annotated[
        Path,
        typer.Argument(help="Local file to upload."),
    ],
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Name to use in Drive. Defaults to the local name."),
    ] = None,
    folder: Annotated[
        Optional[str],
        typer.Option("--folder", "-f", help="Destination parent folder id."),
    ] = None,
) -> None:
    """Upload a local file to Drive."""
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    if not file.exists() or not file.is_file():
        console.print(f"[red]Not a file:[/red] {file}")
        raise typer.Exit(code=1)

    service = get_service()

    metadata: dict = {"name": name or file.name}
    if folder:
        metadata["parents"] = [folder]

    media = MediaFileUpload(str(file), resumable=True)
    total = file.stat().st_size or None

    try:
        request = service.files().create(
            body=metadata,
            media_body=media,
            fields="id, name, size, webViewLink",
            supportsAllDrives=True,
        )
        with Progress(
            TextColumn("[cyan]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Uploading {file.name}", total=total)
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status and total:
                    progress.update(task, completed=int(status.resumable_progress))
            progress.update(task, completed=total or progress.tasks[task].completed)
    except HttpError as exc:
        raise _api_error(exc)

    console.print(
        f"[bold green]✓ Uploaded[/bold green] [cyan]{response['name']}[/cyan]\n"
        f"  id:   [bright_black]{response['id']}[/bright_black]"
    )
    if response.get("webViewLink"):
        console.print(f"  link: [blue]{response['webViewLink']}[/blue]")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


@app.command("delete")
def delete(
    identifier: Annotated[
        str,
        typer.Argument(help="File id (preferred) or exact file name."),
    ],
    permanent: Annotated[
        bool,
        typer.Option(
            "--permanent",
            help="Permanently delete instead of moving to trash.",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
) -> None:
    """Delete a file from Drive (moves to trash by default)."""
    from googleapiclient.errors import HttpError

    service = get_service()
    meta = _resolve_file(service, identifier)

    action = "Permanently delete" if permanent else "Move to trash"
    if not yes:
        if not Confirm.ask(
            f"[yellow]{action}[/yellow] '[cyan]{escape(meta['name'])}[/cyan]' "
            f"([bright_black]{meta['id']}[/bright_black])?"
        ):
            console.print("Aborted.")
            raise typer.Exit(code=0)

    try:
        if permanent:
            service.files().delete(fileId=meta["id"], supportsAllDrives=True).execute()
        else:
            service.files().update(
                fileId=meta["id"],
                body={"trashed": True},
                supportsAllDrives=True,
            ).execute()
    except HttpError as exc:
        raise _api_error(exc)

    verb = "Deleted" if permanent else "Trashed"
    console.print(f"[bold green]✓ {verb}[/bold green] [cyan]{escape(meta['name'])}[/cyan]")


if __name__ == "__main__":
    app()
