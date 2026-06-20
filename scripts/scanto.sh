#!/usr/bin/bash

FORMAT=${1:?Missing FORMAT!}
FILE=${2:?Missing FILE!}
RESOLUTION=${3:?Missing RESOLUTION!}

TMP_FILE_PREFIX=/tmp/scan_

echo "===== Deleting old ${TMP_FILE_PREFIX}*.${FORMAT} files ..."
rm -fr ${TMP_FILE_PREFIX}*.${FORMAT}

echo "===== Launching scanimage ..."
scanimage --batch=${TMP_FILE_PREFIX}%d.${FORMAT} --batch-start=1 --batch-prompt --format=${FORMAT} --resolution=${RESOLUTION}

echo "===== Scan complete"
ls -l ${TMP_FILE_PREFIX}*.${FORMAT}
