#!/bin/bash

# Check that gdb is installed.
gdb --version > /dev/null 2>&1 || {
    echo "Unable to find gdb."
    exit 1
}

function usage {
cat << EOF
Usage: $(basename $0) [ -p <pids> ] <old-log-file> <new-log-file>

Swap/roll a file handle between processes.

Options:
    -p     Space separated list of PIDs (all the PIDs having <old-log-file> open if not specified) 
    -M     Mode (integer) to open <new-log-file> (02102 (i.e. O_APPEND|O_CREAT|O_RDWR) if not specified)
    -P     Permissions (integer) for <new-log-file> (the permissions of <old-log-file> if not specified)
    -v     Verbose mode.
    -n     Dry-run mode.

The <new-log-file> will be opened using the open(path, mode, perm) system call. See man 2 open for details. The flag values
for making mode are defined in /usr/include/bits/fcntl.h.
EOF
exit 1
}

while getopts ":p:M:Pvn" opt; do
    case $opt in
        p) pids=${OPTARG} ;;
        M) mode=${OPTARG} ;;
        P) perm=${OPTARG} ;;
        v) verbose=1 ;;
        n) dry_run=1 ;;
        *) usage ;;
    esac
done

shift $((${OPTIND} - 1))

src=$1
dst=$2

[ "${src}" ] || usage
[ "${dst}" ] || usage

# Check that the source file exists.
[ -f ${src} ] || {
    echo "File not found: ${src}"
    exit 1
}

# Set default option values if necessary.
[ "${pids}" ] || pids=$(fuser ${src})
[ "${mode}" ] || mode=02102
[ "${perm}" ] || perm=$(stat -c 0%a ${src})

# Make the file paths absolute because the CWD of the processes we are going to attach to
# may be different from the current directory.
src=$(readlink -f ${src})
dst=$(readlink -f ${dst})

function print_gdb_script()
{
    pid=$1
    echo "attach ${pid}"
    echo 'call open("'${dst}'", '${mode}', '${perm}')'
    for ufd in $(ls -l /proc/${pid}/fd | grep ${src}\$ | awk '{print $9;}'); do
	echo 'call dup2($1, '${ufd}')'
    done
    echo 'call close($1)'
    echo 'detach'
    echo 'output "***** Waiting for a few seconds... *****"'
    echo 'quit'
}

for pid in ${pids}; do
    echo -------------------------------
    echo "${src} is used by pid ${pid} ..."
    if [ ${dry_run} ]; then
        echo "Would run this script in gdb:"
        print_gdb_script ${pid}
    else
        if [ ${verbose} ]; then
            echo "Running this script in gdb:"
            print_gdb_script ${pid}
        fi
        (
            print_gdb_script ${pid}
	    sleep 3
        ) | gdb -q -x -
        echo
    fi
done
