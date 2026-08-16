# 🤖 Telegram AI Trading Bot

A Telegram bot that analyses trading assets (gold / bitcoin) on demand. When you send
`/analyse XAUUSD`, the bot calls a local trading analysis API and replies with the full
AI trade decision — recommendation, confidence, trade grade, entry plan, module breakdown,
final score and the AI logic explanation.

## How it works

```
You: /analyse XAUUSD
        │
        ▼
Telegram Bot ──POST /api/v1/analyse──▶ Analysis API (FastAPI, port 8001)
        ▲                                      │
        │                                      ▼
        └──────── formatted trade decision ◀─── JSON response
```

## Requirements

- Python 3.10+
- The trading analysis API running locally (default `http://127.0.0.1:8001`)

## Setup

1. **Create your bot token with [@BotFather](https://t.me/BotFather)** and copy the token.

2. **Install dependencies** (a virtualenv is recommended):

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

3. **Configure the environment** — copy the template and fill in your values:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   | Variable             | Description                              | Default                |
   | -------------------- | ---------------------------------------- | ---------------------- |
   | `TELEGRAM_BOT_TOKEN` | Your token from @BotFather               | *(required)*           |
   | `ANALYSE_BASE_URL`   | Analysis API base URL                    | `http://127.0.0.1:8001`|
   | `ANALYSE_ENDPOINT`   | API path for the analyse endpoint        | `/api/v1/analyse`      |
   | `ANALYSE_TIMEOUT`    | Request timeout in seconds               | `120`                  |

4. **Run the bot** (or just `./start.sh` — see below):

   ```bash
   .venv/bin/python bot.py
   ```

## Start / restart script

`./start.sh` stops any running bot instance (if present), then starts a fresh one in the
background with logs written to `bot.log`:

```bash
./start.sh
```

- 💡 Use it whenever you change `bot.py` or `.env` — it restarts with the new settings.
- 📄 Live logs: `tail -f bot.log`
- 🛑 Stop manually: `kill <PID>` (the script prints the PID, or find it with `pgrep -fl bot.py`)

## Usage

Open your bot in Telegram and send:

| Command                          | Description                                      |
| -------------------------------- | ------------------------------------------------ |
| `/start`                         | Show the help message                            |
| `/analyse XAUUSD` or `/analyse xusd` | Analyse gold (default timeframe: 15min)      |
| `/analyse BTCUSD`                | Analyse bitcoin                                  |
| `/analyse XAUUSD 1h`             | Analyse gold on the 1-hour timeframe             |

### Supported assets & timeframes

- **Assets:** `XAUUSD` / `XAU/USD` (gold), `BTCUSD` / `BTC/USD` (bitcoin)
  — aliases like `xusd`, `XAU`, `GOLD`, `BTC`, `BITCOIN` also work.
- **Timeframes:** `5min`, `15min`, `30min`, `1h`, `2h`, `4h`

## Example reply

```
📊 XAUUSD — AI Trade Analysis

🟢 Recommendation: BUY
📈 Confidence: 68.5%
🏅 Trade Grade: B+

💰 Entry Plan
• Entry: 4375.69
• Stop Loss: 4369.13
• TP1: 4382.26 | TP2: 4388.82 | TP3: 4395.39
• Risk:Reward: 1:3

📚 Module Breakdown
• fundamental: Neutral (5/20)
• multi_timeframe: Partial Alignment (7/20)
• trend: Trend Partial (9/15)
• ...

🔢 Final Score: 36 / 115

🧠 AI Logic
The overall analysis shows ...
```

## Project structure

```
.
├── bot.py              # Telegram bot entry point + /analyse handler
├── start.sh            # Restart script — stops any running bot, starts it with logs
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template (copy to .env)
├── .gitignore
└── README.md
