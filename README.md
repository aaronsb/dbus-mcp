# D-Bus MCP Server

A Model Context Protocol (MCP) server that exposes D-Bus functionality to AI assistants, enabling deep integration with Linux systems - from vacuum cleaners to supercomputers.

## Vision

This project enables AI assistants to interact with Linux systems through the standardized D-Bus interface. While Linux runs on everything from vacuum cleaners to supercomputers, this MCP server focuses on two major system roles where D-Bus integration provides the most value:

### 1. Workstation Role (Interactive Desktop Systems)
For Linux desktop/laptop users, AI assistants can enhance productivity by:
- Managing clipboard content and history
- Sending desktop notifications
- Taking and analyzing screenshots
- Controlling media playback
- Monitoring system resources
- Integrating with desktop applications

### 2. Dedicated System Role (Servers, Appliances, Embedded)
For systems with specific purposes (web servers, routers, NAS, IoT devices), AI operates as a "maintenance robot" that can:
- Connect to servers via standardized D-Bus interfaces
- Discover available services and capabilities
- Monitor system health and performance
- Analyze logs and diagnose issues
- Perform authorized remediation actions
- Generate reports across server fleets

## Key Features

- **Secure by Design**: Multiple privilege levels, PolicyKit integration, audit logging
- **Desktop Environment Agnostic**: Uses freedesktop.org standards where possible
- **Discoverable**: Services self-document through D-Bus introspection
- **Type-Safe**: D-Bus provides strong typing for all operations
- **Rate Limited**: Prevents abuse of system resources

## Architecture

The MCP server acts as a bridge between AI assistants and the D-Bus system:

```
AI Assistant <-> MCP Protocol <-> D-Bus MCP Server <-> D-Bus (Session/System)
```

## Security Model

- **Never runs as root**: All operations use appropriate privilege levels
- **Three contexts**: User (default), Read-only system, Privileged helper
- **Hard-blocked operations**: System shutdown, disk format, package management
- **Audit trail**: All operations logged with context

## Getting Started

See the design documents:
- `CONCEPT.md` - Overview and use cases
- `USE-CASES-RANKED.md` - Prioritized feature list
- `SECURITY.md` - Security architecture
- `DISCOVERED-CAPABILITIES.md` - Real D-Bus services on Linux

## Status

Currently in design phase. Implementation will begin with core service discovery and progress through desktop and server capabilities based on use case priorities.

## License

[To be determined]