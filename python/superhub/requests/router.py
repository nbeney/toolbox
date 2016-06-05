#!/usr/bin/env python3

import re
import urllib.parse
import urllib.request

import requests
from bs4 import BeautifulSoup
from nose import with_setup

from superhub.requests.pages import DeviceConnectionStatusPage, DhcpReservationPage, IpFilteringPage, MacFilteringPage, \
    PortBlockingPage, PortForwardingPage, PortTriggeringPage
from utils.password_vault import PasswordVault


class LoginError(Exception):
    pass


class Router:
    def __init__(self, ipaddr, password):
        self.ipaddr = ipaddr
        self.password = password
        self.url = "http://" + ipaddr

    # Login seems to be done purely on the basis of ip address, once logged in, no cookies or anything else is required
    # to be sent
    def login(self):
        home_url = self.url + "/home.html"
        home_resp = requests.get(home_url)
        page = home_resp.text
        logged_in = home_resp.url == home_url

        while not logged_in:
            soup = BeautifulSoup(page, "html.parser")
            password_name = soup.find("input", id="password")["name"]

            login_url = self.url + "/cgi-bin/VmLoginCgi"
            data = {password_name: self.password}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            login_resp = requests.post(login_url, data=data, headers=headers)
            page = login_resp.text

            match = re.search('^\tvar res="([^"]*)";', page, re.M)
            if match.group(1) == "0":
                logged_in = True
            elif match.group(1) == "1":
                print("Incorrect password")
            else:
                raise LoginError

    def logout(self):
        # urllib.request.urlopen(self.url + "/VmLogout2.html")
        logout_url = self.url + "/VmLogout2.html"
        requests.get(logout_url)


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
