# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

D-Bus MCP Server - A Model Context Protocol server that bridges AI assistants with D-Bus system and session buses on Linux systems.

While Linux powers everything from vacuum cleaners to supercomputers, this server focuses on two major system roles:

1. **Workstation Role**: Interactive desktop/laptop systems where AI assists users with productivity tasks
2. **Dedicated System Role**: Purpose-built systems (servers, routers, NAS, embedded devices) where AI performs remote monitoring and management

## Architecture

The project follows a modular architecture:
- **MCP Server Core**: Handles protocol, tool registration, request/response
- **D-Bus Manager**: Manages session/system bus connections
- **Security Layer**: Enforces policies, whitelists safe operations
- **Tool Implementations**: Individual tools for specific D-Bus operations

## Key Design Documents

- `README.md`: Project overview and vision
- `ARCHITECTURE-OVERVIEW.md`: Visual architecture and dual use cases
- `CONCEPT.md`: High-level overview and use cases
- `DESIGN.md`: Technical architecture and implementation details
- `EXAMPLES.md`: Usage examples and best practices
- `SECURITY.md`: Comprehensive security architecture
- `PRIVILEGE-MODEL.md`: Privilege separation and context handling
- `CONTEXT-EXAMPLES.md`: Real-world context scenarios and security patterns
- `DISCOVERED-CAPABILITIES.md`: Live system exploration findings
- `USE-CASES-RANKED.md`: Prioritized capabilities by system role
- `SERVER-FLEET-CONCEPT.md`: "Maintenance robot" model for dedicated systems
- `SYSTEM-ROLES.md`: Linux system diversity and role definitions

## Development Guidelines

### Language: Python
- Use `pydbus` or `dbus-python` for D-Bus integration
- Use the MCP Python SDK
- Follow async patterns for signal handling

### Security First
- **Never run as root** - MCP server always runs as unprivileged user
- **Three privilege levels**: User context (default), System read-only, Privileged helper
- **Hard-blocked operations**: Shutdown, reboot, disk format, package management
- **PolicyKit integration** for any privileged operations
- **Audit logging** for all security-relevant events
- **Rate limiting** on all operations to prevent abuse
- **Fail closed** - Deny by default, whitelist safe operations

### Core Tools to Implement

**Common Core**:
1. `dbus.list_services` - Service discovery
2. `dbus.introspect` - Interface exploration  
3. `dbus.call_method` - Method invocation

**Workstation Tools**:
4. `dbus.notify` - Desktop notifications
5. `dbus.clipboard_read/write` - Clipboard access
6. `dbus.screenshot` - Screen capture
7. `dbus.media_control` - Media player control

**Dedicated System Tools**:
8. `dbus.systemd_status` - Service health monitoring
9. `dbus.journal_query` - Log analysis
10. `dbus.network_status` - Network state discovery

## Testing Approach

- Mock D-Bus connections for unit tests
- Use real D-Bus for integration tests
- Test security policies extensively
- Verify rate limiting works correctly