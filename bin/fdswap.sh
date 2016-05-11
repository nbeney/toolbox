#!/bin/bash
#
# Swap/Roll a file handle between processes.
#
# Posted at https://groups.google.com/forum/#!topic/alt.hackers/0ZMsMc5DvUw
#
# Usage:
#
#    fdswap.sh <old logfile>    <new logfile> [optional pids]
#    fdswap.sh /var/log/logfile /tmp/logfile  [pids]
#
# Author: Robert McKay
# Date: Tue Aug 14 13:36:35 BST 2007

src=$1; shift
dst=$1; shift
pids=$*

for pid in ${pids:=$(fuser $src)}; do
    echo "${src} has ${pid} using it..."
    (
	echo "attach ${pid}"
	echo 'call open("'${dst}'", 66, 0666)'
	for ufd in $(ls -l /proc/${pid}/fd | grep ${src}\$ | awk '{print $9;}'); do
	    echo 'call dup2($1, '${ufd}')'
	done
	echo 'call close($1)'
	echo 'detach'
	echo 'quit'
	sleep 3
    ) | gdb -q -x -
done
