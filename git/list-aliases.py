#!python

from __future__ import print_function

import os
import subprocess


def highlight(text):
    return os.environ["ANSI_FG_GREEN"] + text + os.environ["ANSI_RESET"]


def dim(text):
    return os.environ["ANSI_DIM"] + text + os.environ["ANSI_RESET"]


lines = subprocess.check_output(['git', 'config', '--get-regexp', '^alias']).splitlines()

aliases = []
for line in sorted(lines):
    line = line.replace("alias.", "")
    items = line.split(" ")
    alias = items[0]
    command = " ".join(items[1:])
    aliases.append((alias, command))

max = max(len(_[0]) for _ in aliases)
for alias, command in aliases:
    leader = "-" * (max - len(alias) + 3)
    print("{} {} {}".format(highlight(alias), dim(leader), command))

