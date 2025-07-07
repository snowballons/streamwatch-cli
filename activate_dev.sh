#!/bin/bash
# StreamWatch Development Environment Activation Script

echo "Setting up StreamWatch development environment with uv..."

# Change to the project directory if not already there
cd "$(dirname "$0")"

# Sync dependencies with uv
echo "📦 Syncing dependencies..."
uv sync

echo "✅ Dependencies synchronized!"
echo "✅ StreamWatch CLI is ready for development"
echo ""
echo "Available commands:"
echo "  uv run streamwatch   - Run the StreamWatch CLI"
echo "  uv run streamlink --version - Check streamlink version"
echo "  uv list              - Show installed packages"
echo "  uv run python -m streamwatch.main - Run module directly"
echo ""
echo "To run commands in the uv environment, use: uv run <command>"
