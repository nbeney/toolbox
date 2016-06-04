from superhub.pages import DeviceConnectionStatusPage, DhcpReservationPage, IpFilteringPage, MacFilteringPage, \
    PortBlockingPage, PortForwardingPage, PortTriggeringPage
from superhub.router import Router, IPADDR, PASSWORD

if __name__ == "__main__":
    router = Router(IPADDR, PASSWORD)
    router.login()

    DeviceConnectionStatusPage(router).dump()
    DhcpReservationPage(router).dump()
    IpFilteringPage(router).dump()
    MacFilteringPage(router).dump()
    PortBlockingPage(router).dump()
    PortForwardingPage(router).dump()
    PortTriggeringPage(router).dump()

    router.logout()
