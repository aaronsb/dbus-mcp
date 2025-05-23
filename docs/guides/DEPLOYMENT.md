# D-Bus MCP Server - Deployment Guide

This guide covers the different ways to deploy and run the D-Bus MCP server.

## Overview

The D-Bus MCP server supports two deployment modes:

1. **Production Mode (Recommended)** - SystemD service with Unix socket for reliability and security
2. **Development Mode** - Direct stdio communication for testing and development

## Quick Start

### 🚀 Recommended: Production Installation

```bash
# Clone the repository
git clone https://github.com/aaronsb/dbus-mcp.git
cd dbus-mcp

# Install with systemd service (recommended)
./install.sh --prod-only

# Configure and start
sudo nano /etc/dbus-mcp/config  # Set SAFETY_LEVEL="medium"
systemctl --user start dbus-mcp-standalone.service
systemctl --user enable dbus-mcp-standalone.service
```

### Development Installation

```bash
# For development/testing only
./quickstart.sh
```

## Production Mode (Recommended)

**📖 For detailed systemd setup, see the [SystemD Mode Guide](SYSTEMD-MODE.md)**

Production mode runs D-Bus MCP as a systemd service with Unix socket communication. This is the **recommended deployment method** for all production use.

### Why Production Mode?

✅ **Reliability** - Automatic restart on crashes  
✅ **Security** - SystemD sandboxing and resource limits  
✅ **Management** - Standard systemctl commands  
✅ **Logging** - Full journald integration  
✅ **Multi-client** - Handle multiple connections  

### Quick Setup

```bash
# Install production components
./install.sh --prod-only

# This installs:
# - Standalone executable: /usr/local/bin/dbus-mcp
# - Socket wrapper: /usr/local/bin/dbus-mcp-socket-wrapper  
# - Config file: /etc/dbus-mcp/config
# - SystemD service: ~/.config/systemd/user/dbus-mcp-standalone.service
```

### Configuration

Edit `/etc/dbus-mcp/config`:

```bash
# Safety level (high, medium, or low)
SAFETY_LEVEL="medium"
```

### Starting the Service

```bash
# Start the service
systemctl --user start dbus-mcp-standalone.service

# Enable automatic startup
systemctl --user enable dbus-mcp-standalone.service

# Check status
systemctl --user status dbus-mcp-standalone.service
```

### Connecting Clients

Configure your MCP client to use the Unix socket:

```json
{
  "mcpServers": {
    "dbus-mcp": {
      "command": "socat",
      "args": ["UNIX-CONNECT:$XDG_RUNTIME_DIR/dbus-mcp.sock", "STDIO"]
    }
  }
}
```

## Development Mode

Development mode runs the server directly with stdio communication. This mode is suitable for:
- Testing and debugging
- Development of new features
- Quick experiments
- Environments without systemd

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

### When to Use Development Mode

✅ During active development  
✅ For debugging and testing  
✅ In environments without systemd  
❌ NOT for production use  
❌ NOT for multi-client scenarios  

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