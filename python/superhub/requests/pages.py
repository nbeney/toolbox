import re

import requests
from bs4 import BeautifulSoup

from utils.table import Table


class Page:
    def __init__(self, router, path, header):
        self.header = header
        self.router = router
        self.url = router.url + path

        self.resp = requests.get(self.url)
        assert header in self.resp.text, header

    def dump(self):
        self.dump_header()
        self.dump_details()
        self.dump_footer()

    def dump_header(self):
        print("=" * 60)
        print(self.header)
        print("=" * 60)
        print()

    def dump_details(self):
        for table in self.tables:
            table.pretty_print()
            print()

    def dump_footer(self):
        print()


def get_table_from_list(name, text, caption, headers):
    data = re.search("var " + name + " = '([^']*)';", text, re.M).groups()[0]
    return Table(
        caption=caption,
        headers=headers,
        rows=[_.split("}-{") for _ in data.split("|,|")] if data else [],
    )


def get_table_from_table(table_id, html, caption=None):
    def get_value(val):
        if val is None:
            return None
        elif val.string is None:
            return None
        else:
            return val.string.strip()

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id=table_id)
    caption = caption or table.caption.string
    headers = [_ for _ in table.thead.strings if _ not in  ("\n", "\xa0")]
    rows = [[get_value(td) for td in tr.find_all("td")] for tr in table.tbody.find_all("tr")]
    if rows == [[""]]:
        rows = []

    return Table(
        caption=caption,
        headers=headers,
        rows=rows,
    )


class DeviceConnectionStatusPage(Page):
    def __init__(self, router):
        super().__init__(router, "/device_connection_status.html", "Device Connection Status")
        self.wired_devices = get_table_from_list("WiredDevicesList", self.resp.text, "Wired Devices",
                                                 ["MAC Address", "IP Address", "Device Name", "Time Connected"])
        self.wireless_devices = get_table_from_list("WifiDevicesList", self.resp.text, "Wireless Devices",
                                                    ["MAC Address", "IP Address", "Device Name", "Time Connected"])
        self.tables = [self.wired_devices, self.wireless_devices]

class DhcpReservationPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgDhcpReservation.html", "DHCP Reservation")
        self.attached_devices = get_table_from_list("DHCPClientList", self.resp.text, "Attached Devices", ["Device Name", "MAC Address", "IP Address", "Interface"])
        self.ip_lease_table = get_table_from_list("DHCPReservationList", self.resp.text, "IP Lease Table", ["Device Name", "MAC Address", "IP Address", "Expires"])
        self.tables = [self.attached_devices, self.ip_lease_table]

class IpFilteringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgIpFiltering.html", "IP Filtering")
        self.attached_devices = get_table_from_table("AttachedDevicesTableID", self.resp.text)
        self.ip_filter_list = get_table_from_table("MacFilterListTableID", self.resp.text)
        self.timed_access = get_table_from_table("TimedAccessTableID", self.resp.text)
        self.tables = [self.attached_devices, self.ip_filter_list, self.timed_access]


class MacFilteringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgMacFiltering.html", "MAC Filtering")
        self.attached_devices = get_table_from_table("AttachedDevicesTableID", self.resp.text)
        self.mac_filter_list = get_table_from_table("MacFilterListTableID", self.resp.text)
        self.timed_access = get_table_from_table("TimedAccessTableID", self.resp.text)
        self.tables = [self.attached_devices, self.mac_filter_list, self.timed_access]


class PortBlockingPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortFiltering.html", "Port Blocking")
        self.port_blocking_rules = get_table_from_table("PortBlockingRuleTable", self.resp.text, caption="Port Blocking Rules")
        self.tables = [self.port_blocking_rules]


class PortForwardingPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortForwarding.html", "Port Forwarding")
        self.port_forwarding_rules = get_table_from_table("PortForwardingRuleTable", self.resp.text, caption="Port Forwarding Rules")
        self.tables = [self.port_forwarding_rules]


class PortTriggeringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortTriggering.html", "Port Triggering")
        self.port_triggering_rules = get_table_from_table("PortTriggeringRuleTable", self.resp.text, caption="Port Trigger Rules")
        self.tables = [self.port_triggering_rules]

# TODO: DeviceStatusPage
# TODO: NetworkLogPage
# TODO: FirewallLogPage
