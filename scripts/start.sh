#!/usr/bin/env bash
# Start ai-bubu (development mode).
# Does not require root.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

echo "Starting ai-bubu on localhost..."
exec python -m src.server
