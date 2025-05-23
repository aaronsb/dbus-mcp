# D-Bus MCP Server - Deployment Guide

This guide covers the different ways to deploy and run the D-Bus MCP server.

## Overview

The D-Bus MCP server supports two primary deployment modes:

1. **Development Mode** - Direct stdio communication, perfect for testing and development
2. **Production Mode** - SystemD socket activation for persistent service

## Quick Start

```bash
# Clone the repository
git clone https://github.com/aaronsb/dbus-mcp.git
cd dbus-mcp

# For development mode only
./quickstart.sh

# For full installation (both modes)
./install.sh
```

## Development Mode

Development mode runs the server directly with stdio communication. This is how Claude Code and other MCP clients typically connect during development.

### Setup

```bash
# Install development environment only
./install.sh --dev-only

# This creates:
# - Python virtual environment (venv/)
# - Development launcher script (dbus-mcp-dev)
```

### Usage

```bash
# Run with default settings (high safety)
./dbus-mcp-dev

# Run with medium safety level
./dbus-mcp-dev --safety-level medium

# Use in Claude Code config
{
  "mcpServers": {
    "dbus-mcp": {
      "command": "/path/to/dbus-mcp/dbus-mcp-dev",
      "args": ["--safety-level", "medium"]
    }
  }
}
```

### Advantages
- Simple setup
- Direct console output for debugging
- Easy to restart and modify
- No systemd required

## Production Mode

Production mode uses systemd socket activation for on-demand startup and persistent service.

### Setup

```bash
# Install production components
./install.sh --prod-only

# Or install everything
./install.sh

# This installs:
# - Standalone executable: /usr/local/bin/dbus-mcp
# - Socket wrapper: /usr/local/bin/dbus-mcp-socket-wrapper
# - Config file: /etc/dbus-mcp/config
# - SystemD units: ~/.config/systemd/user/dbus-mcp.*
```

### Configuration

Edit `/etc/dbus-mcp/config` to set safety level and options:

```bash
# Safety level for production
SAFETY_LEVEL="medium"

# Optional: Additional arguments
EXTRA_ARGS="--log-level info"
```

### Starting the Service

```bash
# Enable socket activation (starts on demand)
systemctl --user enable dbus-mcp.socket
systemctl --user start dbus-mcp.socket

# Check status
systemctl --user status dbus-mcp.socket
systemctl --user status dbus-mcp.service
```

### Connecting Clients

For MCP clients to connect to the socket-activated service:

```bash
# Use the provided client wrapper
/usr/local/bin/dbus-mcp-client

# Or use socat directly
socat UNIX-CONNECT:$XDG_RUNTIME_DIR/dbus-mcp.sock STDIO

# In Claude Code config (with socat)
{
  "mcpServers": {
    "dbus-mcp": {
      "command": "socat",
      "args": ["UNIX-CONNECT:/run/user/1000/dbus-mcp.sock", "STDIO"]
    }
  }
}
```

### Advantages
- Starts on demand
- Survives client disconnections
- Central configuration
- System integration
- Can run as system service for multiple users

## Installation Details

### What Gets Installed

**Development Mode (`--dev-only`):**
- `venv/` - Python virtual environment
- `dbus-mcp-dev` - Development launcher script

**Production Mode (`--prod-only`):**
- `/usr/local/bin/dbus-mcp` - Standalone Python zipapp executable
- `/usr/local/bin/dbus-mcp-socket-wrapper` - SystemD wrapper script
- `/usr/local/bin/dbus-mcp-client` - Client connection helper
- `/etc/dbus-mcp/config` - System configuration
- `~/.config/systemd/user/dbus-mcp.socket` - User socket unit
- `~/.config/systemd/user/dbus-mcp.service` - User service unit

### Building the Standalone Executable

The installer creates a standalone executable using Python's zipapp:

```bash
# The installer does this automatically:
pip install --target=build_dir .
python -m zipapp build_dir -p "/usr/bin/env python3" -o dbus-mcp -c
```

This creates a single compressed executable that includes all dependencies.

## Uninstallation

```bash
# Interactive uninstall
./uninstall.sh

# Remove everything
./uninstall.sh --all

# Remove only development
./uninstall.sh --dev

# Remove only production
./uninstall.sh --prod
```

## Multiple User Setup

For system-wide deployment serving multiple users:

```bash
# Install system service template
sudo cp systemd/system/dbus-mcp@.service /etc/systemd/system/

# Enable for specific user
sudo systemctl enable dbus-mcp@alice.socket
sudo systemctl start dbus-mcp@alice.socket
```

## Troubleshooting

### Socket Connection Failed

```bash
# Check if socket exists
ls -la $XDG_RUNTIME_DIR/dbus-mcp.sock

# Check service status
systemctl --user status dbus-mcp.socket
journalctl --user -u dbus-mcp.service -n 50
```

### Permission Denied

```bash
# Check config file permissions
ls -la /etc/dbus-mcp/config

# Check executable permissions
ls -la /usr/local/bin/dbus-mcp*
```

### Service Won't Start

```bash
# Check logs
journalctl --user -u dbus-mcp.service -f

# Test executable directly
/usr/local/bin/dbus-mcp --help

# Test with wrapper
/usr/local/bin/dbus-mcp-socket-wrapper
```

## Security Considerations

- The service always runs as the invoking user, never as root
- Configuration in `/etc/dbus-mcp/config` controls system-wide safety level
- Socket permissions (0600) ensure only the owner can connect
- SystemD security hardening is applied (PrivateTmp, ProtectSystem, etc.)