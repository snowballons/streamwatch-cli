#!/bin/bash
# StreamWatch Development Environment Activation Script

echo "Activating StreamWatch development environment..."

# Change to the project directory if not already there
cd "$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

echo "✅ Virtual environment activated!"
echo "✅ StreamWatch CLI is ready for development"
echo ""
echo "Available commands:"
echo "  streamwatch         - Run the StreamWatch CLI"
echo "  streamlink --version - Check streamlink version"
echo "  pip list            - Show installed packages"
echo "  deactivate          - Exit the virtual environment"
echo ""
echo "To deactivate the environment, simply run: deactivate"
