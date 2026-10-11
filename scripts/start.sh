#!/usr/bin/env bash
# Start ai-bubu (development mode).
# Does not require root.
# Writes its PID to /tmp/ai-bubu.pid and cleans it up on exit.

set -euo pipefail

PID_FILE="/tmp/ai-bubu.pid"

# If a PID file exists, verify the recorded process is ours before refusing.
if [ -f "$PID_FILE" ]; then
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
        # Confirm the process is actually our ai-bubu server, not an
        # unrelated process that happened to reuse the PID.
        if [ -r "/proc/$pid/cmdline" ]; then
            cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline")"
            if echo "$cmdline" | grep -q "src/server"; then
                echo "ai-bubu is already running (PID $pid)"
                exit 1
            fi
        fi
    fi
    # PID no longer running: stale PID file, remove it.
    rm -f "$PID_FILE"
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

cd "$ROOT_DIR"

# Ensure the PID file is always removed when this script exits.
cleanup() {
    rm -f "$PID_FILE"
}
trap cleanup EXIT

echo "Starting ai-bubu on 127.0.0.1:5001..."
python3 -m src.server &
echo $! > "$PID_FILE"

# Block until the server process exits (so Ctrl+C stops the server).
wait $!
