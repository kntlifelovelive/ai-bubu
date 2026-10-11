#!/usr/bin/env bash
# Stop ai-bubu by its PID file.
# Refuses to kill the PID unless it is actually our ai-bubu process.

set -euo pipefail

PID_FILE="/tmp/ai-bubu.pid"

if [ -f "$PID_FILE" ]; then
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
        # Safety check: confirm the PID is actually our ai-bubu server
        # before sending any signal.
        if [ -r "/proc/$pid/cmdline" ]; then
            cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline")"
            if ! echo "$cmdline" | grep -q "src/server"; then
                echo "PID $pid is not ai-bubu; not killing"
                exit 1
            fi
        fi
        kill "$pid"
        echo "Stopped ai-bubu (PID $pid)"
        rm -f "$PID_FILE"
        exit 0
    fi
fi
echo "ai-bubu is not running"
exit 1
