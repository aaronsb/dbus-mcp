#!/usr/bin/env python3
"""
D-Bus MCP Server Main Entry Point

This module provides the command-line interface for running the D-Bus MCP server.
It supports multiple transport modes and safety levels for different use cases.
"""

import argparse
import logging
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from dbus_mcp.server import DBusMCPServer, ServerConfig
from dbus_mcp.security import SecurityPolicy
from dbus_mcp.system_requirements import check_and_warn
from dbus_mcp.profiles.detector import ProfileDetector
from dbus_mcp.profiles.registry import load_profile, PROFILE_REGISTRY


def show_detection_results():
    """Show system profile detection results."""
    profile_name = ProfileDetector.detect()
    profile = load_profile(profile_name)
    
    print("System Profile Detection Results")
    print("================================")
    print(f"Detected Profile: {profile.__class__.__name__}")
    print(f"Distribution: {profile.get_distro_info()['name']}")
    print(f"Version: {profile.get_distro_info()['version']}")
    print(f"Desktop Environment: {profile.get_desktop_info()['name']}")
    print(f"Session Type: {profile.get_desktop_info()['session_type']}")
    print()
    
    # Try to get package info
    print("Common Applications:")
    for app, pkg in [
        ("Kate", "kate"),
        ("Firefox", "firefox"),
        ("LibreOffice Writer", "libreoffice-writer"),
        ("VS Code", "code"),
    ]:
        info = profile.get_package_info(pkg)
        if info['installed']:
            print(f"  {app}: {info['version']}")
        else:
            print(f"  {app}: Not installed")


def main():
    """Main entry point for D-Bus MCP server."""
    parser = argparse.ArgumentParser(
        prog="dbus-mcp",
        description="D-Bus MCP Server - Bridge AI assistants to Linux systems"
    )
    
    # Basic options
    parser.add_argument(
        "--name", 
        default="dbus-mcp",
        help="Server name (default: dbus-mcp)"
    )
    parser.add_argument(
        "--version",
        default="0.1.0",
        help="Server version (default: 0.1.0)"
    )
    
    # Transport mode
    parser.add_argument(
        "--mode",
        choices=["stdio", "socket"],
        default="stdio",
        help="Transport mode (default: stdio)"
    )
    parser.add_argument(
        "--socket-path",
        help="Unix socket path (required for socket mode)"
    )
    
    # Safety level
    parser.add_argument(
        "--safety-level",
        choices=["high", "medium", "low"],
        default="high",
        help="Safety level: high (read-only), medium (safe writes), low (admin) (default: high)"
    )
    
    # Debug options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--log-file",
        help="Log to file instead of stderr"
    )
    parser.add_argument(
        "--expose-internal-errors",
        action="store_true",
        help="Expose internal error details (development only)"
    )
    
    # Special commands
    parser.add_argument(
        "--check-requirements",
        action="store_true",
        help="Check system requirements and exit"
    )
    parser.add_argument(
        "--detect",
        action="store_true",
        help="Show system profile detection results and exit"
    )
    parser.add_argument(
        "--print-version",
        action="store_true",
        help="Print version and exit"
    )
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.print_version:
        print("dbus-mcp version 0.1.0")
        sys.exit(0)
    
    if args.check_requirements:
        check_and_warn()
        sys.exit(0)
    
    if args.detect:
        show_detection_results()
        sys.exit(0)
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if args.log_file:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            filename=args.log_file,
            filemode='a'
        )
    else:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            stream=sys.stderr
        )
    
    logger = logging.getLogger(__name__)
    
    # Safety level is just a string
    safety_level = args.safety_level
    
    # Detect system profile
    profile = load_profile()  # Auto-detects if no name provided
    
    # Create server config
    config = ServerConfig(
        name=args.name,
        version=args.version,
        safety_level=args.safety_level,
        expose_internal_errors=args.expose_internal_errors
    )
    
    logger.info(f"Starting D-Bus MCP Server v{config.version}")
    logger.info(f"Safety level: {config.safety_level}")
    logger.info(f"Transport mode: {args.mode}")
    logger.info(f"System profile: {profile.name}")
    
    # Create the MCP server with dependencies
    mcp_server = DBusMCPServer(profile, config)
    
    # Register all tools based on profile and security
    from dbus_mcp.tools.registry import register_core_tools
    register_core_tools(
        mcp_server,
        profile,
        mcp_server.security,
        mcp_server.dbus_manager,
        mcp_server.file_manager
    )
    
    # Optionally publish on D-Bus for discovery
    if args.mode == 'stdio':
        mcp_server.publish_on_dbus()
    
    # Run based on transport mode
    if args.mode == 'stdio':
        import anyio
        from mcp.server.stdio import stdio_server
        
        async def run():
            async with stdio_server() as (read_stream, write_stream):
                await mcp_server.server.run(
                    read_stream,
                    write_stream,
                    mcp_server.server.create_initialization_options()
                )
        
        anyio.run(run)
    else:
        raise NotImplementedError(f"Mode {args.mode} not yet implemented")
    
    return 0


if __name__ == '__main__':
    main()