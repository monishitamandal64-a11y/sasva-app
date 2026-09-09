# SASVA - single image running both the FastAPI server and the Streamlit client
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

# Streamlit (client) on 8501, FastAPI (server) on 8000
EXPOSE 8501 8000
ENV PORT=8501 API_PORT=8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD curl -fsS "http://localhost:${PORT}/_stcore/health" || exit 1

CMD ["./start.sh"]
