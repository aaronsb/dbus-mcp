#!/bin/bash
# D-Bus MCP Server with socket support
# Creates a Unix socket and bridges connections to the MCP server

# Default configuration
CONFIG_FILE="/etc/dbus-mcp/config"
DEFAULT_SAFETY_LEVEL="high"
DEFAULT_BINARY="/usr/local/bin/dbus-mcp"
SOCKET_PATH="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dbus-mcp.sock"

# Load configuration if it exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Use environment variables or config file values
SAFETY_LEVEL="${SAFETY_LEVEL:-$DEFAULT_SAFETY_LEVEL}"
DBUS_MCP_BIN="${DBUS_MCP_BIN:-$DEFAULT_BINARY}"

# Additional arguments from config
EXTRA_ARGS="${EXTRA_ARGS:-}"

# Remove existing socket if it exists
rm -f "$SOCKET_PATH"

# Log startup
logger -t dbus-mcp "Starting MCP server on socket: $SOCKET_PATH"

# Build command
CMD="$DBUS_MCP_BIN --safety-level $SAFETY_LEVEL"
if [ -n "$EXTRA_ARGS" ]; then
    CMD="$CMD $EXTRA_ARGS"
fi

# Use socat to create socket and forward to MCP server
# Redirect stderr to systemd journal to avoid protocol interference
exec socat UNIX-LISTEN:"$SOCKET_PATH",fork,unlink-early \
    EXEC:"$CMD",stderr