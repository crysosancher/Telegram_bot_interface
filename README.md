# 🤖 Telegram AI Trading Bot

A Telegram bot that analyses trading assets (gold / silver / bitcoin) on demand. When you send
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
   | `BOT_PASSWORD`       | Password that unlocks the bot (see below)| *(empty = open)*       |
   | `SESSION_TTL_HOURS`  | How long an unlock lasts, in hours       | `24`                   |
   | `FREE_CHAT_IDS`      | Comma-separated chat IDs that skip the password | *(empty = none)* |

4. **Run the bot** (or just `./start.sh` — see below):

   ```bash
   .venv/bin/python bot.py
   ```

## Start / restart script

`./start.sh` stops any running bot instance (if present), then starts a fresh one **in the
foreground** — it keeps running in the terminal until you press `Ctrl+C`, exactly like
`python bot.py`:

```bash
./start.sh
```

- 💡 Use it whenever you change `bot.py` or `.env` — it restarts with the new settings.
- 🛑 Stop the bot: press `Ctrl+C` in the same terminal.
- 🔄 If it's already running elsewhere, the script stops the old instance first, then starts fresh.

## Password access (optional)

If you set a `BOT_PASSWORD` in `.env`, the bot becomes private:

1. The **first time** someone messages it (or once their session expires), the bot
   replies asking for the password.
2. They send the password as a normal message.
3. A correct password unlocks the bot for `SESSION_TTL_HOURS` hours (default **24
   hours / one day**). After that they must send the password again.

- Wrong passwords are rejected with an error message.
- Sessions are kept **in memory** — restarting the bot clears all unlocks.
- Leave `BOT_PASSWORD` empty to disable the password and keep the bot open to everyone.

### Free group (no password needed)

To let one chat — e.g. the professor group — use the bot without a password, list
its numeric chat ID in `FREE_CHAT_IDS` (comma-separated for several chats):

```bash
FREE_CHAT_IDS=-1001234567890
```

Find a chat's ID by sending `/chatid` inside that chat — the bot replies with the
numeric ID (groups look like `-100xxxxxxxxxx`). Whitelisted chats skip the password
prompt entirely; every other chat still requires it. `FREE_CHAT_IDS` also works in
a private chat (use that user's numeric ID).

## Usage

Open your bot in Telegram and send:

| Command                          | Description                                      |
| -------------------------------- | ------------------------------------------------ |
| `/start`                         | Show the help message (password prompt first, if enabled) |
| `/analyse XAUUSD` or `/analyse xusd` | Analyse gold (default timeframe: 15min)      |
| `/analyse XAGUSD`                | Analyse silver                                   |
| `/analyse BTCUSD`                | Analyse bitcoin                                  |
| `/analyse XAUUSD 1h`             | Analyse gold on the 1-hour timeframe             |

### Supported assets & timeframes

- **Assets:** `XAUUSD` / `XAU/USD` (gold), `XAGUSD` / `XAG/USD` (silver),
  `BTCUSD` / `BTC/USD` (bitcoin)
  — aliases like `xusd`, `XAU`, `GOLD`, `xag`, `SILVER`, `BTC`, `BITCOIN` also work.
- **Timeframes:** `5min`, `15min`, `30min`, `1h`, `2h`, `4h`

## Example reply

```
📊 XAUUSD — AI Trade Analysis

🟢 Recommendation: BUY
📈 Confidence: 68.5%
🏅 Trade Grade: B+
💲 Live Price: 4375.69 (as of 2026-09-04 22:45:00 UTC)
🕐 Session: New York Session
    13:00-20:45 UTC · 18:30-02:15 IST

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

🔢 Final Score: 68 / 100

🧠 AI Logic
The overall analysis shows ...

📊 Score Breakdown is posted as a separate second message so it never gets truncated.

```

## Project structure

```
.
├── bot.py              # Telegram bot entry point + /analyse handler
├── start.sh            # Restart script — stops any running bot, runs bot.py in foreground
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template (copy to .env)
├── .gitignore
└── README.md
