#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "rich>=14.0.0",
#   "typer>=0.26.7",
# ]
# ///

"""
Git Repo Manager

Manage local and remote git repositories across multiple providers.
"""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

app = typer.Typer(help="Manage local and remote git repositories.")
console = Console()


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------


class State:
    root: Path = Path.cwd()


state = State()


@app.callback()
def main(
    root: Optional[Path] = typer.Option(
        None,
        "--root",
        "-r",
        help="Local directory containing repos. Defaults to cwd.",
    ),
) -> None:
    if root is not None:
        state.root = root.expanduser()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class RemoteRepo:
    def __init__(self, name: str, clone_url: str, default_branch: str = "main"):
        self.name = name
        self.clone_url = clone_url
        self.default_branch = default_branch


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
        result = self._git("status", "--porcelain")
        return bool(result.stdout.strip())

    def status_lines(self) -> list[str]:
        result = self._git("status", "--short")
        return result.stdout.strip().splitlines()

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
                "name,sshUrl,defaultBranchRef",
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
                    clone_url=item["sshUrl"],
                    default_branch=default_branch,
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


# ---------------------------------------------------------------------------
# Provider registry — add new providers here
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, type[Provider]] = {
    "github": GitHubProvider,
}

ProviderOpt = typer.Option(
    "github", "--provider", "-p", help="Hosting provider (github, …)"
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
    compact: bool = typer.Option(False, "--compact", "-c", help="Show only repos with at least one non-zero value."),
) -> None:
    """List all local git repositories."""
    repos = find_local_repos(state.root)

    table = Table(title="Local repositories")
    table.add_column("Name", style="bright_cyan", header_style="white")
    table.add_column("Branch", style="bright_green", header_style="white")
    table.add_column("Unpushed", style="bright_white", header_style="white", justify="right")
    table.add_column("Unpulled", style="bright_white", header_style="white", justify="right")
    table.add_column("Staged", style="bright_white", header_style="white", justify="right")
    table.add_column("Unstaged", style="bright_white", header_style="white", justify="right")
    table.add_column("Untracked", style="bright_white", header_style="white", justify="right")
    table.add_column("Stashes", style="bright_white", header_style="white", justify="right")

    for repo in repos:
        repo.fetch()
        branch = repo.current_branch()
        unpushed = repo.unpushed_commits(branch)
        unpulled = repo.unpulled_commits(branch)
        staged = repo.staged_files()
        unstaged = repo.unstaged_files()
        untracked = repo.untracked_files()
        stashes = len(repo.stashes())
        if compact and not any([unpushed, unpulled, staged, unstaged, untracked, stashes]):
            continue
        table.add_row(
            repo.name,
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
    provider: str = ProviderOpt,
) -> None:
    """List all remote repositories for a provider."""
    prov = get_provider(provider)
    repos = prov.list_repos()

    table = Table(title=f"Remote repositories ({provider})")
    table.add_column("Name", style="cyan")
    table.add_column("Default branch", style="green")
    table.add_column("Clone URL", style="dim")

    for repo in repos:
        table.add_row(repo.name, repo.default_branch, repo.clone_url)

    console.print(table)


@app.command("status")
def status() -> None:
    """Show the status of each local repo, including stashes."""
    repos = find_local_repos(state.root)

    for repo in repos:
        changes = repo.status_lines()
        stashes = repo.stashes()
        branch = repo.current_branch()

        status_color = "green" if not changes else "yellow"
        console.rule(
            f"[bold {status_color}]{repo.name}[/bold {status_color}] ({branch})"
        )

        if not changes and not stashes:
            console.print("  [dim]Clean[/dim]")
        else:
            for line in changes:
                console.print(f"  {line}")
            for stash in stashes:
                console.print(f"  [magenta]{stash}[/magenta]")


@app.command("branches-remote")
def branches_remote(
    provider: str = ProviderOpt,
) -> None:
    """List branches for each remote repository."""
    prov = get_provider(provider)
    repos = prov.list_repos()

    table = Table(title=f"Remote branches ({provider})")
    table.add_column("Repository", style="cyan")
    table.add_column("Branches", style="green")

    for repo in repos:
        branches = prov.list_branches(repo)
        table.add_row(repo.name, ", ".join(branches) if branches else "[dim]—[/dim]")

    console.print(table)


@app.command("branches-local")
def branches_local() -> None:
    """List branches for each local repo with unpushed/unpulled commit counts."""
    repos = find_local_repos(state.root)

    table = Table(title="Local branches")
    table.add_column("Repository", style="bright_cyan", header_style="white")
    table.add_column("Branch", style="bright_green", header_style="white")
    table.add_column("Unpushed", style="bright_yellow", header_style="white", justify="right")
    table.add_column("Unpulled", style="bright_magenta", header_style="white", justify="right")

    for repo in repos:
        repo.fetch()
        branches = repo.local_branches()
        for branch in branches:
            unpushed = repo.unpushed_commits(branch)
            unpulled = repo.unpulled_commits(branch)
            table.add_row(
                repo.name,
                branch,
                str(unpushed) if unpushed else "-",
                str(unpulled) if unpulled else "-",
            )

    console.print(table)


@app.command("sync")
def sync(
    provider: str = ProviderOpt,
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Print what would happen without doing it."
    ),
) -> None:
    """Sync local repos with remote: clone missing, pull existing, delete gone."""
    prov = get_provider(provider)

    console.print(f"[bold]Fetching remote repo list from {provider}…[/bold]")
    remote_repos = prov.list_repos()
    remote_names = {r.name: r for r in remote_repos}

    local_repos = find_local_repos(state.root)
    local_names = {r.name: r for r in local_repos}

    to_clone = [r for name, r in remote_names.items() if name not in local_names]
    to_pull = [r for name, r in local_names.items() if name in remote_names]
    to_delete = [r for name, r in local_names.items() if name not in remote_names]

    # --- 1. Clone missing repos -------------------------------------------
    if to_clone:
        console.rule("[bold green]Clone missing repos[/bold green]")
        for remote in to_clone:
            dest = state.root / remote.name
            if dry_run:
                console.print(f"  [dim]Would clone[/dim] {remote.clone_url} → {dest}")
            else:
                console.print(f"  Cloning [cyan]{remote.name}[/cyan]…")
                result = subprocess.run(
                    ["git", "clone", remote.clone_url, str(dest)],
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
