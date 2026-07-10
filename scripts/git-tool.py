#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31.0",
#   "rich>=14.0.0",
#   "typer>=0.26.7",
# ]
# ///

"""
Git Repo Manager

Manage local and remote git repositories across multiple providers.
"""

from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional

import requests
import typer
from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm
from rich.table import Table

app = typer.Typer(help="Manage local and remote git repositories.")
console = Console()


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class UrlMode(str, Enum):
    https = "https"
    git = "git"


class RepoMode(str, Enum):
    active = "active"
    archived = "archived"
    all = "all"


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------


class State:
    root: Path = Path.cwd()
    url_mode: UrlMode = UrlMode.https
    provider: str = "github"


state = State()


@app.callback()
def main(
    root: Optional[Path] = typer.Option(
        None,
        "--root",
        "-r",
        help="Local directory containing repos. Defaults to cwd.",
    ),
    url_mode: UrlMode = typer.Option(
        UrlMode.https,
        "--url-mode",
        help="URL format to use for cloning: https or git (SSH).",
    ),
    provider: str = typer.Option(
        "github",
        "--provider",
        "-p",
        help="Hosting provider (github, bitbucket).",
    ),
) -> None:
    if root is not None:
        state.root = root.expanduser()
    state.url_mode = url_mode
    state.provider = provider


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class RemoteRepo:
    def __init__(
        self,
        name: str,
        https_url: str,
        ssh_url: str,
        default_branch: str = "main",
        is_archived: bool = False,
    ):
        self.name = name
        self.https_url = https_url
        self.ssh_url = ssh_url
        self.default_branch = default_branch
        self.is_archived = is_archived

    def clone_url(self) -> str:
        return self.ssh_url if state.url_mode == UrlMode.git else self.https_url


class LocalRepo:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name

    # --- git helpers -------------------------------------------------------

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True,
            text=True,
        )

    def current_branch(self) -> str:
        result = self._git("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip() if result.returncode == 0 else "?"

    def has_uncommitted_changes(self) -> bool:
        return bool(self.status_entries())

    def status_entries(self) -> list[tuple[str, str, str]]:
        """Return list of (category, filename, change_code) where category is STAGED/UNSTAGED/UNTRACKED."""
        result = self._git("status", "--porcelain")
        entries = []
        for line in result.stdout.splitlines():
            if len(line) < 3:
                continue
            index = line[0]  # staged state
            worktree = line[1]  # unstaged state
            filename = line[3:]
            if index == "?" and worktree == "?":
                entries.append(("UNTRACKED", filename, ""))
            elif index != " " and worktree == " ":
                entries.append(("STAGED", filename, index))
            elif index == " " and worktree != " ":
                entries.append(("UNSTAGED", filename, worktree))
            else:
                # Both staged and unstaged changes (e.g. partially staged)
                entries.append(("STAGED", filename, index))
                entries.append(("UNSTAGED", filename, worktree))
        return entries

    def stashes(self) -> list[str]:
        result = self._git("stash", "list")
        return result.stdout.strip().splitlines()

    def local_branches(self) -> list[str]:
        result = self._git("branch", "--format=%(refname:short)")
        return [b for b in result.stdout.strip().splitlines() if b]

    def unpushed_commits(self, branch: str) -> int:
        result = self._git("rev-list", "--count", f"origin/{branch}..{branch}")
        if result.returncode != 0:
            return 0
        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0

    def unpulled_commits(self, branch: str) -> int:
        result = self._git("rev-list", "--count", f"{branch}..origin/{branch}")
        if result.returncode != 0:
            return 0
        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0

    def untracked_files(self) -> int:
        result = self._git("ls-files", "--others", "--exclude-standard")
        return len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0

    def staged_files(self) -> int:
        result = self._git("diff", "--cached", "--name-only")
        return len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0

    def unstaged_files(self) -> int:
        result = self._git("diff", "--name-only")
        return len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0

    def fetch(self) -> None:
        self._git("fetch", "--all", "--prune")

    def pull(self) -> subprocess.CompletedProcess:
        return self._git("pull", "--ff-only")


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------


class Provider(ABC):
    """Abstract base for git hosting providers (GitHub, GitLab, Bitbucket…)."""

    @abstractmethod
    def list_repos(self) -> list[RemoteRepo]:
        """Return all repos accessible to the authenticated user."""
        ...

    @abstractmethod
    def list_branches(self, repo: RemoteRepo) -> list[str]:
        """Return branch names for the given remote repo."""
        ...


class GitHubProvider(Provider):
    """GitHub provider — uses the `gh` CLI so no token management needed."""

    def list_repos(self) -> list[RemoteRepo]:
        result = subprocess.run(
            [
                "gh",
                "repo",
                "list",
                "--limit",
                "1000",
                "--json",
                "name,url,sshUrl,defaultBranchRef,isArchived",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(f"[red]gh error:[/red] {result.stderr.strip()}")
            raise typer.Exit(code=1)

        import json

        repos = []
        for item in json.loads(result.stdout):
            default_branch = (item.get("defaultBranchRef") or {}).get("name", "main")
            repos.append(
                RemoteRepo(
                    name=item["name"],
                    https_url=item["url"],
                    ssh_url=item["sshUrl"],
                    default_branch=default_branch,
                    is_archived=item.get("isArchived", False),
                )
            )
        return repos

    def list_branches(self, repo: RemoteRepo) -> list[str]:
        result = subprocess.run(
            ["gh", "repo", "view", repo.name, "--json", "refs"],
            capture_output=True,
            text=True,
        )
        # Fallback: gh api
        if result.returncode != 0 or not result.stdout.strip():
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"repos/{{owner}}/{repo.name}/branches",
                    "--jq",
                    ".[].name",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return []
            return result.stdout.strip().splitlines()

        import json

        data = json.loads(result.stdout)
        return [r["name"] for r in data.get("refs", [])]


class BitbucketServerProvider(Provider):
    """Bitbucket Server (on-prem) provider — uses REST API v1.0.

    Configuration via environment variables:
        BITBUCKET_URL     — Base URL of the Bitbucket Server instance
                            (e.g. https://bitbucket.yourcompany.com)
        BITBUCKET_TOKEN   — Personal access token for authentication
        BITBUCKET_PROJECT — Project key to list repos from (e.g. "CBTECH")
    """

    def __init__(self) -> None:
        self.base_url = os.environ.get("BITBUCKET_URL", "").rstrip("/")
        self.token = os.environ.get("BITBUCKET_TOKEN", "")
        self.project = os.environ.get("BITBUCKET_PROJECT", "")

        missing: list[str] = []
        if not self.base_url:
            missing.append("BITBUCKET_URL")
        if not self.project:
            missing.append("BITBUCKET_PROJECT")
        if not self.token:
            missing.append("BITBUCKET_TOKEN")
        if missing:
            console.print(
                f"[red]Missing required environment variable(s): {', '.join(missing)}[/red]"
            )
            raise typer.Exit(code=1)

    def _get(self, path: str, params: dict[str, str | int] | None = None) -> dict:
        """Make an authenticated GET request to the Bitbucket Server REST API."""
        url = f"{self.base_url}/rest/api/1.0{path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers, params=params or {}, timeout=30)
        if response.status_code != 200:
            console.print(
                f"[red]Bitbucket API error ({response.status_code}):[/red] "
                f"{response.text[:200]}"
            )
            raise typer.Exit(code=1)
        return response.json()

    def _get_paginated(self, path: str) -> list[dict]:
        """Fetch all pages from a paginated Bitbucket Server endpoint."""
        results: list[dict] = []
        start = 0
        while True:
            data = self._get(path, {"start": start, "limit": 100})
            results.extend(data.get("values", []))
            if data.get("isLastPage", True):
                break
            start = data["nextPageStart"]
        return results

    def list_repos(self) -> list[RemoteRepo]:
        items = self._get_paginated(f"/projects/{self.project}/repos")
        repos: list[RemoteRepo] = []
        for item in items:
            clone_links = {
                link["name"]: link["href"]
                for link in item.get("links", {}).get("clone", [])
            }
            # Default branch requires a separate call on some Bitbucket versions;
            # fall back to the top-level metadata if present.
            default_branch_info = item.get("defaultBranch")
            if isinstance(default_branch_info, dict):
                default_branch = default_branch_info.get("displayId", "master")
            elif isinstance(default_branch_info, str):
                default_branch = default_branch_info
            else:
                default_branch = "master"

            repos.append(
                RemoteRepo(
                    name=item["slug"],
                    https_url=clone_links.get("http", ""),
                    ssh_url=clone_links.get("ssh", ""),
                    default_branch=default_branch,
                    is_archived=item.get("archived", False),
                )
            )
        return repos

    def list_branches(self, repo: RemoteRepo) -> list[str]:
        items = self._get_paginated(
            f"/projects/{self.project}/repos/{repo.name}/branches"
        )
        return [item["displayId"] for item in items]


# ---------------------------------------------------------------------------
# Provider registry — add new providers here
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, type[Provider]] = {
    "github": GitHubProvider,
    "bitbucket": BitbucketServerProvider,
}

ModeOpt = typer.Option(
    RepoMode.active,
    "--mode",
    "-m",
    help="Filter repos by status (active, archived, all)",
)


def get_provider(provider_name: str) -> Provider:
    cls = PROVIDERS.get(provider_name.lower())
    if cls is None:
        console.print(
            f"[red]Unknown provider '{provider_name}'. Available: {', '.join(PROVIDERS)}[/red]"
        )
        raise typer.Exit(code=1)
    return cls()


# ---------------------------------------------------------------------------
# Local repo discovery
# ---------------------------------------------------------------------------


def find_local_repos(root: Path) -> list[LocalRepo]:
    """Return immediate subdirectories of root that are git repos."""
    repos = []
    for candidate in sorted(root.iterdir()):
        if candidate.is_dir() and (candidate / ".git").exists():
            repos.append(LocalRepo(candidate))
    return repos


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("list-local")
def list_local(
    compact: bool = typer.Option(
        False,
        "--compact",
        "-c",
        help="Show only repos with at least one non-zero value.",
    ),
) -> None:
    """List all local git repositories."""
    repos = find_local_repos(state.root)

    table = Table(title="Local repositories")
    table.add_column("Name", style="bright_cyan", header_style="white")
    table.add_column("Branch", style="bright_green", header_style="white")
    table.add_column(
        "Unpushed", style="bright_white", header_style="white", justify="right"
    )
    table.add_column(
        "Unpulled", style="bright_white", header_style="white", justify="right"
    )
    table.add_column(
        "Staged", style="bright_white", header_style="white", justify="right"
    )
    table.add_column(
        "Unstaged", style="bright_white", header_style="white", justify="right"
    )
    table.add_column(
        "Untracked", style="bright_white", header_style="white", justify="right"
    )
    table.add_column(
        "Stashes", style="bright_white", header_style="white", justify="right"
    )

    for repo in repos:
        repo.fetch()
        branch = repo.current_branch()
        unpushed = repo.unpushed_commits(branch)
        unpulled = repo.unpulled_commits(branch)
        staged = repo.staged_files()
        unstaged = repo.unstaged_files()
        untracked = repo.untracked_files()
        stashes = len(repo.stashes())
        if compact and not any(
            [unpushed, unpulled, staged, unstaged, untracked, stashes]
        ):
            continue
        has_activity = any([unpushed, unpulled, staged, unstaged, untracked, stashes])
        table.add_row(
            repo.name + ("[white]*[/white]" if has_activity else ""),
            branch,
            str(unpushed) if unpushed else "-",
            str(unpulled) if unpulled else "-",
            str(staged) if staged else "-",
            str(unstaged) if unstaged else "-",
            str(untracked) if untracked else "-",
            str(stashes) if stashes else "-",
        )

    console.print(table)


@app.command("list-remote")
def list_remote(
    mode: RepoMode = ModeOpt,
) -> None:
    """List all remote repositories for a provider."""
    prov = get_provider(state.provider)
    repos = sorted(prov.list_repos(), key=lambda r: r.name)

    if mode == RepoMode.active:
        repos = [r for r in repos if not r.is_archived]
    elif mode == RepoMode.archived:
        repos = [r for r in repos if r.is_archived]

    table = Table(title=f"Remote repositories ({state.provider})")
    table.add_column("Name", style="bright_cyan", header_style="white")
    table.add_column("Default branch", style="bright_green", header_style="white")
    table.add_column("URL", style="bright_white", header_style="white")
    table.add_column("Status", style="bright_yellow", header_style="white")

    for repo in repos:
        status = "archived" if repo.is_archived else "active"
        table.add_row(repo.name, repo.default_branch, repo.clone_url(), status)

    console.print(table)


_CHANGE_LABEL: dict[str, str] = {
    "A": "added",
    "M": "modified",
    "D": "deleted",
    "R": "renamed",
    "C": "copied",
    "U": "unmerged",
}


def _change_label(code: str) -> str:
    return _CHANGE_LABEL.get(code.upper(), code)


_STATUS_ORDER = {"STAGED": 0, "UNSTAGED": 1, "UNTRACKED": 2}

_STATUS_STYLE: dict[str, tuple[str, str]] = {
    "STAGED": ("green", "STAGED   "),
    "UNSTAGED": ("red", "UNSTAGED "),
    "UNTRACKED": ("yellow", "UNTRACKED"),
}


@app.command("status")
def status(
    compact: bool = typer.Option(False, "--compact", "-c", help="Hide clean repos."),
) -> None:
    """Show the status of each local repo, including stashes."""
    repos = find_local_repos(state.root)

    for repo in repos:
        entries = repo.status_entries()
        stashes = repo.stashes()
        branch = repo.current_branch()

        if compact and not entries and not stashes:
            continue

        status_color = "green" if not entries else "yellow"
        console.rule(
            f"[bold {status_color}]{repo.name}[/bold {status_color}] ({branch})",
            style="white",
        )

        if not entries and not stashes:
            console.print("  [dim]Clean[/dim]")
        else:
            sorted_entries = sorted(
                entries, key=lambda e: (_STATUS_ORDER.get(e[0], 99), e[1])
            )
            for category, filename, change_code in sorted_entries:
                color, prefix = _STATUS_STYLE[category]
                suffix = f"  ({_change_label(change_code)})" if change_code else ""
                console.print(
                    f"  [{color}]{prefix}  {escape(filename)}{suffix}[/{color}]"
                )
            for stash in stashes:
                console.print(f"  [magenta]STASH      {escape(stash)}[/magenta]")


@app.command("branches-remote")
def branches_remote() -> None:
    """List branches for each remote repository."""
    prov = get_provider(state.provider)
    repos = [r for r in prov.list_repos() if not r.is_archived]

    table = Table(title=f"Remote branches ({state.provider})")
    table.add_column("Repository", style="bright_cyan", header_style="white")
    table.add_column(
        "#Branches", style="bright_white", header_style="white", justify="right"
    )
    table.add_column("Branches", style="bright_green", header_style="white")

    for repo in repos:
        branches = prov.list_branches(repo)
        table.add_row(
            repo.name, str(len(branches)), ", ".join(branches) if branches else "-"
        )

    console.print(table)


@app.command("branches-local")
def branches_local(
    compact: bool = typer.Option(
        False,
        "--compact",
        "-c",
        help="Show only branches with at least one non-zero value.",
    ),
) -> None:
    """List branches for each local repo with unpushed/unpulled commit counts."""
    repos = find_local_repos(state.root)

    table = Table(title="Local branches")
    table.add_column("Repository", style="bright_cyan", header_style="white")
    table.add_column("Branch", style="bright_green", header_style="white")
    table.add_column(
        "Unpushed", style="bright_white", header_style="white", justify="right"
    )
    table.add_column(
        "Unpulled", style="bright_white", header_style="white", justify="right"
    )

    for repo in repos:
        repo.fetch()
        branches = repo.local_branches()
        for branch in branches:
            unpushed = repo.unpushed_commits(branch)
            unpulled = repo.unpulled_commits(branch)
            if compact and not any([unpushed, unpulled]):
                continue
            table.add_row(
                repo.name,
                branch,
                str(unpushed) if unpushed else "-",
                str(unpulled) if unpulled else "-",
            )

    console.print(table)


@app.command("sync")
def sync(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Print what would happen without doing it."
    ),
) -> None:
    """Sync local repos with remote: clone missing, pull existing, delete gone."""
    prov = get_provider(state.provider)

    console.print(f"[bold]Fetching remote repo list from {state.provider}…[/bold]")
    remote_repos = prov.list_repos()
    remote_names = {r.name: r for r in remote_repos}

    local_repos = find_local_repos(state.root)
    local_names = {r.name: r for r in local_repos}

    to_clone = sorted(
        [
            r
            for name, r in remote_names.items()
            if name not in local_names and not r.is_archived
        ],
        key=lambda r: r.name,
    )
    to_pull = sorted(
        [r for name, r in local_names.items() if name in remote_names],
        key=lambda r: r.name,
    )
    to_delete = sorted(
        [r for name, r in local_names.items() if name not in remote_names],
        key=lambda r: r.name,
    )

    # --- 1. Clone missing repos -------------------------------------------
    if to_clone:
        console.rule("[bold green]Clone missing repos[/bold green]")
        for remote in to_clone:
            dest = state.root / remote.name
            url = remote.clone_url()
            if dry_run:
                console.print(f"  [dim]Would clone[/dim] {url} → {dest}")
            else:
                console.print(f"  Cloning [cyan]{remote.name}[/cyan]…")
                result = subprocess.run(
                    ["git", "clone", url, str(dest)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    console.print("    [green]✓ Cloned[/green]")
                else:
                    console.print(f"    [red]✗ Failed:[/red] {result.stderr.strip()}")
    else:
        console.print("[dim]No missing repos to clone.[/dim]")

    # --- 2. Pull existing repos -------------------------------------------
    if to_pull:
        console.rule("[bold cyan]Pull existing repos[/bold cyan]")
        for local in to_pull:
            if dry_run:
                console.print(f"  [dim]Would pull[/dim] {local.name}")
            else:
                console.print(f"  Pulling [cyan]{local.name}[/cyan]…")
                local.fetch()
                result = local.pull()
                if result.returncode == 0:
                    msg = (
                        result.stdout.strip().splitlines()[0]
                        if result.stdout.strip()
                        else "Already up to date."
                    )
                    console.print(f"    [green]✓ {msg}[/green]")
                else:
                    console.print(
                        f"    [yellow]⚠ {result.stderr.strip() or result.stdout.strip()}[/yellow]"
                    )
    else:
        console.print("[dim]No existing repos to pull.[/dim]")

    # --- 3. Delete repos no longer on remote ------------------------------
    if to_delete:
        console.rule("[bold red]Delete repos no longer on remote[/bold red]")
        for local in to_delete:
            dirty = local.has_uncommitted_changes()
            stashes = local.stashes()

            if dirty or stashes:
                warnings = []
                if dirty:
                    warnings.append("uncommitted changes")
                if stashes:
                    warnings.append(f"{len(stashes)} stash(es)")
                console.print(
                    f"  [yellow]Skipping[/yellow] [cyan]{local.name}[/cyan] — has {' and '.join(warnings)}."
                )
                continue

            if dry_run:
                console.print(f"  [dim]Would delete[/dim] {local.path}")
            else:
                confirmed = Confirm.ask(
                    f"  Delete [cyan]{local.name}[/cyan] ({local.path})?"
                )
                if confirmed:
                    import shutil

                    shutil.rmtree(local.path)
                    console.print(f"    [red]✗ Deleted[/red] {local.path}")
                else:
                    console.print("    Skipped.")
    else:
        console.print("[dim]No repos to delete.[/dim]")


if __name__ == "__main__":
    app()
