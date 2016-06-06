from superhub.requests.pages import DeviceConnectionStatusPage, DhcpReservationPage, IpFilteringPage, MacFilteringPage, \
    PortBlockingPage, PortForwardingPage, PortTriggeringPage
from superhub.requests.router import Router
from utils.password_vault import PasswordVault

if __name__ == "__main__":
    ipaddr = "192.168.0.1"
    password = PasswordVault.get()

    router = Router(ipaddr, password)
    router.login()

    DeviceConnectionStatusPage(router).dump()
    DhcpReservationPage(router).dump()
    IpFilteringPage(router).dump()
    MacFilteringPage(router).dump()
    PortBlockingPage(router).dump()
    PortForwardingPage(router).dump()
    PortTriggeringPage(router).dump()

    router.logout()
