#!/usr/bin/env bash
set -e

echo "========================================================"
echo "   Installing Docker Desktop on macOS (via Homebrew)"
echo "========================================================"

if ! command -v brew &> /dev/null; then
    echo "ERROR: Homebrew is not installed. Please install Homebrew from https://brew.sh first."
    exit 1
fi

if command -v docker &> /dev/null; then
    echo "==> Docker is already installed: $(docker --version)"
    exit 0
fi

echo "==> Installing Docker Desktop cask..."
brew install --cask docker

echo ""
echo "========================================================"
echo " Docker Desktop installed successfully!"
echo " IMPORTANT: Please launch Docker.app from your Applications"
echo " folder to finish initial setup and grant permissions."
echo "========================================================"
