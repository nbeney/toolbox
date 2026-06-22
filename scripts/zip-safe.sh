#!/usr/bin/env bash
# sip-safe.sh
# Usage: ./zip-safe.sh <output-name> <file-or-dir> [file-or-dir ...]
# Example: ./zip-safe.sh tax2025 ./invoices ./contracts/nda.pdf

set -euo pipefail

# ── Arguments ────────────────────────────────────────────────────────────────
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <output-name> <file-or-dir> [file-or-dir ...]"
    exit 1
fi

OUTPUT_NAME="$1"
shift
SOURCES=("$@")

# ── Password (prompted once, never visible in shell history) ──────────────────
read -rsp "Enter archive password: " PASSWORD
echo
read -rsp "Confirm password:       " PASSWORD2
echo
if [[ "$PASSWORD" != "$PASSWORD2" ]]; then
    echo "Passwords do not match. Aborting." >&2
    exit 1
fi

# ── Create archives ───────────────────────────────────────────────────────────

# 1. ZIP — widest tool compatibility (Windows, macOS, Linux)
#    AES-256 encryption via zip (needs zip ≥ 3.0) or 7z
if command -v 7z &>/dev/null; then
    7z a -tzip -mem=AES256 -p"$PASSWORD" "${OUTPUT_NAME}.zip" "${SOURCES[@]}"
    echo "✓  ${OUTPUT_NAME}.zip  (AES-256, via 7z)"
elif command -v zip &>/dev/null; then
    zip -r --encrypt --password "$PASSWORD" "${OUTPUT_NAME}.zip" "${SOURCES[@]}"
    echo "✓  ${OUTPUT_NAME}.zip  (ZipCrypto — legacy, weaker)"
fi

# 2. 7z — strongest encryption; needs 7-Zip on the recipient's side
if command -v 7z &>/dev/null; then
    7z a -t7z -mhe=on -mmt=on -p"$PASSWORD" "${OUTPUT_NAME}.7z" "${SOURCES[@]}"
    echo "✓  ${OUTPUT_NAME}.7z   (AES-256, header encrypted)"
fi

# 3. tar.gz.gpg — standard on any Linux/macOS without extra tools
if command -v gpg &>/dev/null; then
    tar czf - "${SOURCES[@]}" |
        gpg --batch --yes --passphrase "$PASSWORD" \
            --symmetric --cipher-algo AES256 \
            -o "${OUTPUT_NAME}.tar.gz.gpg"
    echo "✓  ${OUTPUT_NAME}.tar.gz.gpg  (AES-256 via GPG)"
fi

# ── Wipe the password variable from memory ────────────────────────────────────
PASSWORD=""
PASSWORD2=""

echo ""
echo "Done. Send whichever format suits your advisor:"
echo "  .zip        → any OS, no extra software (recommend this first)"
echo "  .7z         → Windows: 7-Zip  |  Linux: p7zip  |  macOS: Keka / p7zip"
echo "  .tar.gz.gpg → Linux/macOS: gpg --decrypt  |  Windows: Gpg4win"
