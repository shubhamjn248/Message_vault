FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/messages.db \
    CERT_DIR=/certs

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY client ./client
COPY scripts ./scripts
COPY certs/ /certs/
RUN chmod +x /app/scripts/entrypoint.sh && mkdir -p /data /certs
EXPOSE 8443
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
