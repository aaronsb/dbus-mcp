# D-Bus MCP Server Documentation

Welcome to the D-Bus MCP Server documentation. This project enables AI assistants to interact with Linux systems through D-Bus, from vacuum cleaners to supercomputers.

## 🚀 Getting Started

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in minutes
- **[SystemD Mode Guide](guides/SYSTEMD-MODE.md)** - 🔥 **Recommended** production deployment with Unix socket
- **[Installation Guide](QUICKSTART.md#installation)** - Detailed installation instructions  
- **[Configuration Examples](QUICKSTART.md#configuring-ai-clients)** - Set up Claude Desktop, Claude Code, and VS Code
- **[Troubleshooting](QUICKSTART.md#troubleshooting)** - Common issues and solutions

## Documentation Structure

### 📐 Design Documents
Core concepts and use cases for the D-Bus MCP Server.

- [**Concept Overview**](design/CONCEPT.md) - High-level overview and use cases
- [**Use Cases Ranked**](design/USE-CASES-RANKED.md) - Prioritized capabilities by system role
- [**Server Fleet Concept**](design/SERVER-FLEET-CONCEPT.md) - "Maintenance robot" model for dedicated systems
- [**System Roles**](design/SYSTEM-ROLES.md) - Linux system diversity and role definitions
- [**🚀 Roadmap**](ROADMAP.md) - Future features and development priorities

### 🏗️ Architecture Documents
Technical architecture and implementation details.

- [**Architecture Overview**](architecture/ARCHITECTURE-OVERVIEW.md) - Visual architecture and dual use cases
- [**Architecture Decisions**](architecture/ARCHITECTURE-DECISIONS.md) - SystemD integration and deployment
- [**Connection Architecture**](architecture/CONNECTION-ARCHITECTURE.md) - Client-server-systemd connection model
- [**System Profiles**](architecture/SYSTEM-PROFILES.md) - Modular adaptation to different distros/DEs
- [**Language Evaluation**](architecture/LANGUAGE-EVALUATION.md) - Why Python was chosen
- [**Project Structure**](architecture/PROJECT-STRUCTURE.md) - Code organization
- [**File Pipe Manager**](architecture/FILE-PIPE-MANAGER.md) - 📸 Temporary file management for screenshots & exports
- [**Security Categories**](architecture/SECURITY-CATEGORIES.md) - Category-based security model

### 📚 Implementation Guides
Practical guides for development and deployment.

- [**SystemD Mode**](guides/SYSTEMD-MODE.md) - 🔥 **Recommended** production deployment with Unix socket
- [**Deployment**](guides/DEPLOYMENT.md) - 🚀 Development vs production deployment options
- [**Tool Presentation**](guides/TOOL-PRESENTATION.md) - Strategy for presenting tools to AI clients
- [**Tool Hierarchy**](guides/TOOL-HIERARCHY.md) - Progressive disclosure and tool organization
- [**Security**](guides/SECURITY.md) - Comprehensive security architecture
- [**Privilege Model**](guides/PRIVILEGE-MODEL.md) - Privilege separation and context handling
- [**Context Examples**](guides/CONTEXT-EXAMPLES.md) - Real-world context scenarios
- [**Discovered Capabilities**](guides/DISCOVERED-CAPABILITIES.md) - Live system exploration findings
- [**Examples**](guides/EXAMPLES.md) - Usage examples and best practices
- [**Screenshot Authorization**](guides/SCREENSHOT-AUTHORIZATION.md) - 📸 Enable screenshot capture on KDE
- [**Application Support**](guides/APPLICATION-SUPPORT.md) - Linux applications with D-Bus support
- [**Workstation Capabilities**](guides/WORKSTATION-CAPABILITIES.md) - Desktop/laptop features by safety level

## Quick Links

- [Back to Main README](../README.md)
- [Development Guide (CLAUDE.md)](../CLAUDE.md)
- [Getting Started](#getting-started)

## Getting Started

1. **Understand the Concept**: Start with the [Concept Overview](design/CONCEPT.md)
2. **Review Architecture**: Check the [Architecture Overview](architecture/ARCHITECTURE-OVERVIEW.md)
3. **Security First**: Read the [Security Guide](guides/SECURITY.md)
4. **Try Examples**: See [Usage Examples](guides/EXAMPLES.md)

## For Developers

If you're contributing to the project:
1. Read [CLAUDE.md](../CLAUDE.md) for development guidelines
2. Understand the [Project Structure](architecture/PROJECT-STRUCTURE.md)
3. Review [System Profiles](architecture/SYSTEM-PROFILES.md) for adaptation patterns

## For Operators

If you're deploying the D-Bus MCP Server:
1. Start with [SystemD Mode](guides/SYSTEMD-MODE.md) for production deployment
2. Check your [System Role](design/SYSTEM-ROLES.md)
3. Review [Security](guides/SECURITY.md) and [Privilege Model](guides/PRIVILEGE-MODEL.md)
4. See [Connection Architecture](architecture/CONNECTION-ARCHITECTURE.md) for advanced options