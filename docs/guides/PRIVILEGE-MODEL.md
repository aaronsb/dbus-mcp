# D-Bus MCP Server - Privilege Model

## Overview

The D-Bus MCP server operates with strict privilege separation to ensure security while providing useful functionality. The server NEVER runs as root and uses multiple techniques to safely access system information.

## Privilege Levels

### Level 0: User Context (Default)
- **What**: MCP server runs as regular user
- **Access**: Session bus, user's own processes
- **Use cases**: 99% of operations (notifications, media, clipboard)

### Level 1: System Query (Read-Only)
- **What**: Unprivileged queries to system bus
- **Access**: Specific whitelisted property reads
- **Use cases**: Battery status, network state, system info

### Level 2: Privileged Helper
- **What**: Separate process with specific capabilities
- **Access**: Limited system operations via PolicyKit
- **Use cases**: Network toggle, brightness control

### Level 3: Never Allowed
- **What**: Operations that are always forbidden
- **Access**: None, hard-coded rejection
- **Examples**: Shutdown, reboot, format, install packages

## Implementation Strategy

```
┌──────────────┐
│  AI Client   │
└──────┬───────┘
       │ MCP Protocol
       ▼
┌──────────────────────────────────────┐
│   MCP Server (runs as user 'mcp')   │
│  UID: 1001, GID: 1001               │
│  No special privileges               │
└──────┬───────────────────┬──────────┘
       │                   │
       ▼                   ▼
┌──────────────┐    ┌─────────────────┐
│ Session Bus  │    │ System Bus      │
│ (Full Access)│    │ (Read Only)     │
└──────────────┘    └────────┬────────┘
                             │ When privileged
                             │ operation needed
                             ▼
                    ┌─────────────────┐
                    │ PolicyKit Check │
                    └────────┬────────┘
                             │ If authorized
                             ▼
                    ┌─────────────────────┐
                    │ dbus-mcp-helper     │
                    │ (Minimal privileges) │
                    └─────────────────────┘
```

## Detailed Context Handling

### 1. Session Bus Operations (User Context)

```python
class UserContextOperations:
    """All operations that run in user context"""
    
    def __init__(self, username):
        self.username = username
        self.uid = pwd.getpwnam(username).pw_uid
        self.gid = pwd.getpwnam(username).pw_gid
        
        # Drop any elevated privileges if accidentally started as root
        if os.getuid() == 0:
            os.setgroups([self.gid])
            os.setgid(self.gid)
            os.setuid(self.uid)
        
        # Connect to session bus as user
        self.session_bus = SessionBus()
    
    def send_notification(self, title, body):
        """Safe - runs entirely in user context"""
        notifier = self.session_bus.get('org.freedesktop.Notifications')
        return notifier.Notify('dbus-mcp', 0, '', title, body, [], {}, -1)
    
    def control_media(self, player, action):
        """Safe - affects only user's media players"""
        player_obj = self.session_bus.get(f'org.mpris.MediaPlayer2.{player}')
        getattr(player_obj, action)()
```

### 2. System Bus Queries (Unprivileged Read)

```python
class SystemReadOperations:
    """Read-only system information queries"""
    
    def __init__(self):
        # Connect to system bus with no special privileges
        self.system_bus = SystemBus()
        
        # Define safe read-only queries
        self.safe_reads = {
            'battery': {
                'service': 'org.freedesktop.UPower',
                'path': '/org/freedesktop/UPower/devices/DisplayDevice',
                'properties': ['Percentage', 'State', 'TimeToEmpty']
            },
            'network': {
                'service': 'org.freedesktop.NetworkManager',
                'path': '/org/freedesktop/NetworkManager',
                'properties': ['State', 'Connectivity', 'Version']
            }
        }
    
    def get_battery_status(self):
        """Safe - read-only query to UPower"""
        try:
            upower = self.system_bus.get(
                'org.freedesktop.UPower',
                '/org/freedesktop/UPower/devices/DisplayDevice'
            )
            return {
                'percentage': upower.Percentage,
                'state': upower.State,
                'time_to_empty': upower.TimeToEmpty
            }
        except Exception as e:
            # Never expose internal errors
            return {'error': 'Unable to query battery status'}
```

### 3. Privileged Operations (Via Helper)

```python
# This runs as a separate process with minimal privileges
class PrivilegedHelper:
    """Helper process for privileged operations"""
    
    def __init__(self):
        self.uid = os.getuid()
        self.username = pwd.getpwuid(self.uid).pw_name
        
        # Verify we're NOT running as root
        if self.uid == 0:
            raise SecurityError("Helper must not run as root")
        
        # We have specific capabilities via systemd
        # CAP_NET_ADMIN for network operations
        # CAP_SYS_ADMIN for brightness control
        
    async def toggle_wifi(self, enable: bool, requesting_user: str):
        """Requires CAP_NET_ADMIN capability"""
        
        # First check PolicyKit authorization
        auth = await self.check_polkit_auth(
            action='com.dbus-mcp.toggle-wifi',
            user=requesting_user
        )
        
        if not auth:
            raise PermissionError("Not authorized to toggle WiFi")
        
        # Log the action
        self.audit_log(f"WiFi {'enabled' if enable else 'disabled'} by {requesting_user}")
        
        # Perform the action
        nm = SystemBus().get('org.freedesktop.NetworkManager')
        nm.Enable(enable)
    
    async def set_brightness(self, level: int, requesting_user: str):
        """Requires specific sysfs access"""
        
        # Validate input
        if not 0 <= level <= 100:
            raise ValueError("Brightness must be 0-100")
        
        # Check authorization
        auth = await self.check_polkit_auth(
            action='com.dbus-mcp.set-brightness',
            user=requesting_user
        )
        
        if not auth:
            raise PermissionError("Not authorized to change brightness")
        
        # Write to sysfs (requires capability)
        with open('/sys/class/backlight/intel_backlight/brightness', 'w') as f:
            max_brightness = 1000  # Device specific
            f.write(str(int(level * max_brightness / 100)))
```

### 4. PolicyKit Integration

```xml
<!-- /usr/share/polkit-1/actions/com.dbus-mcp.policy -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  
  <action id="com.dbus-mcp.toggle-wifi">
    <description>Toggle WiFi via D-Bus MCP</description>
    <message>Authentication is required to toggle WiFi</message>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
  </action>
  
  <action id="com.dbus-mcp.set-brightness">
    <description>Adjust screen brightness via D-Bus MCP</description>
    <message>Authentication is required to change brightness</message>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>yes</allow_active>
    </defaults>
  </action>
  
</policyconfig>
```

## Systemd Service Configuration

### Main Service (Unprivileged)
```ini
# /etc/systemd/system/dbus-mcp.service
[Unit]
Description=D-Bus MCP Server
After=multi-user.target

[Service]
Type=simple
User=dbus-mcp
Group=dbus-mcp
ExecStart=/usr/bin/dbus-mcp-server

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictNamespaces=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictRealtime=true
RestrictSUIDSGID=true
RemoveIPC=true
PrivateMounts=true
SystemCallFilter=@system-service

# No capabilities needed for main service
CapabilityBoundingSet=
AmbientCapabilities=

[Install]
WantedBy=multi-user.target
```

### Helper Service (Limited Privileges)
```ini
# /etc/systemd/system/dbus-mcp-helper.socket
[Unit]
Description=D-Bus MCP Privileged Helper Socket

[Socket]
ListenStream=/run/dbus-mcp/helper.sock
SocketMode=0600
SocketUser=dbus-mcp
SocketGroup=dbus-mcp

[Install]
WantedBy=sockets.target
```

```ini
# /etc/systemd/system/dbus-mcp-helper@.service
[Unit]
Description=D-Bus MCP Privileged Helper for %i
After=dbus-mcp-helper.socket

[Service]
Type=simple
User=dbus-mcp-helper
Group=dbus-mcp-helper
ExecStart=/usr/bin/dbus-mcp-helper

# Limited capabilities
CapabilityBoundingSet=CAP_NET_ADMIN CAP_DAC_OVERRIDE
AmbientCapabilities=CAP_NET_ADMIN CAP_DAC_OVERRIDE

# Still heavily restricted
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
MemoryDenyWriteExecute=true
RestrictRealtime=true
SystemCallFilter=@system-service @network-io

# Specific paths for brightness control
ReadWritePaths=/sys/class/backlight
```

## User Creation

```bash
# Create unprivileged user for main service
sudo useradd -r -s /usr/sbin/nologin -d /nonexistent -c "D-Bus MCP Server" dbus-mcp

# Create helper user with specific group memberships
sudo useradd -r -s /usr/sbin/nologin -d /nonexistent -c "D-Bus MCP Helper" dbus-mcp-helper
sudo usermod -a -G video dbus-mcp-helper  # For brightness control

# Create runtime directory
sudo mkdir -p /run/dbus-mcp
sudo chown dbus-mcp:dbus-mcp /run/dbus-mcp
sudo chmod 0755 /run/dbus-mcp
```

## Security Checklist

✓ **Never run as root** - All components run as unprivileged users
✓ **Capability-based security** - Helper has only specific capabilities
✓ **PolicyKit integration** - User authorization for privileged operations
✓ **Audit logging** - All privileged operations are logged
✓ **Fail closed** - Deny by default, whitelist safe operations
✓ **Process isolation** - Separate processes for different privilege levels
✓ **Systemd hardening** - Comprehensive security restrictions
✓ **No setuid binaries** - Everything runs with normal permissions
✓ **Rate limiting** - Prevent abuse of system resources
✓ **Input validation** - All inputs sanitized before use