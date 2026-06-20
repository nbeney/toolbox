#!/usr/bin/bash

FILE=${1:?Missing FILE!}

TMP_FILE_PREFIX=/tmp/scan_

echo "===== Deleting old ${TMP_FILE_PREFIX}*.tiff files ..."
rm -fr ${TMP_FILE_PREFIX}*.tiff

echo "===== Launching scanimage ..."
scanimage --batch=${TMP_FILE_PREFIX}%d.tiff --batch-start=1 --batch-prompt --format=tiff --resolution=300

echo "===== Generating PDF ..."
convert ${TMP_FILE_PREFIX}*.tiff "${FILE}"

echo "===== Deleting new ${TMP_FILE_PREFIX}*.tiff files"
rm -fr ${TMP_FILE_PREFIX}*.tiff

echo "===== PDF created: ${FILE}"
