"""Telegram trading bot — /analyse <asset> calls the analysis API and posts the trade decision."""

import asyncio
import html
import os
import re
import sys
from typing import Optional

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

# ---------------------------------------------------------------- config (env)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ANALYSE_BASE_URL = os.getenv("ANALYSE_BASE_URL", "http://127.0.0.1:8001")
ANALYSE_ENDPOINT = os.getenv("ANALYSE_ENDPOINT", "/api/v1/analyse")
ANALYSE_TIMEOUT = float(os.getenv("ANALYSE_TIMEOUT", "120"))

ANALYSE_URL = f"{ANALYSE_BASE_URL.rstrip('/')}/{ANALYSE_ENDPOINT.lstrip('/')}"

# Marker the score explainer uses for its heading. Newer API responses expose
# the breakdown as a dedicated "score_breakdown" field; older ones embed it at
# the end of ai_logic. Either way the bot sends it as its own second message.
BREAKDOWN_MARKER = "📊 Score Breakdown — how each module was scored:"

# ---------------------------------------------------------------- domain helpers
VALID_ASSETS = {"XAUUSD", "XAU/USD", "XAGUSD", "XAG/USD", "BTCUSD", "BTC/USD"}
VALID_TIMEFRAMES = {"5min", "15min", "30min", "1h", "2h", "4h"}

ASSET_ALIASES = {
    "XAUUSD": "XAUUSD",
    "XAU/USD": "XAU/USD",
    "XAU": "XAUUSD",
    "XUSD": "XAUUSD",
    "GOLD": "XAUUSD",
    "XAGUSD": "XAGUSD",
    "XAG/USD": "XAG/USD",
    "XAG": "XAGUSD",
    "SILVER": "XAGUSD",
    "BTCUSD": "BTCUSD",
    "BTC/USD": "BTC/USD",
    "BTC": "BTCUSD",
    "XBTUSD": "BTCUSD",
    "BITCOIN": "BTCUSD",
}


class ApiError(Exception):
    """Raised when the analysis API cannot produce a result."""


def normalize_asset(raw: str) -> Optional[str]:
    """Map user input (e.g. xusd/xau/btc) to an API-accepted asset."""
    alias = ASSET_ALIASES.get(raw.strip().upper())
    if alias and alias in VALID_ASSETS:
        return alias
    return None


def esc(value) -> str:
    """Escape arbitrary API strings for Telegram HTML."""
    return html.escape(str(value), quote=False)


async def call_analysis_api(asset: str, timeframe: Optional[str]) -> dict:
    """POST the analyse request and return the parsed JSON response."""
    payload = {"asset": asset}
    if timeframe:
        payload["timeframe"] = timeframe

    try:
        async with httpx.AsyncClient(timeout=ANALYSE_TIMEOUT) as client:
            response = await client.post(ANALYSE_URL, json=payload)
    except httpx.TimeoutException:
        raise ApiError(
            f"the analysis API timed out after {ANALYSE_TIMEOUT:g}s. "
            "It might be busy — try again in a moment."
        )
    except httpx.HTTPError as exc:
        raise ApiError(f"could not reach the analysis API: {exc}")

    if response.status_code == 422:
        raise ApiError(
            "the analysis API rejected the request (422). Please check the asset/timeframe."
        )
    if response.status_code != 200:
        raise ApiError(f"the analysis API returned HTTP {response.status_code}")

    return response.json()


def format_analysis(data: dict) -> str:
    """Render the API response as a readable Telegram HTML message."""
    asset = esc(data.get("asset", "?"))
    recommendation = data.get("recommendation", "?")
    confidence = data.get("confidence", "?")
    grade = esc(data.get("trade_grade", "?"))

    rec_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}.get(recommendation, "•")

    lines = [f"📊 <b>{asset} — AI Trade Analysis</b>", ""]
    lines.append(f"{rec_emoji} <b>Recommendation:</b> {esc(recommendation)}")
    lines.append(f"📈 <b>Confidence:</b> {confidence}%")
    lines.append(f"🏅 <b>Trade Grade:</b> {grade}")

    # ---- entry plan
    entry = data.get("entry") or {}
    if entry:
        lines.append("")
        lines.append("💰 <b>Entry Plan</b>")
        if entry.get("price") is not None:
            lines.append(f"• Entry: {esc(entry['price'])}")
        if entry.get("stop_loss") is not None:
            lines.append(f"• Stop Loss: {esc(entry['stop_loss'])}")
        take_profit = entry.get("take_profit") or {}
        if take_profit:
            tps = " | ".join(
                f"{esc(key.upper())}: {esc(value)}"
                for key, value in sorted(take_profit.items())
            )
            lines.append(f"• {tps}")
        if entry.get("risk_reward"):
            lines.append(f"• Risk:Reward: {esc(entry['risk_reward'])}")

    # ---- module breakdown
    analysis = data.get("analysis") or {}
    if analysis:
        lines.append("")
        lines.append("📚 <b>Module Breakdown</b>")
        for name, module in analysis.items():
            score = module.get("score", "?")
            max_score = module.get("max_score", "?")
            result = module.get("result", "")
            suffix = f"({score}/{max_score})"
            if result:
                # The result often already contains its score, e.g. "Neutral (5/20)".
                has_score = re.search(r"\(\d+/\d+\)", result)
                label = f"{esc(result)} {suffix}" if not has_score else esc(result)
            else:
                label = suffix
            lines.append(f"• <b>{esc(name)}</b>: {label}")

    # ---- final score
    final_score = data.get("final_score") or {}
    if final_score.get("total") is not None:
        lines.append("")
        lines.append(
            f"🔢 <b>Final Score:</b> {esc(final_score['total'])} / {esc(final_score.get('total_max', '?'))}"
        )

    # ---- AI logic (narrative only; the point-wise score breakdown is sent as
    # its own second message via format_score_breakdown, so never truncate it).
    ai_logic = data.get("ai_logic", "")
    if ai_logic:
        lines.append("")
        lines.append("🧠 <b>AI Logic</b>")
        # Older API responses may still embed the breakdown at the end of
        # ai_logic — cut it so it isn't duplicated/truncated here.
        ai_logic = ai_logic.split(BREAKDOWN_MARKER, 1)[0].rstrip()
        max_ai = 1400
        if len(ai_logic) > max_ai:
            ai_logic = ai_logic[:max_ai].rsplit(" ", 1)[0] + "…"
        if ai_logic:
            lines.append(esc(ai_logic))

    return "\n".join(lines)


def format_score_breakdown(data: dict) -> Optional[str]:
    """Return the point-wise score breakdown, or None when there is none.

    Newer API responses carry it in ``score_breakdown``; older responses embed
    it inside ``ai_logic`` after BREAKDOWN_MARKER. Either way it is rendered as
    a separate second Telegram message.
    """
    breakdown = (data.get("score_breakdown") or "").strip()
    if not breakdown:
        ai_logic = data.get("ai_logic") or ""
        idx = ai_logic.find(BREAKDOWN_MARKER)
        if idx != -1:
            breakdown = ai_logic[idx:].strip()
    if not breakdown:
        return None
    return esc(breakdown)


def split_text(text: str, limit: int = 4000) -> list[str]:
    """Split a long message into chunks at line boundaries (Telegram 4096 limit)."""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        if current and len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


# ---------------------------------------------------------------- bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 <b>Welcome to the AI Trading Bot!</b>\n\n"
        "Analyse an asset with a single command:\n\n"
        "• <code>/analyse XAUUSD</code> — gold\n"
        "• <code>/analyse XAGUSD</code> — silver\n"
        "• <code>/analyse BTCUSD</code> — bitcoin\n"
        "• <code>/analyse XAUUSD 1h</code> — optional timeframe "
        "(5min/15min/30min/1h/2h/4h)\n\n"
        "The bot will call the trading analysis API and post the full "
        "AI trade decision.",
        parse_mode="HTML",
    )


async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if not args:
        await update.message.reply_text(
            "Usage: <code>/analyse XAUUSD</code> or <code>/analyse XAGUSD</code>\n\n"
            "Supported assets: XAU/USD (gold), XAG/USD (silver), BTC/USD (bitcoin)\n"
            "Supported timeframes: 5min, 15min, 30min, 1h, 2h, 4h",
            parse_mode="HTML",
        )
        return

    asset = normalize_asset(args[0])
    if not asset:
        await update.message.reply_text(
            f"❌ Unknown asset <code>{esc(args[0])}</code>.\n"
            "Supported: <code>XAUUSD</code> (gold), <code>XAGUSD</code> (silver), "
            "<code>BTCUSD</code> (bitcoin).",
            parse_mode="HTML",
        )
        return

    timeframe = args[1].lower() if len(args) > 1 else None
    if timeframe and timeframe not in VALID_TIMEFRAMES:
        await update.message.reply_text(
            f"❌ Unknown timeframe <code>{esc(args[1])}</code>.\n"
            "Supported: 5min, 15min, 30min, 1h, 2h, 4h.",
            parse_mode="HTML",
        )
        return

    tf_label = f" ({timeframe})" if timeframe else ""
    status = await update.message.reply_text(
        f"⏳ Analysing <b>{esc(asset)}</b>{tf_label}… "
        f"this can take up to {ANALYSE_TIMEOUT:g}s.",
        parse_mode="HTML",
    )

    try:
        data = await call_analysis_api(asset, timeframe)
    except ApiError as exc:
        await status.edit_text(f"❌ <b>Analysis failed</b>\n{esc(str(exc))}", parse_mode="HTML")
        return

    message = format_analysis(data)
    chunks = split_text(message)

    try:
        await status.edit_text(chunks[0], parse_mode="HTML")
    except Exception:
        # If the original status message can't be edited (e.g. too long / race), send fresh.
        await update.message.reply_text(chunks[0], parse_mode="HTML")

    for chunk in chunks[1:]:
        await update.message.reply_text(chunk, parse_mode="HTML")

    # Second message — full point-wise score breakdown (never truncated).
    breakdown = format_score_breakdown(data)
    if breakdown:
        for chunk in split_text(breakdown):
            await update.message.reply_text(chunk, parse_mode="HTML")


# ---------------------------------------------------------------- entry point
def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        print(
            "❌ TELEGRAM_BOT_TOKEN is not set.\n"
            "   Copy .env.example to .env and add your token from @BotFather.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Python 3.14 removed the implicit event-loop creation in
    # asyncio.get_event_loop(); set one explicitly for run_polling().
    asyncio.set_event_loop(asyncio.new_event_loop())

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyse", analyse))

    print(f"🤖 Bot started. API endpoint: {ANALYSE_URL}")
    app.run_polling()


if __name__ == "__main__":
    main()