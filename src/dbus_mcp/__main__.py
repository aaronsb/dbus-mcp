#!/usr/bin/env python3
"""
D-Bus MCP Server - Main entry point

This module provides the command-line interface for running the D-Bus MCP server.
It can run in different modes:
- stdio: Default mode for AI clients (Claude Desktop, etc.)
- socket: SystemD socket activation
- http: HTTP/SSE for remote access
"""

import sys
import argparse
import logging
import asyncio
from typing import Optional

from mcp.server import FastMCP

from .server import DBusMCPServer
from .profiles import load_profile, ProfileDetector
from .tools.registry import register_core_tools
from .system_requirements import check_and_warn
from .systemd_server import setup_systemd_stdio, restore_stdio


def setup_logging(level: str = "INFO"):
    """Configure logging based on verbosity level."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="D-Bus MCP Server - Bridge AI assistants to Linux systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with stdio (default for AI clients)
  dbus-mcp-server
  
  # Force a specific profile
  dbus-mcp-server --profile kde-arch
  
  # Show detected system information
  dbus-mcp-server --detect
  
  # Run with debug logging
  dbus-mcp-server --log-level debug
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['stdio', 'socket', 'http'],
        default='stdio',
        help='Server mode (default: stdio)'
    )
    
    parser.add_argument(
        '--profile',
        type=str,
        help='Force specific system profile (e.g., kde-arch, gnome-ubuntu)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='Logging verbosity (default: info)'
    )
    
    parser.add_argument(
        '--safety-level',
        choices=['high', 'medium', 'low'],
        default='high',
        help='Security safety level (default: high). Medium allows text editor and file manager operations.'
    )
    
    parser.add_argument(
        '--detect',
        action='store_true',
        help='Detect and display system information, then exit'
    )
    
    parser.add_argument(
        '--check-requirements',
        action='store_true',
        help='Check system package requirements and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    # Mode-specific options
    parser.add_argument(
        '--socket-path',
        type=str,
        help='Socket path for socket mode'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host for HTTP mode (default: localhost)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port for HTTP mode (default: 8080)'
    )
    
    return parser


def detect_and_display():
    """Detect system information and display it."""
    info = ProfileDetector.get_environment_info()
    
    print("D-Bus MCP Server - System Detection")
    print("=" * 40)
    print(f"Distribution:    {info['distro'] or 'Unknown'}")
    print(f"Desktop:         {info['desktop'] or 'None'}")
    print(f"Display Server:  {info['display_server']}")
    print(f"Session Type:    {info['session_type']}")
    print(f"Is Server:       {'Yes' if info['is_server'] else 'No'}")
    print(f"")
    print(f"Detected Profile: {info['detected_profile']}")
    print(f"Compatible:       {', '.join(info['compatible_profiles'])}")
    print(f"")
    print("Environment Variables:")
    for key, value in info['env_vars'].items():
        if value:
            print(f"  {key}: {value}")


async def run_stdio_server(server: FastMCP, profile):
    """Run the MCP server with stdio transport."""
    # Check if we need to set up systemd socket wrapping
    is_systemd = setup_systemd_stdio()
    
    if is_systemd:
        logging.info(f"Starting D-Bus MCP Server (systemd socket mode)")
    else:
        logging.info(f"Starting D-Bus MCP Server (stdio mode)")
    
    logging.info(f"Using profile: {profile.name}")
    
    try:
        # Run the stdio server using FastMCP's built-in method
        await server.run_stdio_async()
    finally:
        # Restore stdio if we modified it
        if is_systemd:
            restore_stdio()


async def run_socket_server(server: FastMCP, profile, socket_path: Optional[str]):
    """Run the MCP server with socket transport (SystemD activation)."""
    # TODO: Implement socket mode
    raise NotImplementedError("Socket mode not yet implemented")


async def run_http_server(server: FastMCP, profile, host: str, port: int):
    """Run the MCP server with HTTP/SSE transport."""
    # TODO: Implement HTTP mode using FastMCP's SSE support
    # await server.run_sse_async(host=host, port=port)
    raise NotImplementedError("HTTP mode not yet implemented")


async def async_main(args):
    """Async main function."""
    # Check system requirements
    check_and_warn()
    
    # Load system profile
    profile = load_profile(args.profile)
    logging.info(f"Loaded profile: {profile.name} - {profile.description}")
    
    # Validate environment
    issues = profile.validate_environment()
    if issues:
        logging.warning("Profile validation issues:")
        for issue in issues:
            logging.warning(f"  - {issue}")
    
    # Create server config with safety level
    from .server import ServerConfig
    config = ServerConfig(safety_level=args.safety_level)
    
    # Create MCP server
    mcp_server = DBusMCPServer(profile=profile, config=config)
    server = mcp_server.server
    
    # Register tools based on profile, passing server components
    register_core_tools(
        server, 
        profile, 
        mcp_server.security,
        mcp_server.dbus_manager,
        mcp_server.file_manager
    )
    
    # Run appropriate mode
    if args.mode == 'stdio':
        await run_stdio_server(server, profile)
    elif args.mode == 'socket':
        await run_socket_server(server, profile, args.socket_path)
    elif args.mode == 'http':
        await run_http_server(server, profile, args.host, args.port)


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Handle detection mode
    if args.detect:
        detect_and_display()
        return 0
    
    # Handle requirements check mode
    if args.check_requirements:
        from .system_requirements import print_requirements_report
        success = print_requirements_report()
        return 0 if success else 1
    
    try:
        # Run the async main
        asyncio.run(async_main(args))
        return 0
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        return 0
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())