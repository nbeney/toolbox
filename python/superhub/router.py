import os

from nose.tools import with_setup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from superhub.pages import DeviceConnectionStatusPage, DhcpReservationPage, IpFilteringPage, MacFilteringPage, \
    PortBlockingPage, PortForwardingPage, PortTriggeringPage

IPADDR = "192.168.0.1"
PASSWORD = None  # the SUPERHUB_PASSWORD environment variable will be used if unset


class Router:
    def __init__(self, ipaddr, password):
        if not password:
            password = os.environ["SUPERHUB_PASSWORD"]

        self.ipaddr = ipaddr
        self.password = password
        self.url = "http://" + ipaddr
        self.driver = webdriver.Chrome()

    def login(self):
        self.driver.get(self.url)
        password = self.driver.find_element_by_id("password")
        password.send_keys(self.password, Keys.ENTER)
        assert "Manage your Super Hub and wireless network" in self.driver.page_source

    def logout(self):
        try:
            self.driver.close()
            self.driver.quit()
        except:
            pass


def setup_func():
    global router
    router = Router(IPADDR, PASSWORD)
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
    assert page.timed_access.caption == "Timed Access"
    page.dump()


@with_setup(setup_func, teardown_func)
def test_MacFilteringPage():
    global router
    page = MacFilteringPage(router)
    assert page.attached_devices.caption == "Attached Devices"
    assert page.mac_filter_list.caption == "MAC Filter List"
    assert page.timed_access.caption == "Timed Access"
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
