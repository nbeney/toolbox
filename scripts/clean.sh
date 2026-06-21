#!/usr/bin/bash

dry_run=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--dry-run) dry_run=true; shift ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

clean() {
    local pattern="${1}"
    local rm_opts="${2}"
    find . -name "${pattern}" | fgrep -v /.venv/ | while read -r path; do
        if "${dry_run}"; then
            echo "Would remove: ${path}"
        else
            echo "Removing: ${path}"
            rm ${rm_opts} "${path}"
        fi
    done
}

clean "htmlcov"     "-fr"
clean "__pycache__" "-fr"
clean "*.pyc"       ""
