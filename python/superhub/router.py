from nose import with_setup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from superhub.pages import DeviceConnectionStatusPage

IPADDR = "192.168.0.1"
PASSWORD = "S5g5r0ck18"


class SuperHub:
    def __init__(self, ipaddr, password):
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
    router = SuperHub(IPADDR, PASSWORD)
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
