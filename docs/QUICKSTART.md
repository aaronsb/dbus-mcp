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

## Installation

### Option 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/aaronsb/dbus-mcp.git
cd dbus-mcp

# Run the quick start script
./quickstart.sh
```

This will:
- ✅ Check your Python version
- ✅ Create a virtual environment with system packages
- ✅ Install all dependencies
- ✅ Run tests to verify everything works

### Option 2: Manual Install

```bash
# Clone the repository
git clone https://github.com/aaronsb/dbus-mcp.git
cd dbus-mcp

# Create virtual environment with system packages access
python -m venv venv --system-site-packages
source venv/bin/activate

# Install the package
pip install -e .

# Check requirements
python -m dbus_mcp --check-requirements

# Test the installation
python test_installation.py
```

## Running the Server

### Method 1: Direct Execution (Development)

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python -m dbus_mcp
```

### Method 2: Systemd Service (Recommended for Daily Use)

Install as a systemd user service for automatic startup:

```bash
# Install the service
./scripts/install-service.sh

# Start the service
systemctl --user start dbus-mcp

# Check status
systemctl --user status dbus-mcp

# View logs
journalctl --user -u dbus-mcp -f
```

The service will automatically start when you log in.

## Configuring AI Clients

### Claude Desktop

Add to your Claude Desktop configuration:

**Linux:** `~/.config/claude/claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "dbus": {
      "command": "/absolute/path/to/dbus-mcp/venv/bin/python",
      "args": ["-m", "dbus_mcp"],
      "cwd": "/absolute/path/to/dbus-mcp"
    }
  }
}
```

### Claude Code (claude.ai/code)

Use the Claude CLI to add the server:

```bash
# Add the server
claude mcp add dbus-mcp /absolute/path/to/dbus-mcp/venv/bin/python -- -m dbus_mcp

# Verify it was added
claude mcp list

# The server will be available in your next Claude Code session
```

### VS Code with Continue.dev

Add to your Continue configuration (`~/.continue/config.json`):

```json
{
  "models": [...],
  "mcpServers": {
    "dbus": {
      "command": "/absolute/path/to/dbus-mcp/venv/bin/python",
      "args": ["-m", "dbus_mcp"],
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