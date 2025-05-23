#!/bin/bash
# D-Bus MCP Server Installation Script
# Supports both development (direct) and production (systemd) modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
PREFIX="${PREFIX:-/usr/local}"
BINDIR="${PREFIX}/bin"
LIBDIR="${PREFIX}/lib/dbus-mcp"
SYSCONFDIR="${SYSCONFDIR:-/etc}"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
SYSTEMD_SYSTEM_DIR="/etc/systemd/system"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_dependencies() {
    print_header "Checking dependencies"
    
    local deps_missing=0
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python 3 found: $(python3 --version)"
    else
        print_error "Python 3 not found"
        deps_missing=1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null || python3 -m pip --version &> /dev/null; then
        print_success "pip found"
    else
        print_error "pip not found"
        deps_missing=1
    fi
    
    # Check git (for development mode)
    if command -v git &> /dev/null; then
        print_success "git found"
    else
        print_warning "git not found (optional for development)"
    fi
    
    # Check systemd (for production mode)
    if command -v systemctl &> /dev/null; then
        print_success "systemd found"
    else
        print_warning "systemd not found (required for production mode)"
    fi
    
    if [ $deps_missing -eq 1 ]; then
        print_error "Missing required dependencies"
        exit 1
    fi
}

create_venv() {
    print_header "Setting up Python virtual environment"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Created virtual environment"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate and install
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel >/dev/null 2>&1
    pip install -e . >/dev/null 2>&1
    print_success "Installed dbus-mcp in development mode"
}

install_production() {
    print_header "Installing for production use"
    
    # Create directories
    sudo mkdir -p "$BINDIR" "$LIBDIR" "$SYSCONFDIR/dbus-mcp"
    
    # Build standalone executable using zipapp
    print_header "Building standalone executable"
    
    # Create a temporary build directory
    local BUILD_DIR=$(mktemp -d)
    trap "rm -rf $BUILD_DIR" EXIT
    
    # Install dependencies to build directory
    pip install --target="$BUILD_DIR" . >/dev/null 2>&1
    
    # Create __main__.py for zipapp
    cat > "$BUILD_DIR/__main__.py" << 'EOF'
#!/usr/bin/env python3
import sys
from dbus_mcp.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    # Create zipapp
    python3 -m zipapp "$BUILD_DIR" \
        -p "/usr/bin/env python3" \
        -o "$BUILD_DIR/dbus-mcp" \
        -c
    
    # Install the executable
    sudo install -m 755 "$BUILD_DIR/dbus-mcp" "$BINDIR/dbus-mcp"
    print_success "Installed dbus-mcp executable to $BINDIR"
    
    # Install wrapper script
    sudo install -m 755 scripts/dbus-mcp-socket-wrapper.sh "$BINDIR/dbus-mcp-socket-wrapper"
    print_success "Installed socket wrapper"
    
    # Install config file
    if [ ! -f "$SYSCONFDIR/dbus-mcp/config" ]; then
        sudo install -m 644 config/dbus-mcp.conf.example "$SYSCONFDIR/dbus-mcp/config"
        print_success "Installed default configuration"
    else
        print_warning "Configuration already exists, not overwriting"
    fi
    
    # Update wrapper to use installed binary
    sudo sed -i "s|PYTHON_BIN=.*|PYTHON_BIN=\"$BINDIR/dbus-mcp\"|" "$BINDIR/dbus-mcp-socket-wrapper"
    sudo sed -i "s|MCP_MODULE=.*|# MCP_MODULE not needed for standalone|" "$BINDIR/dbus-mcp-socket-wrapper"
}

install_systemd_user() {
    print_header "Installing systemd user service"
    
    mkdir -p "$SYSTEMD_USER_DIR"
    
    # Install service files
    cp systemd/user/dbus-mcp.service "$SYSTEMD_USER_DIR/"
    cp systemd/user/dbus-mcp.socket "$SYSTEMD_USER_DIR/"
    
    # Update service to use installed wrapper
    sed -i "s|ExecStart=.*|ExecStart=$BINDIR/dbus-mcp-socket-wrapper|" \
        "$SYSTEMD_USER_DIR/dbus-mcp.service"
    
    print_success "Installed systemd user units"
    
    # Reload systemd
    systemctl --user daemon-reload
    print_success "Reloaded systemd configuration"
}

install_systemd_system() {
    print_header "Installing systemd system service (requires sudo)"
    
    # Install service files
    sudo cp systemd/system/dbus-mcp@.service "$SYSTEMD_SYSTEM_DIR/" 2>/dev/null || true
    
    if [ -f "$SYSTEMD_SYSTEM_DIR/dbus-mcp@.service" ]; then
        # Update service to use installed wrapper
        sudo sed -i "s|ExecStart=.*|ExecStart=$BINDIR/dbus-mcp-socket-wrapper|" \
            "$SYSTEMD_SYSTEM_DIR/dbus-mcp@.service"
        
        print_success "Installed systemd system template unit"
        sudo systemctl daemon-reload
    else
        print_warning "System service not installed (may require template creation)"
    fi
}

setup_development() {
    print_header "Setting up development environment"
    
    create_venv
    
    # Create convenience script
    cat > dbus-mcp-dev << EOF
#!/bin/bash
# Development mode launcher
cd "$SCRIPT_DIR"
source venv/bin/activate
python -m dbus_mcp "\$@"
EOF
    chmod +x dbus-mcp-dev
    
    print_success "Created development launcher: ./dbus-mcp-dev"
}

show_usage() {
    print_header "Installation complete!"
    
    echo ""
    echo "Development mode (direct stdio):"
    echo "  cd $SCRIPT_DIR"
    echo "  ./dbus-mcp-dev --safety-level medium"
    echo ""
    echo "Production mode (systemd socket):"
    echo "  # Start the socket"
    echo "  systemctl --user start dbus-mcp.socket"
    echo "  "
    echo "  # Enable on boot"
    echo "  systemctl --user enable dbus-mcp.socket"
    echo "  "
    echo "  # Check status"
    echo "  systemctl --user status dbus-mcp.socket"
    echo "  systemctl --user status dbus-mcp.service"
    echo ""
    echo "Configure safety level for production:"
    echo "  sudo editor $SYSCONFDIR/dbus-mcp/config"
    echo ""
    echo "Use with Claude/MCP clients:"
    echo "  Development: $SCRIPT_DIR/dbus-mcp-dev"
    echo "  Production:  socat UNIX-CONNECT:\$XDG_RUNTIME_DIR/dbus-mcp.sock STDIO"
}

# Main installation flow
main() {
    print_header "D-Bus MCP Server Installer"
    
    # Parse arguments
    local MODE="both"
    local SKIP_SYSTEMD=0
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev-only)
                MODE="dev"
                shift
                ;;
            --prod-only)
                MODE="prod"
                shift
                ;;
            --skip-systemd)
                SKIP_SYSTEMD=1
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--dev-only|--prod-only] [--skip-systemd]"
                echo "  --dev-only    Install development mode only"
                echo "  --prod-only   Install production mode only"
                echo "  --skip-systemd Skip systemd unit installation"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Check we're in the right directory
    if [ ! -f "pyproject.toml" ] || [ ! -d "src/dbus_mcp" ]; then
        print_error "Please run this script from the dbus-mcp project root"
        exit 1
    fi
    
    check_dependencies
    
    if [ "$MODE" = "dev" ] || [ "$MODE" = "both" ]; then
        setup_development
    fi
    
    if [ "$MODE" = "prod" ] || [ "$MODE" = "both" ]; then
        install_production
        
        if [ $SKIP_SYSTEMD -eq 0 ]; then
            install_systemd_user
            install_systemd_system
        fi
    fi
    
    show_usage
}

# Run main
main "$@"