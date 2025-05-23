# Quick Start Guide

This guide will get you up and running with the D-Bus MCP server in just a few minutes.

## Prerequisites

Before you begin, ensure you have:

1. **Linux** with D-Bus (most desktop distributions have this)
2. **Python 3.9+** installed
3. **System packages** for your distribution:

```bash
# Arch Linux
sudo pacman -S python-gobject python-systemd

# Ubuntu/Debian  
sudo apt install python3-gi python3-systemd

# Fedora
sudo dnf install python3-gobject python3-systemd
```

## Installation Options

### 🚀 Option 1: Production Install with SystemD (Recommended)

For daily use, install D-Bus MCP as a systemd service:

```bash
# Clone the repository
git clone https://github.com/aaronsb/dbus-mcp.git
cd dbus-mcp

# Install with systemd service
./install.sh --prod-only

# Configure safety level
sudo nano /etc/dbus-mcp/config  # Set SAFETY_LEVEL="medium"

# Start the service
systemctl --user start dbus-mcp-standalone.service
systemctl --user enable dbus-mcp-standalone.service
```

This provides:
- ✅ Automatic startup on demand
- ✅ Unix socket for reliable connections
- ✅ Full systemd logging and management
- ✅ Security hardening

**📖 See the [SystemD Mode Guide](guides/SYSTEMD-MODE.md) for details**

### 🛠️ Option 2: Development Install

For development or testing:

```bash
# Clone the repository
git clone https://github.com/aaronsb/dbus-mcp.git
cd dbus-mcp

# Run the quick start script
./quickstart.sh
```

This will:
- ✅ Check your Python version
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Run tests to verify everything works

### Option 3: Manual Install

For custom setups:

```bash
# Clone the repository
git clone https://github.com/aaronsb/dbus-mcp.git
cd dbus-mcp

# Create virtual environment with system packages access
python -m venv venv --system-site-packages
source venv/bin/activate

# Install the package
pip install -e .

# Test the installation
python test_installation.py
```

## Running the Server

### Method 1: SystemD Service (Recommended)

If you installed with systemd support:

```bash
# The service should already be running if you followed Option 1
systemctl --user status dbus-mcp-standalone.service

# View logs
journalctl --user -u dbus-mcp-standalone.service -f

# Restart after config changes
systemctl --user restart dbus-mcp-standalone.service
```

### Method 2: Direct Execution (Development)

For development or testing:

```bash
# Activate virtual environment
source venv/bin/activate

# Run with default safety (high)
python -m dbus_mcp

# Run with specific safety level
python -m dbus_mcp --safety-level medium
```

## 📸 KDE Screenshot Permission (If Using KDE)

If you're using KDE Plasma and want to enable screenshot functionality, you need to install the desktop entry file:

```bash
sudo cp systemd/dbus-mcp-screenshot.desktop /usr/share/applications/
```

This allows the D-Bus MCP server to request screenshot permissions through KDE's security system. You'll be prompted to authorize screenshots on first use.

**📖 See [Screenshot Authorization Guide](guides/SCREENSHOT-AUTHORIZATION.md) for details**

## 🔒 Safety Levels - Choose Your Security

**Before configuring AI clients**, choose your safety level based on what you want the AI to do:

### 🟢 **HIGH Safety (Default)** - Recommended for Most Users
Perfect for essential desktop integration with maximum security:
```bash
python -m dbus_mcp --safety-level high
```
**Allows:** clipboard, notifications, media control, system monitoring  
**Blocks:** text editor injection, file operations, URL opening

### 🟡 **MEDIUM Safety** - Productivity Mode
For users who want AI assistance with text editing and file management:
```bash
python -m dbus_mcp --safety-level medium  
```
**Adds:** text editor operations (Kate, etc.), file manager control, browser integration  
**Still blocks:** system configuration, service management

### ⚫ **Always Blocked** - Hard Security Boundaries
These operations are **never allowed** regardless of safety level:
- ❌ System shutdown/reboot
- ❌ Disk formatting  
- ❌ Package installation/removal
- ❌ Password changes
- ❌ Root privilege escalation

> **💡 Recommendation:** Start with HIGH safety and only switch to MEDIUM if you specifically need AI to write text into editors or manage files.

**📖 [Complete Security Guide](../guides/SECURITY.md)**

## Configuring AI Clients

### Claude Desktop

Add to your Claude Desktop configuration:

**Linux:** `~/.config/claude/claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

#### For SystemD Mode (Recommended):
```json
{
  "mcpServers": {
    "dbus": {
      "command": "socat",
      "args": ["UNIX-CONNECT:$XDG_RUNTIME_DIR/dbus-mcp.sock", "STDIO"]
    }
  }
}
```

#### For Development Mode:
```json
{
  "mcpServers": {
    "dbus": {
      "command": "/absolute/path/to/dbus-mcp/venv/bin/python",
      "args": ["-m", "dbus_mcp", "--safety-level", "medium"],
      "cwd": "/absolute/path/to/dbus-mcp"
    }
  }
}
```

### Claude Code (claude.ai/code)

#### For SystemD Mode (Recommended):
```bash
# Add the server using socat to connect to the Unix socket
claude mcp add dbus-mcp socat -- UNIX-CONNECT:$XDG_RUNTIME_DIR/dbus-mcp.sock STDIO

# Verify it was added
claude mcp list
```

#### For Development Mode:
```bash
# Add the server with medium safety for text editor integration
claude mcp add dbus-mcp /absolute/path/to/dbus-mcp/venv/bin/python -- -m dbus_mcp --safety-level medium

# Verify it was added
claude mcp list
```

Note: The server will be available in your next Claude Code session.

### VS Code with Continue.dev

Add to your Continue configuration (`~/.continue/config.json`):

#### For SystemD Mode (Recommended):
```json
{
  "models": [...],
  "mcpServers": {
    "dbus": {
      "command": "socat",
      "args": ["UNIX-CONNECT:$XDG_RUNTIME_DIR/dbus-mcp.sock", "STDIO"]
    }
  }
}
```

#### For Development Mode:
```json
{
  "models": [...],
  "mcpServers": {
    "dbus": {
      "command": "/absolute/path/to/dbus-mcp/venv/bin/python",
      "args": ["-m", "dbus_mcp", "--safety-level", "medium"],
      "cwd": "/absolute/path/to/dbus-mcp"
    }
  }
}
```

## Testing the Integration

### 1. Run the Demo

```bash
source venv/bin/activate
python examples/demo_tools.py
```

This will demonstrate all core tools including:
- Sending desktop notifications
- Reading system status
- Listing D-Bus services
- Introspecting interfaces

### 2. Manual Test

Start the server and send it MCP protocol commands:

```bash
# Terminal 1: Start server
python -m dbus_mcp

# Terminal 2: Send test commands
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python -m dbus_mcp
```

### 3. Check Available Tools

Once connected through an AI client, ask:
- "What D-Bus tools do you have available?"
- "Can you show my system status?"
- "What's in my clipboard?"

## Troubleshooting

### Service Won't Start

```bash
# Check service status
systemctl --user status dbus-mcp

# View detailed logs
journalctl --user -u dbus-mcp -n 50

# Try running directly to see errors
cd /path/to/dbus-mcp
source venv/bin/activate
python -m dbus_mcp
```

### Missing System Packages

```bash
# Check what's missing
python -m dbus_mcp --check-requirements

# Install missing packages (example for Arch)
sudo pacman -S python-gobject python-systemd
```

### Permission Errors

- The server should **never** run as root
- Ensure your user is in the appropriate groups for D-Bus access
- Check that D-Bus session bus is running: `echo $DBUS_SESSION_BUS_ADDRESS`

### Virtual Environment Issues

Always create the venv with system packages access:
```bash
python -m venv venv --system-site-packages
```

## Uninstalling

### Remove Systemd Service

```bash
./scripts/uninstall-service.sh
```

### Remove from Claude Code

```bash
claude mcp remove dbus-mcp
```

### Complete Removal

```bash
# Remove service first
./scripts/uninstall-service.sh

# Remove from AI clients
claude mcp remove dbus-mcp

# Delete the directory
cd ..
rm -rf dbus-mcp
```

## Next Steps

- Read the [full documentation](../README.md)
- Explore [available tools](TOOL-HIERARCHY.md)
- Learn about [security model](SECURITY.md)
- See [examples](EXAMPLES.md) of what you can do

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/aaronsb/dbus-mcp/issues)
- **Documentation**: [docs/](../)
- **System Detection**: `python -m dbus_mcp --detect`
- **Requirements Check**: `python -m dbus_mcp --check-requirements`