from superhub.scraping import get_table


class Page:
    def __init__(self, router, path, header):
        self.header = header
        self.router = router
        self.driver = router.driver
        self.url = router.url + path

        self.driver.get(self.url)
        assert header in self.driver.page_source, header

    def dump(self):
        print("=" * 60)
        print(self.header)
        print("=" * 60)
        print()
        self.dump_details()
        print()
        print()

    def dump_details(self):
        raise NotImplemented()


class DeviceConnectionStatusPage(Page):
    def __init__(self, router):
        super().__init__(router, "/device_connection_status.html", "Device Connection Status")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.wired_devices = get_table(table_elems[1])
        self.wireless_devices = get_table(table_elems[2])

    def dump_details(self):
        self.wired_devices.pretty_print()
        print()
        self.wireless_devices.pretty_print()


class DhcpReservationPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgDhcpReservation.html", "DHCP Reservation")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.attached_devices = get_table(table_elems[0])
        self.ip_lease_table = get_table(table_elems[2])

    def dump_details(self):
        self.attached_devices.pretty_print()
        print()
        self.ip_lease_table.pretty_print()


class IpFilteringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgIpFiltering.html", "IP Filtering")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.attached_devices = get_table(table_elems[0])
        self.ip_filter_list = get_table(table_elems[2])
        self.timed_access = get_table(table_elems[4])

    def dump_details(self):
        self.attached_devices.pretty_print()
        print()
        self.ip_filter_list.pretty_print()
        print()
        self.timed_access.pretty_print()


class MacFilteringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgMacFiltering.html", "MAC Filtering")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.attached_devices = get_table(table_elems[0])
        self.mac_filter_list = get_table(table_elems[2])
        self.timed_access = get_table(table_elems[4])

    def dump_details(self):
        self.attached_devices.pretty_print()
        print()
        self.mac_filter_list.pretty_print()
        print()
        self.timed_access.pretty_print()


class PortBlockingPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortFiltering.html", "Port Blocking")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.port_blocking_rules = get_table(table_elems[1], caption="Port Blocking Rules")

    def dump_details(self):
        self.port_blocking_rules.pretty_print()


class PortForwardingPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortForwarding.html", "Port Forwarding")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.port_forwarding_rules = get_table(table_elems[1], caption="Port Forwarding Rules")

    def dump_details(self):
        self.port_forwarding_rules.pretty_print()


class PortTriggeringPage(Page):
    def __init__(self, router):
        super().__init__(router, "/VmRgPortTriggering.html", "Port Triggering")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.port_triggering_rules = get_table(table_elems[1], caption="Port Trigger Rules")

    def dump_details(self):
        self.port_triggering_rules.pretty_print()

# TODO: DeviceStatusPage
# TODO: NetworkLogPage
# TODO: FirewallLogPage
