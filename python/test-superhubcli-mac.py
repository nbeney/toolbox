import os

from click.testing import CliRunner
from nose import with_setup

from  superhubcli import cli

runner = CliRunner()


def run(args, expected=[], unexpected=[], fail=False):
    prefix = ["--password", os.environ["SUPERHUB_PASSWORD"], "--keep-logged-in", "mac"]
    res = runner.invoke(cli, prefix + args)
    assert (not fail and res.exit_code == 0) or (fail and res.exit_code != 0)
    for _ in expected:
        assert _ in res.output, _
    for _ in unexpected:
        assert _ not in res.output, _


def setup_func():
    run(["delete", "TEST*"])


def teardown_func():
    run(["delete", "TEST*"])


@with_setup(setup_func, teardown_func)
def test_mac_list():
    run(["add", "TEST1", "11:11:11:11:11:11", "yes"])
    run(["list"], expected=["Device Name", "MAC Address", "Enable", "TEST1", "11:11:11:11:11:11", "True"])


@with_setup(setup_func, teardown_func)
def test_mac_add():
    run(["add", "TEST1", "11:11:11:11:11:11", "yes"])
    run(["add", "TEST1", "11:11:11:11:11:11", "yes"], fail=True)
    run(["list"], expected=["TEST1", "11:11:11:11:11:11", "True"])
    run(["add", "TEST2", "", "yes"], fail=True)
    run(["add", "TEST3", "abc", "yes"], fail=True)
    run(["add", "TEST4", "44:44:44:4g:44:44", "yes"], fail=True)


@with_setup(setup_func, teardown_func)
def test_mac_delete():
    run(["add", "TEST1", "11:11:11:11:11:11", "yes"])
    run(["add", "TEST2", "22:22:22:22:22:22", "yes"])
    run(["add", "TEST3", "33:33:33:33:33:33", "yes"])
    run(["add", "TEST4", "44:44:44:44:44:44", "yes"])
    run(["add", "TEST5", "55:55:55:55:55:55", "yes"])
    run(["add", "TEST6", "66:66:66:66:66:66", "yes"])
    run(["add", "TEST7", "77:77:77:77:77:77", "yes"])
    run(["list"], expected=["TEST1", "TEST2", "TEST3", "TEST4", "TEST5", "TEST6", "TEST7"])
    run(["delete", "TEST2"])
    run(["list"], expected=["TEST1", "TEST3", "TEST4", "TEST5", "TEST6", "TEST7"], unexpected=["TEST2"])
    run(["delete", "TEST4", "TEST5"])
    run(["list"], expected=["TEST1", "TEST3", "TEST6", "TEST7"], unexpected=["TEST2", "TEST4", "TEST5"])
    run(["delete", "TEST*"])
    run(["list"], unexpected=["TEST"])


@with_setup(setup_func, teardown_func)
def test_mac_enable():
    run(["add", "TEST1", "11:11:11:11:11:11", "no"])
    run(["list"], expected=["TEST1", "11:11:11:11:11:11", "False"])
    run(["enable", "TEST1"])
    run(["list"], expected=["TEST1", "11:11:11:11:11:11", "True"])


@with_setup(setup_func, teardown_func)
def test_mac_disable():
    run(["add", "TEST1", "11:11:11:11:11:11", "yes"])
    run(["list"], expected=["TEST1", "11:11:11:11:11:11", "True"])
    run(["disable", "TEST1"])
    run(["list"], expected=["TEST1", "11:11:11:11:11:11", "False"])
