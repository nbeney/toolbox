#!/usr/bin/python3

"""
Command line utility to print out the free space for a list of hosts and directories.
"""

import subprocess

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

HOSTS = ["pi1", "kano"]
DIRS = ["/dev", "/", "/dev/shm", "/run",
        "/run/lock", "/sys/fs/cgroup", "/boot"]

DfStats = namedtuple("DfStats", "total available used used_pct")


def get_space(hosts, dirs):
    """
    Check the free space for a list of hosts and directories.

    Return a dict of the form {host: {dir: DfStats}}.

    <DfStats> is a namedtuple with the following fields: total, available, used, and used_pct.
    """

    def get_space_for_one_host(host, dirs):
        cmd = ["ssh", host, "df", "-P"] + dirs
        output = subprocess.check_output(cmd).decode('ascii')
        lines = output.split("\n")
        map_ = {dir_: DfStats(*lines[idx].split()[1:5])
                for idx, dir_ in enumerate(dirs, 1)}
        return (host, map_)

    with ThreadPoolExecutor(max_workers=len(hosts)) as pool:
        futures = [pool.submit(get_space_for_one_host, host, dirs)
                   for host in hosts]
        results = [_.result() for _ in futures]
        return dict(results)


def print_table(table):
    """
    Pretty-print a table.

    <table> is a list of lists. Each row must have the same length.
    """

    ncols = len(table[0])
    widths = [max(len(row[col]) for row in table) for col in range(ncols)]
    fmt = "  ".join("{{:>{}}}".format(_) for _ in widths)
    for row in table:
        print(fmt.format(*row))

if __name__ == "__main__":
    data = get_space(HOSTS, DIRS)
    headers = [[""] + HOSTS]
    rows = [[dir_] + [data[host][dir_].used_pct for host in HOSTS]
            for dir_ in DIRS]
    table = headers + rows
    print_table(table)
