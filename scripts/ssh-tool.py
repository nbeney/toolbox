#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "rich>=14.0.0",
#   "typer>=0.26.7",
# ]
# ///

"""
SSH Multi-Tool

Execute commands on multiple remote hosts via SSH, with support for
immediate mode (one-shot) and REPL mode (interactive session).
"""

from __future__ import annotations

import asyncio
import fnmatch
import ipaddress
import readline
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import typer
import yaml
from rich.console import Console


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class ConfigError(Exception):
    """Raised for configuration-related errors (invalid TOML, missing references, cycles)."""

    pass


class ValidationError(Exception):
    """Raised for input validation errors (invalid hostname, port out of range, etc.)."""

    pass


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class HostDefinition:
    """A single host's connection parameters."""

    name: str  # unique identifier within config
    hostname: str  # actual hostname or IP
    user: str | None = None  # SSH username override
    port: int = 22  # SSH port
    identity_file: str | None = None  # path to SSH key


@dataclass
class HostGroup:
    """A named collection of host refs and nested group refs."""

    name: str
    hosts: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)


@dataclass
class Config:
    """Parsed configuration."""

    hosts: dict[str, HostDefinition] = field(default_factory=dict)
    groups: dict[str, HostGroup] = field(default_factory=dict)


@dataclass
class CommandResult:
    """Result from executing a command on a single host."""

    host: HostDefinition
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False
    error: str | None = None  # connection error message


# ---------------------------------------------------------------------------
# Host Validation
# ---------------------------------------------------------------------------

# RFC 1123 label pattern: 1-63 alphanumeric chars and hyphens, no leading/trailing hyphens
_HOSTNAME_LABEL_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")


def validate_hostname(s: str) -> bool:
    """Validate a hostname per RFC 1123.

    Rules:
    - Total length <= 253 characters
    - Split by dots into labels
    - Each label: 1-63 characters, alphanumeric and hyphens only
    - No leading or trailing hyphens in labels
    """
    if not s or len(s) > 253:
        return False

    # Remove trailing dot (FQDN notation)
    if s.endswith("."):
        s = s[:-1]

    if not s:
        return False

    labels = s.split(".")
    for label in labels:
        if not label or len(label) > 63:
            return False
        if not _HOSTNAME_LABEL_RE.match(label):
            return False

    return True


def validate_ipv4(s: str) -> bool:
    """Validate an IPv4 address string."""
    try:
        ipaddress.IPv4Address(s)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def validate_ipv6(s: str) -> bool:
    """Validate an IPv6 address string."""
    try:
        ipaddress.IPv6Address(s)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def validate_host_entry(s: str) -> bool:
    """Validate a host entry as a valid hostname, IPv4, or IPv6 address."""
    return validate_hostname(s) or validate_ipv4(s) or validate_ipv6(s)


# ---------------------------------------------------------------------------
# Range Validation
# ---------------------------------------------------------------------------


def validate_port(port: int) -> bool:
    """Validate that a port number is within the valid range [1, 65535]."""
    return 1 <= port <= 65535


def validate_connection_timeout(timeout: int) -> bool:
    """Validate that a connection timeout is within the valid range [1, 300]."""
    return 1 <= timeout <= 300


# ---------------------------------------------------------------------------
# Host File Parsing
# ---------------------------------------------------------------------------

_MAX_HOST_FILE_ENTRIES = 10_000


def parse_host_file(path: Path) -> list[str]:
    """Read a host file and return a list of validated host entries.

    Reads the file at the given path, strips blank and whitespace-only lines,
    validates each remaining entry, and returns the list of valid hosts.

    Raises:
        ValidationError: If the file cannot be read, contains invalid entries,
            or exceeds the maximum entry limit.
    """
    try:
        content = path.read_text()
    except FileNotFoundError:
        raise ValidationError(f"host file '{path}': No such file or directory")
    except OSError as e:
        raise ValidationError(f"host file '{path}': {e.strerror}")

    entries: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not validate_host_entry(stripped):
            raise ValidationError(
                f"invalid host entry '{stripped}': does not match hostname, IPv4, or IPv6 format"
            )
        entries.append(stripped)

    if len(entries) > _MAX_HOST_FILE_ENTRIES:
        raise ValidationError(
            f"host file '{path}': exceeds maximum of {_MAX_HOST_FILE_ENTRIES} entries"
        )

    return entries


# ---------------------------------------------------------------------------
# Host Merge
# ---------------------------------------------------------------------------


def merge_hosts(cli_hosts: list[str], file_hosts: list[str]) -> list[str]:
    """Merge CLI hosts and file hosts into a single deduplicated list.

    Concatenates cli_hosts + file_hosts and deduplicates case-insensitively,
    preserving the first occurrence order.
    """
    seen: set[str] = set()
    result: list[str] = []
    for host in cli_hosts + file_hosts:
        key = host.lower()
        if key not in seen:
            seen.add(key)
            result.append(host)
    return result


# ---------------------------------------------------------------------------
# Configuration Loading
# ---------------------------------------------------------------------------


def load_config(path: Path) -> Config:
    """Parse a YAML configuration file and return a validated Config object.

    The YAML file is expected to have:
    - hosts.<name> mappings with at least a 'hostname' field
    - groups.<name> mappings with a 'hosts' list and optional 'groups' list

    Raises:
        ConfigError: If the file cannot be read, is not valid YAML, or contains
            invalid host definitions (missing hostname, invalid port).
    """
    try:
        content = path.read_text()
    except FileNotFoundError:
        raise ConfigError(f"config file '{path}': No such file or directory")
    except OSError as e:
        raise ConfigError(f"config file '{path}': {e.strerror}")

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ConfigError(f"config file '{path}': invalid YAML: {e}")

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ConfigError(f"config file '{path}': top-level must be a mapping")

    hosts: dict[str, HostDefinition] = {}
    groups: dict[str, HostGroup] = {}

    # Parse host definitions
    raw_hosts = data.get("hosts", {})
    if not isinstance(raw_hosts, dict):
        raise ConfigError(f"config file '{path}': 'hosts' must be a mapping")

    for name, host_data in raw_hosts.items():
        if not isinstance(host_data, dict):
            raise ConfigError(
                f"config file '{path}': host '{name}' must be a mapping"
            )

        # Validate required field: hostname
        hostname = host_data.get("hostname")
        if not hostname:
            raise ConfigError(
                f"config file '{path}': host '{name}' is missing required field 'hostname'"
            )

        # Validate port if provided
        port = host_data.get("port", 22)
        if not isinstance(port, int):
            raise ConfigError(
                f"config file '{path}': host '{name}' has invalid port: must be an integer"
            )
        if not validate_port(port):
            raise ConfigError(
                f"config file '{path}': host '{name}' has invalid port {port}: must be in range [1, 65535]"
            )

        hosts[name] = HostDefinition(
            name=name,
            hostname=str(hostname),
            user=host_data.get("user"),
            port=port,
            identity_file=host_data.get("identity_file"),
        )

    # Parse group definitions
    raw_groups = data.get("groups", {})
    if not isinstance(raw_groups, dict):
        raise ConfigError(f"config file '{path}': 'groups' must be a mapping")

    for name, group_data in raw_groups.items():
        if not isinstance(group_data, dict):
            raise ConfigError(
                f"config file '{path}': group '{name}' must be a mapping"
            )

        group_hosts = group_data.get("hosts", [])
        if not isinstance(group_hosts, list):
            raise ConfigError(
                f"config file '{path}': group '{name}' 'hosts' must be a list"
            )

        group_groups = group_data.get("groups", [])
        if not isinstance(group_groups, list):
            raise ConfigError(
                f"config file '{path}': group '{name}' 'groups' must be a list"
            )

        groups[name] = HostGroup(
            name=name,
            hosts=[str(h) for h in group_hosts],
            groups=[str(g) for g in group_groups],
        )

    return Config(hosts=hosts, groups=groups)


def resolve_group(
    config: Config, group_name: str, seen: set[str] | None = None
) -> list[HostDefinition]:
    """Recursively resolve a group to a flat list of HostDefinitions.

    Detects circular references and undefined host/group references.

    Args:
        config: The parsed configuration.
        group_name: The name of the group to resolve.
        seen: Set of group names already visited (for cycle detection).

    Raises:
        ConfigError: If the group references an undefined host/group or if a
            circular reference is detected.
    """
    if seen is None:
        seen = set()

    group_key = group_name.lower()
    if group_key in seen:
        cycle_path = " -> ".join(sorted(seen)) + " -> " + group_name
        raise ConfigError(f"config group cycle detected: {cycle_path}")

    # Find the group (case-sensitive lookup)
    if group_name not in config.groups:
        raise ConfigError(
            f"config group '{group_name}': references undefined group '{group_name}'"
        )

    seen = seen | {group_key}
    group = config.groups[group_name]
    result: list[HostDefinition] = []

    # Resolve direct host references (supports glob patterns)
    for host_ref in group.hosts:
        if any(c in host_ref for c in "*?["):
            matched = [
                config.hosts[name]
                for name in sorted(config.hosts.keys())
                if fnmatch.fnmatchcase(name, host_ref)
            ]
            if not matched:
                raise ConfigError(
                    f"config group '{group_name}': host pattern '{host_ref}' matched no hosts"
                )
            result.extend(matched)
        else:
            if host_ref not in config.hosts:
                raise ConfigError(
                    f"config group '{group_name}': references undefined host '{host_ref}'"
                )
            result.append(config.hosts[host_ref])

    # Resolve nested group references
    for nested_group_ref in group.groups:
        nested_hosts = resolve_group(config, nested_group_ref, seen)
        result.extend(nested_hosts)

    # Deduplicate by name (case-insensitive), keeping first occurrence
    seen_names: set[str] = set()
    deduplicated: list[HostDefinition] = []
    for host in result:
        key = host.name.lower()
        if key not in seen_names:
            seen_names.add(key)
            deduplicated.append(host)

    return deduplicated


# ---------------------------------------------------------------------------
# Host Registry
# ---------------------------------------------------------------------------


class HostRegistry:
    """Manages the final resolved host list from all sources."""

    def __init__(self) -> None:
        self.hosts: list[HostDefinition] = []

    def add_from_cli(
        self,
        hostnames: list[str],
        user: str | None,
        port: int,
        identity_file: str | None,
    ) -> None:
        """Add hosts from CLI-provided hostnames.

        Creates HostDefinition objects from the given hostnames, using
        the hostname as the name identifier.

        Args:
            hostnames: List of hostnames/IPs from CLI options.
            user: SSH username override (applied to all CLI hosts).
            port: SSH port (applied to all CLI hosts).
            identity_file: Path to SSH key (applied to all CLI hosts).
        """
        for hostname in hostnames:
            self.hosts.append(
                HostDefinition(
                    name=hostname,
                    hostname=hostname,
                    user=user,
                    port=port,
                    identity_file=identity_file,
                )
            )

    def add_from_config(self, config: Config, group_names: list[str]) -> None:
        """Add hosts from TOML config groups.

        Resolves the specified groups via `resolve_group` and adds
        the resulting hosts to the registry.

        Args:
            config: The parsed configuration.
            group_names: List of group names to resolve and add.
        """
        for group_name in group_names:
            resolved = resolve_group(config, group_name)
            self.hosts.extend(resolved)

    def deduplicate(self) -> None:
        """Remove duplicate entries by name (case-insensitive), keeping first occurrence."""
        seen: set[str] = set()
        deduplicated: list[HostDefinition] = []
        for host in self.hosts:
            key = host.name.lower()
            if key not in seen:
                seen.add(key)
                deduplicated.append(host)
        self.hosts = deduplicated

    def all_hosts(self) -> list[HostDefinition]:
        """Return the final flat host list, sorted alphabetically by name."""
        return sorted(self.hosts, key=lambda h: h.name.lower())


def resolve_group(
    config: Config, group_name: str, seen: list[str] | None = None
) -> list[HostDefinition]:
    """Recursively resolve a group to a flat, deduplicated list of HostDefinitions.

    Resolves all host references and nested group references within the named group.
    Detects circular group references and undefined host/group references.

    Args:
        config: The parsed configuration containing hosts and groups.
        group_name: The name of the group to resolve.
        seen: List of group names already visited in this resolution path (for cycle detection).

    Returns:
        A list of HostDefinition objects, deduplicated case-insensitively by name,
        preserving first-occurrence order.

    Raises:
        ConfigError: If the group name is not defined, references an undefined host or group,
            or a circular reference is detected.
    """
    if seen is None:
        seen = []

    # Cycle detection
    if group_name in seen:
        cycle_path = " -> ".join(seen) + " -> " + group_name
        raise ConfigError(f"config group cycle detected: {cycle_path}")

    # Undefined group check
    if group_name not in config.groups:
        raise ConfigError(
            f"config group references undefined group '{group_name}'"
        )

    seen = seen + [group_name]
    group = config.groups[group_name]
    result: list[HostDefinition] = []

    # Resolve direct host references (supports glob patterns)
    for host_ref in group.hosts:
        if any(c in host_ref for c in "*?["):
            # Glob pattern: match against all host definition names
            matched = [
                config.hosts[name]
                for name in sorted(config.hosts.keys())
                if fnmatch.fnmatchcase(name, host_ref)
            ]
            if not matched:
                raise ConfigError(
                    f"config group '{group_name}': host pattern '{host_ref}' matched no hosts"
                )
            result.extend(matched)
        else:
            # Literal host name
            if host_ref not in config.hosts:
                raise ConfigError(
                    f"config group '{group_name}': references undefined host '{host_ref}'"
                )
            result.append(config.hosts[host_ref])

    # Resolve nested group references
    for nested_group_name in group.groups:
        nested_hosts = resolve_group(config, nested_group_name, seen)
        result.extend(nested_hosts)

    # Deduplicate case-insensitively by host definition name, keeping first occurrence
    seen_names: set[str] = set()
    deduped: list[HostDefinition] = []
    for host_def in result:
        key = host_def.name.lower()
        if key not in seen_names:
            seen_names.add(key)
            deduped.append(host_def)

    return deduped


# ---------------------------------------------------------------------------
# SSH Command Construction
# ---------------------------------------------------------------------------


def build_ssh_args(host: HostDefinition, connection_timeout: float) -> list[str]:
    """Build the ssh command arguments list.

    Constructs the full argument list for invoking the system ssh binary,
    including connection options, port, identity file, and user@host target.

    Args:
        host: The host definition containing connection parameters.
        connection_timeout: SSH connection timeout in seconds (converted to int).

    Returns:
        A list of strings suitable for subprocess invocation, e.g.:
        ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes', '-p', '2222',
         '-i', '/path/key', 'user@host']
    """
    args: list[str] = ["ssh"]

    # Always include ConnectTimeout (convert float to int)
    args.extend(["-o", f"ConnectTimeout={int(connection_timeout)}"])

    # Always include BatchMode=yes for non-interactive behavior
    args.extend(["-o", "BatchMode=yes"])

    # Accept new host keys automatically (reject changed ones)
    args.extend(["-o", "StrictHostKeyChecking=accept-new"])

    # Include port only if not the default
    if host.port != 22:
        args.extend(["-p", str(host.port)])

    # Include identity file if specified
    if host.identity_file:
        args.extend(["-i", host.identity_file])

    # Build the target: user@hostname if user is set, otherwise just hostname
    if host.user:
        args.append(f"{host.user}@{host.hostname}")
    else:
        args.append(host.hostname)

    return args


def build_remote_command(command: str, working_dir: str | None = None) -> str:
    """Wrap command with cd prefix if working_dir is set.

    Args:
        command: The command string to execute on the remote host.
        working_dir: Optional working directory to cd into before executing.

    Returns:
        'cd /some/dir && command' when working_dir is set, or just 'command'.
    """
    if working_dir:
        return f"cd {working_dir} && {command}"
    return command


# ---------------------------------------------------------------------------
# SSH Execution
# ---------------------------------------------------------------------------


async def run_command_on_host(
    host: HostDefinition,
    command: str,
    working_dir: str | None = None,
    timeout: float = 30.0,
    connection_timeout: float = 10.0,
) -> CommandResult:
    """Execute a command on a single host via ssh subprocess.

    Builds the full SSH command using `build_ssh_args` and `build_remote_command`,
    then runs it asynchronously. Handles timeouts and connection failures gracefully.

    Args:
        host: The host definition containing connection parameters.
        command: The command string to execute on the remote host.
        working_dir: Optional working directory to cd into before executing.
        timeout: Maximum time in seconds to wait for command completion.
        connection_timeout: SSH connection timeout in seconds.

    Returns:
        A CommandResult with stdout, stderr, exit_code, and error/timeout info.
    """
    ssh_args = build_ssh_args(host, connection_timeout)
    remote_cmd = build_remote_command(command, working_dir)

    try:
        process = await asyncio.create_subprocess_exec(
            *ssh_args,
            remote_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as e:
        return CommandResult(
            host=host,
            stdout="",
            stderr="",
            exit_code=1,
            error=str(e),
        )

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        # Kill the process on timeout
        try:
            process.kill()
        except ProcessLookupError:
            pass
        # Wait for the process to be reaped
        await process.wait()
        return CommandResult(
            host=host,
            stdout="",
            stderr="",
            exit_code=1,
            timed_out=True,
        )

    return CommandResult(
        host=host,
        stdout=stdout_bytes.decode(errors="replace"),
        stderr=stderr_bytes.decode(errors="replace"),
        exit_code=process.returncode if process.returncode is not None else 1,
    )


async def run_command_on_all(
    hosts: list[HostDefinition],
    command: str,
    working_dirs: dict[str, str] | None = None,
    timeout: float = 30.0,
    connection_timeout: float = 10.0,
    sequential: bool = False,
) -> list[CommandResult]:
    """Execute a command on all hosts (concurrently by default).

    Args:
        hosts: List of host definitions to execute the command on.
        command: The command string to execute on each remote host.
        working_dirs: Optional mapping of host names to their working directory.
        timeout: Maximum time in seconds to wait for each command.
        connection_timeout: SSH connection timeout in seconds.
        sequential: If True, execute on hosts one at a time; otherwise concurrently.

    Returns:
        A list of CommandResult objects, one per host, in the same order as hosts.
    """
    if sequential:
        results: list[CommandResult] = []
        for host in hosts:
            working_dir = working_dirs.get(host.name) if working_dirs else None
            result = await run_command_on_host(
                host, command, working_dir, timeout, connection_timeout
            )
            results.append(result)
        return results
    else:
        tasks = [
            run_command_on_host(
                host,
                command,
                working_dirs.get(host.name) if working_dirs else None,
                timeout,
                connection_timeout,
            )
            for host in hosts
        ]
        return list(await asyncio.gather(*tasks))


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------


class OutputFormatter:
    """Formats command results for display.

    Supports two modes:
    - TTY mode: Rich-formatted block output with bold cyan host headers,
      red ERR: prefixes for stderr, and yellow exit code indicators.
    - Piped mode: Plain prefixed output suitable for grep/filtering,
      with [host] prefix on stdout lines and [host] ERR: on stderr lines.

    The --color option controls colorization:
    - "auto": colorize only when stdout is a TTY
    - "always": colorize regardless of TTY
    - "never": no colorization regardless of TTY
    """

    def __init__(
        self,
        color: str = "auto",
        is_tty: bool | None = None,
        file: object | None = None,
    ) -> None:
        """Initialize the OutputFormatter.

        Args:
            color: Color mode — "always", "never", or "auto".
            is_tty: Override TTY detection (for testing). If None, uses sys.stdout.isatty().
            file: Override output file (for testing). If None, uses sys.stdout.
        """
        self._color = color

        # Determine if we're in TTY mode
        if is_tty is not None:
            self._is_tty = is_tty
        else:
            self._is_tty = sys.stdout.isatty()

        # Determine if color should be enabled
        if color == "always":
            force_terminal = True
        elif color == "never":
            force_terminal = False
        else:  # auto
            force_terminal = None  # let Rich auto-detect

        # Create the Rich Console
        self._console = Console(
            file=file if file is not None else sys.stdout,
            force_terminal=force_terminal,
            no_color=(color == "never"),
            highlight=False,
        )

    @property
    def is_tty(self) -> bool:
        """Whether output is in TTY (interactive) mode."""
        return self._is_tty

    @property
    def console(self) -> Console:
        """The Rich Console instance used for output."""
        return self._console

    def format_results(self, results: list[CommandResult]) -> None:
        """Print all results grouped by host using the appropriate mode.

        Each host's output is printed contiguously (no interleaving).
        Results are sorted alphabetically by host name.

        Args:
            results: List of CommandResult objects to format.
        """
        for result in results:
            if self._is_tty:
                self._format_tty(result)
            else:
                self._format_piped(result)

    def _format_tty(self, result: CommandResult) -> None:
        """Rich-formatted block output with host headers.

        Format:
        - Header: "--- host ---" in bold cyan
        - stdout lines printed as-is
        - stderr lines prefixed with "ERR: " in red
        - "(no output)" when both stdout and stderr are empty
        - "exited with code N" in yellow for non-zero exit codes
        """
        host_name = result.host.name

        # Print host header
        self._console.print(f"--- {host_name} ---", style="bold cyan")

        has_output = False

        # Print stdout lines
        if result.stdout:
            for line in result.stdout.splitlines():
                self._console.print(line)
                has_output = True

        # Print stderr lines with ERR: prefix
        if result.stderr:
            for line in result.stderr.splitlines():
                self._console.print(f"ERR: {line}", style="red")
                has_output = True

        # No output indicator
        if not has_output:
            self._console.print("(no output)", style="dim")

        # Non-zero exit code indicator
        if result.exit_code != 0:
            self._console.print(
                f"exited with code {result.exit_code}", style="yellow"
            )

    def _format_piped(self, result: CommandResult) -> None:
        """Plain prefixed output for piped/scripted usage.

        Format:
        - stdout lines: "[host] line"
        - stderr lines: "[host] ERR: line"
        - "(no output)": "[host] (no output)"
        - exit code: "[host] exited with code N"
        """
        host_name = result.host.name
        prefix = f"[{host_name}]"

        has_output = False

        # Print stdout lines with prefix
        if result.stdout:
            for line in result.stdout.splitlines():
                self._console.print(f"{prefix} {line}", markup=False, highlight=False)
                has_output = True

        # Print stderr lines with prefix and ERR: marker
        if result.stderr:
            for line in result.stderr.splitlines():
                self._console.print(f"{prefix} ERR: {line}", markup=False, highlight=False)
                has_output = True

        # No output indicator
        if not has_output:
            self._console.print(f"{prefix} (no output)", markup=False, highlight=False)

        # Non-zero exit code indicator
        if result.exit_code != 0:
            self._console.print(f"{prefix} exited with code {result.exit_code}", markup=False, highlight=False)


# ---------------------------------------------------------------------------
# Immediate Mode
# ---------------------------------------------------------------------------


def compute_exit_code(results: list[CommandResult]) -> int:
    """Compute the aggregated exit code from a list of command results.

    Returns 0 if all results have exit code 0, otherwise returns 1.

    Args:
        results: List of CommandResult objects from command execution.

    Returns:
        0 if every result has exit_code == 0, else 1.
    """
    if all(r.exit_code == 0 for r in results):
        return 0
    return 1


def run_immediate_mode(
    hosts: list[HostDefinition],
    command: str,
    formatter: OutputFormatter,
    timeout: float = 30.0,
    connection_timeout: float = 10.0,
    sequential: bool = False,
) -> int:
    """Execute a command on all hosts and display results (immediate mode).

    Validates that the command is non-empty, executes it on all hosts via
    `run_command_on_all`, formats and displays results via the formatter,
    and returns the aggregated exit code.

    Args:
        hosts: List of host definitions to execute the command on.
        command: The command string to execute on each remote host.
        formatter: OutputFormatter instance for displaying results.
        timeout: Maximum time in seconds to wait for each command.
        connection_timeout: SSH connection timeout in seconds.
        sequential: If True, execute on hosts one at a time; otherwise concurrently.

    Returns:
        0 if all hosts returned exit code 0, otherwise 1.

    Raises:
        ValidationError: If the command is empty or whitespace-only.
    """
    if not command or not command.strip():
        raise ValidationError("command must not be empty")

    results = asyncio.run(
        run_command_on_all(
            hosts=hosts,
            command=command,
            timeout=timeout,
            connection_timeout=connection_timeout,
            sequential=sequential,
        )
    )

    formatter.format_results(results)

    return compute_exit_code(results)


# ---------------------------------------------------------------------------
# REPL Mode
# ---------------------------------------------------------------------------


class MetaCommandHandler:
    """Dispatches and executes colon-prefixed meta-commands.

    Interprets commands like :help, :quit, :hosts, :history, :pwd, :reconnect,
    and :!<command>. Returns True from handle() if the REPL should exit.
    """

    def __init__(self, session: "ReplSession") -> None:
        self.session = session
        self.commands: dict[str, tuple[object, str]] = {
            "help": (self._cmd_help, "Show available meta-commands"),
            "quit": (self._cmd_quit, "Exit the REPL"),
            "hosts": (self._cmd_hosts, "Show hosts and connection status"),
            "history": (self._cmd_history, "Show recent command history"),
            "pwd": (self._cmd_pwd, "Show tracked working directory per host"),
            "reconnect": (self._cmd_reconnect, "Reconnect to disconnected hosts"),
        }

    def handle(self, line: str) -> bool:
        """Parse and execute a meta-command. Returns True if REPL should exit.

        Args:
            line: The full input line starting with ':'.

        Returns:
            True if the REPL should exit, False otherwise.
        """
        # Strip the leading colon
        stripped = line[1:].strip()

        # Handle :!<command> (local execution)
        if stripped.startswith("!"):
            local_cmd = stripped[1:]
            self._handle_local_exec(local_cmd)
            return False

        # Parse command name (first word)
        parts = stripped.split(None, 1)
        cmd_name = parts[0].lower() if parts else ""

        if cmd_name in self.commands:
            handler_fn, _desc = self.commands[cmd_name]
            return handler_fn()
        else:
            print(
                f"Error: unknown meta-command ':{cmd_name}'. Run :help to see available commands.",
                file=sys.stderr,
            )
            return False

    def _handle_local_exec(self, command: str) -> None:
        """Handle :!command — run locally via subprocess.

        Args:
            command: The local command string to execute.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
        except OSError as e:
            print(f"Error: local command failed: {e}", file=sys.stderr)

    def _cmd_help(self) -> bool:
        """Display all available meta-commands with descriptions."""
        print("Available meta-commands:")
        for name, (_fn, desc) in sorted(self.commands.items()):
            print(f"  :{name:<12} {desc}")
        print(f"  :!<command>  Execute command locally")
        return False

    def _cmd_quit(self) -> bool:
        """Signal REPL exit."""
        return True

    def _cmd_hosts(self) -> bool:
        """Display hosts with their connection status and current directory."""
        for host in self.session.hosts:
            status = "connected" if self.session.connected.get(host.name, False) else "disconnected"
            wd = self.session.working_dirs.get(host.name, "~")
            if self.session.connected.get(host.name, False):
                print(f"  {host.name} ({host.hostname}): {status}  cwd={wd}")
            else:
                print(f"  {host.name} ({host.hostname}): {status}")
        return False

    def _cmd_history(self) -> bool:
        """Display the last 50 history entries with line numbers."""
        history_len = readline.get_current_history_length()
        start = max(1, history_len - 49)
        for i in range(start, history_len + 1):
            item = readline.get_history_item(i)
            if item:
                print(f"  {i:4d}  {item}")
        return False

    def _cmd_pwd(self) -> bool:
        """Display tracked working directory per host."""
        for host in self.session.hosts:
            if self.session.connected.get(host.name, False):
                wd = self.session.working_dirs.get(host.name, "~")
                print(f"  {host.name}: {wd}")
            else:
                print(f"  {host.name}: (disconnected)")
        return False

    def _cmd_reconnect(self) -> bool:
        """Attempt to reconnect to all disconnected hosts."""
        disconnected = [
            h for h in self.session.hosts
            if not self.session.connected.get(h.name, False)
        ]
        if not disconnected:
            print("All hosts are connected.")
            return False

        print(f"Attempting to reconnect to {len(disconnected)} host(s)...")
        results = asyncio.run(
            run_command_on_all(
                hosts=disconnected,
                command="echo ok",
                timeout=self.session.timeout,
                connection_timeout=self.session.connection_timeout,
            )
        )
        for result in results:
            if result.exit_code == 0 and not result.error and not result.timed_out:
                self.session.connected[result.host.name] = True
                print(f"  {result.host.name}: reconnected")
            else:
                reason = _format_connection_failure(result)
                print(f"  {result.host.name}: failed ({reason})", file=sys.stderr)
        return False


class ReplSession:
    """Manages the interactive REPL session.

    Provides readline-based input with history persistence, working directory
    tracking per host, connection state management, and meta-command dispatch.
    """

    def __init__(
        self,
        hosts: list[HostDefinition],
        formatter: OutputFormatter,
        timeout: float = 30.0,
        connection_timeout: float = 10.0,
        history_file: Path | None = None,
    ) -> None:
        """Initialize the REPL session.

        Args:
            hosts: List of host definitions to connect to.
            formatter: OutputFormatter instance for displaying command results.
            timeout: Command timeout in seconds.
            connection_timeout: SSH connection timeout in seconds.
            history_file: Path to the history file. Defaults to ~/.ssh_tool_history.
        """
        self.hosts = hosts
        self.formatter = formatter
        self.timeout = timeout
        self.connection_timeout = connection_timeout
        self.working_dirs: dict[str, str] = {}  # host_name -> cwd
        self.connected: dict[str, bool] = {}  # host_name -> connected
        self.history_file = history_file or Path.home() / ".ssh_tool_history"
        self.meta_handler = MetaCommandHandler(self)

        # Initialize all hosts as not yet connected
        for host in self.hosts:
            self.connected[host.name] = False

    def run(self) -> int:
        """Main REPL loop. Returns exit code.

        Performs initial connection check, then reads commands interactively.
        Dispatches to meta-command handler or SSH execution as appropriate.
        Handles exit/quit/EOF for graceful shutdown.

        Returns:
            0 on clean exit, 1 if all hosts were unreachable.
        """
        # Load command history
        self._load_history()

        # Configure readline
        readline.set_history_length(1000)

        # Initial connection attempt
        if not self._initial_connect():
            return 1

        # Display readiness prompt
        connected_count = sum(1 for v in self.connected.values() if v)
        total_count = len(self.hosts)
        print(f"Connected to {connected_count}/{total_count} host(s). Type :help for commands.")

        try:
            while True:
                try:
                    line = input("ssh> ")
                except EOFError:
                    # Ctrl+D: graceful shutdown
                    print()  # newline after ^D
                    break

                # Empty/whitespace input: no-op
                if not line.strip():
                    continue

                stripped = line.strip()

                # Check for exit/quit commands
                if stripped in ("exit", "quit"):
                    break

                # Meta-command dispatch (colon-prefixed)
                if stripped.startswith(":"):
                    should_exit = self.meta_handler.handle(stripped)
                    if should_exit:
                        break
                    continue

                # Regular command: execute on connected hosts
                self._execute_command(stripped)

        except KeyboardInterrupt:
            print("\nInterrupted.")
        finally:
            self._save_history()

        return 0

    def _initial_connect(self) -> bool:
        """Test connectivity to all hosts. Returns False if all unreachable.

        Runs `echo ok` on each host to verify connectivity.
        Marks hosts as connected or disconnected based on results.
        Reports failures to stderr.

        Returns:
            True if at least one host is reachable, False if all failed.
        """
        start_time = time.time()
        results = asyncio.run(
            run_command_on_all(
                hosts=self.hosts,
                command="echo ok",
                timeout=self.timeout,
                connection_timeout=self.connection_timeout,
            )
        )

        for result in results:
            elapsed = time.time() - start_time
            if result.exit_code == 0 and not result.error and not result.timed_out:
                self.connected[result.host.name] = True
            else:
                self.connected[result.host.name] = False
                reason = _format_connection_failure(result)
                print(
                    f"Error: host '{result.host.name}' ({result.host.hostname}): "
                    f"{reason} ({elapsed:.1f}s)",
                    file=sys.stderr,
                )

        # Check if any host is reachable
        if not any(self.connected.values()):
            print(
                "Error: no hosts could be reached. Exiting.",
                file=sys.stderr,
            )
            return False

        return True

    def _load_history(self) -> None:
        """Load readline history from file.

        If the history file exists, attempts to read it.
        On failure (corrupt file), warns and starts with empty history.
        """
        if self.history_file.exists():
            try:
                readline.read_history_file(str(self.history_file))
            except OSError:
                print(
                    f"Warning: could not load history file '{self.history_file}'. Starting with empty history.",
                    file=sys.stderr,
                )
                readline.clear_history()

    def _save_history(self) -> None:
        """Persist readline history to file (max 1000 entries)."""
        readline.set_history_length(1000)
        try:
            readline.write_history_file(str(self.history_file))
        except OSError:
            pass  # Best-effort; don't error on save failure

    def _get_connected_hosts(self) -> list[HostDefinition]:
        """Return the list of currently connected hosts.

        Returns:
            List of HostDefinition objects for hosts marked as connected.
        """
        return [h for h in self.hosts if self.connected.get(h.name, False)]

    def _execute_command(self, command: str) -> None:
        """Execute a command on all hosts, auto-reconnecting disconnected ones.

        Before executing, attempts to reconnect any disconnected hosts.
        If reconnection succeeds, includes them in the command execution.
        Detects cd commands and handles them specially via _handle_cd.
        For all other commands, prepends cd to working directory before execution.

        Args:
            command: The command string entered by the user.
        """
        # Auto-reconnect disconnected hosts
        self._auto_reconnect()

        connected_hosts = self._get_connected_hosts()
        if not connected_hosts:
            print("Error: no connected hosts available.", file=sys.stderr)
            return

        # Detect if this is a cd command
        is_cd = self._is_cd_command(command)

        if is_cd:
            # Extract cd target
            cd_target = self._extract_cd_target(command)
            self._run_cd(cd_target, connected_hosts)
        else:
            # Regular command: run with working directory context
            results = asyncio.run(
                run_command_on_all(
                    hosts=connected_hosts,
                    command=command,
                    working_dirs=self.working_dirs,
                    timeout=self.timeout,
                    connection_timeout=self.connection_timeout,
                )
            )
            # Check for connection drops
            self._check_connection_state(results)
            self.formatter.format_results(results)

    def _auto_reconnect(self) -> None:
        """Silently attempt to reconnect any disconnected hosts.

        On success, marks the host as connected and prints a notice.
        On failure, prints a warning with the host name and reason.
        """
        disconnected = [
            h for h in self.hosts
            if not self.connected.get(h.name, False)
        ]
        if not disconnected:
            return

        results = asyncio.run(
            run_command_on_all(
                hosts=disconnected,
                command="echo ok",
                timeout=self.timeout,
                connection_timeout=self.connection_timeout,
            )
        )
        for result in results:
            if result.exit_code == 0 and not result.error and not result.timed_out:
                self.connected[result.host.name] = True
                print(
                    f"  [{result.host.name}] reconnected",
                    file=sys.stderr,
                )
            else:
                reason = _format_connection_failure(result)
                print(
                    f"  [{result.host.name}] still disconnected: {reason}",
                    file=sys.stderr,
                )

    def _is_cd_command(self, command: str) -> bool:
        """Check if a command is a cd command.

        Args:
            command: The command string to check.

        Returns:
            True if the command is a cd invocation.
        """
        stripped = command.strip()
        return stripped == "cd" or stripped.startswith("cd ") or stripped.startswith("cd\t")

    def _extract_cd_target(self, command: str) -> str:
        """Extract the target directory from a cd command.

        Args:
            command: The full cd command string.

        Returns:
            The target path, or empty string for bare 'cd' (home directory).
        """
        stripped = command.strip()
        if stripped == "cd":
            return ""
        # Remove 'cd ' prefix
        return stripped[3:].strip()

    def _run_cd(self, target: str, connected_hosts: list[HostDefinition]) -> None:
        """Execute a cd command and update working directories per host.

        Runs 'cd <target> && pwd' (or just 'cd && pwd' for home directory)
        on each host, and updates working_dirs based on the resolved path.

        Args:
            target: The cd target directory (empty string means home).
            connected_hosts: List of connected hosts to run on.
        """
        if target:
            # cd to specific directory, resolving relative to current working dir
            cd_command = f"cd {target} && pwd"
        else:
            # cd with no argument: go to home directory
            cd_command = "cd && pwd"

        results = asyncio.run(
            run_command_on_all(
                hosts=connected_hosts,
                command=cd_command,
                working_dirs=self.working_dirs,
                timeout=self.timeout,
                connection_timeout=self.connection_timeout,
            )
        )

        self._handle_cd(target, results)

    def _handle_cd(self, args: str, results: list[CommandResult]) -> None:
        """Update working_dirs based on cd command results.

        For each host, if the cd+pwd succeeded, update the tracked working
        directory to the resolved path. If it failed, retain the previous
        directory and display a warning.

        Args:
            args: The cd target argument (for display purposes).
            results: List of CommandResult from the cd+pwd execution.
        """
        for result in results:
            host_name = result.host.name
            if result.exit_code == 0 and not result.error and not result.timed_out:
                # pwd output is the resolved directory
                new_dir = result.stdout.strip()
                if new_dir:
                    self.working_dirs[host_name] = new_dir
            else:
                # cd failed: retain previous working directory, show warning
                if result.error or result.timed_out:
                    # Connection issue during cd
                    self._check_connection_state([result])
                else:
                    target_desc = args if args else "~"
                    print(
                        f"Warning: cd to '{target_desc}' failed on {host_name}",
                        file=sys.stderr,
                    )

    def _check_connection_state(self, results: list[CommandResult]) -> None:
        """Check results for connection failures and update state.

        Marks hosts as disconnected if they show connection errors.
        SSH connection failures typically manifest as exit code 255 with
        error messages in stderr (e.g., "Connection refused", "No route to host").
        Reports disconnections to stderr.

        Args:
            results: List of CommandResult to check.
        """
        _SSH_CONNECTION_ERRORS = (
            "connection refused",
            "no route to host",
            "connection timed out",
            "connection reset",
            "network is unreachable",
            "permission denied",
            "host key verification failed",
        )

        for result in results:
            is_connection_failure = (
                result.error
                or result.timed_out
                or (
                    result.exit_code == 255
                    and result.stderr
                    and any(
                        err in result.stderr.lower()
                        for err in _SSH_CONNECTION_ERRORS
                    )
                )
            )
            if is_connection_failure:
                if self.connected.get(result.host.name, False):
                    self.connected[result.host.name] = False
                    reason = _format_connection_failure(result)
                    print(
                        f"Error: host '{result.host.name}' disconnected: {reason}",
                        file=sys.stderr,
                    )


def _format_connection_failure(result: CommandResult) -> str:
    """Format a connection failure reason from a CommandResult.

    Args:
        result: The CommandResult with error information.

    Returns:
        A human-readable failure reason string.
    """
    if result.timed_out:
        return "connection timed out"
    if result.error:
        return result.error
    if result.stderr:
        return result.stderr.strip()
    return "connection failed"


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

app = typer.Typer(help="Execute commands on multiple remote hosts via SSH.")


@app.command()
def main(
    command: list[str] = typer.Argument(
        None,
        help="Command to execute on remote hosts. If omitted, enters REPL mode.",
    ),
    hosts: list[str] = typer.Option(
        [],
        "--hosts",
        "-H",
        help="Host targets (hostnames or IPs).",
    ),
    host_file: Path = typer.Option(
        None,
        "--host-file",
        "-f",
        help="File containing host list (one per line).",
    ),
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="YAML configuration file with host definitions and groups. Defaults to ~/.ssh-tool.yaml if it exists.",
    ),
    group: list[str] = typer.Option(
        [],
        "--group",
        "-g",
        help="Host group names from config to target.",
    ),
    user: str = typer.Option(
        None,
        "--user",
        "-u",
        help="SSH username.",
    ),
    identity: Path = typer.Option(
        None,
        "--identity",
        "-i",
        help="SSH identity file (private key).",
    ),
    port: int = typer.Option(
        22,
        "--port",
        "-p",
        help="SSH port.",
    ),
    timeout: float = typer.Option(
        30.0,
        "--timeout",
        "-t",
        help="Command timeout in seconds.",
    ),
    connect_timeout: float = typer.Option(
        10.0,
        "--connect-timeout",
        help="SSH connection timeout in seconds.",
    ),
    sequential: bool = typer.Option(
        False,
        "--sequential",
        "-s",
        help="Execute commands sequentially instead of concurrently.",
    ),
    color: str = typer.Option(
        "auto",
        "--color",
        help="Color mode: always, never, or auto.",
    ),
) -> None:
    """Execute commands on multiple remote hosts via SSH."""
    # Validate --color option
    if color not in ("always", "never", "auto"):
        print(
            f"Error: invalid --color value '{color}': must be always, never, or auto",
            file=sys.stderr,
        )
        raise SystemExit(1)

    # Validate port range
    if not validate_port(port):
        print(
            f"Error: invalid port {port}: must be in range [1, 65535]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    # Validate identity file if provided
    if identity is not None:
        if not identity.exists():
            print(
                f"Error: identity file '{identity}': No such file or directory",
                file=sys.stderr,
            )
            raise SystemExit(1)
        if not identity.is_file():
            print(
                f"Error: identity file '{identity}': Not a regular file",
                file=sys.stderr,
            )
            raise SystemExit(1)
        try:
            identity.open("r").close()
        except OSError as e:
            print(
                f"Error: identity file '{identity}': {e.strerror}",
                file=sys.stderr,
            )
            raise SystemExit(1)

    # Load config if provided (or use default ~/.ssh-tool.yaml)
    loaded_config: Config | None = None
    config_path = config
    if config_path is None:
        default_config = Path.home() / ".ssh-tool.yaml"
        if default_config.exists():
            config_path = default_config

    if config_path is not None:
        try:
            loaded_config = load_config(config_path)
        except ConfigError as e:
            print(f"Error: {e}", file=sys.stderr)
            raise SystemExit(1)

    # Build HostRegistry from all sources
    registry = HostRegistry()

    # Add CLI hosts
    cli_hostnames: list[str] = list(hosts)

    # Add hosts from host file
    file_hostnames: list[str] = []
    if host_file is not None:
        try:
            file_hostnames = parse_host_file(host_file)
        except ValidationError as e:
            print(f"Error: {e}", file=sys.stderr)
            raise SystemExit(1)

    # Merge and deduplicate CLI + file hosts, then add to registry
    merged = merge_hosts(cli_hostnames, file_hostnames)
    identity_str = str(identity) if identity else None
    registry.add_from_cli(merged, user=user, port=port, identity_file=identity_str)

    # Add hosts from config groups
    if group and loaded_config is not None:
        try:
            registry.add_from_config(loaded_config, group)
        except ConfigError as e:
            print(f"Error: {e}", file=sys.stderr)
            raise SystemExit(1)
    elif group and loaded_config is None:
        print(
            "Error: --group requires --config to be specified",
            file=sys.stderr,
        )
        raise SystemExit(1)

    # Deduplicate
    registry.deduplicate()

    # Validate at least one host was resolved
    resolved_hosts = registry.all_hosts()
    if not resolved_hosts:
        print(
            "Error: no hosts specified. Use --hosts, --host-file, or --config with --group.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    # Create OutputFormatter
    formatter = OutputFormatter(color=color)

    # Route to immediate mode or REPL mode
    if command:
        command_str = " ".join(command)
        exit_code = run_immediate_mode(
            hosts=resolved_hosts,
            command=command_str,
            formatter=formatter,
            timeout=timeout,
            connection_timeout=connect_timeout,
            sequential=sequential,
        )
        sys.exit(exit_code)
    else:
        session = ReplSession(
            hosts=resolved_hosts,
            formatter=formatter,
            timeout=timeout,
            connection_timeout=connect_timeout,
        )
        exit_code = session.run()
        sys.exit(exit_code)


if __name__ == "__main__":
    app()
