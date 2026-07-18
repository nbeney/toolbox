#!/usr/bin/env bash
# Wrapper to run task-tool from anywhere via uv.
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
exec uv run --project "$SCRIPT_DIR/../task-tool" task-tool "$@"
