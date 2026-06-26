#!/usr/bin/bash

# Scan the screen for QR codes using scrot and zbarimg.

missing=()

for cmd in scrot zbarimg; do
    if ! command -v "$cmd" &>/dev/null; then
        missing+=("$cmd")
    fi
done

if [ ${#missing[@]} -ne 0 ]; then
    echo "Error: missing required command(s): ${missing[*]}"
    echo ""
    echo "Install them with:"
    echo "  sudo apt install scrot zbar-tools"
    exit 1
fi

TMP_FILE=/tmp/full-screen.png

scrot "${TMP_FILE}" && zbarimg --raw --quiet "${TMP_FILE}" 2>/dev/null && rm -f "${TMP_FILE}"
