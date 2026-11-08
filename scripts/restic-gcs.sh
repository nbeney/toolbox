#!/usr/bin/bash

GOOGLE_PROJECT_ID="${RESTIC_GCS_PROJECT_ID}" GOOGLE_APPLICATION_CREDENTIALS="${HOME}/secrets/restic-gcs-key.json" restic --repo="gs:${RESTIC_GCS_BUCKET}:/" --password-file="${HOME}/secrets/restic-password" $@
