# D-Bus MCP Server - Technical Design

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐
│   AI Assistant  │────▶│   MCP Protocol   │
└─────────────────┘     └──────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  D-Bus MCP Server   │
                    ├─────────────────────┤
                    │  - Tool Registry    │
                    │  - Request Handler  │
                    │  - Security Filter  │
                    └─────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌──────────────┐     ┌──────────────┐
            │ Session Bus  │     │  System Bus  │
            └──────────────┘     └──────────────┘
                    │                     │
        ┌───────────┼───────────┐         │
        ▼           ▼           ▼         ▼
    [Desktop]  [Media]    [Clipboard] [Hardware]
    [Apps]     [Players]             [Services]
```

## Core Components

### 1. MCP Server Implementation

```python
# server.py
from mcp import Server, Tool
from mcp.types import TextContent
import asyncio
from typing import Any, Dict

class DBusMCPServer:
    def __init__(self):
        self.server = Server("dbus-mcp")
        self.session_bus = None
        self.system_bus = None
        self.setup_tools()
    
    def setup_tools(self):
        # Register all D-Bus tools
        self.server.add_tool(self.list_services_tool())
        self.server.add_tool(self.call_method_tool())
        self.server.add_tool(self.notify_tool())
        # ... more tools
```

### 2. D-Bus Connection Manager

```python
# dbus_manager.py
from pydbus import SessionBus, SystemBus
from gi.repository import GLib
import threading

class DBusManager:
    def __init__(self):
        self.session_bus = SessionBus()
        self.system_bus = SystemBus()
        self.main_loop = GLib.MainLoop()
        self.loop_thread = None
    
    def start(self):
        self.loop_thread = threading.Thread(
            target=self.main_loop.run,
            daemon=True
        )
        self.loop_thread.start()
    
    def get_service(self, bus_type: str, service_name: str):
        bus = self.session_bus if bus_type == "session" else self.system_bus
        return bus.get(service_name)
```

### 3. Security Policy Engine

```python
# security.py
from dataclasses import dataclass
from typing import List, Set
import re

@dataclass
class SecurityPolicy:
    allowed_interfaces: Set[str]
    blocked_methods: Set[str]
    requires_confirmation: Set[str]
    rate_limits: Dict[str, int]

DEFAULT_POLICY = SecurityPolicy(
    allowed_interfaces={
        "org.freedesktop.Notifications",
        "org.freedesktop.DBus.Properties",
        "org.mpris.MediaPlayer2.*",
        "org.gnome.Shell.Screenshot",
        # ... safe interfaces
    },
    blocked_methods={
        "Shutdown",
        "Reboot",
        "Format",
        "Delete",
        # ... dangerous methods
    },
    requires_confirmation={
        "org.freedesktop.login1.Manager.PowerOff",
        "org.freedesktop.NetworkManager.Enable",
        # ... sensitive operations
    },
    rate_limits={
        "default": 100,  # per minute
        "org.freedesktop.Notifications": 10,
    }
)
```

### 4. Tool Implementations

```python
# tools/notify.py
from mcp import Tool
from mcp.types import TextContent

class NotifyTool(Tool):
    name = "dbus.notify"
    description = "Send desktop notifications"
    
    input_schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "body": {"type": "string"},
            "icon": {"type": "string", "default": "dialog-information"},
            "urgency": {"type": "integer", "minimum": 0, "maximum": 2},
            "timeout": {"type": "integer", "default": 5000}
        },
        "required": ["summary", "body"]
    }
    
    async def run(self, args: Dict[str, Any]) -> TextContent:
        notifications = self.dbus_manager.get_service(
            "session",
            "org.freedesktop.Notifications"
        )
        
        notification_id = notifications.Notify(
            "dbus-mcp",  # app_name
            0,  # replaces_id
            args.get("icon", "dialog-information"),
            args["summary"],
            args["body"],
            [],  # actions
            {"urgency": args.get("urgency", 1)},  # hints
            args.get("timeout", 5000)
        )
        
        return TextContent(
            type="text",
            text=f"Notification sent with ID: {notification_id}"
        )
```

## Implementation Plan

### Phase 1: Core Infrastructure
- [x] Basic MCP server setup
- [ ] D-Bus connection management
- [ ] Security policy framework
- [ ] Error handling

### Phase 2: Essential Tools
- [ ] `list_services` - Discover available services
- [ ] `introspect` - Explore service interfaces
- [ ] `call_method` - Generic method invocation
- [ ] `notify` - Desktop notifications

### Phase 3: Convenience Tools
- [ ] `clipboard_read/write` - Clipboard access
- [ ] `media_control` - MPRIS media player control
- [ ] `screenshot` - Screen capture
- [ ] `list_applications` - Running apps

### Phase 4: Advanced Features
- [ ] Signal subscriptions
- [ ] Property monitoring
- [ ] Batch operations
- [ ] Custom policies

## Configuration

```yaml
# dbus-mcp.config.yaml
server:
  name: "dbus-mcp"
  version: "1.0.0"
  
security:
  # Whitelist specific interfaces
  allowed_interfaces:
    - "org.freedesktop.Notifications"
    - "org.mpris.MediaPlayer2.*"
    - "org.gnome.Shell.Screenshot"
  
  # Never allow these methods
  blocked_methods:
    - "Shutdown"
    - "Reboot"
    - "PowerOff"
  
  # Ask user before executing
  requires_confirmation:
    - "org.freedesktop.NetworkManager.*"
  
  # Rate limiting (calls per minute)
  rate_limits:
    default: 100
    "org.freedesktop.Notifications": 10

logging:
  level: "INFO"
  file: "/tmp/dbus-mcp.log"
```

## Testing Strategy

### Unit Tests
- Mock D-Bus connections
- Test security policies
- Validate tool schemas

### Integration Tests
- Real D-Bus interaction
- End-to-end MCP flow
- Error scenarios

### System Tests
- Multiple applications
- Permission boundaries
- Performance benchmarks

## Deployment

### Package Structure
```
dbus-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── dbus_mcp/
│       ├── __init__.py
│       ├── server.py
│       ├── dbus_manager.py
│       ├── security.py
│       └── tools/
│           ├── __init__.py
│           ├── notify.py
│           ├── clipboard.py
│           └── media.py
├── tests/
├── docs/
└── examples/
```

### Installation
```bash
pip install dbus-mcp
# or
pipx install dbus-mcp
```

### Running
```bash
# Start the server
dbus-mcp serve

# With custom config
dbus-mcp serve --config /path/to/config.yaml

# Debug mode
dbus-mcp serve --debug
```