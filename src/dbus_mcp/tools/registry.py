"""
Tool Registry

Registers MCP tools based on system profile and configuration.
"""

import logging
from typing import Dict, Any

from mcp.server import FastMCP
from mcp import Tool
from mcp.types import TextContent

from ..profiles.base import SystemProfile

logger = logging.getLogger(__name__)


def register_core_tools(server: FastMCP, profile: SystemProfile):
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
            "- list_services: List all D-Bus services",
            "- introspect: Explore service interfaces and methods",
            "- call_method: Call arbitrary D-Bus methods",
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
    
    # 5. List services tool - enumerate D-Bus services
    @server.tool()
    async def list_services(bus: str = "session") -> str:
        """
        List all available D-Bus services on the specified bus.
        
        Args:
            bus: Which bus to list services from ('session' or 'system')
        """
        try:
            from ..dbus_manager import DBusManager
            
            dbus = DBusManager()
            
            # Get the appropriate bus
            if bus == "session":
                if not dbus.session_bus:
                    return "Session bus not available"
                bus_obj = dbus.session_bus
            elif bus == "system":
                if not dbus.system_bus:
                    return "System bus not available"
                bus_obj = dbus.system_bus
            else:
                return f"Invalid bus type: {bus}. Use 'session' or 'system'"
            
            # Get service list from org.freedesktop.DBus
            dbus_service = bus_obj.get('org.freedesktop.DBus', '/org/freedesktop/DBus')
            services = dbus_service.ListNames()
            
            # Sort and categorize services
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
    
    # 6. Introspect tool - explore service interfaces
    @server.tool()
    async def introspect(service: str, path: str = "/", bus: str = "session") -> str:
        """
        Introspect a D-Bus service to discover its interfaces and methods.
        
        Args:
            service: The D-Bus service name (e.g., 'org.kde.klipper')
            path: Object path (default: '/')
            bus: Which bus to use ('session' or 'system')
        """
        try:
            from ..dbus_manager import DBusManager
            import xml.etree.ElementTree as ET
            
            dbus = DBusManager()
            
            # Get the appropriate bus
            if bus == "session":
                if not dbus.session_bus:
                    return "Session bus not available"
                bus_obj = dbus.session_bus
            elif bus == "system":
                if not dbus.system_bus:
                    return "System bus not available"
                bus_obj = dbus.system_bus
            else:
                return f"Invalid bus type: {bus}. Use 'session' or 'system'"
            
            # Get the service object
            try:
                service_obj = bus_obj.get(service, path)
            except Exception as e:
                return f"Failed to connect to {service} at {path}: {str(e)}"
            
            # Call Introspect method
            introspect_xml = service_obj.Introspect()
            
            # Parse XML and extract useful information
            root = ET.fromstring(introspect_xml)
            
            lines = [f"Service: {service}"]
            lines.append(f"Path: {path}")
            lines.append("")
            
            # List child nodes
            nodes = root.findall('node')
            if nodes:
                lines.append("Child nodes:")
                for node in nodes:
                    name = node.get('name')
                    if name:
                        lines.append(f"  {path.rstrip('/')}/{name}")
                lines.append("")
            
            # List interfaces
            interfaces = root.findall('interface')
            for interface in interfaces:
                iface_name = interface.get('name')
                if iface_name.startswith('org.freedesktop.DBus.'):
                    continue  # Skip standard interfaces
                
                lines.append(f"Interface: {iface_name}")
                
                # Methods
                methods = interface.findall('method')
                if methods:
                    lines.append("  Methods:")
                    for method in methods:
                        method_name = method.get('name')
                        # Get arguments
                        args_in = []
                        args_out = []
                        for arg in method.findall('arg'):
                            arg_type = arg.get('type')
                            arg_name = arg.get('name', '')
                            if arg.get('direction') == 'out':
                                args_out.append(f"{arg_name}:{arg_type}" if arg_name else arg_type)
                            else:
                                args_in.append(f"{arg_name}:{arg_type}" if arg_name else arg_type)
                        
                        args_str = f"({', '.join(args_in)})"
                        if args_out:
                            args_str += f" → ({', '.join(args_out)})"
                        
                        lines.append(f"    - {method_name}{args_str}")
                
                # Properties
                properties = interface.findall('property')
                if properties:
                    lines.append("  Properties:")
                    for prop in properties:
                        prop_name = prop.get('name')
                        prop_type = prop.get('type')
                        prop_access = prop.get('access', 'read')
                        lines.append(f"    - {prop_name} ({prop_type}) [{prop_access}]")
                
                # Signals
                signals = interface.findall('signal')
                if signals:
                    lines.append("  Signals:")
                    for signal in signals:
                        signal_name = signal.get('name')
                        lines.append(f"    - {signal_name}")
                
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Failed to introspect service: {e}")
            return f"Failed to introspect: {str(e)}"
    
    # 7. Call method tool - invoke D-Bus methods
    @server.tool()
    async def call_method(
        service: str,
        path: str,
        interface: str,
        method: str,
        args: list = None,
        bus: str = "session"
    ) -> str:
        """
        Call a D-Bus method with the specified arguments.
        
        Args:
            service: The D-Bus service name
            path: Object path
            interface: Interface name
            method: Method name
            args: List of arguments to pass to the method
            bus: Which bus to use ('session' or 'system')
        """
        try:
            from ..dbus_manager import DBusManager
            from ..security import SecurityPolicy
            
            # Security check
            security = SecurityPolicy()
            
            # Check if this method call is allowed
            if not security.is_method_allowed(service, interface, method):
                return f"Security: Method {interface}.{method} is not allowed"
            
            dbus = DBusManager()
            
            # Get the appropriate bus
            if bus == "session":
                if not dbus.session_bus:
                    return "Session bus not available"
                bus_obj = dbus.session_bus
            elif bus == "system":
                if not dbus.system_bus:
                    return "System bus not available"
                bus_obj = dbus.system_bus
            else:
                return f"Invalid bus type: {bus}. Use 'session' or 'system'"
            
            # Get the service object
            try:
                service_obj = bus_obj.get(service, path)
            except Exception as e:
                return f"Failed to connect to {service} at {path}: {str(e)}"
            
            # Get the interface proxy
            try:
                # For pydbus, we can access methods directly on the proxy object
                method_func = getattr(service_obj, method)
            except AttributeError:
                return f"Method {method} not found on interface {interface}"
            
            # Call the method
            try:
                if args:
                    result = method_func(*args)
                else:
                    result = method_func()
                
                # Format the result
                if result is None:
                    return f"Method {method} called successfully (no return value)"
                elif isinstance(result, (list, tuple)):
                    lines = [f"Method {method} returned:"]
                    for i, item in enumerate(result):
                        lines.append(f"  [{i}]: {repr(item)}")
                    return "\n".join(lines)
                else:
                    return f"Method {method} returned: {repr(result)}"
                    
            except Exception as e:
                return f"Method call failed: {str(e)}"
            
        except Exception as e:
            logger.error(f"Failed to call method: {e}")
            return f"Failed to call method: {str(e)}"
    
    # Register profile-specific clipboard tools if available
    if profile.get_available_tools().get('clipboard', False):
        register_clipboard_tools(server, profile)
    
    logger.info(f"Registered core tools for profile: {profile.name}")


def register_clipboard_tools(server: FastMCP, profile: SystemProfile):
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