#!/usr/bin/bash

restic --repo="${RESTIC_LOCAL_DIR}" --password-file="${HOME}/secrets/restic-password" $@
