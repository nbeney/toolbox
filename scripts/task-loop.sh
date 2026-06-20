#!/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_TODO="${SCRIPT_DIR}/task-todo.sh"

OLD_SUM=0

while true; do
    NEW_SUM=$(task rc.verbose=none export | sum)
    if [ "${OLD_SUM}" != "${NEW_SUM}" ]; then
        clear
        "${TASK_TODO}"
        OLD_SUM=${NEW_SUM}
    fi
    sleep 2
done
