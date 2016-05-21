#!/usr/bin/python3

import subprocess

from concurrent.futures import ThreadPoolExecutor

HOSTS = ["pi1", "kano"]
DIRS = ["/dev", "/", "/dev/shm", "/run", "/run/lock", "/sys/fs/cgroup", "/boot"]

def get_space(hosts, dirs, max_workers=None):
    def get_space_for_one_host(host, dirs):
        cmd = ["ssh", host, "df", "-P"] + dirs
        output = subprocess.check_output(cmd).decode('ascii')
        lines = output.split("\n")
        map_ = {dir_: lines[idx].split()[4] for idx, dir_ in enumerate(dirs, 1)}
        return (host, map_)

    max_workers = max_workers or len(hosts)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(get_space_for_one_host, host, dirs) for host in hosts]
        results = [_.result() for _ in futures]
        return dict(results)

def print_table(table):
    ncols = len(table[0])
    widths = [max(len(row[col]) for row in table) for col in range(ncols)]
    fmt = "  ".join("{{:>{}}}".format(_) for _ in widths)
    for row in table:
        print(fmt.format(*row))

if __name__ == "__main__":
    data = get_space(HOSTS, DIRS)
    headers = [[""] + HOSTS]
    rows = [[dir_] + [data[host][dir_] for host in HOSTS] for dir_ in DIRS]
    table = headers + rows
    print_table(table)
