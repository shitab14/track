#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "==> Starting Track Frontend Service..."

if [ ! -d "node_modules" ]; then
    echo "==> Installing Node dependencies..."
    npm install
fi

if [ ! -f ".env.local" ] && [ -f ".env.example" ]; then
    echo "==> Copying .env.example to .env.local..."
    cp .env.example .env.local
fi

echo "==> Running Next.js dev server on http://localhost:3000..."
npm run dev
