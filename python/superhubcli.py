import re
import sys
from contextlib import contextmanager
from fnmatch import fnmatch

import click

from superhub.requests.pages import DeviceConnectionStatusPage, DhcpReservationPage, IpFilteringPage, MacFilteringPage, \
    PortBlockingPage, PortForwardingPage, PortTriggeringPage
from superhub.requests.router import Router, SuperHubError


def validate_mac_address(ctx, param, value):
    value = value.lower()
    hex_digit_pair = "[0-9A-F]{2}"
    if not re.match(":".join([hex_digit_pair] * 6), value):
        raise click.BadParameter("MAC addresses must be in format xx:xx:xx:xx:xx:xx")
    return value


@contextmanager
def get_router(ctx):
    try:
        router = Router(ctx.host, ctx.password)
        router.login()
        yield router
    except SuperHubError as e:
        sys.exit("Error: " + str(e))
    finally:
        if not ctx.keep_logged_in:
            router.logout()


# TODO: This should be moved to a click_utils module.
def fill_context(ctx, dict_):
    assert hasattr(ctx.__class__, "__slots__")
    for k, v in dict_.items():
        if k in ctx.__class__.__slots__:
            setattr(ctx, k, v)


class Context:
    __slots__ = ["host", "password", "keep_logged_in", "verbose"]


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group(help="Command line utility tool for the Virgin Media Super Hub router.")
@click.option("-H", "--host", default="192.168.0.1", show_default=True, help="The IP address/host name of the router.")
@click.option("-P", "--password", prompt=True, hide_input=True, help="The admin password.")
@click.option("-K", "--keep-logged-in", is_flag=True, help="Keep logged in when done.")
@click.option("-v", "--verbose", is_flag=True, help="Activate the verbose output mode.")
@pass_context
def cli(ctx, host, password, keep_logged_in, verbose):
    fill_context(ctx, locals())


@cli.command(help="Check the status of the router.")
@pass_context
def status(ctx):
    with get_router(ctx) as router:
        DeviceConnectionStatusPage(router).dump()
        DhcpReservationPage(router).dump()
        IpFilteringPage(router).dump()
        MacFilteringPage(router).dump()
        PortBlockingPage(router).dump()
        PortForwardingPage(router).dump()
        PortTriggeringPage(router).dump()


@cli.group(help="IP related commands.")
@pass_context
def ip(ctx):
    pass


@ip.command(name="list", help="Print the IP Filter table.")
@pass_context
def list_ip(ctx):
    with get_router(ctx) as router:
        IpFilteringPage(router).ip_filter_list.pretty_print(caption=False)


@cli.group(help="MAC related commands.")
@pass_context
def mac(ctx):
    pass


@mac.command(name="list", help="Print the MAC Filter table.")
@pass_context
def list_mac(ctx):
    with get_router(ctx) as router:
        MacFilteringPage(router).mac_filter_list.pretty_print(caption=False)


@mac.command(name="add", help="Add a new entry to the MAC Filter table.")
@click.argument("device-name")
@click.argument("mac-address", callback=validate_mac_address)
@click.argument("enable", type=bool)
@pass_context
def add_mac(ctx, device_name, mac_address, enable):
    with get_router(ctx) as router:
        MacFilteringPage(router).add_entry(device_name, mac_address, enable).save()


@mac.command(name="delete", help="Delete an entry from the MAC Filter table.")
@click.argument("device-name", nargs=-1)
@pass_context
def delete_mac(ctx, device_name):
    apply_mac(ctx, device_name, MacFilteringPage.delete_entry)


@mac.command(name="enable", help="Enable an entry in the MAC Filter table.")
@click.argument("device-name", nargs=-1)
@pass_context
def enable_mac(ctx, device_name):
    apply_mac(ctx, device_name, MacFilteringPage.enable_entry)


@mac.command(name="disable", help="Disable an entry in the MAC Filter table.")
@click.argument("device-name", nargs=-1)
@pass_context
def disable_mac(ctx, device_name):
    apply_mac(ctx, device_name, MacFilteringPage.disable_entry)


def apply_mac(ctx, device_name, method):
    with get_router(ctx) as router:
        page = MacFilteringPage(router)
        dns = set(entry.device_name for entry in page.entries.values() if
                  any(fnmatch(entry.device_name, _) for _ in device_name))
        for dn in dns:
            method(page, dn)
        page.save()


if __name__ == "__main__":
    try:
        cli(auto_envvar_prefix="SUPERHUB")
    except KeyboardInterrupt:
        pass
