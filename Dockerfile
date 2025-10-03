# Multi-stage build for minimal image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 botuser

# Copy Python dependencies from builder to botuser home
COPY --from=builder --chown=botuser:botuser /root/.local /home/botuser/.local

# Copy application code
COPY --chown=botuser:botuser bot/ ./bot/

# Switch to non-root user
USER botuser

# Update PATH to use botuser's local packages
ENV PATH=/home/botuser/.local/bin:$PATH

# Run the bot
CMD ["python", "-m", "bot.main"]
