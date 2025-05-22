"""
Tool Registry

Registers MCP tools based on system profile and configuration.
"""

import logging
from typing import Dict, Any

from mcp import Server
from mcp.server import Tool
from mcp.types import TextContent

from ..profiles.base import SystemProfile

logger = logging.getLogger(__name__)


def register_core_tools(server: Server, profile: SystemProfile):
    """
    Register the core set of tools that are always available.
    
    These are the minimal tools for progressive disclosure.
    """
    
    # 1. Help tool - always available
    @server.tool()
    async def help() -> str:
        """Get help about available D-Bus capabilities and tools."""
        available = profile.get_available_tools()
        
        help_text = [
            "D-Bus MCP Server - Available Capabilities",
            f"Profile: {profile.name} - {profile.description}",
            "",
            "Core Tools:",
            "- help: Show this help message",
            "- notify: Send desktop notification",
            "- status: Get system status overview",
            "- discover: Explore available tools by category",
            "",
            "Available Categories:"
        ]
        
        for category, enabled in available.items():
            status = "✓" if enabled else "✗"
            help_text.append(f"  {status} {category}")
        
        if profile.get_profile_specific_tools():
            help_text.extend([
                "",
                "Profile-Specific Tools:",
            ])
            for tool in profile.get_profile_specific_tools():
                help_text.append(f"  - {tool}")
        
        return "\n".join(help_text)
    
    # 2. Notify tool - basic notification
    @server.tool()
    async def notify(title: str, message: str, urgency: str = "normal") -> str:
        """
        Send a desktop notification to the user.
        
        Args:
            title: Notification title
            message: Notification message body
            urgency: Urgency level (low, normal, critical)
        """
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
            notification_id = notifier.Notify(
                'dbus-mcp',      # app_name
                0,               # replaces_id
                '',              # icon
                title,           # summary
                message,         # body
                [],              # actions
                {'urgency': urgency_int},  # hints
                5000             # timeout (ms)
            )
            
            return f"Notification sent (ID: {notification_id})"
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return f"Failed to send notification: {str(e)}"
    
    # 3. Status tool - system overview
    @server.tool()
    async def status() -> str:
        """Get a quick system status overview including battery, network, and load."""
        try:
            from ..dbus_manager import DBusManager
            
            dbus = DBusManager()
            status_info = []
            
            # Try to get battery status
            if dbus.system_bus:
                try:
                    upower = dbus.get_service(
                        'system',
                        'org.freedesktop.UPower',
                        '/org/freedesktop/UPower/devices/DisplayDevice'
                    )
                    battery = upower.Get('org.freedesktop.UPower.Device', 'Percentage')
                    state = upower.Get('org.freedesktop.UPower.Device', 'State')
                    state_map = {1: 'Unknown', 2: 'Charging', 4: 'Discharging', 5: 'Empty', 6: 'Full'}
                    status_info.append(f"Battery: {battery}% ({state_map.get(state, 'Unknown')})")
                except:
                    pass
            
            # Try to get network status
            if dbus.system_bus:
                try:
                    nm = dbus.get_service(
                        'system',
                        'org.freedesktop.NetworkManager',
                        '/org/freedesktop/NetworkManager'
                    )
                    connectivity = nm.Get('org.freedesktop.NetworkManager', 'Connectivity')
                    conn_map = {0: 'Unknown', 1: 'None', 2: 'Portal', 3: 'Limited', 4: 'Full'}
                    status_info.append(f"Network: {conn_map.get(connectivity, 'Unknown')}")
                except:
                    pass
            
            # Get system info from profile
            env = profile.detect_environment()
            status_info.extend([
                f"Profile: {env['profile']}",
                f"Desktop: {env.get('desktop', 'None')}",
                f"Display: {env.get('display_server', 'None')}"
            ])
            
            return "\n".join(status_info) if status_info else "Unable to get system status"
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return f"Failed to get status: {str(e)}"
    
    # 4. Discover tool - explore available tools
    @server.tool()
    async def discover(category: str = None) -> str:
        """
        Discover available D-Bus tools and capabilities.
        
        Args:
            category: Optional category to explore (desktop, media, system, etc.)
        """
        if category:
            # TODO: Return tools for specific category
            return f"Tools for category '{category}' will be implemented based on profile"
        else:
            # Return available categories
            available = profile.get_available_tools()
            lines = ["Available categories (use discover(category='name') for details):"]
            
            for cat, enabled in available.items():
                if enabled:
                    lines.append(f"  - {cat}")
            
            return "\n".join(lines)
    
    # Register profile-specific clipboard tools if available
    if profile.get_available_tools().get('clipboard', False):
        register_clipboard_tools(server, profile)
    
    logger.info(f"Registered {len(server._tools)} core tools")


def register_clipboard_tools(server: Server, profile: SystemProfile):
    """Register clipboard tools based on profile configuration."""
    
    @server.tool()
    async def clipboard_read() -> str:
        """Read the current clipboard contents."""
        try:
            from ..dbus_manager import DBusManager
            
            # Get clipboard config from profile
            config = profile.get_clipboard_config()
            
            if config.get('adapter') == 'klipper':
                # KDE Klipper specific
                dbus = DBusManager()
                klipper = dbus.get_service(
                    'session',
                    config['service'],
                    config['path']
                )
                
                # Call the appropriate method
                method_name = config['methods']['read']
                contents = getattr(klipper, method_name)()
                
                return contents if contents else "(empty)"
            else:
                # Generic portal or other adapter
                return "Clipboard adapter not yet implemented"
                
        except Exception as e:
            logger.error(f"Failed to read clipboard: {e}")
            return f"Failed to read clipboard: {str(e)}"
    
    @server.tool()
    async def clipboard_write(text: str) -> str:
        """
        Write text to the clipboard.
        
        Args:
            text: Text to write to clipboard
        """
        try:
            from ..dbus_manager import DBusManager
            
            # Get clipboard config from profile
            config = profile.get_clipboard_config()
            
            if config.get('adapter') == 'klipper':
                # KDE Klipper specific
                dbus = DBusManager()
                klipper = dbus.get_service(
                    'session',
                    config['service'],
                    config['path']
                )
                
                # Call the appropriate method
                method_name = config['methods']['write']
                getattr(klipper, method_name)(text)
                
                return "Text written to clipboard"
            else:
                # Generic portal or other adapter
                return "Clipboard adapter not yet implemented"
                
        except Exception as e:
            logger.error(f"Failed to write clipboard: {e}")
            return f"Failed to write clipboard: {str(e)}"