#!/usr/bin/bash

LOCATIONS="local aws gcs qnap"

for loc in ${LOCATIONS}; do
    echo
    printf "${TBX_ANSI_BG_WHITE}${TBX_ANSI_FG_BLACK}%-110s${TBX_ANSI_RESET}\n" "${loc@U}"
    restic-${loc}.sh snapshots
done
