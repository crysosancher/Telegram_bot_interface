#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# ---------------------------------------------------------------- stop any running bot
if pgrep -f "[b]ot\.py" >/dev/null 2>&1; then
    echo "🛑 Stopped existing bot instance."
    pkill -f "[b]ot\.py"
    # Wait up to 10s for it to fully exit
    for _ in $(seq 1 20); do
        if ! pgrep -f "[b]ot\.py" >/dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
fi

# ---------------------------------------------------------------- run the bot in the foreground
echo "🚀 Starting bot — press Ctrl+C to stop."
exec .venv/bin/python -u bot.py