# D-Bus MCP Server - Architecture Overview

## Two Primary Linux System Roles

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AI Assistant (Claude)                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ MCP Protocol
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        D-Bus MCP Server                              │
│  ┌─────────────────────────────┬─────────────────────────────────┐ │
│  │   Workstation Role          │    Dedicated System Role         │ │
│  │  (Interactive Desktop)      │   (Servers, Appliances, etc)     │ │
│  └─────────────────────────────┴─────────────────────────────────┘ │
└──────────────────┬───────────────────────────┬──────────────────────┘
                   ▼                           ▼
         ┌─────────────────┐         ┌─────────────────┐
         │  Session Bus    │         │   System Bus    │
         │  (User Context) │         │ (Read + Helper) │
         └────────┬────────┘         └────────┬────────┘
                  │                            │
    ┌─────────────┼─────────────┐             │
    ▼             ▼             ▼             ▼
[Clipboard]  [Notifications] [Media]    [SystemD] [Logs] [Network]
[Screenshot] [File Dialogs]  [Portal]   [UPower]  [Journal] [NM]

```

## Workstation Role: Desktop Collaboration Flow

```
User's Desktop Session
├── AI reads clipboard to understand context
├── AI sends notification "Starting task..."
├── User shares screenshot of error
├── AI analyzes screenshot
├── AI writes fix to clipboard
├── AI pauses media during focus work
└── AI notifies "Task complete!"
```

## Dedicated System Role: Remote Management Flow

```
Fleet Management Scenario
├── AI connects to server-prod-03
├── Discovers available D-Bus services
├── Introspects custom app interfaces
├── Queries systemd for service status
├── Analyzes journal logs for errors
├── Identifies failed worker process
├── Restarts service (with auth)
├── Verifies service health
├── Logs actions taken
└── Disconnects and moves to next server
```

## Security Zones

### Zone 1: Interactive Session (Green Zone)
- **Trust Level**: High (user's own session)
- **Operations**: Clipboard, notifications, screenshots
- **Restrictions**: Rate limiting, no system changes

### Zone 2: System Read (Yellow Zone)  
- **Trust Level**: Medium (read-only access)
- **Operations**: Battery status, network state, service info
- **Restrictions**: No modifications allowed

### Zone 3: Privileged Operations (Red Zone)
- **Trust Level**: Low (requires explicit auth)
- **Operations**: Service restart, network toggle
- **Restrictions**: PolicyKit authorization, audit logging

### Zone 4: Forbidden (Black Zone)
- **Trust Level**: None (always denied)
- **Operations**: Shutdown, disk format, package install
- **Restrictions**: Hard-coded rejection

## Implementation Layers

```
┌─────────────────────────────────────────────┐
│          MCP Protocol Handler               │ <- Handles MCP requests
├─────────────────────────────────────────────┤
│          Tool Registry                      │ <- Maps tools to handlers
├─────────────────────────────────────────────┤
│          Security Policy Engine             │ <- Enforces permissions
├─────────────────────────────────────────────┤
│     D-Bus Connection Manager                │ <- Manages bus connections
├─────────────────────────────────────────────┤
│   Desktop Tools  │  Server Tools            │ <- Tool implementations
└─────────────────────────────────────────────┘
```

## Connection Modes

### Workstation Role
- Long-lived connection
- Stateful session
- User authentication
- Interactive operations
- Desktop environment integration

### Dedicated System Role
- Ephemeral connections
- Stateless operations
- Service authentication
- Batch processing
- Works on servers, routers, NAS, IoT devices, etc.

## Tool Categories

### Universal Tools
- `list_services` - Available on both buses
- `introspect` - Discover interfaces
- `call_method` - Generic invocation

### Desktop-Specific Tools
- `clipboard_*` - Session bus only
- `screenshot` - Requires display
- `media_control` - User media players

### Server-Specific Tools
- `systemd_*` - Service management
- `journal_*` - Log analysis
- `network_config` - Network state

This architecture enables the D-Bus MCP server to adapt to different Linux system roles - from interactive workstations where users need productivity tools, to dedicated systems (servers, appliances, embedded devices) that require remote monitoring and management. The same core technology serves vastly different purposes based on the system's role.