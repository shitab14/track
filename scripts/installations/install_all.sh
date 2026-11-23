#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================================"
echo "   Installing All Track Dependencies & Prerequisites"
echo "========================================================"

# 1. PostgreSQL installation & start
bash "$SCRIPT_DIR/install_postgres.sh"

# 2. Docker installation
bash "$SCRIPT_DIR/install_docker.sh"

echo ""
echo "========================================================"
echo "   All installation steps completed!"
echo "========================================================"
