#!/usr/bin/env bash
# Stop ai-bubu by its PID file.
# Requires the process to be running.

set -e

PID_FILE="/tmp/ai-bubu.pid"

if [ -f "$PID_FILE" ]; then
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        echo "Stopped ai-bubu (PID $pid)"
        rm -f "$PID_FILE"
        exit 0
    fi
fi
echo "ai-bubu is not running"
exit 1
