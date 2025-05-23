#!/bin/bash
# D-Bus MCP Server Uninstallation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths (must match install.sh)
PREFIX="${PREFIX:-/usr/local}"
BINDIR="${PREFIX}/bin"
LIBDIR="${PREFIX}/lib/dbus-mcp"
SYSCONFDIR="${SYSCONFDIR:-/etc}"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
SYSTEMD_SYSTEM_DIR="/etc/systemd/system"

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

confirm() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    read -p "$prompt" response
    response=${response:-$default}
    
    [[ "$response" =~ ^[Yy]$ ]]
}

remove_systemd_user() {
    print_header "Removing systemd user services"
    
    # Stop and disable services
    if systemctl --user is-active dbus-mcp.socket &>/dev/null; then
        systemctl --user stop dbus-mcp.socket
        print_success "Stopped dbus-mcp.socket"
    fi
    
    if systemctl --user is-active dbus-mcp.service &>/dev/null; then
        systemctl --user stop dbus-mcp.service
        print_success "Stopped dbus-mcp.service"
    fi
    
    if systemctl --user is-enabled dbus-mcp.socket &>/dev/null; then
        systemctl --user disable dbus-mcp.socket
        print_success "Disabled dbus-mcp.socket"
    fi
    
    # Remove unit files
    rm -f "$SYSTEMD_USER_DIR/dbus-mcp.service"
    rm -f "$SYSTEMD_USER_DIR/dbus-mcp.socket"
    
    # Reload systemd
    systemctl --user daemon-reload
    print_success "Removed systemd user units"
}

remove_systemd_system() {
    print_header "Removing systemd system services"
    
    # Check if system service exists
    if [ -f "$SYSTEMD_SYSTEM_DIR/dbus-mcp@.service" ]; then
        sudo systemctl stop 'dbus-mcp@*.service' 2>/dev/null || true
        sudo systemctl disable 'dbus-mcp@*.service' 2>/dev/null || true
        
        sudo rm -f "$SYSTEMD_SYSTEM_DIR/dbus-mcp@.service"
        sudo systemctl daemon-reload
        print_success "Removed systemd system units"
    else
        print_warning "No system units found"
    fi
}

remove_production() {
    print_header "Removing production installation"
    
    # Remove binaries
    if [ -f "$BINDIR/dbus-mcp" ]; then
        sudo rm -f "$BINDIR/dbus-mcp"
        print_success "Removed dbus-mcp executable"
    fi
    
    if [ -f "$BINDIR/dbus-mcp-socket-wrapper" ]; then
        sudo rm -f "$BINDIR/dbus-mcp-socket-wrapper"
        print_success "Removed socket wrapper"
    fi
    
    # Remove lib directory
    if [ -d "$LIBDIR" ]; then
        sudo rm -rf "$LIBDIR"
        print_success "Removed library directory"
    fi
    
    # Handle config directory
    if [ -d "$SYSCONFDIR/dbus-mcp" ]; then
        if confirm "Remove configuration directory $SYSCONFDIR/dbus-mcp?"; then
            sudo rm -rf "$SYSCONFDIR/dbus-mcp"
            print_success "Removed configuration"
        else
            print_warning "Preserved configuration directory"
        fi
    fi
}

remove_development() {
    print_header "Cleaning development environment"
    
    # Remove venv
    if [ -d "venv" ] && confirm "Remove Python virtual environment?"; then
        rm -rf venv
        print_success "Removed virtual environment"
    fi
    
    # Remove dev launcher
    if [ -f "dbus-mcp-dev" ]; then
        rm -f dbus-mcp-dev
        print_success "Removed development launcher"
    fi
    
    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    print_success "Cleaned Python cache"
}

clean_user_data() {
    print_header "Cleaning user data"
    
    # Clean runtime data
    if [ -d "/tmp/dbus-mcp" ]; then
        rm -rf /tmp/dbus-mcp
        print_success "Removed temporary files"
    fi
    
    # Clean any socket files
    if [ -S "$XDG_RUNTIME_DIR/dbus-mcp.sock" ]; then
        rm -f "$XDG_RUNTIME_DIR/dbus-mcp.sock"
        print_success "Removed socket file"
    fi
}

main() {
    print_header "D-Bus MCP Server Uninstaller"
    
    # Parse arguments
    local CLEAN_ALL=0
    local CLEAN_DEV=0
    local CLEAN_PROD=0
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                CLEAN_ALL=1
                shift
                ;;
            --dev)
                CLEAN_DEV=1
                shift
                ;;
            --prod)
                CLEAN_PROD=1
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--all|--dev|--prod]"
                echo "  --all   Remove everything (development and production)"
                echo "  --dev   Remove development environment only"
                echo "  --prod  Remove production installation only"
                echo "  (default: interactive mode)"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Interactive mode if no options
    if [ $CLEAN_ALL -eq 0 ] && [ $CLEAN_DEV -eq 0 ] && [ $CLEAN_PROD -eq 0 ]; then
        echo "What would you like to remove?"
        echo "1) Everything (development and production)"
        echo "2) Development environment only"
        echo "3) Production installation only"
        echo "4) Cancel"
        
        read -p "Choice [1-4]: " choice
        
        case $choice in
            1) CLEAN_ALL=1 ;;
            2) CLEAN_DEV=1 ;;
            3) CLEAN_PROD=1 ;;
            *) 
                echo "Cancelled."
                exit 0
                ;;
        esac
    fi
    
    # Execute removal
    if [ $CLEAN_ALL -eq 1 ] || [ $CLEAN_PROD -eq 1 ]; then
        if command -v systemctl &>/dev/null; then
            remove_systemd_user
            remove_systemd_system
        fi
        remove_production
    fi
    
    if [ $CLEAN_ALL -eq 1 ] || [ $CLEAN_DEV -eq 1 ]; then
        remove_development
    fi
    
    # Always clean user data
    clean_user_data
    
    print_header "Uninstallation complete!"
}

# Run main
main "$@"