#!/usr/bin/env python3

import re

import requests
from bs4 import BeautifulSoup


class SuperHubError(Exception):
    pass


class LoginError(SuperHubError):
    pass


class PageError(SuperHubError):
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
