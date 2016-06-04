from superhub.scraping import get_table

# ROUTER_IP_FILTERING_URL = "%s/VmRgIpFiltering.html" % ROUTER_URL
# ROUTER_MAC_FILTERING_URL = "%s/VmRgMacFiltering.html" % ROUTER_URL
# ROUTER_PORT_FILTERING_URL = "%s/VmRgPortFiltering.html" % ROUTER_URL
# ROUTER_PORT_FORWARDING_URL = "%s/VmRgPortForwarding.html" % ROUTER_URL
# ROUTER_PORT_TRIGGERING_URL = "%s/VmRgPortTriggering.html" % ROUTER_URL
# ROUTER_DEVICE_STATUS_URL = "%s/VmRgDeviceStatus.html" % ROUTER_URL
# ROUTER_NETWORK_STATUS_URL = "%s/VmRgNetworkStatus.html" % ROUTER_URL
# ROUTER_NETWORK_LOG_URL = "%s/VmRgNetworkLog.html" % ROUTER_URL
# ROUTER_FIREWALL_LOG_URL = "%s/VmRgFirewallLog.html" % ROUTER_URL


class Page:
    def __init__(self, router, path):
        self.router = router
        self.driver = router.driver
        self.path = path
        self.url = router.url + path
        self.driver.get(self.url)


class DeviceConnectionStatusPage(Page):
    def __init__(self, router):
        super().__init__(router, "/device_connection_status.html")
        table_elems = self.driver.find_elements_by_tag_name("table")
        self.wired_devices = get_table(table_elems[1])
        self.wireless_devices = get_table(table_elems[2])
