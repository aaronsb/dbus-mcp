#!/bin/bash
# D-Bus MCP Server - Service Uninstallation Script

set -e

SERVICE_NAME="dbus-mcp"

echo "D-Bus MCP Server - Service Uninstallation"
echo "========================================="
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "❌ This script should not be run as root"
   exit 1
fi

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    echo "❌ systemd is not available on this system"
    exit 1
fi

USER_SERVICE_DIR="$HOME/.config/systemd/user"

echo "This will remove the D-Bus MCP systemd service."
echo "Service files to be removed:"
echo "  - $USER_SERVICE_DIR/${SERVICE_NAME}.service"
echo "  - $USER_SERVICE_DIR/${SERVICE_NAME}.socket"
echo
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Stop the service if running
if systemctl --user is-active --quiet "${SERVICE_NAME}.service"; then
    echo "✓ Stopping service..."
    systemctl --user stop "${SERVICE_NAME}.service"
fi

# Stop the socket if running
if systemctl --user is-active --quiet "${SERVICE_NAME}.socket"; then
    echo "✓ Stopping socket..."
    systemctl --user stop "${SERVICE_NAME}.socket"
fi

# Disable the service
if systemctl --user is-enabled --quiet "${SERVICE_NAME}.service" 2>/dev/null; then
    echo "✓ Disabling service..."
    systemctl --user disable "${SERVICE_NAME}.service"
fi

# Disable the socket
if systemctl --user is-enabled --quiet "${SERVICE_NAME}.socket" 2>/dev/null; then
    echo "✓ Disabling socket..."
    systemctl --user disable "${SERVICE_NAME}.socket"
fi

# Remove service files
echo "✓ Removing service files..."
rm -f "$USER_SERVICE_DIR/${SERVICE_NAME}.service"
rm -f "$USER_SERVICE_DIR/${SERVICE_NAME}.socket"

# Reload systemd
echo "✓ Reloading systemd daemon..."
systemctl --user daemon-reload

# Reset failed state if any
systemctl --user reset-failed "${SERVICE_NAME}.service" 2>/dev/null || true
systemctl --user reset-failed "${SERVICE_NAME}.socket" 2>/dev/null || true

echo
echo "✅ Service uninstallation complete!"
echo
echo "Note: The D-Bus MCP server files are still installed at:"
echo "  $(dirname "$(dirname "$0")")"
echo
echo "To completely remove the server, delete that directory."