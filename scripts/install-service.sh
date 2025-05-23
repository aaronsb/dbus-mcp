#!/bin/bash
# D-Bus MCP Server - Service Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="dbus-mcp"

echo "D-Bus MCP Server - Service Installation"
echo "======================================="
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "❌ This script should not be run as root"
   echo "   It installs a user service that runs with your permissions"
   exit 1
fi

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    echo "❌ systemd is not available on this system"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "❌ Virtual environment not found at $PROJECT_DIR/venv"
    echo "   Please run ./quickstart.sh first"
    exit 1
fi

# Detect installation paths
USER_SERVICE_DIR="$HOME/.config/systemd/user"
INSTALL_DIR="$PROJECT_DIR"
VENV_PYTHON="$INSTALL_DIR/venv/bin/python"

echo "📍 Installation paths:"
echo "   Project directory: $INSTALL_DIR"
echo "   Service directory: $USER_SERVICE_DIR"
echo

# Create service directory
mkdir -p "$USER_SERVICE_DIR"

# Generate service file with correct paths
echo "✓ Creating service file..."
cat > "$USER_SERVICE_DIR/${SERVICE_NAME}.service" << EOF
[Unit]
Description=D-Bus Model Context Protocol Server
Documentation=https://github.com/aaronsb/dbus-mcp
After=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/venv/bin/python -m dbus_mcp
WorkingDirectory=$INSTALL_DIR
Restart=on-failure
RestartSec=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.cache %h/.local/share

# Environment
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=default.target
EOF

# Create socket file for socket activation (optional)
echo "✓ Creating socket file..."
cat > "$USER_SERVICE_DIR/${SERVICE_NAME}.socket" << EOF
[Unit]
Description=D-Bus MCP Server Socket
Documentation=https://github.com/aaronsb/dbus-mcp

[Socket]
ListenStream=%t/${SERVICE_NAME}.sock
SocketMode=0600

[Install]
WantedBy=sockets.target
EOF

# Reload systemd
echo "✓ Reloading systemd daemon..."
systemctl --user daemon-reload

# Enable the service
echo "✓ Enabling service..."
systemctl --user enable "${SERVICE_NAME}.service"

echo
echo "✅ Service installation complete!"
echo

# Install desktop entry for screenshot authorization if on KDE
if [[ "${XDG_CURRENT_DESKTOP}" == *"KDE"* ]] || [[ "${DESKTOP_SESSION}" == *"plasma"* ]]; then
    DESKTOP_SOURCE="${SCRIPT_DIR}/../systemd/dbus-mcp-screenshot.desktop"
    DESKTOP_DEST="/usr/share/applications/dbus-mcp-screenshot.desktop"
    
    if [ -f "${DESKTOP_SOURCE}" ]; then
        echo "📸 KDE detected - Screenshot authorization setup:"
        echo "   To enable screenshot capture, run:"
        echo
        echo "   sudo tee ${DESKTOP_DEST} << EOF"
        cat "${DESKTOP_SOURCE}" | sed "s|Exec=/usr/bin/python|Exec=${VENV_PYTHON}|g"
        echo "EOF"
        echo
        echo "   This grants D-Bus MCP permission to use KDE's screenshot interface."
        echo
    fi
fi

echo "Available commands:"
echo "  Start service:   systemctl --user start ${SERVICE_NAME}"
echo "  Stop service:    systemctl --user stop ${SERVICE_NAME}"
echo "  Service status:  systemctl --user status ${SERVICE_NAME}"
echo "  View logs:       journalctl --user -u ${SERVICE_NAME} -f"
echo
echo "The service will automatically start on login."
echo
echo "To start the service now, run:"
echo "  systemctl --user start ${SERVICE_NAME}"