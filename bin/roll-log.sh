#!/bin/bash

function make_copy_name {
    file=$1

    num=1
    copy="${file}-${num}"
    while [ -f ${copy} ]; do
        num=$[${num} + 1]
        copy="${file}-${num}"
    done
    
    echo ${copy}
}

function usage {
cat << EOF
Usage: $(basename $0) [ -C | -F ] [ -v ] [ -n ] <log-file> [ <log-copy> ]

Roll an open log file. This should be used only for log files created by processes
that don't already support log rolling. 

Options:
    -C     Use the copy-truncate method (this is the default). 
    -F     Use the fdswap method (experimental).
    -f     Roll log file even if it is closed.
    -v     Verbose mode.
    -n     Dry-run mode.

The copy-truncate method will work only for log files opened with the O_APPEND flag.

If <log-copy> is omitted a hyphen plus the next available sequential number is appended.
EOF
exit 1
}

method="copy-truncate"
force=""
verbose=""
dry_run=""

while getopts "CFfvn" opt; do
    case ${opt} in
        C) method="copy-truncate" ;;
        F) method="fdswap" ;;
        f) force=1 ;;
        v) verbose=1 ;;
        n) dry_run=1 ;;
        *) usage ;;
    esac
done

shift $((${OPTIND} - 1))

log=$1
copy=$2

[ "${log}" ] || usage

[ "${copy}" ] || copy=$(make_copy_name ${log})

# Check that the log file exists.
[ -f ${log} ] || {
    echo "File not found: ${log}"
    exit 1
}

# Check that the log copy doesn't exists.
[ -f ${copy} ] && {
    echo "File already exists: ${copy}"
    exit 1
}

# Check if <log-file> is opened.
if ! [ "${force}" ]; then
    if ! fuser ${log} > /dev/null 2>&1; then
        echo "Nothing to do because ${log} is currently not opened by any process."
        exit
    fi
fi

function run()
{
    cmd=$*
    if [ ${dry_run} ]; then
        echo "Would run ${cmd}"
    else
        if [ ${verbose} ]; then
            echo "Running ${cmd}"
        fi
        eval ${cmd} 
    fi
}

case ${method} in
    "copy-truncate")
        run cp ${log} ${copy}
        run truncate --size=0 ${log}
        ;;
    "fdswap")
        run /prod/cbtech/bin/fdswap ${log} ${copy}
        ;;
esac
