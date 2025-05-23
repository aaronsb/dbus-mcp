#!/bin/bash
# D-Bus MCP Server Quick Start Script

set -e

echo "D-Bus MCP Server - Quick Start"
echo "=============================="
echo

# Check Python version
echo "✓ Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "  ❌ Python $PYTHON_VERSION is too old. Need Python 3.9+"
    exit 1
fi
echo "  ✓ Python $PYTHON_VERSION"

# Check for venv module
echo
echo "✓ Checking for venv module..."
if ! python -m venv --help >/dev/null 2>&1; then
    echo "  ❌ Python venv module not found"
    echo "  Please install: python3-venv (apt/dnf) or python-virtualenv (pacman)"
    exit 1
fi
echo "  ✓ venv module available"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo
    echo "✓ Creating virtual environment..."
    python -m venv venv --system-site-packages
    echo "  ✓ Virtual environment created with system packages access"
else
    echo
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo
echo "✓ Activating virtual environment..."
source venv/bin/activate
echo "  ✓ Virtual environment activated"

# Install package
echo
echo "✓ Installing D-Bus MCP server..."
pip install -e . -q
echo "  ✓ Package installed"

# Run requirements check
echo
echo "✓ Checking system requirements..."
python -m dbus_mcp --check-requirements

# Run installation test
echo
echo "✓ Running installation test..."
if python test_installation.py; then
    echo
    echo "✅ Installation successful!"
    echo
    echo "Next steps:"
    echo "1. Run the demo: python examples/demo_tools.py"
    echo "2. Start the server: python -m dbus_mcp"
    echo "3. Add to Claude Desktop config (see README.md)"
    echo
    echo "To activate the virtual environment in the future:"
    echo "  source venv/bin/activate"
else
    echo
    echo "❌ Installation test failed. Please check the errors above."
    exit 1
fi