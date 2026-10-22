#!/bin/sh
set -eu

CERT_DIR="${CERT_DIR:-/certs}"
CERT_FILE="$CERT_DIR/localhost-cert.pem"
KEY_FILE="$CERT_DIR/localhost-key.pem"

mkdir -p "$CERT_DIR" /data

# Generate a self-signed certificate only if the supplied files are missing.
if [ ! -s "$CERT_FILE" ] || [ ! -s "$KEY_FILE" ]; then
  echo "SSL certificate or key not found. Generating a self-signed certificate..."

  CERT_FILE="$CERT_DIR/server.crt"
  KEY_FILE="$CERT_DIR/server.key"

  if [ ! -s "$CERT_FILE" ] || [ ! -s "$KEY_FILE" ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$KEY_FILE" -out "$CERT_FILE" \
      -subj "/CN=localhost" \
      -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

    chmod 600 "$KEY_FILE"
  fi
else
  echo "Using supplied SSL certificate and key."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8443 \
  --ssl-certfile "$CERT_FILE" \
  --ssl-keyfile "$KEY_FILE"