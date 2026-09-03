# Telegram Trading Bot image (long-running poller)
FROM python:3.12-slim

# Run as non-root for security
RUN groupadd --gid 1000 trading \
    && useradd --uid 1000 --gid trading --create-home trading

WORKDIR /bot

# Install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot source (no .env — secrets injected at runtime)
COPY bot.py .

# Switch to the non-root user
USER trading

# No EXPOSE — the bot only makes outbound calls to Telegram & the API.
# -u forces unbuffered output so logs stream to docker compose logs.
CMD ["python", "-u", "bot.py"]