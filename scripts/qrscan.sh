#!/usr/bin/bash

TMP_FILE=/tmp/full-screen.png

scrot ${TMP_FILE} && zbarimg --raw --quiet ${TMP_FILE} 2>/dev/null && rm ${TMP_FILE}
