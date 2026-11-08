#!/usr/bin/bash

restic --repo="sftp:qnap:${RESTIC_QNAP_DIR}" --password-file="${HOME}/secrets/restic-password" $@
