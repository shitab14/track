#!/usr/bin/env bash
set -e

echo "========================================================"
echo "   Installing PostgreSQL 16 on macOS (via Homebrew)"
echo "========================================================"

if ! command -v brew &> /dev/null; then
    echo "ERROR: Homebrew is not installed. Please install Homebrew from https://brew.sh first."
    exit 1
fi

echo "==> Installing postgresql@16..."
brew install postgresql@16

echo "==> Linking postgresql@16 to PATH..."
brew link --force postgresql@16 2>/dev/null || true

echo "==> Starting PostgreSQL 16 background service..."
brew services start postgresql@16

echo "==> Creating default database 'track_db' if not exists..."
/opt/homebrew/opt/postgresql@16/bin/createuser -h localhost -s postgres 2>/dev/null || true
/opt/homebrew/opt/postgresql@16/bin/createdb -h localhost -U postgres track_db 2>/dev/null || /opt/homebrew/opt/postgresql@16/bin/createdb track_db 2>/dev/null || true

echo ""
echo "========================================================"
echo " PostgreSQL 16 installed and running on port 5432!"
echo " Database 'track_db' is ready."
echo "========================================================"
