#!/bin/bash
# D-Bus MCP Socket Wrapper using socat
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

# Check if we have systemd socket activation
if [ -n "$LISTEN_FDS" ] && [ "$LISTEN_FDS" -gt 0 ]; then
    # Use socat to bridge the socket FD to stdio
    # FD 3 is the first socket passed by systemd
    exec socat FD:3 EXEC:"$DBUS_MCP_BIN --safety-level $SAFETY_LEVEL $EXTRA_ARGS",pty,raw,echo=0
else
    # Direct execution without socket activation
    exec "$DBUS_MCP_BIN" \
        --safety-level "$SAFETY_LEVEL" \
        $EXTRA_ARGS
fi