# D-Bus MCP Server - Architecture Decisions

## Key Questions to Address

### 1. SystemD Integration Pattern

**Status: ✅ Implemented as the recommended deployment method**

The MCP server runs as a systemd user service with Unix socket communication. This is now the **recommended production deployment** pattern.

**Current Architecture:**
```
┌─────────────────┐
│   AI Client     │
└────────┬────────┘
         │ MCP Protocol (stdio/SSE)
         ▼
┌─────────────────────────────────────┐
│   systemd service unit              │
│  ┌─────────────────────────────┐    │
│  │  dbus-mcp-server.service    │    │
│  │  - Runs as user service     │    │
│  │  - Socket activated         │    │
│  │  - Resource controlled      │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
         │
         ├──→ Session Bus (user operations)
         └──→ System Bus (read-only queries)
```

**Benefits of SystemD Integration:**
- **Socket Activation**: Start on-demand when AI connects
- **Resource Control**: Memory/CPU limits via cgroups
- **Lifecycle Management**: Clean startup/shutdown
- **Logging**: Integrated with journald
- **Security**: SystemD's sandboxing features

### 2. D-Bus Self-Exposure

The MCP server should expose its own D-Bus interface for meta-operations:

```xml
<interface name="org.mcp.DBusServer">
  <!-- Status and monitoring -->
  <method name="GetStatus">
    <arg type="s" direction="out" name="status"/>
  </method>
  <method name="GetStatistics">
    <arg type="a{sv}" direction="out" name="stats"/>
  </method>
  
  <!-- Configuration -->
  <method name="ReloadConfig">
  </method>
  <property name="RateLimits" type="a{su}" access="read"/>
  
  <!-- Signals -->
  <signal name="ClientConnected">
    <arg type="s" name="client_id"/>
  </signal>
  <signal name="SecurityEvent">
    <arg type="s" name="event_type"/>
    <arg type="a{sv}" name="details"/>
  </signal>
</interface>
```

This enables:
- System monitoring tools to track MCP server health
- Dynamic configuration updates
- Security event monitoring
- Integration with desktop environments

### 3. Architectural Pattern: Hybrid Approach

Neither pure lightweight shim nor heavyweight server, but a **hybrid architecture**:

```
┌──────────────────────────────────────────────┐
│            MCP Server Core (Medium Weight)    │
│                                              │
│  ┌──────────────┐  ┌───────────────────┐    │
│  │ MCP Protocol │  │  D-Bus Connection  │    │
│  │   Handler    │  │     Manager        │    │
│  └──────────────┘  └───────────────────┘    │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │          Tool Execution Engine          │ │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ │ │
│  │  │ Notify  │ │Clipboard│ │ SystemD  │ │ │
│  │  │ Tool    │ │  Tool   │ │  Tool    │ │ │
│  │  └─────────┘ └─────────┘ └──────────┘ │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

**Rationale:**
- **MCP Handler**: Moderate weight - handles protocol, authentication, rate limiting
- **D-Bus Operations**: Lightweight - mostly translating calls
- **Tool Engine**: Pluggable architecture for easy extension

### 4. Language Decision: Python

After careful consideration, **Python** is the optimal choice:

**Pros:**
1. **Official MCP SDK**: First-class support from Anthropic
2. **Excellent D-Bus Bindings**: 
   - `pydbus` - Pythonic, GObject-based
   - `dbus-python` - Lower level, more control
3. **SystemD Integration**: `systemd-python` for deep integration
4. **Rapid Development**: Quick iteration on tools
5. **AI/MCP Ecosystem**: Most MCP examples are in Python
6. **Async Support**: `asyncio` for handling concurrent operations

**Cons:**
- Performance overhead (mitigated by token generation being the bottleneck)
- Memory usage (acceptable for this use case)

**Alternative Considered: TypeScript**
- Pros: Also has official SDK, good async
- Cons: D-Bus bindings less mature, more complex deployment

## Proposed Implementation Architecture

### 1. Service Structure
```
dbus-mcp/
├── systemd/
│   ├── dbus-mcp-server@.service    # User service template
│   ├── dbus-mcp-system.service     # System service (optional)
│   └── dbus-mcp-server.socket      # Socket activation
├── src/
│   ├── mcp_server.py               # Main MCP server
│   ├── dbus_manager.py             # D-Bus connection handling
│   ├── tools/                      # Individual tool implementations
│   └── security.py                 # Security policy engine
└── config/
    └── dbus-mcp.conf               # Configuration file
```

### 2. Startup Flow
```python
# Simplified startup
async def main():
    # 1. Parse config and args
    config = load_config()
    
    # 2. Initialize D-Bus connections
    session_bus = SessionBus()
    system_bus = SystemBus()  # Read-only
    
    # 3. Export our own D-Bus service
    server_object = DBusMCPServer()
    session_bus.publish("org.mcp.DBusServer", server_object)
    
    # 4. Initialize MCP server
    mcp = Server("dbus-mcp")
    
    # 5. Register tools based on context
    if is_workstation():
        register_workstation_tools(mcp)
    if has_system_access():
        register_system_tools(mcp)
    
    # 6. Start serving
    stdio_transport = StdioServerTransport()
    await mcp.connect(stdio_transport)
```

### 3. SystemD Service Files

**User Service** (`~/.config/systemd/user/dbus-mcp-server.service`):
```ini
[Unit]
Description=D-Bus MCP Server
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m dbus_mcp.server
Restart=on-failure
StandardInput=socket
StandardOutput=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=read-only
ProtectSystem=strict

[Install]
WantedBy=default.target
```

**Socket Activation** (`dbus-mcp-server.socket`):
```ini
[Unit]
Description=D-Bus MCP Server Socket

[Socket]
ListenStream=/run/user/%U/dbus-mcp.socket
Accept=false

[Install]
WantedBy=sockets.target
```

### 4. Current Implementation Status

**Implemented Deployment Model:**
- ✅ SystemD user service (`dbus-mcp-standalone.service`)
- ✅ Unix socket at `$XDG_RUNTIME_DIR/dbus-mcp.sock`
- ✅ socat bridge for stdio-to-socket translation
- ✅ System-wide configuration at `/etc/dbus-mcp/config`
- ✅ Full journald integration

**Why Unix Socket + socat:**
Due to FastMCP's stdio-based transport, we use socat as a bridge between the Unix socket and the MCP server's stdio interface. This provides:
- Socket-based reliability and persistence
- Multiple client support
- SystemD integration benefits
- Compatibility with existing MCP protocol

**📖 See [SystemD Mode Guide](../guides/SYSTEMD-MODE.md) for deployment instructions**

## Design Principles

1. **Separation of Concerns**: MCP protocol handling separate from D-Bus operations
2. **Pluggable Tools**: Easy to add new D-Bus tools
3. **Context Awareness**: Adapt to workstation vs server role
4. **Observable**: Expose metrics and status via D-Bus
5. **Secure by Default**: Minimal privileges, sandboxed execution

## Why This Architecture Works

1. **Natural Integration**: SystemD and D-Bus are already tightly coupled
2. **Flexible Deployment**: Can run as user or system service
3. **Resource Efficient**: Socket activation means zero resource usage when idle
4. **Monitorable**: System admins can track via standard tools
5. **Language Fit**: Python's strengths align with our needs

This hybrid approach balances the needs of MCP protocol handling with efficient D-Bus operations, while leveraging SystemD's powerful service management capabilities.