from nose import with_setup

from superhub.requests.pages import DeviceConnectionStatusPage, DhcpReservationPage, IpFilteringPage, MacFilteringPage, \
    PortBlockingPage, PortForwardingPage, PortTriggeringPage
from superhub.requests.router import Router
from utils.password_vault import PasswordVault


def setup_func():
    global router
    router = Router("192.168.0.1", PasswordVault.get())
    router.login()


def teardown_func():
    global router
    router.logout()


@with_setup(setup_func, teardown_func)
def test_login_logout():
    global router


@with_setup(setup_func, teardown_func)
def test_DeviceStatusConnectionPage():
    global router
    page = DeviceConnectionStatusPage(router)
    assert page.wired_devices.caption == "Wired Devices"
    assert page.wireless_devices.caption == "Wireless Devices"
    page.dump()


@with_setup(setup_func, teardown_func)
def test_DhcpReservationPage():
    global router
    page = DhcpReservationPage(router)
    assert page.attached_devices.caption == "Attached Devices"
    assert page.ip_lease_table.caption == "IP Lease Table"
    page.dump()


@with_setup(setup_func, teardown_func)
def test_IpFilteringPage():
    global router
    page = IpFilteringPage(router)
    assert page.attached_devices.caption == "Attached Devices"
    assert page.ip_filter_list.caption == "IP Filter List"
    page.dump()


@with_setup(setup_func, teardown_func)
def test_MacFilteringPage():
    global router
    page = MacFilteringPage(router)
    assert page.attached_devices.caption == "Attached Devices"
    assert page.mac_filter_list.caption == "MAC Filter List"
    page.dump()


@with_setup(setup_func, teardown_func)
def test_PortBlockingPage():
    global router
    page = PortBlockingPage(router)
    assert page.port_blocking_rules.caption == "Port Blocking Rules"
    page.dump()


@with_setup(setup_func, teardown_func)
def test_PortForwardingPage():
    global router
    page = PortForwardingPage(router)
    assert page.port_forwarding_rules.caption == "Port Forwarding Rules"
    page.dump()


@with_setup(setup_func, teardown_func)
def test_PortTriggeringPage():
    global router
    page = PortTriggeringPage(router)
    assert page.port_triggering_rules.caption == "Port Trigger Rules"
    page.dump()