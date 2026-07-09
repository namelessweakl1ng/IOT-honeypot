FROM python:3.11-slim
LABEL honeypot="true" service="telnet"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY app.py .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 2323
CMD ["python", "app.py"]
