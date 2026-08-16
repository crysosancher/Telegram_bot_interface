#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# ---------------------------------------------------------------- stop any running bot
# [b]ot.py bracket trick so this script's own pgrep doesn't match itself
if pkill -f "[b]ot\.py" 2>/dev/null; then
    echo "🛑 Stopped existing bot instance."
    # Wait up to 10s for the old process to fully exit
    for _ in $(seq 1 20); do
        if ! pgrep -f "[b]ot\.py" >/dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
else
    echo "ℹ️  No existing bot instance found."
fi

# ---------------------------------------------------------------- restart the bot
# -u = unbuffered output so bot.log stays live
nohup .venv/bin/python -u bot.py > bot.log 2>&1 &
BOT_PID=$!

echo "🚀 Bot restarted with PID ${BOT_PID} — logs in bot.log"
echo "   Check status:  tail -f bot.log"
echo "   Stop manually: kill ${BOT_PID}"