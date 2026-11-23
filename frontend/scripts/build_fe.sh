#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "==> Building Track Frontend Production Bundle..."

if [ ! -d "node_modules" ]; then
    npm install
fi

npm run build
