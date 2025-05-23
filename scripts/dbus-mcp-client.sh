#!/bin/bash
# D-Bus MCP Client Wrapper
# Connects to the systemd socket-activated MCP server

# Default socket path
SOCKET_PATH="${XDG_RUNTIME_DIR:-/run/user/$UID}/dbus-mcp.sock"

# Check if socket exists
if [ ! -S "$SOCKET_PATH" ]; then
    echo "Error: D-Bus MCP socket not found at $SOCKET_PATH" >&2
    echo "Make sure the service is running:" >&2
    echo "  systemctl --user start dbus-mcp.socket" >&2
    exit 1
fi

# Check for socat
if ! command -v socat &> /dev/null; then
    echo "Error: socat is required but not installed" >&2
    echo "Install it with your package manager:" >&2
    echo "  sudo apt install socat    # Debian/Ubuntu" >&2
    echo "  sudo dnf install socat    # Fedora" >&2
    echo "  sudo pacman -S socat      # Arch" >&2
    exit 1
fi

# Connect to socket
exec socat UNIX-CONNECT:"$SOCKET_PATH" STDIO