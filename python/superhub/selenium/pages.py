from superhub.selenium.scraping import get_table


class Page:
    def __init__(self, router, path, header):
        self.header = header
        self.router = router
        self.driver = router.driver
        self.url = router.url + path

        self.driver.get(self.url)
        assert header in self.driver.page_source, header

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
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.wired_devices = get_table(table_elems[1])
        self.wireless_devices = get_table(table_elems[2])
        self.tables = [self.wired_devices, self.wireless_devices]


class DhcpReservationPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgDhcpReservation.html", "DHCP Reservation")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.attached_devices = get_table(table_elems[0])
        self.ip_lease_table = get_table(table_elems[2])
        self.tables = [self.attached_devices, self.ip_lease_table]


class IpFilteringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgIpFiltering.html", "IP Filtering")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.attached_devices = get_table(table_elems[0])
        self.ip_filter_list = get_table(table_elems[2])
        self.timed_access = get_table(table_elems[4])
        self.tables = [self.attached_devices, self.ip_filter_list, self.timed_access]


class MacFilteringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgMacFiltering.html", "MAC Filtering")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.attached_devices = get_table(table_elems[0])
        self.mac_filter_list = get_table(table_elems[2])
        self.timed_access = get_table(table_elems[4])
        self.tables = [self.attached_devices, self.mac_filter_list, self.timed_access]


class PortBlockingPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortFiltering.html", "Port Blocking")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.port_blocking_rules = get_table(table_elems[1], caption="Port Blocking Rules")
        self.tables = [self.port_blocking_rules]


class PortForwardingPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortForwarding.html", "Port Forwarding")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.port_forwarding_rules = get_table(table_elems[1], caption="Port Forwarding Rules")
        self.tables = [self.port_forwarding_rules]


class PortTriggeringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortTriggering.html", "Port Triggering")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.port_triggering_rules = get_table(table_elems[1], caption="Port Trigger Rules")
        self.tables = [self.port_triggering_rules]

# TODO: DeviceStatusPage
# TODO: NetworkLogPage
# TODO: FirewallLogPage
