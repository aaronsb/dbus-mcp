# D-Bus MCP Server - Project Structure

## Directory Layout

```
dbus-mcp/
├── src/
│   └── dbus_mcp/
│       ├── __init__.py
│       ├── __main__.py          # Entry point for CLI
│       ├── server.py            # Main MCP server implementation
│       ├── config.py            # Configuration handling
│       ├── security.py          # Security policy engine
│       ├── dbus_manager.py      # D-Bus connection management
│       ├── constants.py         # Security whitelists, constants
│       ├── tools/               # Individual tool implementations
│       │   ├── __init__.py
│       │   ├── base.py          # Base tool class
│       │   ├── common/          # Universal tools
│       │   │   ├── __init__.py
│       │   │   ├── list_services.py
│       │   │   ├── introspect.py
│       │   │   └── call_method.py
│       │   ├── workstation/     # Desktop-specific tools
│       │   │   ├── __init__.py
│       │   │   ├── notify.py
│       │   │   ├── clipboard.py
│       │   │   ├── screenshot.py
│       │   │   └── media_control.py
│       │   └── system/          # Server/system tools
│       │       ├── __init__.py
│       │       ├── systemd_status.py
│       │       ├── journal_query.py
│       │       └── network_status.py
│       └── services/            # D-Bus service exposure
│           ├── __init__.py
│           └── mcp_service.py   # org.mcp.DBusServer implementation
│
├── systemd/                     # SystemD unit files
│   ├── user/
│   │   ├── dbus-mcp-server.service
│   │   └── dbus-mcp-server.socket
│   └── system/
│       └── dbus-mcp-system.service
│
├── config/                      # Configuration files
│   ├── default.yaml             # Default configuration
│   ├── workstation.yaml         # Workstation-specific defaults
│   └── server.yaml              # Server-specific defaults
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/                    # Unit tests
│   │   ├── test_security.py
│   │   ├── test_tools.py
│   │   └── test_dbus_manager.py
│   ├── integration/             # Integration tests
│   │   ├── test_mcp_server.py
│   │   └── test_systemd.py
│   └── mocks/                   # Mock D-Bus services
│       └── mock_services.py
│
├── scripts/                     # Development/deployment scripts
│   ├── install-systemd.sh       # Install systemd units
│   ├── test-dbus.py             # D-Bus testing utility
│   └── generate-policy.py       # Generate PolicyKit policies
│
├── docs/                        # Additional documentation
│   ├── API.md                   # Tool API documentation
│   ├── DEPLOYMENT.md            # Deployment guide
│   └── CONTRIBUTING.md          # Contribution guidelines
│
├── examples/                    # Usage examples
│   ├── basic_usage.py
│   ├── custom_tool.py
│   └── fleet_management.py
│
├── .github/                     # GitHub specific
│   └── workflows/
│       ├── test.yml
│       └── release.yml
│
├── pyproject.toml               # Project metadata and dependencies
├── README.md                    # Project overview
├── LICENSE                      # License file
└── Makefile                     # Development tasks
```

## Key Modules Explained

### Core Components

1. **server.py**: Main MCP server that:
   - Initializes MCP protocol handler
   - Loads and registers tools based on context
   - Handles client connections
   - Manages lifecycle

2. **dbus_manager.py**: Manages D-Bus connections:
   - Lazy connection to session/system buses
   - Connection pooling and reuse
   - Error handling and reconnection
   - Introspection caching

3. **security.py**: Enforces security policies:
   - Operation whitelisting
   - Rate limiting implementation
   - Privilege checking
   - Audit logging

4. **config.py**: Configuration management:
   - Loads from YAML files
   - Environment variable overrides
   - Runtime configuration updates
   - Validation with Pydantic

### Tool Organization

Tools are organized by system role:

- **common/**: Tools available in all contexts
- **workstation/**: Desktop-specific tools requiring GUI
- **system/**: System management tools

Each tool inherits from `base.Tool` which provides:
- Automatic registration
- Security policy checking
- Error handling
- Logging

### Service Layer

The MCP server exposes its own D-Bus service for monitoring:
- Status queries
- Statistics collection
- Configuration reload
- Security event signals

## Development Workflow

```bash
# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Code formatting
black src/ tests/
ruff check src/ tests/

# Run locally
python -m dbus_mcp.server --config config/workstation.yaml

# Install systemd service (user)
./scripts/install-systemd.sh --user

# Start via systemd
systemctl --user start dbus-mcp-server
```

## Configuration Hierarchy

1. Built-in defaults
2. System configuration (`/etc/dbus-mcp/config.yaml`)
3. User configuration (`~/.config/dbus-mcp/config.yaml`)
4. Environment variables (`DBUS_MCP_*`)
5. Command-line arguments

## Testing Strategy

- **Unit tests**: Mock D-Bus connections, test individual components
- **Integration tests**: Use real D-Bus with test services
- **System tests**: Full systemd integration testing
- **Security tests**: Verify all security policies

This structure provides clear separation of concerns while maintaining flexibility for both workstation and server deployments.