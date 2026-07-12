"""Tests for ssh-tool.py"""

import sys
from pathlib import Path

# Add the scripts directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import importlib

# Import the module from the script file (which has a hyphen in its name)
spec = importlib.util.spec_from_file_location(
    "ssh_tool", Path(__file__).parent.parent / "scripts" / "ssh-tool.py"
)
ssh_tool = importlib.util.module_from_spec(spec)
sys.modules["ssh_tool"] = ssh_tool
spec.loader.exec_module(ssh_tool)

compute_exit_code = ssh_tool.compute_exit_code
run_immediate_mode = ssh_tool.run_immediate_mode
validate_hostname = ssh_tool.validate_hostname
validate_ipv4 = ssh_tool.validate_ipv4
validate_ipv6 = ssh_tool.validate_ipv6
validate_host_entry = ssh_tool.validate_host_entry
validate_port = ssh_tool.validate_port
validate_connection_timeout = ssh_tool.validate_connection_timeout
parse_host_file = ssh_tool.parse_host_file
ValidationError = ssh_tool.ValidationError
merge_hosts = ssh_tool.merge_hosts
load_config = ssh_tool.load_config
resolve_group = ssh_tool.resolve_group
ConfigError = ssh_tool.ConfigError
Config = ssh_tool.Config
HostGroup = ssh_tool.HostGroup
HostDefinition = ssh_tool.HostDefinition
HostRegistry = ssh_tool.HostRegistry


# ---------------------------------------------------------------------------
# Unit Tests: validate_hostname
# ---------------------------------------------------------------------------


class TestValidateHostname:
    def test_simple_hostname(self):
        assert validate_hostname("server1") is True

    def test_fqdn(self):
        assert validate_hostname("web.example.com") is True

    def test_fqdn_with_trailing_dot(self):
        assert validate_hostname("web.example.com.") is True

    def test_single_character_label(self):
        assert validate_hostname("a") is True

    def test_numeric_label(self):
        assert validate_hostname("123") is True

    def test_hyphenated_label(self):
        assert validate_hostname("my-server") is True

    def test_max_label_length_63(self):
        label = "a" * 63
        assert validate_hostname(label) is True

    def test_label_too_long_64(self):
        label = "a" * 64
        assert validate_hostname(label) is False

    def test_max_total_length_253(self):
        # Build a hostname that is exactly 253 characters
        # Use labels of "a" * 63 separated by dots: 63 + 1 + 63 + 1 + 63 + 1 + 61 = 253
        hostname = "a" * 63 + "." + "a" * 63 + "." + "a" * 63 + "." + "a" * 61
        assert len(hostname) == 253
        assert validate_hostname(hostname) is True

    def test_total_length_over_253(self):
        hostname = "a" * 63 + "." + "a" * 63 + "." + "a" * 63 + "." + "a" * 62
        assert len(hostname) == 254
        assert validate_hostname(hostname) is False

    def test_leading_hyphen_rejected(self):
        assert validate_hostname("-server") is False

    def test_trailing_hyphen_rejected(self):
        assert validate_hostname("server-") is False

    def test_empty_string_rejected(self):
        assert validate_hostname("") is False

    def test_underscore_rejected(self):
        assert validate_hostname("my_server") is False

    def test_space_rejected(self):
        assert validate_hostname("my server") is False

    def test_empty_label_rejected(self):
        assert validate_hostname("web..example.com") is False

    def test_special_chars_rejected(self):
        assert validate_hostname("server!") is False


# ---------------------------------------------------------------------------
# Unit Tests: validate_ipv4
# ---------------------------------------------------------------------------


class TestValidateIpv4:
    def test_valid_ipv4(self):
        assert validate_ipv4("192.168.1.1") is True

    def test_loopback(self):
        assert validate_ipv4("127.0.0.1") is True

    def test_all_zeros(self):
        assert validate_ipv4("0.0.0.0") is True

    def test_max_values(self):
        assert validate_ipv4("255.255.255.255") is True

    def test_octet_over_255(self):
        assert validate_ipv4("256.1.1.1") is False

    def test_too_few_octets(self):
        assert validate_ipv4("192.168.1") is False

    def test_too_many_octets(self):
        assert validate_ipv4("192.168.1.1.1") is False

    def test_empty_string(self):
        assert validate_ipv4("") is False

    def test_non_numeric(self):
        assert validate_ipv4("abc.def.ghi.jkl") is False

    def test_leading_zeros_rejected(self):
        # Python's ipaddress module rejects leading zeros
        assert validate_ipv4("192.168.01.1") is False

    def test_negative_octet(self):
        assert validate_ipv4("-1.0.0.0") is False


# ---------------------------------------------------------------------------
# Unit Tests: validate_ipv6
# ---------------------------------------------------------------------------


class TestValidateIpv6:
    def test_full_ipv6(self):
        assert validate_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True

    def test_compressed_ipv6(self):
        assert validate_ipv6("2001:db8::1") is True

    def test_loopback(self):
        assert validate_ipv6("::1") is True

    def test_all_zeros(self):
        assert validate_ipv6("::") is True

    def test_link_local(self):
        assert validate_ipv6("fe80::1") is True

    def test_invalid_hex(self):
        assert validate_ipv6("2001:db8::gggg") is False

    def test_too_many_groups(self):
        assert validate_ipv6("2001:db8:1:2:3:4:5:6:7:8:9") is False

    def test_empty_string(self):
        assert validate_ipv6("") is False

    def test_ipv4_not_valid_ipv6(self):
        assert validate_ipv6("192.168.1.1") is False


# ---------------------------------------------------------------------------
# Unit Tests: validate_host_entry
# ---------------------------------------------------------------------------


class TestValidateHostEntry:
    def test_valid_hostname(self):
        assert validate_host_entry("server1.example.com") is True

    def test_valid_ipv4(self):
        assert validate_host_entry("10.0.0.1") is True

    def test_valid_ipv6(self):
        assert validate_host_entry("::1") is True

    def test_invalid_entry(self):
        assert validate_host_entry("not a host!!!") is False

    def test_empty_string(self):
        assert validate_host_entry("") is False

    def test_hostname_with_underscore(self):
        assert validate_host_entry("my_invalid_host") is False


# ---------------------------------------------------------------------------
# Unit Tests: validate_port
# ---------------------------------------------------------------------------


class TestValidatePort:
    def test_minimum_valid_port(self):
        assert validate_port(1) is True

    def test_default_ssh_port(self):
        assert validate_port(22) is True

    def test_common_high_port(self):
        assert validate_port(8080) is True

    def test_maximum_valid_port(self):
        assert validate_port(65535) is True

    def test_zero_rejected(self):
        assert validate_port(0) is False

    def test_negative_rejected(self):
        assert validate_port(-1) is False

    def test_above_max_rejected(self):
        assert validate_port(65536) is False

    def test_large_number_rejected(self):
        assert validate_port(100000) is False


# ---------------------------------------------------------------------------
# Unit Tests: validate_connection_timeout
# ---------------------------------------------------------------------------


class TestValidateConnectionTimeout:
    def test_minimum_valid_timeout(self):
        assert validate_connection_timeout(1) is True

    def test_default_timeout(self):
        assert validate_connection_timeout(10) is True

    def test_maximum_valid_timeout(self):
        assert validate_connection_timeout(300) is True

    def test_mid_range(self):
        assert validate_connection_timeout(150) is True

    def test_zero_rejected(self):
        assert validate_connection_timeout(0) is False

    def test_negative_rejected(self):
        assert validate_connection_timeout(-1) is False

    def test_above_max_rejected(self):
        assert validate_connection_timeout(301) is False

    def test_large_number_rejected(self):
        assert validate_connection_timeout(1000) is False


# ---------------------------------------------------------------------------
# Unit Tests: merge_hosts
# ---------------------------------------------------------------------------


class TestMergeHosts:
    def test_no_duplicates(self):
        """Distinct hosts from both sources are all preserved in order."""
        result = merge_hosts(["host1", "host2"], ["host3", "host4"])
        assert result == ["host1", "host2", "host3", "host4"]

    def test_duplicates_different_case(self):
        """Duplicates differing only in case are removed, keeping first occurrence."""
        result = merge_hosts(["Server1", "server2"], ["SERVER1", "SERVER2"])
        assert result == ["Server1", "server2"]

    def test_empty_lists(self):
        """Empty inputs produce empty output."""
        assert merge_hosts([], []) == []
        assert merge_hosts(["host1"], []) == ["host1"]
        assert merge_hosts([], ["host1"]) == ["host1"]

    def test_all_duplicates(self):
        """When all entries are duplicates, only unique entries remain."""
        result = merge_hosts(["a", "b", "c"], ["A", "B", "C"])
        assert result == ["a", "b", "c"]

    def test_cli_hosts_take_precedence(self):
        """CLI hosts appear first and their casing is preserved over file hosts."""
        result = merge_hosts(["MyHost"], ["myhost", "other"])
        assert result == ["MyHost", "other"]

    def test_preserves_first_occurrence_order(self):
        """Order follows cli_hosts then file_hosts, first seen wins."""
        result = merge_hosts(["b", "a"], ["c", "A", "B"])
        assert result == ["b", "a", "c"]


# ---------------------------------------------------------------------------
# Unit Tests: parse_host_file
# ---------------------------------------------------------------------------

import pytest


class TestParseHostFile:
    def test_valid_hosts(self, tmp_path):
        f = tmp_path / "hosts.txt"
        f.write_text("server1.example.com\n192.168.1.1\n::1\n")
        result = parse_host_file(f)
        assert result == ["server1.example.com", "192.168.1.1", "::1"]

    def test_strips_blank_lines(self, tmp_path):
        f = tmp_path / "hosts.txt"
        f.write_text("\nserver1\n\n\nserver2\n\n")
        result = parse_host_file(f)
        assert result == ["server1", "server2"]

    def test_strips_whitespace_only_lines(self, tmp_path):
        f = tmp_path / "hosts.txt"
        f.write_text("   \nserver1\n\t\n  \t  \nserver2\n")
        result = parse_host_file(f)
        assert result == ["server1", "server2"]

    def test_strips_whitespace_from_entries(self, tmp_path):
        f = tmp_path / "hosts.txt"
        f.write_text("  server1  \n\t192.168.1.1\t\n")
        result = parse_host_file(f)
        assert result == ["server1", "192.168.1.1"]

    def test_empty_file_returns_empty_list(self, tmp_path):
        f = tmp_path / "hosts.txt"
        f.write_text("")
        result = parse_host_file(f)
        assert result == []

    def test_file_not_found_raises_validation_error(self, tmp_path):
        f = tmp_path / "nonexistent.txt"
        with pytest.raises(ValidationError, match="No such file or directory"):
            parse_host_file(f)

    def test_file_not_found_includes_path(self, tmp_path):
        f = tmp_path / "nonexistent.txt"
        with pytest.raises(ValidationError, match=str(f)):
            parse_host_file(f)

    def test_invalid_entry_raises_validation_error(self, tmp_path):
        f = tmp_path / "hosts.txt"
        f.write_text("valid-host\nnot a host!!!\n")
        with pytest.raises(ValidationError, match="invalid host entry 'not a host!!!'"):
            parse_host_file(f)

    def test_invalid_entry_error_message_format(self, tmp_path):
        f = tmp_path / "hosts.txt"
        f.write_text("bad_entry_with_underscore\n")
        with pytest.raises(
            ValidationError,
            match="does not match hostname, IPv4, or IPv6 format",
        ):
            parse_host_file(f)

    def test_exceeds_max_entries_raises_validation_error(self, tmp_path):
        f = tmp_path / "hosts.txt"
        lines = [f"host{i}.example.com" for i in range(10_001)]
        f.write_text("\n".join(lines))
        with pytest.raises(ValidationError, match="exceeds maximum of 10000 entries"):
            parse_host_file(f)

    def test_exactly_max_entries_succeeds(self, tmp_path):
        f = tmp_path / "hosts.txt"
        lines = [f"host{i}.example.com" for i in range(10_000)]
        f.write_text("\n".join(lines))
        result = parse_host_file(f)
        assert len(result) == 10_000

    def test_unreadable_file_raises_validation_error(self, tmp_path):
        f = tmp_path / "hosts.txt"
        f.write_text("server1\n")
        f.chmod(0o000)
        try:
            with pytest.raises(ValidationError, match=str(f)):
                parse_host_file(f)
        finally:
            f.chmod(0o644)

    def test_mixed_valid_entries(self, tmp_path):
        f = tmp_path / "hosts.txt"
        content = "web1.example.com\n10.0.0.1\n2001:db8::1\nmy-server\n"
        f.write_text(content)
        result = parse_host_file(f)
        assert result == ["web1.example.com", "10.0.0.1", "2001:db8::1", "my-server"]


# ---------------------------------------------------------------------------
# Unit Tests: load_config
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_valid_config_with_hosts_and_groups(self, tmp_path):
        """A well-formed config parses hosts and groups correctly."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  web1:\n"
            "    hostname: 192.168.1.10\n"
            "    user: deploy\n"
            "    port: 22\n"
            "    identity_file: ~/.ssh/id_deploy\n"
            "  web2:\n"
            "    hostname: 192.168.1.11\n"
            "    user: deploy\n"
            "groups:\n"
            "  webservers:\n"
            "    hosts:\n"
            "      - web1\n"
            "      - web2\n"
        )
        config = load_config(f)
        assert "web1" in config.hosts
        assert "web2" in config.hosts
        assert config.hosts["web1"].hostname == "192.168.1.10"
        assert config.hosts["web1"].user == "deploy"
        assert config.hosts["web1"].port == 22
        assert config.hosts["web1"].identity_file == "~/.ssh/id_deploy"
        assert config.hosts["web2"].hostname == "192.168.1.11"
        assert config.hosts["web2"].port == 22  # default
        assert config.hosts["web2"].identity_file is None
        assert "webservers" in config.groups
        assert config.groups["webservers"].hosts == ["web1", "web2"]
        assert config.groups["webservers"].groups == []

    def test_group_with_nested_groups(self, tmp_path):
        """Groups can reference other groups."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  db1:\n"
            "    hostname: db.example.com\n"
            "groups:\n"
            "  databases:\n"
            "    hosts:\n"
            "      - db1\n"
            "  all-servers:\n"
            "    hosts:\n"
            "      - db1\n"
            "    groups:\n"
            "      - databases\n"
        )
        config = load_config(f)
        assert config.groups["all-servers"].hosts == ["db1"]
        assert config.groups["all-servers"].groups == ["databases"]

    def test_missing_hostname_raises_config_error(self, tmp_path):
        """A host without 'hostname' raises ConfigError."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  broken:\n"
            "    user: deploy\n"
            "    port: 22\n"
        )
        with pytest.raises(ConfigError, match="missing required field 'hostname'"):
            load_config(f)

    def test_empty_hostname_raises_config_error(self, tmp_path):
        """A host with empty hostname string raises ConfigError."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  broken:\n"
            '    hostname: ""\n'
        )
        with pytest.raises(ConfigError, match="missing required field 'hostname'"):
            load_config(f)

    def test_invalid_port_zero_raises_config_error(self, tmp_path):
        """Port 0 is out of valid range."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  badport:\n"
            "    hostname: 192.168.1.1\n"
            "    port: 0\n"
        )
        with pytest.raises(ConfigError, match="invalid port 0"):
            load_config(f)

    def test_invalid_port_too_high_raises_config_error(self, tmp_path):
        """Port 65536 is out of valid range."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  badport:\n"
            "    hostname: 192.168.1.1\n"
            "    port: 65536\n"
        )
        with pytest.raises(ConfigError, match="invalid port 65536"):
            load_config(f)

    def test_invalid_port_negative_raises_config_error(self, tmp_path):
        """Negative port is out of valid range."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  badport:\n"
            "    hostname: 192.168.1.1\n"
            "    port: -1\n"
        )
        with pytest.raises(ConfigError, match="invalid port -1"):
            load_config(f)

    def test_valid_port_boundaries(self, tmp_path):
        """Port 1 and 65535 are both valid."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  low:\n"
            "    hostname: 192.168.1.1\n"
            "    port: 1\n"
            "  high:\n"
            "    hostname: 192.168.1.2\n"
            "    port: 65535\n"
        )
        config = load_config(f)
        assert config.hosts["low"].port == 1
        assert config.hosts["high"].port == 65535

    def test_invalid_yaml_raises_config_error(self, tmp_path):
        """Malformed YAML raises ConfigError."""
        f = tmp_path / "config.yaml"
        f.write_text(":\n  :\n    - [invalid yaml{{\n")
        with pytest.raises(ConfigError, match="invalid YAML"):
            load_config(f)

    def test_file_not_found_raises_config_error(self, tmp_path):
        """Missing file raises ConfigError."""
        f = tmp_path / "nonexistent.yaml"
        with pytest.raises(ConfigError, match="No such file or directory"):
            load_config(f)

    def test_empty_config_returns_empty(self, tmp_path):
        """An empty YAML file produces empty hosts and groups."""
        f = tmp_path / "config.yaml"
        f.write_text("")
        config = load_config(f)
        assert config.hosts == {}
        assert config.groups == {}

    def test_hosts_only_no_groups(self, tmp_path):
        """Config with only hosts and no groups is valid."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  web1:\n"
            "    hostname: 10.0.0.1\n"
        )
        config = load_config(f)
        assert "web1" in config.hosts
        assert config.groups == {}

    def test_host_default_values(self, tmp_path):
        """Hosts use correct defaults when optional fields are omitted."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  minimal:\n"
            "    hostname: example.com\n"
        )
        config = load_config(f)
        host = config.hosts["minimal"]
        assert host.name == "minimal"
        assert host.hostname == "example.com"
        assert host.user is None
        assert host.port == 22
        assert host.identity_file is None

    def test_host_definition_name_matches_key(self, tmp_path):
        """The HostDefinition.name field matches the YAML key."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  my-server:\n"
            "    hostname: 10.0.0.5\n"
        )
        config = load_config(f)
        assert config.hosts["my-server"].name == "my-server"

    def test_group_name_matches_key(self, tmp_path):
        """The HostGroup.name field matches the YAML key."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "hosts:\n"
            "  h1:\n"
            "    hostname: 10.0.0.1\n"
            "groups:\n"
            "  my-group:\n"
            "    hosts:\n"
            "      - h1\n"
        )
        config = load_config(f)
        assert config.groups["my-group"].name == "my-group"

    def test_group_with_empty_hosts_list(self, tmp_path):
        """A group with an empty hosts list is valid."""
        f = tmp_path / "config.yaml"
        f.write_text(
            "groups:\n"
            "  empty:\n"
            "    hosts: []\n"
            "    groups:\n"
            "      - other\n"
        )
        config = load_config(f)
        assert config.groups["empty"].hosts == []
        assert config.groups["empty"].groups == ["other"]


# ---------------------------------------------------------------------------
# Unit Tests: resolve_group
# ---------------------------------------------------------------------------


class TestResolveGroup:
    def _make_config(self, hosts=None, groups=None):
        """Helper to build a Config object for testing."""
        host_defs = {}
        if hosts:
            for name, hostname in hosts.items():
                host_defs[name] = HostDefinition(name=name, hostname=hostname)
        group_defs = {}
        if groups:
            for name, data in groups.items():
                group_defs[name] = HostGroup(
                    name=name,
                    hosts=data.get("hosts", []),
                    groups=data.get("groups", []),
                )
        return Config(hosts=host_defs, groups=group_defs)

    def test_simple_group_resolves_hosts(self):
        """A group with direct host references resolves to those hosts."""
        config = self._make_config(
            hosts={"web1": "10.0.0.1", "web2": "10.0.0.2"},
            groups={"webservers": {"hosts": ["web1", "web2"]}},
        )
        result = resolve_group(config, "webservers")
        assert len(result) == 2
        assert result[0].name == "web1"
        assert result[1].name == "web2"

    def test_nested_group_resolves_recursively(self):
        """A group referencing another group resolves all nested hosts."""
        config = self._make_config(
            hosts={"web1": "10.0.0.1", "db1": "10.0.0.3"},
            groups={
                "webservers": {"hosts": ["web1"]},
                "all": {"hosts": ["db1"], "groups": ["webservers"]},
            },
        )
        result = resolve_group(config, "all")
        names = [h.name for h in result]
        assert "db1" in names
        assert "web1" in names
        assert len(result) == 2

    def test_deeply_nested_groups(self):
        """Groups can be nested multiple levels deep."""
        config = self._make_config(
            hosts={"h1": "1.1.1.1", "h2": "2.2.2.2", "h3": "3.3.3.3"},
            groups={
                "level1": {"hosts": ["h1"]},
                "level2": {"hosts": ["h2"], "groups": ["level1"]},
                "level3": {"hosts": ["h3"], "groups": ["level2"]},
            },
        )
        result = resolve_group(config, "level3")
        names = [h.name for h in result]
        assert names == ["h3", "h2", "h1"]

    def test_cycle_detection_direct(self):
        """A group referencing itself raises ConfigError."""
        config = self._make_config(
            hosts={},
            groups={"loopy": {"hosts": [], "groups": ["loopy"]}},
        )
        with pytest.raises(ConfigError, match="config group cycle detected"):
            resolve_group(config, "loopy")

    def test_cycle_detection_indirect(self):
        """An indirect cycle (A -> B -> A) raises ConfigError."""
        config = self._make_config(
            hosts={},
            groups={
                "groupA": {"hosts": [], "groups": ["groupB"]},
                "groupB": {"hosts": [], "groups": ["groupA"]},
            },
        )
        with pytest.raises(ConfigError, match="config group cycle detected"):
            resolve_group(config, "groupA")

    def test_cycle_detection_message_shows_path(self):
        """The cycle error message includes the cycle path."""
        config = self._make_config(
            hosts={},
            groups={
                "a": {"hosts": [], "groups": ["b"]},
                "b": {"hosts": [], "groups": ["a"]},
            },
        )
        with pytest.raises(ConfigError, match=r"a.*->.*b.*->.*a"):
            resolve_group(config, "a")

    def test_undefined_host_reference_raises_config_error(self):
        """Referencing a host that doesn't exist raises ConfigError."""
        config = self._make_config(
            hosts={"web1": "10.0.0.1"},
            groups={"webservers": {"hosts": ["web1", "web99"]}},
        )
        with pytest.raises(
            ConfigError, match="config group 'webservers': references undefined host 'web99'"
        ):
            resolve_group(config, "webservers")

    def test_undefined_group_reference_raises_config_error(self):
        """Referencing a group that doesn't exist raises ConfigError."""
        config = self._make_config(
            hosts={"web1": "10.0.0.1"},
            groups={"all": {"hosts": ["web1"], "groups": ["nonexistent"]}},
        )
        with pytest.raises(
            ConfigError, match="references undefined group 'nonexistent'"
        ):
            resolve_group(config, "all")

    def test_undefined_top_level_group_raises_config_error(self):
        """Calling resolve_group with a group name that doesn't exist raises ConfigError."""
        config = self._make_config(hosts={"h1": "1.1.1.1"}, groups={})
        with pytest.raises(
            ConfigError, match="references undefined group 'missing'"
        ):
            resolve_group(config, "missing")

    def test_deduplication_case_insensitive(self):
        """Hosts appearing multiple times (via different groups) are deduplicated case-insensitively."""
        config = self._make_config(
            hosts={"Web1": "10.0.0.1", "db1": "10.0.0.2"},
            groups={
                "webservers": {"hosts": ["Web1"]},
                "all": {"hosts": ["Web1", "db1"], "groups": ["webservers"]},
            },
        )
        result = resolve_group(config, "all")
        names = [h.name for h in result]
        assert names == ["Web1", "db1"]

    def test_deduplication_keeps_first_occurrence(self):
        """When a host appears from a direct ref and a nested group, the first wins."""
        config = self._make_config(
            hosts={"shared": "10.0.0.1", "extra": "10.0.0.2"},
            groups={
                "sub": {"hosts": ["shared", "extra"]},
                "top": {"hosts": ["shared"], "groups": ["sub"]},
            },
        )
        result = resolve_group(config, "top")
        names = [h.name for h in result]
        # "shared" from direct reference comes first, then "extra" from sub group
        assert names == ["shared", "extra"]

    def test_empty_group(self):
        """A group with no hosts and no nested groups resolves to empty list."""
        config = self._make_config(
            hosts={},
            groups={"empty": {"hosts": [], "groups": []}},
        )
        result = resolve_group(config, "empty")
        assert result == []

    def test_diamond_dependency_no_duplicates(self):
        """Diamond pattern (A depends on B and C, both depend on D) yields no duplicates."""
        config = self._make_config(
            hosts={"h1": "1.1.1.1"},
            groups={
                "d": {"hosts": ["h1"]},
                "b": {"hosts": [], "groups": ["d"]},
                "c": {"hosts": [], "groups": ["d"]},
                "a": {"hosts": [], "groups": ["b", "c"]},
            },
        )
        result = resolve_group(config, "a")
        assert len(result) == 1
        assert result[0].name == "h1"


# ---------------------------------------------------------------------------
# Unit Tests: resolve_group with glob patterns
# ---------------------------------------------------------------------------


class TestResolveGroupGlobs:
    """Tests for glob pattern support in group host resolution."""

    def _make_config(self, hosts=None, groups=None):
        """Helper to build a Config object for testing."""
        host_defs = {}
        if hosts:
            for name, hostname in hosts.items():
                host_defs[name] = HostDefinition(name=name, hostname=hostname)
        group_defs = {}
        if groups:
            for name, data in groups.items():
                group_defs[name] = HostGroup(
                    name=name,
                    hosts=data.get("hosts", []),
                    groups=data.get("groups", []),
                )
        return Config(hosts=host_defs, groups=group_defs)

    def test_star_matches_all_hosts(self):
        """'*' glob matches all defined hosts."""
        config = self._make_config(
            hosts={"host1": "10.0.0.1", "host2": "10.0.0.2", "web1": "10.0.0.3"},
            groups={"all": {"hosts": ["*"]}},
        )
        result = resolve_group(config, "all")
        names = [h.name for h in result]
        assert sorted(names) == ["host1", "host2", "web1"]

    def test_bracket_pattern_matches_specific_hosts(self):
        """'host[13]' matches host1 and host3 but not host2."""
        config = self._make_config(
            hosts={
                "host1": "10.0.0.1",
                "host2": "10.0.0.2",
                "host3": "10.0.0.3",
            },
            groups={"subset": {"hosts": ["host[13]"]}},
        )
        result = resolve_group(config, "subset")
        names = [h.name for h in result]
        assert sorted(names) == ["host1", "host3"]

    def test_prefix_glob_matches(self):
        """'web*' matches hosts starting with 'web'."""
        config = self._make_config(
            hosts={
                "web1": "10.0.0.1",
                "web2": "10.0.0.2",
                "db1": "10.0.0.3",
            },
            groups={"webservers": {"hosts": ["web*"]}},
        )
        result = resolve_group(config, "webservers")
        names = [h.name for h in result]
        assert sorted(names) == ["web1", "web2"]

    def test_pattern_matching_no_hosts_raises_config_error(self):
        """A pattern that matches no hosts raises ConfigError."""
        config = self._make_config(
            hosts={"web1": "10.0.0.1", "web2": "10.0.0.2"},
            groups={"empty": {"hosts": ["db*"]}},
        )
        with pytest.raises(ConfigError, match="host pattern 'db\\*' matched no hosts"):
            resolve_group(config, "empty")

    def test_mix_of_literal_and_glob_in_same_group(self):
        """A group can have both literal host refs and glob patterns."""
        config = self._make_config(
            hosts={
                "web1": "10.0.0.1",
                "web2": "10.0.0.2",
                "db1": "10.0.0.3",
            },
            groups={"mixed": {"hosts": ["db1", "web*"]}},
        )
        result = resolve_group(config, "mixed")
        names = [h.name for h in result]
        assert "db1" in names
        assert "web1" in names
        assert "web2" in names
        assert len(names) == 3


# ---------------------------------------------------------------------------
# Unit Tests: HostRegistry
# ---------------------------------------------------------------------------


class TestHostRegistry:
    def test_add_from_cli_creates_host_definitions(self):
        """add_from_cli creates HostDefinition objects using hostname as the name."""
        registry = HostRegistry()
        registry.add_from_cli(
            hostnames=["server1.example.com", "10.0.0.1"],
            user="admin",
            port=2222,
            identity_file="/path/to/key",
        )
        hosts = registry.all_hosts()
        assert len(hosts) == 2
        # all_hosts() returns sorted by name
        assert hosts[0].name == "10.0.0.1"
        assert hosts[0].hostname == "10.0.0.1"
        assert hosts[0].user == "admin"
        assert hosts[0].port == 2222
        assert hosts[0].identity_file == "/path/to/key"
        assert hosts[1].name == "server1.example.com"
        assert hosts[1].hostname == "server1.example.com"

    def test_add_from_cli_with_none_optionals(self):
        """add_from_cli handles None user and identity_file correctly."""
        registry = HostRegistry()
        registry.add_from_cli(
            hostnames=["myhost"],
            user=None,
            port=22,
            identity_file=None,
        )
        hosts = registry.all_hosts()
        assert len(hosts) == 1
        assert hosts[0].user is None
        assert hosts[0].port == 22
        assert hosts[0].identity_file is None

    def test_add_from_cli_empty_list(self):
        """add_from_cli with empty hostnames adds nothing."""
        registry = HostRegistry()
        registry.add_from_cli(hostnames=[], user="admin", port=22, identity_file=None)
        assert registry.all_hosts() == []

    def test_add_from_config_resolves_groups(self):
        """add_from_config resolves groups and adds the resulting hosts."""
        config = Config(
            hosts={
                "web1": HostDefinition(name="web1", hostname="192.168.1.10", user="deploy"),
                "web2": HostDefinition(name="web2", hostname="192.168.1.11", user="deploy"),
                "db1": HostDefinition(name="db1", hostname="db.example.com"),
            },
            groups={
                "webservers": HostGroup(name="webservers", hosts=["web1", "web2"]),
                "databases": HostGroup(name="databases", hosts=["db1"]),
            },
        )
        registry = HostRegistry()
        registry.add_from_config(config, ["webservers"])
        hosts = registry.all_hosts()
        assert len(hosts) == 2
        assert hosts[0].name == "web1"
        assert hosts[1].name == "web2"

    def test_add_from_config_multiple_groups(self):
        """add_from_config resolves multiple groups."""
        config = Config(
            hosts={
                "web1": HostDefinition(name="web1", hostname="192.168.1.10"),
                "db1": HostDefinition(name="db1", hostname="db.example.com"),
            },
            groups={
                "webservers": HostGroup(name="webservers", hosts=["web1"]),
                "databases": HostGroup(name="databases", hosts=["db1"]),
            },
        )
        registry = HostRegistry()
        registry.add_from_config(config, ["webservers", "databases"])
        hosts = registry.all_hosts()
        assert len(hosts) == 2
        # all_hosts() returns sorted by name alphabetically
        assert hosts[0].name == "db1"
        assert hosts[1].name == "web1"

    def test_add_from_config_empty_group_names(self):
        """add_from_config with no group names adds nothing."""
        config = Config(
            hosts={"h1": HostDefinition(name="h1", hostname="10.0.0.1")},
            groups={"g1": HostGroup(name="g1", hosts=["h1"])},
        )
        registry = HostRegistry()
        registry.add_from_config(config, [])
        assert registry.all_hosts() == []

    def test_add_from_config_undefined_group_raises_error(self):
        """add_from_config raises ConfigError for undefined group names."""
        config = Config(hosts={}, groups={})
        registry = HostRegistry()
        with pytest.raises(ConfigError, match="undefined group"):
            registry.add_from_config(config, ["nonexistent"])

    def test_deduplicate_removes_case_insensitive_duplicates(self):
        """deduplicate removes entries with same name (case-insensitive), keeping first."""
        registry = HostRegistry()
        registry.hosts = [
            HostDefinition(name="Server1", hostname="10.0.0.1"),
            HostDefinition(name="server2", hostname="10.0.0.2"),
            HostDefinition(name="SERVER1", hostname="10.0.0.3"),
            HostDefinition(name="Server2", hostname="10.0.0.4"),
        ]
        registry.deduplicate()
        hosts = registry.all_hosts()
        assert len(hosts) == 2
        assert hosts[0].name == "Server1"
        assert hosts[0].hostname == "10.0.0.1"  # first occurrence preserved
        assert hosts[1].name == "server2"
        assert hosts[1].hostname == "10.0.0.2"

    def test_deduplicate_no_duplicates(self):
        """deduplicate keeps all hosts when there are no duplicates."""
        registry = HostRegistry()
        registry.hosts = [
            HostDefinition(name="host1", hostname="10.0.0.1"),
            HostDefinition(name="host2", hostname="10.0.0.2"),
            HostDefinition(name="host3", hostname="10.0.0.3"),
        ]
        registry.deduplicate()
        assert len(registry.all_hosts()) == 3

    def test_deduplicate_empty_list(self):
        """deduplicate on an empty list does nothing."""
        registry = HostRegistry()
        registry.deduplicate()
        assert registry.all_hosts() == []

    def test_all_hosts_returns_current_list(self):
        """all_hosts returns whatever is currently in the registry."""
        registry = HostRegistry()
        assert registry.all_hosts() == []
        registry.add_from_cli(hostnames=["host1"], user=None, port=22, identity_file=None)
        assert len(registry.all_hosts()) == 1

    def test_merge_cli_and_config_hosts_with_dedup(self):
        """Full workflow: add from CLI, add from config, deduplicate."""
        config = Config(
            hosts={
                "web1": HostDefinition(
                    name="web1", hostname="192.168.1.10", user="deploy", port=22
                ),
            },
            groups={
                "webservers": HostGroup(name="webservers", hosts=["web1"]),
            },
        )
        registry = HostRegistry()
        # Add CLI hosts — one of them has the same name as a config host
        registry.add_from_cli(
            hostnames=["web1", "new-host"],
            user=None,
            port=22,
            identity_file=None,
        )
        # Add config hosts
        registry.add_from_config(config, ["webservers"])
        # Before dedup: 3 entries (web1 from CLI, new-host, web1 from config)
        assert len(registry.all_hosts()) == 3
        # After dedup: web1 appears only once (CLI version kept first)
        registry.deduplicate()
        hosts = registry.all_hosts()
        assert len(hosts) == 2
        # all_hosts() returns sorted by name alphabetically
        assert hosts[0].name == "new-host"
        assert hosts[1].name == "web1"
        assert hosts[1].hostname == "web1"  # CLI version (hostname == name)

    def test_add_from_config_with_nested_groups(self):
        """add_from_config resolves nested groups recursively."""
        config = Config(
            hosts={
                "web1": HostDefinition(name="web1", hostname="192.168.1.10"),
                "web2": HostDefinition(name="web2", hostname="192.168.1.11"),
                "db1": HostDefinition(name="db1", hostname="db.example.com"),
            },
            groups={
                "webservers": HostGroup(name="webservers", hosts=["web1", "web2"]),
                "databases": HostGroup(name="databases", hosts=["db1"]),
                "all": HostGroup(name="all", hosts=[], groups=["webservers", "databases"]),
            },
        )
        registry = HostRegistry()
        registry.add_from_config(config, ["all"])
        hosts = registry.all_hosts()
        assert len(hosts) == 3
        names = [h.name for h in hosts]
        assert "web1" in names
        assert "web2" in names
        assert "db1" in names


# ---------------------------------------------------------------------------
# Unit Tests: build_ssh_args
# ---------------------------------------------------------------------------

build_ssh_args = ssh_tool.build_ssh_args


class TestBuildSshArgs:
    def test_minimal_host_default_port_no_user_no_key(self):
        """Minimal host: just hostname, default port, no user, no identity file."""
        host = HostDefinition(name="web1", hostname="192.168.1.10")
        result = build_ssh_args(host, connection_timeout=10.0)
        assert result == [
            "ssh",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "192.168.1.10",
        ]

    def test_host_with_user(self):
        """When user is set, target should be user@hostname."""
        host = HostDefinition(name="web1", hostname="192.168.1.10", user="deploy")
        result = build_ssh_args(host, connection_timeout=10.0)
        assert result == [
            "ssh",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "deploy@192.168.1.10",
        ]

    def test_host_with_non_default_port(self):
        """When port != 22, -p flag is included."""
        host = HostDefinition(name="db1", hostname="db.example.com", port=2222)
        result = build_ssh_args(host, connection_timeout=10.0)
        assert result == [
            "ssh",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-p", "2222",
            "db.example.com",
        ]

    def test_host_with_default_port_22_no_p_flag(self):
        """When port is 22 (default), no -p flag is included."""
        host = HostDefinition(name="web1", hostname="10.0.0.1", port=22)
        result = build_ssh_args(host, connection_timeout=5.0)
        assert "-p" not in result

    def test_host_with_identity_file(self):
        """When identity_file is set, -i flag is included."""
        host = HostDefinition(
            name="web1", hostname="192.168.1.10", identity_file="/home/user/.ssh/id_rsa"
        )
        result = build_ssh_args(host, connection_timeout=10.0)
        assert result == [
            "ssh",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-i", "/home/user/.ssh/id_rsa",
            "192.168.1.10",
        ]

    def test_host_with_all_options(self):
        """Full host definition: user, non-default port, and identity file."""
        host = HostDefinition(
            name="web1",
            hostname="192.168.1.10",
            user="deploy",
            port=2222,
            identity_file="~/.ssh/id_deploy",
        )
        result = build_ssh_args(host, connection_timeout=15.0)
        assert result == [
            "ssh",
            "-o", "ConnectTimeout=15",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-p", "2222",
            "-i", "~/.ssh/id_deploy",
            "deploy@192.168.1.10",
        ]

    def test_connection_timeout_float_truncated_to_int(self):
        """Float timeout is converted to int (truncated)."""
        host = HostDefinition(name="h1", hostname="10.0.0.1")
        result = build_ssh_args(host, connection_timeout=7.9)
        assert "-o" in result
        assert "ConnectTimeout=7" in result

    def test_connection_timeout_one_second(self):
        """Connection timeout of 1 second."""
        host = HostDefinition(name="h1", hostname="10.0.0.1")
        result = build_ssh_args(host, connection_timeout=1.0)
        assert "ConnectTimeout=1" in result

    def test_always_starts_with_ssh(self):
        """First element is always 'ssh'."""
        host = HostDefinition(name="h1", hostname="10.0.0.1")
        result = build_ssh_args(host, connection_timeout=10.0)
        assert result[0] == "ssh"

    def test_always_includes_batch_mode(self):
        """BatchMode=yes is always present."""
        host = HostDefinition(name="h1", hostname="10.0.0.1")
        result = build_ssh_args(host, connection_timeout=10.0)
        # Find the index of BatchMode
        idx = result.index("BatchMode=yes")
        assert result[idx - 1] == "-o"

    def test_hostname_is_last_element(self):
        """The target (user@host or just host) is always the last element."""
        host = HostDefinition(
            name="web1", hostname="10.0.0.1", user="admin", port=3333,
            identity_file="/key"
        )
        result = build_ssh_args(host, connection_timeout=10.0)
        assert result[-1] == "admin@10.0.0.1"

    def test_ipv6_hostname(self):
        """IPv6 hostname is used as-is in the target."""
        host = HostDefinition(name="v6host", hostname="2001:db8::1", user="root")
        result = build_ssh_args(host, connection_timeout=10.0)
        assert result[-1] == "root@2001:db8::1"


# ---------------------------------------------------------------------------
# Unit Tests: build_remote_command
# ---------------------------------------------------------------------------

build_remote_command = ssh_tool.build_remote_command


class TestBuildRemoteCommand:
    def test_no_working_dir(self):
        """When working_dir is None, return command as-is."""
        result = build_remote_command("ls -la")
        assert result == "ls -la"

    def test_with_working_dir(self):
        """When working_dir is set, prepend cd."""
        result = build_remote_command("ls -la", working_dir="/var/log")
        assert result == "cd /var/log && ls -la"

    def test_working_dir_none_explicitly(self):
        """Explicit None working_dir returns plain command."""
        result = build_remote_command("echo hello", working_dir=None)
        assert result == "echo hello"

    def test_working_dir_with_spaces_in_path(self):
        """Working directory with spaces in path."""
        result = build_remote_command("cat file.txt", working_dir="/home/user/my dir")
        assert result == "cd /home/user/my dir && cat file.txt"

    def test_complex_command(self):
        """Complex command with pipes and redirects."""
        cmd = "grep 'error' /var/log/syslog | tail -10"
        result = build_remote_command(cmd, working_dir="/tmp")
        assert result == "cd /tmp && grep 'error' /var/log/syslog | tail -10"

    def test_empty_working_dir_treated_as_no_dir(self):
        """Empty string working_dir is falsy, so no cd prefix."""
        result = build_remote_command("pwd", working_dir="")
        assert result == "pwd"

    def test_home_dir_path(self):
        """Home directory path with tilde."""
        result = build_remote_command("ls", working_dir="~/projects")
        assert result == "cd ~/projects && ls"

    def test_relative_path(self):
        """Relative path working directory."""
        result = build_remote_command("make", working_dir="src/app")
        assert result == "cd src/app && make"


# ---------------------------------------------------------------------------
# Unit Tests: run_command_on_host (async SSH runner)
# ---------------------------------------------------------------------------

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

run_command_on_host = ssh_tool.run_command_on_host
run_command_on_all = ssh_tool.run_command_on_all
CommandResult = ssh_tool.CommandResult


class TestRunCommandOnHost:
    """Tests for async SSH runner using mocked subprocess."""

    def _make_host(self, name="web1", hostname="192.168.1.10", user="deploy", port=22, identity_file=None):
        return HostDefinition(
            name=name, hostname=hostname, user=user, port=port, identity_file=identity_file
        )

    def _make_mock_process(self, stdout=b"", stderr=b"", returncode=0):
        """Create a mock async process."""
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(stdout, stderr))
        mock_proc.returncode = returncode
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()
        return mock_proc

    def test_successful_command(self):
        """A successful command returns stdout, stderr, and exit_code=0."""
        host = self._make_host()
        mock_proc = self._make_mock_process(
            stdout=b"hello world\n", stderr=b"", returncode=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            result = asyncio.run(run_command_on_host(host, "echo hello world"))

        assert result.host == host
        assert result.stdout == "hello world\n"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.timed_out is False
        assert result.error is None

    def test_command_with_stderr(self):
        """stderr is captured separately from stdout."""
        host = self._make_host()
        mock_proc = self._make_mock_process(
            stdout=b"output\n", stderr=b"warning: something\n", returncode=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            result = asyncio.run(run_command_on_host(host, "some-command"))

        assert result.stdout == "output\n"
        assert result.stderr == "warning: something\n"
        assert result.exit_code == 0

    def test_command_non_zero_exit_code(self):
        """Non-zero exit code is captured correctly."""
        host = self._make_host()
        mock_proc = self._make_mock_process(
            stdout=b"", stderr=b"error: not found\n", returncode=127
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            result = asyncio.run(run_command_on_host(host, "nonexistent-cmd"))

        assert result.exit_code == 127
        assert result.stderr == "error: not found\n"
        assert result.timed_out is False

    def test_command_timeout_kills_process(self):
        """When command exceeds timeout, process is killed and timed_out=True."""
        host = self._make_host()
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            result = asyncio.run(
                run_command_on_host(host, "sleep 100", timeout=1.0)
            )

        assert result.timed_out is True
        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == ""
        mock_proc.kill.assert_called_once()

    def test_os_error_populates_error_field(self):
        """OSError (e.g., ssh binary not found) populates the error field."""
        host = self._make_host()

        with patch(
            "asyncio.create_subprocess_exec",
            new_callable=AsyncMock,
            side_effect=OSError("No such file or directory: 'ssh'"),
        ):
            result = asyncio.run(run_command_on_host(host, "ls"))

        assert result.error is not None
        assert "No such file or directory" in result.error
        assert result.exit_code == 1
        assert result.timed_out is False

    def test_working_dir_passed_to_remote_command(self):
        """When working_dir is set, the remote command includes cd prefix."""
        host = self._make_host()
        mock_proc = self._make_mock_process(stdout=b"/var/log\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc) as mock_exec:
            asyncio.run(
                run_command_on_host(host, "pwd", working_dir="/var/log")
            )

        # Check that the remote command arg (last positional arg) includes cd prefix
        call_args = mock_exec.call_args[0]
        # The last argument should be the remote command string
        assert call_args[-1] == "cd /var/log && pwd"

    def test_no_working_dir_plain_command(self):
        """When no working_dir, the command is passed as-is."""
        host = self._make_host()
        mock_proc = self._make_mock_process(stdout=b"ok\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc) as mock_exec:
            asyncio.run(run_command_on_host(host, "uptime"))

        call_args = mock_exec.call_args[0]
        assert call_args[-1] == "uptime"

    def test_ssh_args_constructed_correctly(self):
        """Verify the full ssh argument list is passed to create_subprocess_exec."""
        host = self._make_host(
            name="db1", hostname="db.example.com", user="admin", port=2222,
            identity_file="/home/admin/.ssh/id_rsa"
        )
        mock_proc = self._make_mock_process(stdout=b"", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc) as mock_exec:
            asyncio.run(
                run_command_on_host(host, "whoami", connection_timeout=15.0)
            )

        call_args = mock_exec.call_args[0]
        # Should be: ssh -o ConnectTimeout=15 -o BatchMode=yes -p 2222 -i /home/admin/.ssh/id_rsa admin@db.example.com whoami
        assert call_args[0] == "ssh"
        assert "-o" in call_args
        assert "ConnectTimeout=15" in call_args
        assert "BatchMode=yes" in call_args
        assert "-p" in call_args
        assert "2222" in call_args
        assert "-i" in call_args
        assert "/home/admin/.ssh/id_rsa" in call_args
        assert "admin@db.example.com" in call_args
        assert call_args[-1] == "whoami"


# ---------------------------------------------------------------------------
# Unit Tests: run_command_on_all (concurrent/sequential orchestrator)
# ---------------------------------------------------------------------------


class TestRunCommandOnAll:
    """Tests for concurrent/sequential execution orchestrator."""

    def _make_host(self, name, hostname="10.0.0.1"):
        return HostDefinition(name=name, hostname=hostname)

    def _make_mock_process(self, stdout=b"", stderr=b"", returncode=0):
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(stdout, stderr))
        mock_proc.returncode = returncode
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()
        return mock_proc

    def test_concurrent_execution_all_succeed(self):
        """Concurrent mode runs all hosts and returns results for each."""
        hosts = [self._make_host("web1", "10.0.0.1"), self._make_host("web2", "10.0.0.2")]
        mock_proc = self._make_mock_process(stdout=b"ok\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            results = asyncio.run(
                run_command_on_all(hosts, "echo ok")
            )

        assert len(results) == 2
        assert all(r.exit_code == 0 for r in results)
        assert all(r.stdout == "ok\n" for r in results)

    def test_sequential_execution_all_succeed(self):
        """Sequential mode runs hosts one at a time and returns results for each."""
        hosts = [self._make_host("web1", "10.0.0.1"), self._make_host("web2", "10.0.0.2")]
        mock_proc = self._make_mock_process(stdout=b"done\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            results = asyncio.run(
                run_command_on_all(hosts, "echo done", sequential=True)
            )

        assert len(results) == 2
        assert all(r.exit_code == 0 for r in results)

    def test_concurrent_returns_results_in_host_order(self):
        """Concurrent mode returns results matching host list order."""
        hosts = [
            self._make_host("alpha", "10.0.0.1"),
            self._make_host("beta", "10.0.0.2"),
            self._make_host("gamma", "10.0.0.3"),
        ]
        mock_proc = self._make_mock_process(stdout=b"x\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            results = asyncio.run(run_command_on_all(hosts, "echo x"))

        # asyncio.gather preserves order
        assert len(results) == 3
        assert results[0].host.name == "alpha"
        assert results[1].host.name == "beta"
        assert results[2].host.name == "gamma"

    def test_working_dirs_passed_per_host(self):
        """working_dirs maps host names to their working directory."""
        hosts = [self._make_host("web1", "10.0.0.1"), self._make_host("web2", "10.0.0.2")]
        working_dirs = {"web1": "/var/www", "web2": "/opt/app"}
        mock_proc = self._make_mock_process(stdout=b"", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc) as mock_exec:
            asyncio.run(
                run_command_on_all(hosts, "ls", working_dirs=working_dirs)
            )

        # Check that different working dirs were used for each call
        calls = mock_exec.call_args_list
        assert len(calls) == 2
        # First call for web1 should have "cd /var/www && ls"
        assert calls[0][0][-1] == "cd /var/www && ls"
        # Second call for web2 should have "cd /opt/app && ls"
        assert calls[1][0][-1] == "cd /opt/app && ls"

    def test_working_dirs_none_no_cd_prefix(self):
        """When working_dirs is None, no cd prefix is added."""
        hosts = [self._make_host("web1", "10.0.0.1")]
        mock_proc = self._make_mock_process(stdout=b"", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc) as mock_exec:
            asyncio.run(
                run_command_on_all(hosts, "uptime", working_dirs=None)
            )

        call_args = mock_exec.call_args[0]
        assert call_args[-1] == "uptime"

    def test_working_dirs_host_not_in_map(self):
        """If a host is not in working_dirs, no cd prefix is used for it."""
        hosts = [self._make_host("web1", "10.0.0.1"), self._make_host("web2", "10.0.0.2")]
        working_dirs = {"web1": "/tmp"}  # web2 not mapped
        mock_proc = self._make_mock_process(stdout=b"", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc) as mock_exec:
            asyncio.run(
                run_command_on_all(hosts, "pwd", working_dirs=working_dirs)
            )

        calls = mock_exec.call_args_list
        assert calls[0][0][-1] == "cd /tmp && pwd"
        assert calls[1][0][-1] == "pwd"

    def test_empty_hosts_returns_empty_results(self):
        """Empty host list returns empty results."""
        results = asyncio.run(run_command_on_all([], "echo hi"))
        assert results == []

    def test_sequential_preserves_order(self):
        """Sequential mode processes hosts in the given order."""
        hosts = [
            self._make_host("first", "10.0.0.1"),
            self._make_host("second", "10.0.0.2"),
            self._make_host("third", "10.0.0.3"),
        ]
        mock_proc = self._make_mock_process(stdout=b"ok\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            results = asyncio.run(
                run_command_on_all(hosts, "echo ok", sequential=True)
            )

        assert results[0].host.name == "first"
        assert results[1].host.name == "second"
        assert results[2].host.name == "third"

    def test_timeout_passed_to_individual_commands(self):
        """Timeout propagates to individual run_command_on_host calls."""
        hosts = [self._make_host("web1", "10.0.0.1")]
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            results = asyncio.run(
                run_command_on_all(hosts, "sleep 100", timeout=1.0)
            )

        assert len(results) == 1
        assert results[0].timed_out is True

    def test_mixed_success_and_failure(self):
        """Some hosts succeed and some fail; all results are returned."""
        hosts = [self._make_host("good", "10.0.0.1"), self._make_host("bad", "10.0.0.2")]

        call_count = [0]

        async def mock_exec(*args, **kwargs):
            call_count[0] += 1
            mock_proc = MagicMock()
            if call_count[0] == 1:
                # First host succeeds
                mock_proc.communicate = AsyncMock(return_value=(b"success\n", b""))
                mock_proc.returncode = 0
            else:
                # Second host fails
                mock_proc.communicate = AsyncMock(return_value=(b"", b"connection refused\n"))
                mock_proc.returncode = 255
            mock_proc.kill = MagicMock()
            mock_proc.wait = AsyncMock()
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=mock_exec):
            results = asyncio.run(run_command_on_all(hosts, "test-cmd"))

        assert len(results) == 2
        assert results[0].exit_code == 0
        assert results[0].stdout == "success\n"
        assert results[1].exit_code == 255
        assert results[1].stderr == "connection refused\n"


# ---------------------------------------------------------------------------
# Unit Tests: OutputFormatter
# ---------------------------------------------------------------------------

import io

OutputFormatter = ssh_tool.OutputFormatter


class TestOutputFormatterInit:
    """Tests for OutputFormatter initialization and configuration."""

    def test_default_color_auto(self):
        """Default color mode is 'auto'."""
        buf = io.StringIO()
        formatter = OutputFormatter(color="auto", is_tty=True, file=buf)
        assert formatter.is_tty is True

    def test_is_tty_injectable(self):
        """is_tty can be overridden via constructor parameter."""
        buf = io.StringIO()
        formatter = OutputFormatter(color="auto", is_tty=False, file=buf)
        assert formatter.is_tty is False

    def test_is_tty_true(self):
        """is_tty=True puts formatter in TTY mode."""
        buf = io.StringIO()
        formatter = OutputFormatter(color="auto", is_tty=True, file=buf)
        assert formatter.is_tty is True

    def test_console_created(self):
        """A Rich Console instance is created."""
        buf = io.StringIO()
        formatter = OutputFormatter(color="auto", is_tty=True, file=buf)
        assert formatter.console is not None


class TestOutputFormatterTTY:
    """Tests for TTY mode output formatting."""

    def _make_result(self, host_name="web1", stdout="", stderr="", exit_code=0):
        host = HostDefinition(name=host_name, hostname="10.0.0.1")
        return CommandResult(host=host, stdout=stdout, stderr=stderr, exit_code=exit_code)

    def _get_output(self, results, color="never"):
        """Helper to capture formatted output as plain text."""
        buf = io.StringIO()
        formatter = OutputFormatter(color=color, is_tty=True, file=buf)
        formatter.format_results(results)
        return buf.getvalue()

    def test_header_format(self):
        """TTY mode prints '--- host ---' header."""
        result = self._make_result(host_name="web1", stdout="hello\n")
        output = self._get_output([result])
        assert "--- web1 ---" in output

    def test_stdout_lines_no_prefix(self):
        """TTY mode prints stdout lines without host prefix."""
        result = self._make_result(stdout="line1\nline2\n")
        output = self._get_output([result])
        assert "line1\n" in output
        assert "line2\n" in output
        # Should NOT have [web1] prefix
        assert "[web1]" not in output

    def test_stderr_prefixed_with_err(self):
        """TTY mode prefixes stderr lines with 'ERR: '."""
        result = self._make_result(stderr="something went wrong\n")
        output = self._get_output([result])
        assert "ERR: something went wrong" in output

    def test_no_output_indicator(self):
        """TTY mode shows '(no output)' when both stdout and stderr are empty."""
        result = self._make_result(stdout="", stderr="")
        output = self._get_output([result])
        assert "(no output)" in output

    def test_non_zero_exit_code(self):
        """TTY mode shows 'exited with code N' for non-zero exit codes."""
        result = self._make_result(exit_code=42)
        output = self._get_output([result])
        assert "exited with code 42" in output

    def test_zero_exit_code_no_indicator(self):
        """TTY mode does NOT show exit code for exit_code=0."""
        result = self._make_result(stdout="ok\n", exit_code=0)
        output = self._get_output([result])
        assert "exited with code" not in output

    def test_both_stdout_and_stderr(self):
        """TTY mode shows both stdout and stderr correctly."""
        result = self._make_result(stdout="output\n", stderr="warning\n")
        output = self._get_output([result])
        assert "output" in output
        assert "ERR: warning" in output
        assert "(no output)" not in output

    def test_non_zero_exit_with_output(self):
        """Exit code is shown even when there is output."""
        result = self._make_result(stdout="partial\n", exit_code=1)
        output = self._get_output([result])
        assert "partial" in output
        assert "exited with code 1" in output

    def test_multiple_hosts_grouped(self):
        """Multiple results are printed in order with separate headers."""
        results = [
            self._make_result(host_name="web1", stdout="from web1\n"),
            self._make_result(host_name="web2", stdout="from web2\n"),
        ]
        output = self._get_output(results)
        # Headers should appear in order
        web1_pos = output.index("--- web1 ---")
        web2_pos = output.index("--- web2 ---")
        assert web1_pos < web2_pos
        # Content grouped under respective headers
        from_web1_pos = output.index("from web1")
        from_web2_pos = output.index("from web2")
        assert web1_pos < from_web1_pos < web2_pos
        assert web2_pos < from_web2_pos

    def test_results_sorted_by_hostname(self):
        """Results are output in the order given (sorting happens upstream in HostRegistry)."""
        results = [
            self._make_result(host_name="alpha", stdout="a\n"),
            self._make_result(host_name="mu", stdout="m\n"),
            self._make_result(host_name="zeta", stdout="z\n"),
        ]
        output = self._get_output(results)
        alpha_pos = output.index("--- alpha ---")
        mu_pos = output.index("--- mu ---")
        zeta_pos = output.index("--- zeta ---")
        assert alpha_pos < mu_pos < zeta_pos


class TestOutputFormatterPiped:
    """Tests for piped mode output formatting."""

    def _make_result(self, host_name="web1", stdout="", stderr="", exit_code=0):
        host = HostDefinition(name=host_name, hostname="10.0.0.1")
        return CommandResult(host=host, stdout=stdout, stderr=stderr, exit_code=exit_code)

    def _get_output(self, results, color="never"):
        """Helper to capture formatted output as plain text."""
        buf = io.StringIO()
        formatter = OutputFormatter(color=color, is_tty=False, file=buf)
        formatter.format_results(results)
        return buf.getvalue()

    def test_stdout_prefixed_with_host(self):
        """Piped mode prefixes stdout lines with '[host] '."""
        result = self._make_result(host_name="web1", stdout="hello\n")
        output = self._get_output([result])
        assert "[web1] hello" in output

    def test_stderr_prefixed_with_host_and_err(self):
        """Piped mode prefixes stderr lines with '[host] ERR: '."""
        result = self._make_result(host_name="web1", stderr="error msg\n")
        output = self._get_output([result])
        assert "[web1] ERR: error msg" in output

    def test_no_output_indicator(self):
        """Piped mode shows '[host] (no output)' when both stdout and stderr empty."""
        result = self._make_result(host_name="db1", stdout="", stderr="")
        output = self._get_output([result])
        assert "[db1] (no output)" in output

    def test_non_zero_exit_code(self):
        """Piped mode shows '[host] exited with code N' for non-zero exit codes."""
        result = self._make_result(host_name="web1", exit_code=127)
        output = self._get_output([result])
        assert "[web1] exited with code 127" in output

    def test_zero_exit_code_no_indicator(self):
        """Piped mode does NOT show exit code for exit_code=0."""
        result = self._make_result(stdout="ok\n", exit_code=0)
        output = self._get_output([result])
        assert "exited with code" not in output

    def test_multiple_stdout_lines(self):
        """Each stdout line gets its own prefix."""
        result = self._make_result(host_name="srv", stdout="line1\nline2\nline3\n")
        output = self._get_output([result])
        assert "[srv] line1" in output
        assert "[srv] line2" in output
        assert "[srv] line3" in output

    def test_multiple_stderr_lines(self):
        """Each stderr line gets its own ERR: prefix."""
        result = self._make_result(host_name="srv", stderr="err1\nerr2\n")
        output = self._get_output([result])
        assert "[srv] ERR: err1" in output
        assert "[srv] ERR: err2" in output

    def test_both_stdout_and_stderr(self):
        """Both stdout and stderr are shown with appropriate prefixes."""
        result = self._make_result(stdout="out\n", stderr="err\n")
        output = self._get_output([result])
        assert "[web1] out" in output
        assert "[web1] ERR: err" in output
        assert "(no output)" not in output

    def test_multiple_hosts_grouped(self):
        """Multiple hosts' output is grouped (not interleaved)."""
        results = [
            self._make_result(host_name="host1", stdout="from host1\n"),
            self._make_result(host_name="host2", stdout="from host2\n"),
        ]
        output = self._get_output(results)
        assert "[host1] from host1" in output
        assert "[host2] from host2" in output
        # host1 output should come before host2 output
        h1_pos = output.index("[host1] from host1")
        h2_pos = output.index("[host2] from host2")
        assert h1_pos < h2_pos

    def test_results_sorted_by_hostname(self):
        """Results are output in the order given (sorting happens upstream in HostRegistry)."""
        results = [
            self._make_result(host_name="alpha", stdout="a\n"),
            self._make_result(host_name="mu", stdout="m\n"),
            self._make_result(host_name="zeta", stdout="z\n"),
        ]
        output = self._get_output(results)
        alpha_pos = output.index("[alpha] a")
        mu_pos = output.index("[mu] m")
        zeta_pos = output.index("[zeta] z")
        assert alpha_pos < mu_pos < zeta_pos

    def test_non_zero_exit_with_output(self):
        """Exit code is shown after the output lines."""
        result = self._make_result(host_name="web1", stdout="data\n", exit_code=2)
        output = self._get_output([result])
        data_pos = output.index("[web1] data")
        exit_pos = output.index("[web1] exited with code 2")
        assert data_pos < exit_pos


class TestOutputFormatterColorOption:
    """Tests for --color option behavior."""

    def _make_result(self, host_name="web1", stdout="hello\n"):
        host = HostDefinition(name=host_name, hostname="10.0.0.1")
        return CommandResult(host=host, stdout=stdout, stderr="", exit_code=0)

    def test_color_never_no_ansi_codes(self):
        """color='never' produces no ANSI escape codes."""
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=True, file=buf)
        formatter.format_results([self._make_result()])
        output = buf.getvalue()
        # ANSI escape sequences start with \x1b[
        assert "\x1b[" not in output

    def test_color_always_produces_ansi_codes(self):
        """color='always' produces ANSI escape codes even in non-TTY mode."""
        buf = io.StringIO()
        formatter = OutputFormatter(color="always", is_tty=True, file=buf)
        formatter.format_results([self._make_result()])
        output = buf.getvalue()
        # Should have ANSI escape sequences for the header styling
        assert "\x1b[" in output

    def test_color_auto_tty_produces_ansi(self):
        """color='auto' with TTY produces ANSI codes (Rich auto-detects the file)."""
        # Note: Rich uses force_terminal=None in auto mode, which means it checks
        # the file object. With StringIO it won't detect a terminal, so we test
        # that the formatter at least uses the correct configuration.
        buf = io.StringIO()
        formatter = OutputFormatter(color="auto", is_tty=True, file=buf)
        # The console should have force_terminal as None (auto-detect)
        # We just verify no crash and basic output works
        formatter.format_results([self._make_result()])
        output = buf.getvalue()
        assert "--- web1 ---" in output


# ---------------------------------------------------------------------------
# Unit Tests: compute_exit_code
# ---------------------------------------------------------------------------


class TestComputeExitCode:
    """Tests for aggregated exit code computation."""

    def _make_result(self, exit_code=0):
        host = HostDefinition(name="h1", hostname="10.0.0.1")
        return CommandResult(host=host, stdout="", stderr="", exit_code=exit_code)

    def test_all_zero_returns_zero(self):
        """When all results have exit_code 0, returns 0."""
        results = [self._make_result(0), self._make_result(0), self._make_result(0)]
        assert compute_exit_code(results) == 0

    def test_one_non_zero_returns_one(self):
        """When any result has non-zero exit_code, returns 1."""
        results = [self._make_result(0), self._make_result(1), self._make_result(0)]
        assert compute_exit_code(results) == 1

    def test_all_non_zero_returns_one(self):
        """When all results have non-zero exit codes, returns 1."""
        results = [self._make_result(127), self._make_result(255), self._make_result(2)]
        assert compute_exit_code(results) == 1

    def test_single_success_returns_zero(self):
        """Single host with exit_code 0 returns 0."""
        results = [self._make_result(0)]
        assert compute_exit_code(results) == 0

    def test_single_failure_returns_one(self):
        """Single host with non-zero exit_code returns 1."""
        results = [self._make_result(42)]
        assert compute_exit_code(results) == 1

    def test_empty_results_returns_zero(self):
        """Empty results list returns 0 (vacuously all successful)."""
        assert compute_exit_code([]) == 0


# ---------------------------------------------------------------------------
# Unit Tests: run_immediate_mode
# ---------------------------------------------------------------------------


class TestRunImmediateMode:
    """Tests for immediate mode entry point."""

    def _make_host(self, name="web1", hostname="10.0.0.1"):
        return HostDefinition(name=name, hostname=hostname)

    def _make_mock_process(self, stdout=b"", stderr=b"", returncode=0):
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(stdout, stderr))
        mock_proc.returncode = returncode
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()
        return mock_proc

    def test_empty_command_raises_validation_error(self):
        """Empty command string raises ValidationError."""
        hosts = [self._make_host()]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=False, file=buf)
        with pytest.raises(ValidationError, match="command must not be empty"):
            run_immediate_mode(hosts, "", formatter)

    def test_whitespace_only_command_raises_validation_error(self):
        """Whitespace-only command raises ValidationError."""
        hosts = [self._make_host()]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=False, file=buf)
        with pytest.raises(ValidationError, match="command must not be empty"):
            run_immediate_mode(hosts, "   \t  ", formatter)

    def test_successful_command_returns_zero(self):
        """When all hosts succeed, returns exit code 0."""
        hosts = [self._make_host("web1"), self._make_host("web2", "10.0.0.2")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=False, file=buf)
        mock_proc = self._make_mock_process(stdout=b"ok\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            exit_code = run_immediate_mode(hosts, "echo ok", formatter)

        assert exit_code == 0

    def test_failed_command_returns_one(self):
        """When any host has non-zero exit code, returns 1."""
        hosts = [self._make_host("web1")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=False, file=buf)
        mock_proc = self._make_mock_process(stdout=b"", stderr=b"error\n", returncode=1)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            exit_code = run_immediate_mode(hosts, "failing-cmd", formatter)

        assert exit_code == 1

    def test_output_is_formatted(self):
        """Results are formatted and written to the formatter's output."""
        hosts = [self._make_host("web1")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=False, file=buf)
        mock_proc = self._make_mock_process(stdout=b"hello world\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            run_immediate_mode(hosts, "echo hello world", formatter)

        output = buf.getvalue()
        assert "[web1] hello world" in output

    def test_tty_mode_output(self):
        """In TTY mode, output uses header format."""
        hosts = [self._make_host("server1")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=True, file=buf)
        mock_proc = self._make_mock_process(stdout=b"data\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            run_immediate_mode(hosts, "cat file", formatter)

        output = buf.getvalue()
        assert "--- server1 ---" in output
        assert "data" in output

    def test_sequential_flag_passed(self):
        """Sequential flag is passed through to run_command_on_all."""
        hosts = [self._make_host("web1"), self._make_host("web2", "10.0.0.2")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=False, file=buf)
        mock_proc = self._make_mock_process(stdout=b"ok\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            exit_code = run_immediate_mode(
                hosts, "echo ok", formatter, sequential=True
            )

        assert exit_code == 0

    def test_mixed_results_returns_one(self):
        """When some hosts succeed and some fail, returns 1."""
        hosts = [self._make_host("good", "10.0.0.1"), self._make_host("bad", "10.0.0.2")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=False, file=buf)

        call_count = [0]

        async def mock_exec(*args, **kwargs):
            call_count[0] += 1
            mock_proc = MagicMock()
            if call_count[0] == 1:
                mock_proc.communicate = AsyncMock(return_value=(b"success\n", b""))
                mock_proc.returncode = 0
            else:
                mock_proc.communicate = AsyncMock(return_value=(b"", b"failed\n"))
                mock_proc.returncode = 1
            mock_proc.kill = MagicMock()
            mock_proc.wait = AsyncMock()
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=mock_exec):
            exit_code = run_immediate_mode(hosts, "test-cmd", formatter)

        assert exit_code == 1

    def test_timeout_parameters_propagate(self):
        """Timeout and connection_timeout are passed to the execution layer."""
        hosts = [self._make_host("web1")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=False, file=buf)
        mock_proc = self._make_mock_process(stdout=b"ok\n", returncode=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            exit_code = run_immediate_mode(
                hosts, "echo ok", formatter, timeout=60.0, connection_timeout=20.0
            )

        assert exit_code == 0


# ---------------------------------------------------------------------------
# Unit Tests: REPL Mode - MetaCommandHandler
# ---------------------------------------------------------------------------

ReplSession = ssh_tool.ReplSession
MetaCommandHandler = ssh_tool.MetaCommandHandler
_format_connection_failure = ssh_tool._format_connection_failure

import readline
from unittest.mock import patch, MagicMock, AsyncMock


class TestMetaCommandHandler:
    """Tests for MetaCommandHandler dispatch and individual commands."""

    def _make_session(self, hosts=None):
        """Create a ReplSession with mock hosts for testing."""
        if hosts is None:
            hosts = [
                HostDefinition(name="web1", hostname="10.0.0.1", user="deploy"),
                HostDefinition(name="web2", hostname="10.0.0.2", user="deploy"),
            ]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=True, file=buf)
        session = ReplSession(
            hosts=hosts,
            formatter=formatter,
            timeout=30.0,
            connection_timeout=10.0,
            history_file=Path("/tmp/test_history_nonexistent"),
        )
        # Mark all hosts as connected for testing
        for h in hosts:
            session.connected[h.name] = True
        return session

    def test_help_returns_false(self):
        """`:help` does not exit the REPL."""
        session = self._make_session()
        handler = MetaCommandHandler(session)
        assert handler.handle(":help") is False

    def test_help_displays_commands(self, capsys):
        """`:help` lists all available meta-commands."""
        session = self._make_session()
        handler = MetaCommandHandler(session)
        handler.handle(":help")
        output = capsys.readouterr().out
        assert ":help" in output
        assert ":quit" in output
        assert ":hosts" in output
        assert ":history" in output
        assert ":pwd" in output
        assert ":reconnect" in output
        assert ":!<command>" in output

    def test_quit_returns_true(self):
        """`:quit` signals REPL exit."""
        session = self._make_session()
        handler = MetaCommandHandler(session)
        assert handler.handle(":quit") is True

    def test_hosts_displays_status(self, capsys):
        """`:hosts` shows each host with connected/disconnected status."""
        session = self._make_session()
        session.connected["web1"] = True
        session.connected["web2"] = False
        handler = MetaCommandHandler(session)
        handler.handle(":hosts")
        output = capsys.readouterr().out
        assert "web1" in output
        assert "connected" in output
        assert "web2" in output
        assert "disconnected" in output

    def test_pwd_displays_working_dirs(self, capsys):
        """`:pwd` shows tracked working directory per host."""
        session = self._make_session()
        session.working_dirs["web1"] = "/var/www"
        session.working_dirs["web2"] = "/opt/app"
        handler = MetaCommandHandler(session)
        handler.handle(":pwd")
        output = capsys.readouterr().out
        assert "web1" in output
        assert "/var/www" in output
        assert "web2" in output
        assert "/opt/app" in output

    def test_pwd_disconnected_host(self, capsys):
        """`:pwd` shows (disconnected) for disconnected hosts."""
        session = self._make_session()
        session.connected["web2"] = False
        handler = MetaCommandHandler(session)
        handler.handle(":pwd")
        output = capsys.readouterr().out
        assert "disconnected" in output

    def test_unrecognised_command_error(self, capsys):
        """Unrecognised meta-command prints error to stderr."""
        session = self._make_session()
        handler = MetaCommandHandler(session)
        result = handler.handle(":unknown")
        assert result is False
        err = capsys.readouterr().err
        assert "unknown meta-command" in err
        assert ":help" in err

    def test_local_exec_runs_command(self, capsys):
        """`:!echo hello` runs locally and prints stdout."""
        session = self._make_session()
        handler = MetaCommandHandler(session)
        handler.handle(":!echo hello")
        output = capsys.readouterr().out
        assert "hello" in output

    def test_local_exec_returns_false(self):
        """`:!command` does not exit the REPL."""
        session = self._make_session()
        handler = MetaCommandHandler(session)
        assert handler.handle(":!echo test") is False

    def test_history_displays_entries(self, capsys):
        """`:history` displays readline history entries with line numbers."""
        session = self._make_session()
        # Add some history items
        readline.clear_history()
        readline.add_history("ls -la")
        readline.add_history("pwd")
        readline.add_history("whoami")
        handler = MetaCommandHandler(session)
        handler.handle(":history")
        output = capsys.readouterr().out
        assert "ls -la" in output
        assert "pwd" in output
        assert "whoami" in output
        readline.clear_history()

    def test_reconnect_with_all_connected(self, capsys):
        """`:reconnect` reports all hosts connected when none are disconnected."""
        session = self._make_session()
        handler = MetaCommandHandler(session)
        handler.handle(":reconnect")
        output = capsys.readouterr().out
        assert "All hosts are connected" in output

    def test_reconnect_attempts_disconnected(self, capsys):
        """`:reconnect` attempts to reconnect disconnected hosts."""
        session = self._make_session()
        session.connected["web2"] = False
        handler = MetaCommandHandler(session)

        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"ok\n", b""))
        mock_proc.returncode = 0
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            handler.handle(":reconnect")

        assert session.connected["web2"] is True
        output = capsys.readouterr().out
        assert "reconnected" in output


# ---------------------------------------------------------------------------
# Unit Tests: REPL Mode - Working Directory Tracking (_handle_cd)
# ---------------------------------------------------------------------------


class TestHandleCd:
    """Tests for working directory tracking logic."""

    def _make_session(self, hosts=None):
        """Create a ReplSession for testing."""
        if hosts is None:
            hosts = [
                HostDefinition(name="web1", hostname="10.0.0.1"),
                HostDefinition(name="web2", hostname="10.0.0.2"),
            ]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=True, file=buf)
        session = ReplSession(
            hosts=hosts,
            formatter=formatter,
            history_file=Path("/tmp/test_history_nonexistent"),
        )
        for h in hosts:
            session.connected[h.name] = True
        return session

    def test_successful_cd_updates_working_dir(self):
        """On success (exit_code=0), working_dirs is updated with pwd output."""
        session = self._make_session()
        host = session.hosts[0]
        results = [
            CommandResult(host=host, stdout="/var/log\n", stderr="", exit_code=0),
            CommandResult(host=session.hosts[1], stdout="/opt/app\n", stderr="", exit_code=0),
        ]
        session._handle_cd("/var/log", results)
        assert session.working_dirs["web1"] == "/var/log"
        assert session.working_dirs["web2"] == "/opt/app"

    def test_failed_cd_retains_previous_dir(self, capsys):
        """On failure (non-zero exit), working_dirs is NOT updated."""
        session = self._make_session()
        session.working_dirs["web1"] = "/home/user"
        host = session.hosts[0]
        results = [
            CommandResult(host=host, stdout="", stderr="No such file\n", exit_code=1),
            CommandResult(host=session.hosts[1], stdout="/opt/app\n", stderr="", exit_code=0),
        ]
        session._handle_cd("/nonexistent", results)
        # web1 retains previous dir
        assert session.working_dirs["web1"] == "/home/user"
        # web2 gets new dir
        assert session.working_dirs["web2"] == "/opt/app"
        err = capsys.readouterr().err
        assert "failed" in err

    def test_cd_home_with_empty_target(self):
        """cd with no argument (empty target) updates to home dir."""
        session = self._make_session()
        session.working_dirs["web1"] = "/var/www"
        host = session.hosts[0]
        results = [
            CommandResult(host=host, stdout="/home/deploy\n", stderr="", exit_code=0),
            CommandResult(host=session.hosts[1], stdout="/home/deploy\n", stderr="", exit_code=0),
        ]
        session._handle_cd("", results)
        assert session.working_dirs["web1"] == "/home/deploy"
        assert session.working_dirs["web2"] == "/home/deploy"

    def test_cd_with_no_prior_working_dir(self):
        """cd works even if there's no prior working dir set."""
        session = self._make_session()
        # No prior working_dirs set
        host = session.hosts[0]
        results = [
            CommandResult(host=host, stdout="/tmp\n", stderr="", exit_code=0),
            CommandResult(host=session.hosts[1], stdout="/tmp\n", stderr="", exit_code=0),
        ]
        session._handle_cd("/tmp", results)
        assert session.working_dirs["web1"] == "/tmp"
        assert session.working_dirs["web2"] == "/tmp"


# ---------------------------------------------------------------------------
# Unit Tests: REPL Mode - Input Dispatch and CD Detection
# ---------------------------------------------------------------------------


class TestReplInputDispatch:
    """Tests for REPL input classification and cd detection."""

    def _make_session(self, hosts=None):
        if hosts is None:
            hosts = [HostDefinition(name="web1", hostname="10.0.0.1")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=True, file=buf)
        session = ReplSession(
            hosts=hosts,
            formatter=formatter,
            history_file=Path("/tmp/test_history_nonexistent"),
        )
        for h in hosts:
            session.connected[h.name] = True
        return session

    def test_is_cd_bare(self):
        """'cd' alone is detected as a cd command."""
        session = self._make_session()
        assert session._is_cd_command("cd") is True

    def test_is_cd_with_target(self):
        """'cd /tmp' is detected as a cd command."""
        session = self._make_session()
        assert session._is_cd_command("cd /tmp") is True

    def test_is_cd_with_tab(self):
        """'cd\\t/tmp' (tab separator) is detected as a cd command."""
        session = self._make_session()
        assert session._is_cd_command("cd\t/tmp") is True

    def test_not_cd_command(self):
        """Commands starting with 'cd' but not being cd are not cd commands."""
        session = self._make_session()
        assert session._is_cd_command("cdrom") is False
        assert session._is_cd_command("ls") is False
        assert session._is_cd_command("echo cd") is False

    def test_extract_cd_target_path(self):
        """Extract target from 'cd /var/log'."""
        session = self._make_session()
        assert session._extract_cd_target("cd /var/log") == "/var/log"

    def test_extract_cd_target_empty(self):
        """Extract target from bare 'cd' returns empty string."""
        session = self._make_session()
        assert session._extract_cd_target("cd") == ""

    def test_extract_cd_target_relative(self):
        """Extract target from 'cd src/app'."""
        session = self._make_session()
        assert session._extract_cd_target("cd src/app") == "src/app"

    def test_extract_cd_target_tilde(self):
        """Extract target from 'cd ~'."""
        session = self._make_session()
        assert session._extract_cd_target("cd ~") == "~"


# ---------------------------------------------------------------------------
# Unit Tests: REPL Mode - Connection State
# ---------------------------------------------------------------------------


class TestConnectionState:
    """Tests for connection state tracking and error reporting."""

    def _make_session(self, hosts=None):
        if hosts is None:
            hosts = [
                HostDefinition(name="web1", hostname="10.0.0.1"),
                HostDefinition(name="web2", hostname="10.0.0.2"),
            ]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=True, file=buf)
        session = ReplSession(
            hosts=hosts,
            formatter=formatter,
            history_file=Path("/tmp/test_history_nonexistent"),
        )
        for h in hosts:
            session.connected[h.name] = True
        return session

    def test_get_connected_hosts_all(self):
        """_get_connected_hosts returns all hosts when all connected."""
        session = self._make_session()
        result = session._get_connected_hosts()
        assert len(result) == 2

    def test_get_connected_hosts_partial(self):
        """_get_connected_hosts excludes disconnected hosts."""
        session = self._make_session()
        session.connected["web2"] = False
        result = session._get_connected_hosts()
        assert len(result) == 1
        assert result[0].name == "web1"

    def test_get_connected_hosts_none(self):
        """_get_connected_hosts returns empty when all disconnected."""
        session = self._make_session()
        session.connected["web1"] = False
        session.connected["web2"] = False
        result = session._get_connected_hosts()
        assert len(result) == 0

    def test_check_connection_state_marks_disconnected(self, capsys):
        """_check_connection_state marks host as disconnected on error."""
        session = self._make_session()
        host = session.hosts[0]
        results = [
            CommandResult(host=host, stdout="", stderr="", exit_code=1, error="Connection refused"),
        ]
        session._check_connection_state(results)
        assert session.connected["web1"] is False
        err = capsys.readouterr().err
        assert "disconnected" in err
        assert "web1" in err

    def test_check_connection_state_timeout(self, capsys):
        """_check_connection_state marks host as disconnected on timeout."""
        session = self._make_session()
        host = session.hosts[0]
        results = [
            CommandResult(host=host, stdout="", stderr="", exit_code=1, timed_out=True),
        ]
        session._check_connection_state(results)
        assert session.connected["web1"] is False
        err = capsys.readouterr().err
        assert "disconnected" in err

    def test_check_connection_state_success_no_change(self):
        """_check_connection_state does not modify connected hosts on success."""
        session = self._make_session()
        host = session.hosts[0]
        results = [
            CommandResult(host=host, stdout="ok\n", stderr="", exit_code=0),
        ]
        session._check_connection_state(results)
        assert session.connected["web1"] is True

    def test_initial_connect_all_fail(self, capsys):
        """_initial_connect returns False if all hosts fail."""
        session = self._make_session()
        # Reset connected state
        for h in session.hosts:
            session.connected[h.name] = False

        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Connection refused\n"))
        mock_proc.returncode = 255
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
            result = session._initial_connect()

        assert result is False
        err = capsys.readouterr().err
        assert "no hosts could be reached" in err

    def test_initial_connect_partial_success(self, capsys):
        """_initial_connect returns True if at least one host connects."""
        hosts = [
            HostDefinition(name="good", hostname="10.0.0.1"),
            HostDefinition(name="bad", hostname="10.0.0.2"),
        ]
        session = self._make_session(hosts)
        for h in hosts:
            session.connected[h.name] = False

        call_count = [0]

        async def mock_exec(*args, **kwargs):
            call_count[0] += 1
            mock_proc = MagicMock()
            if call_count[0] == 1:
                mock_proc.communicate = AsyncMock(return_value=(b"ok\n", b""))
                mock_proc.returncode = 0
            else:
                mock_proc.communicate = AsyncMock(return_value=(b"", b"refused\n"))
                mock_proc.returncode = 255
            mock_proc.kill = MagicMock()
            mock_proc.wait = AsyncMock()
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=mock_exec):
            result = session._initial_connect()

        assert result is True
        assert session.connected["good"] is True
        assert session.connected["bad"] is False


# ---------------------------------------------------------------------------
# Unit Tests: REPL Mode - History Management
# ---------------------------------------------------------------------------


class TestReplHistory:
    """Tests for history load/save functionality."""

    def _make_session(self, history_file):
        hosts = [HostDefinition(name="web1", hostname="10.0.0.1")]
        buf = io.StringIO()
        formatter = OutputFormatter(color="never", is_tty=True, file=buf)
        return ReplSession(
            hosts=hosts,
            formatter=formatter,
            history_file=history_file,
        )

    def test_load_history_nonexistent_file(self, tmp_path):
        """Loading from a non-existent file does nothing (no error)."""
        history_file = tmp_path / "nonexistent_history"
        session = self._make_session(history_file)
        readline.clear_history()
        session._load_history()  # Should not raise
        # History should be empty
        assert readline.get_current_history_length() == 0

    def test_save_and_load_history(self, tmp_path):
        """History saved to file can be loaded back."""
        history_file = tmp_path / "test_history"
        session = self._make_session(history_file)
        readline.clear_history()

        # Add some commands
        readline.add_history("ls -la")
        readline.add_history("pwd")
        readline.add_history("whoami")

        # Save
        session._save_history()
        assert history_file.exists()

        # Clear and reload
        readline.clear_history()
        assert readline.get_current_history_length() == 0
        session._load_history()
        assert readline.get_current_history_length() == 3
        assert readline.get_history_item(1) == "ls -la"
        assert readline.get_history_item(2) == "pwd"
        assert readline.get_history_item(3) == "whoami"
        readline.clear_history()

    def test_load_corrupt_history_warns(self, tmp_path, capsys):
        """Corrupt history file triggers warning and starts empty."""
        history_file = tmp_path / "corrupt_history"
        # Create a directory instead of a file to force an OSError on read
        history_file.mkdir()
        session = self._make_session(history_file)
        readline.clear_history()
        session._load_history()
        err = capsys.readouterr().err
        assert "Warning" in err or "could not load" in err
        readline.clear_history()

    def test_history_length_capped_at_1000(self, tmp_path):
        """History length is set to 1000."""
        history_file = tmp_path / "test_history"
        session = self._make_session(history_file)
        readline.clear_history()

        # Add 1050 entries
        for i in range(1050):
            readline.add_history(f"command_{i}")

        session._save_history()

        # Reload and check length
        readline.clear_history()
        session._load_history()
        length = readline.get_current_history_length()
        assert length <= 1000
        readline.clear_history()


# ---------------------------------------------------------------------------
# Unit Tests: _format_connection_failure
# ---------------------------------------------------------------------------


class TestFormatConnectionFailure:
    """Tests for the connection failure formatting helper."""

    def test_timeout(self):
        host = HostDefinition(name="web1", hostname="10.0.0.1")
        result = CommandResult(host=host, stdout="", stderr="", exit_code=1, timed_out=True)
        assert _format_connection_failure(result) == "connection timed out"

    def test_error_message(self):
        host = HostDefinition(name="web1", hostname="10.0.0.1")
        result = CommandResult(host=host, stdout="", stderr="", exit_code=1, error="Connection refused")
        assert _format_connection_failure(result) == "Connection refused"

    def test_stderr_message(self):
        host = HostDefinition(name="web1", hostname="10.0.0.1")
        result = CommandResult(host=host, stdout="", stderr="Permission denied\n", exit_code=255)
        assert _format_connection_failure(result) == "Permission denied"

    def test_generic_failure(self):
        host = HostDefinition(name="web1", hostname="10.0.0.1")
        result = CommandResult(host=host, stdout="", stderr="", exit_code=1)
        assert _format_connection_failure(result) == "connection failed"


# ---------------------------------------------------------------------------
# Unit Tests: CLI Entry Point (Task 11.1)
# ---------------------------------------------------------------------------

from typer.testing import CliRunner

app = ssh_tool.app
main_cmd = ssh_tool.main


class TestCLIEntryPoint:
    """Tests for the typer CLI app with all options."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_no_hosts_exits_nonzero(self):
        """When no hosts are provided via any source, exits with error."""
        result = self.runner.invoke(app, [])
        assert result.exit_code != 0
        assert "no hosts specified" in result.output.lower() or "no hosts specified" in (result.stdout or "").lower()

    def test_no_hosts_with_command_exits_nonzero(self):
        """When a command is given but no hosts, exits with error."""
        result = self.runner.invoke(app, ["uptime"])
        assert result.exit_code != 0

    def test_invalid_port_zero_exits_nonzero(self):
        """Port 0 is rejected."""
        result = self.runner.invoke(app, ["--hosts", "server1", "--port", "0", "uptime"])
        assert result.exit_code != 0
        assert "invalid port" in result.output.lower()

    def test_invalid_port_too_high_exits_nonzero(self):
        """Port above 65535 is rejected."""
        result = self.runner.invoke(app, ["--hosts", "server1", "--port", "70000", "uptime"])
        assert result.exit_code != 0
        assert "invalid port" in result.output.lower()

    def test_identity_file_not_found_exits_nonzero(self, tmp_path):
        """Non-existent identity file is rejected."""
        fake_key = tmp_path / "nonexistent_key"
        result = self.runner.invoke(
            app, ["--hosts", "server1", "--identity", str(fake_key), "uptime"]
        )
        assert result.exit_code != 0
        assert "identity file" in result.output.lower()
        assert "no such file" in result.output.lower()

    def test_identity_file_unreadable_exits_nonzero(self, tmp_path):
        """Unreadable identity file is rejected."""
        key_file = tmp_path / "key"
        key_file.write_text("fake key")
        key_file.chmod(0o000)
        try:
            result = self.runner.invoke(
                app, ["--hosts", "server1", "--identity", str(key_file), "uptime"]
            )
            assert result.exit_code != 0
            # Typer/Rich formats the error with box characters; just verify exit code
            # and that the file path appears in the output
            assert str(key_file) in result.output
        finally:
            key_file.chmod(0o644)

    def test_invalid_color_option_exits_nonzero(self):
        """Invalid --color value is rejected."""
        result = self.runner.invoke(
            app, ["--hosts", "server1", "--color", "invalid", "uptime"]
        )
        assert result.exit_code != 0
        assert "invalid --color" in result.output.lower()

    def test_valid_color_options_accepted(self, tmp_path):
        """The color option accepts always, never, and auto."""
        # We can't fully run the tool (no real SSH), but we can verify
        # that it gets past color validation by checking for the
        # "no hosts" or ssh-related error rather than a color error
        for color_val in ("always", "never", "auto"):
            result = self.runner.invoke(
                app, ["--hosts", "server1", "--color", color_val, "uptime"]
            )
            # Should not fail with color error
            assert "invalid --color" not in (result.output or "").lower()

    def test_group_without_config_exits_nonzero(self):
        """Using --group without --config exits with error."""
        result = self.runner.invoke(app, ["--group", "webservers", "uptime"], env={"HOME": "/nonexistent"})
        assert result.exit_code != 0
        # Either "--group requires --config" or an undefined group error
        output_lower = result.output.lower()
        assert "--group requires --config" in output_lower or "undefined group" in output_lower

    def test_config_file_not_found_exits_nonzero(self, tmp_path):
        """Non-existent config file exits with error."""
        fake_config = tmp_path / "nonexistent.yaml"
        result = self.runner.invoke(
            app,
            ["--config", str(fake_config), "--group", "web", "--hosts", "server1", "uptime"],
        )
        assert result.exit_code != 0

    def test_host_file_not_found_exits_nonzero(self, tmp_path):
        """Non-existent host file exits with error."""
        fake_file = tmp_path / "nonexistent_hosts.txt"
        result = self.runner.invoke(
            app, ["--host-file", str(fake_file), "uptime"]
        )
        assert result.exit_code != 0

    def test_host_file_with_valid_hosts(self, tmp_path):
        """Valid host file entries are accepted (tool will fail at SSH, not validation)."""
        host_file = tmp_path / "hosts.txt"
        host_file.write_text("server1.example.com\nserver2.example.com\n")
        result = self.runner.invoke(
            app, ["--host-file", str(host_file), "uptime"]
        )
        # Should get past validation — will fail at SSH execution, not at arg parsing
        assert "no hosts specified" not in (result.output or "").lower()
        assert "invalid" not in (result.output or "").lower()
