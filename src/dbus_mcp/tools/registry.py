"""
Tool registry for D-Bus MCP server using low-level MCP API.

This module handles registration of all available tools based on
the system profile and security settings.
"""

import logging
from typing import Dict, Any, List
import json

from mcp import Tool

from ..profiles.base import SystemProfile
from ..security import SecurityPolicy
from ..dbus_manager import DBusManager
from ..file_manager import FilePipeManager


logger = logging.getLogger(__name__)


def create_help_tool(server, profile: SystemProfile, security: SecurityPolicy) -> tuple[Tool, callable]:
    """Create the help tool."""
    
    async def help_handler(arguments: Dict[str, Any]) -> str:
        """Show available D-Bus MCP capabilities and tools."""
        lines = [
            "D-Bus MCP Server - Available Capabilities",
            f"Profile: {profile.name} - {profile.description}",
            f"Safety Level: {security.safety_level_emoji} {security.safety_level.upper()}",
            "",
            "Core Tools:",
            "- show_help: Show this help message",
            "- notify: Send desktop notification",
            "- status: Get system status overview",
            "- discover: Explore available tools by category",
            "- list_services: List all D-Bus services",
            "- introspect: Explore service interfaces and methods",
            "- call_method: Call arbitrary D-Bus methods",
            ""
        ]
        
        # Add safety level info
        if security.safety_level == "medium":
            lines.extend([
                f"Current Safety Level - {security.safety_level_emoji} Productivity operations (recommended for development):",
                "",
                "  ✏️ Send text to editors (Kate, KWrite)",
                "  📁 Open files/folders in Dolphin",
                "  🌐 Open URLs in browser",
                "  🪟 Focus and activate windows",
                "  📸 Take screenshots (with user consent)",
                "  ⌨️ Simulate keyboard input to active window",
                ""
            ])
        
        # Add profile-specific capabilities
        capabilities = profile.get_available_tools()
        if capabilities:
            lines.append("Profile-Specific Tools:")
            for category, tools in capabilities.items():
                if tools:
                    lines.append(f"  - {category}")
        
        lines.append(f"\nTo change safety level, restart with: --safety-level {security.safety_level}")
        
        return "\n".join(lines)
    
    tool = Tool(
        name="show_help",
        description="Show available D-Bus MCP capabilities and tools",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
    
    return tool, help_handler


def create_notify_tool(profile: SystemProfile) -> tuple[Tool, callable]:
    """Create the notify tool."""
    
    async def notify_handler(arguments: Dict[str, Any]) -> str:
        """Send a desktop notification."""
        title = arguments.get("title", "")
        message = arguments.get("message", "")
        urgency = arguments.get("urgency", "normal")
        
        try:
            from ..dbus_manager import DBusManager
            
            # Get notification config from profile
            config = profile.get_notification_config()
            
            # Connect to D-Bus
            dbus = DBusManager()
            notifier = dbus.get_service(
                'session',
                config['service'],
                config.get('path', '/org/freedesktop/Notifications')
            )
            
            # Convert urgency to int
            urgency_map = {'low': 0, 'normal': 1, 'critical': 2}
            urgency_int = urgency_map.get(urgency, 1)
            
            # Send notification
            from gi.repository import GLib
            hints = {'urgency': GLib.Variant('y', urgency_int)}
            
            notification_id = notifier.Notify(
                'dbus-mcp',      # app_name
                0,               # replaces_id
                '',              # icon
                title,           # summary
                message,         # body
                [],              # actions
                hints,           # hints with GLib.Variant
                5000             # timeout (ms)
            )
            
            return f"Notification sent (ID: {notification_id})"
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return f"Failed to send notification: {str(e)}"
    
    tool = Tool(
        name="notify",
        description="Send a desktop notification to the user",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Notification title"
                },
                "message": {
                    "type": "string",
                    "description": "Notification message body"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "normal", "critical"],
                    "default": "normal",
                    "description": "Urgency level"
                }
            },
            "required": ["title", "message"]
        }
    )
    
    return tool, notify_handler


def create_list_services_tool(dbus_manager: DBusManager) -> tuple[Tool, callable]:
    """Create the list_services tool."""
    
    async def list_services_handler(arguments: Dict[str, Any]) -> str:
        """List available D-Bus services."""
        bus = arguments.get("bus", "session")
        
        try:
            # Get the appropriate bus
            if bus == "session":
                if not dbus_manager.session_bus:
                    return "Session bus not available"
                bus_obj = dbus_manager.session_bus
            elif bus == "system":
                if not dbus_manager.system_bus:
                    return "System bus not available"
                bus_obj = dbus_manager.system_bus
            else:
                return f"Invalid bus type: {bus}. Use 'session' or 'system'"
            
            # Get service list
            dbus_service = bus_obj.get('org.freedesktop.DBus', '/org/freedesktop/DBus')
            services = dbus_service.ListNames()
            
            # Sort and categorize
            well_known = sorted([s for s in services if not s.startswith(':')])
            unique = [s for s in services if s.startswith(':')]
            
            lines = [f"{bus.capitalize()} Bus Services ({len(well_known)} well-known, {len(unique)} unique):"]
            lines.append("\nWell-known services:")
            for service in well_known:
                lines.append(f"  {service}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return f"Failed to list services: {str(e)}"
    
    tool = Tool(
        name="list_services",
        description="List all available D-Bus services",
        inputSchema={
            "type": "object",
            "properties": {
                "bus": {
                    "type": "string",
                    "enum": ["session", "system"],
                    "default": "session",
                    "description": "D-Bus type to query"
                }
            }
        }
    )
    
    return tool, list_services_handler


def register_core_tools(
    server,
    profile: SystemProfile,
    security: SecurityPolicy,
    dbus_manager: DBusManager,
    file_manager: FilePipeManager
):
    """
    Register core tools available to all profiles.
    
    Args:
        server: The MCP server instance
        profile: System profile for environment-specific features
        security: Security policy for access control
        dbus_manager: D-Bus connection manager
        file_manager: File management for screenshots etc
    """
    logger.info("Registering core tools...")
    
    # 1. Help tool
    tool, handler = create_help_tool(server, profile, security)
    server.add_tool(tool, handler)
    
    # 2. Notify tool
    tool, handler = create_notify_tool(profile)
    server.add_tool(tool, handler)
    
    # 3. List services tool
    tool, handler = create_list_services_tool(dbus_manager)
    server.add_tool(tool, handler)
    
    # TODO: Add more core tools (status, discover, introspect, call_method)
    
    # Register screenshot tools if on desktop
    if profile.has_display():
        from .common.screenshot import create_screenshot_tools
        screenshot_tools = create_screenshot_tools(profile, security, dbus_manager, file_manager)
        for tool, handler in screenshot_tools:
            server.add_tool(tool, handler)
        logger.info("Registered screenshot tools")
    
    # Register MCP discovery tools
    from .system.mcp_discovery import create_mcp_discovery_tools_lowlevel
    mcp_tools = create_mcp_discovery_tools_lowlevel(dbus_manager)
    for tool, handler in mcp_tools:
        server.add_tool(tool, handler)
    logger.info("Registered MCP discovery tools")
    
    logger.info(f"Registered core tools for profile: {profile.name}")