# CCTV Camera honeypot — Dockerfile
FROM python:3.11-slim

LABEL honeypot="true" service="camera"
LABEL description="Intentionally vulnerable CCTV camera web panel — for lab use only"

# Avoid interactive prompts
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install OS deps (kept minimal — this is a fake device, not a real RTSP server)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Non-root for realism (real IoT firmware runs as root, but we don't need to here)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
  CMD curl -fsS http://localhost:5000/ || exit 1

CMD ["python", "app.py"]
