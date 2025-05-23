# SystemD Mode for D-Bus MCP Server

This guide explains how to run the D-Bus MCP server as a systemd service with Unix socket support - the **recommended production deployment method**.

## Overview

Running D-Bus MCP in systemd mode is the recommended approach for production deployments. This provides:

### ✅ Key Benefits
- **Automatic startup** - Service starts on demand when clients connect
- **Socket persistence** - Connections survive server restarts
- **System integration** - Full journald logging and systemctl management
- **Security hardening** - SystemD sandboxing and privilege restrictions
- **Resource management** - CPU and memory limits enforced by systemd
- **Multi-client support** - Handle multiple simultaneous connections

### 🏗️ Architecture

The systemd mode uses a Unix socket for reliable inter-process communication:

```
AI Client → socat → Unix Socket → D-Bus MCP Server
                     ↑
                  Managed by systemd
```

## Installation

### Quick Install

The recommended way to install D-Bus MCP with systemd support:

```bash
# Clone the repository
git clone https://github.com/aaronsb/dbus-mcp.git
cd dbus-mcp

# Install with systemd service (production mode)
./install.sh --prod-only
```

### What Gets Installed

The installation creates:
- `/usr/local/bin/dbus-mcp` - Standalone executable
- `/usr/local/bin/dbus-mcp-socket-wrapper` - Configuration wrapper
- `~/.config/systemd/user/dbus-mcp-standalone.service` - SystemD user service
- `/etc/dbus-mcp/config` - System-wide configuration (requires sudo)

## Configuration

Edit `/etc/dbus-mcp/config` to set the safety level:

```bash
SAFETY_LEVEL="medium"  # or "high", "low"
```

## Usage

### Managing the Service

```bash
# Start the service
systemctl --user start dbus-mcp-standalone.service

# Enable automatic startup on boot
systemctl --user enable dbus-mcp-standalone.service

# Check service status
systemctl --user status dbus-mcp-standalone.service

# View logs
journalctl --user -u dbus-mcp-standalone.service -f

# Restart after configuration changes
systemctl --user restart dbus-mcp-standalone.service
```

### Configuring AI Clients

Configure your AI client to connect via the Unix socket:

#### Claude Desktop / Claude Code
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

#### Manual Testing
```bash
# Test the connection
socat - UNIX-CONNECT:$XDG_RUNTIME_DIR/dbus-mcp.sock
```

## Troubleshooting

### Check Logs

```bash
journalctl --user -u dbus-mcp-standalone.service -f
```

### Socket Issues

If the socket already exists:
```bash
systemctl --user stop dbus-mcp-standalone.service
rm -f $XDG_RUNTIME_DIR/dbus-mcp.sock
systemctl --user start dbus-mcp-standalone.service
```

## Advantages Over Direct Mode

### Why Use SystemD Mode?

| Feature | SystemD Mode | Direct Mode |
|---------|--------------|-------------|
| **Automatic startup** | ✅ On-demand | ❌ Manual |
| **Process management** | ✅ SystemD handles | ❌ User manages |
| **Logging** | ✅ Journald integration | ❌ Console only |
| **Security** | ✅ Sandboxing + limits | ❌ Basic only |
| **Multi-client** | ✅ Supported | ❌ Single client |
| **Persistence** | ✅ Survives crashes | ❌ Manual restart |
| **Production ready** | ✅ Yes | ❌ Development only |

## Technical Details

### Socket Bridge Architecture

Due to FastMCP's stdio-based transport, we use socat to bridge between the Unix socket and the MCP server's stdio interface. This provides the benefits of socket-based communication while maintaining compatibility with the MCP protocol.

### Security Hardening

The systemd service includes comprehensive security measures:

```ini
# Privilege restrictions
NoNewPrivileges=true          # Prevent privilege escalation
PrivateUsers=true             # Isolated user namespace

# Filesystem protection
ProtectSystem=strict          # Read-only system directories
ProtectHome=read-only         # Read-only home directory
PrivateTmp=true              # Isolated /tmp
ReadWritePaths=~/.cache ~/.local/share  # Limited write access

# Resource limits
MemoryLimit=512M             # Prevent memory exhaustion
CPUQuota=50%                 # Limit CPU usage
```

### File Locations

- **Socket**: `$XDG_RUNTIME_DIR/dbus-mcp.sock` (typically `/run/user/1000/dbus-mcp.sock`)
- **Configuration**: `/etc/dbus-mcp/config`
- **Service file**: `~/.config/systemd/user/dbus-mcp-standalone.service`
- **Logs**: Accessible via `journalctl`

## Migration from Direct Mode

If you've been using direct mode, migrating to systemd mode is simple:

1. Install systemd mode: `./install.sh --prod-only`
2. Configure safety level in `/etc/dbus-mcp/config`
3. Update your AI client configuration to use socat
4. Start the service: `systemctl --user start dbus-mcp-standalone.service`

## Future Improvements

- Native socket support in FastMCP (eliminating socat requirement)
- True systemd socket activation
- Per-connection instance support for better isolation