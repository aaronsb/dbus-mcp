#!/bin/bash
# D-Bus MCP Server Quick Start Script

echo "D-Bus MCP Server - Quick Start"
echo "=============================="
echo ""
echo "This script sets up a development environment."
echo "For production installation with systemd support, use ./install.sh"
echo ""

# Run the installer in development-only mode
exec ./install.sh --dev-only "$@"