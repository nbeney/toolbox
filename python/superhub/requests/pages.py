import http
import re
from collections import namedtuple, OrderedDict

import requests
from bs4 import BeautifulSoup

from superhub.requests.router import PageError
from utils.table import Table


def get_table_from_list(name, text, caption, headers):
    data = re.search("var " + name + " = '([^']*)';", text, re.M).groups()[0]
    return Table(
        caption=caption,
        headers=headers,
        rows=[_.split("}-{") for _ in data.split("|,|")] if data else [],
    )


def get_table_from_table(table_id, soup, caption=None, ignore_cols=tuple()):
    def get_checkbox(val):
        inputs = val.find_all("input")
        if inputs and inputs[0]["type"] == "checkbox":
            res = inputs[0].get("checked")
            return res == ""
        else:
            return "???"

    def get_header(val):
        return get_value(val)

    def get_value(val):
        if val is None:
            return None
        elif val.string is None:
            l = list(val.stripped_strings)
            if l:
                return l[0]
            else:
                return get_checkbox(val)
        else:
            return val.string.strip()

    table = soup.find("table", id=table_id)
    caption = caption or table.caption.string
    headers = [get_header(_) for _ in table.thead.tr.find_all("th")]
    rows = [[get_value(td) for td in tr.find_all("td")] for tr in table.tbody.find_all("tr")]
    if rows == [[""]]:
        rows = []

    # Removed the ignored columns.
    for idx in sorted(ignore_cols, reverse=True):
        headers.pop(idx)
        for row in rows:
            row.pop(idx)

    return Table(
        caption=caption,
        headers=headers,
        rows=rows,
    )


class Page:
    def __init__(self, router, path, header):
        self.header = header
        self.router = router
        self.url = router.url + path

        self.resp = requests.get(self.url)
        with open("dump-" + path.split("/")[-1], "w") as fd:
            print(self.resp.text, file=fd)
        self.soup = BeautifulSoup(self.resp.text, "html.parser")
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
        self.attached_devices = get_table_from_list("DHCPClientList", self.resp.text, "Attached Devices",
                                                    ["Device Name", "MAC Address", "IP Address", "Interface"])
        self.ip_lease_table = get_table_from_list("DHCPReservationList", self.resp.text, "IP Lease Table",
                                                  ["Device Name", "MAC Address", "IP Address", "Expires"])
        self.tables = [self.attached_devices, self.ip_lease_table]


class IpFilteringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgIpFiltering.html", "IP Filtering")
        self.attached_devices = get_table_from_table("AttachedDevicesTableID", self.soup)
        self.ip_filter_list = get_table_from_table("MacFilterListTableID", self.soup, ignore_cols=(0, 4))
        self.tables = [self.attached_devices, self.ip_filter_list]


class MacFilteringPage(Page):
    MacEntry = namedtuple("MacEntry", ["device_name", "mac_address", "enable", "delete"])

    def __init__(self, router):
        super().__init__(router, "/VmRgMacFiltering.html", "MAC Filtering")
        self.attached_devices = get_table_from_table("AttachedDevicesTableID", self.soup)
        self.mac_filter_list = get_table_from_table("MacFilterListTableID", self.soup, ignore_cols=(0, 4))
        self.tables = [self.attached_devices, self.mac_filter_list]
        self.magic_name = self.soup.find_all("h3")[-1].parent.input["name"]

        self.entries = self._parse_entries()

    def add_entry(self, device_name, mac_address, enable):
        if len(self.entries) >= 30:
            raise PageError("Cannot have more than 30 entries")
        if device_name in self.entries:
            raise PageError("There is already an entry for " + device_name)
        if any(_.mac_address.lower() == mac_address.lower() for _ in self.entries.values()):
            raise PageError("There is already an entry for " + mac_address)
        self.entries[device_name] = self.MacEntry(device_name, mac_address.lower(), enable, delete=False)
        return self

    def delete_entry(self, device_name):
        if device_name not in self.entries:
            raise PageError("There is no entry for " + device_name)
        if not self.entries[device_name].delete:
            self.entries[device_name] = self.entries[device_name]._replace(delete=True)
        return self

    def enable_entry(self, device_name):
        if device_name not in self.entries:
            raise PageError("There is no entry for " + device_name)
        if not self.entries[device_name].enable:
            self.entries[device_name] = self.entries[device_name]._replace(enable=True)
        return self

    def disable_entry(self, device_name):
        if device_name not in self.entries:
            raise PageError("There is no entry for " + device_name)
        if self.entries[device_name].enable:
            self.entries[device_name] = self.entries[device_name]._replace(enable=False)
        return self

    def save(self):
        data = OrderedDict()
        for idx, entry in enumerate(self.entries.values()):
            data["VmMacFilterName" + str(idx)] = entry.device_name
            data["VmMacFilterMAC" + str(idx)] = entry.mac_address.lower()
            if entry.enable:
                data["VmMacFilterEnable" + str(idx)] = 1
            if entry.delete:
                data["VmMacFilterDelete" + str(idx)] = 1
        data[self.magic_name] = 0
        data["VmMACFilteringResetDefault"] = 0
        data["VmMACFilteringApplyValue"] = 1

        resp = requests.post(self.router.url + "/cgi-bin/MacTodFilteringCgi", data)
        assert resp.status_code == http.client.OK

    def _parse_entries(self):
        entries = OrderedDict()
        for device_name, mac_address, enable in self.mac_filter_list.rows:
            entry = self.MacEntry(device_name, mac_address.lower(), enable, delete=False)
            entries[entry.device_name] = entry
        return entries


class PortBlockingPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortFiltering.html", "Port Blocking")
        self.port_blocking_rules = get_table_from_table("PortBlockingRuleTable", self.soup,
                                                        caption="Port Blocking Rules")
        self.tables = [self.port_blocking_rules]


class PortForwardingPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortForwarding.html", "Port Forwarding")
        self.port_forwarding_rules = get_table_from_table("PortForwardingRuleTable", self.soup,
                                                          caption="Port Forwarding Rules")
        self.tables = [self.port_forwarding_rules]


class PortTriggeringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortTriggering.html", "Port Triggering")
        self.port_triggering_rules = get_table_from_table("PortTriggeringRuleTable", self.soup,
                                                          caption="Port Trigger Rules")
        self.tables = [self.port_triggering_rules]

# TODO: DeviceStatusPage
# TODO: NetworkLogPage
# TODO: FirewallLogPage
