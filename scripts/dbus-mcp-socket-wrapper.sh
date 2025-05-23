#!/bin/bash
# D-Bus MCP Socket Wrapper
# Bridges systemd socket to stdio-based MCP server

# Default configuration
CONFIG_FILE="/etc/dbus-mcp/config"
DEFAULT_SAFETY_LEVEL="high"
DEFAULT_BINARY="/usr/local/bin/dbus-mcp"

# Load configuration if it exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Use environment variables or config file values
SAFETY_LEVEL="${SAFETY_LEVEL:-$DEFAULT_SAFETY_LEVEL}"
DBUS_MCP_BIN="${DBUS_MCP_BIN:-$DEFAULT_BINARY}"

# Additional arguments from config
EXTRA_ARGS="${EXTRA_ARGS:-}"

# Log startup
logger -t dbus-mcp "Starting MCP server with safety level: $SAFETY_LEVEL"

# Execute the MCP server with configured options
exec "$DBUS_MCP_BIN" \
    --safety-level "$SAFETY_LEVEL" \
    $EXTRA_ARGS