#!/usr/bin/bash

AWS_PROFILE=restic-backup restic --repo="s3:s3.${RESTIC_S3_REGION}.amazonaws.com/${RESTIC_S3_BUCKET}" --password-file="${HOME}/secrets/restic-password" $@
