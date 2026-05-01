#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR"

python reserve_courts.py >> "$SCRIPT_DIR/cron.log" 2>&1

echo "Run completed at $(date)" >> "$SCRIPT_DIR/cron.log"
