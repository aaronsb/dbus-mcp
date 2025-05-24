#!/usr/bin/env python3
"""
MCP instance discovery tools for low-level API.

These tools enable discovery and communication between multiple MCP instances.
"""

import logging
import json
from typing import Dict, List, Any

from mcp import Tool

logger = logging.getLogger(__name__)


def create_mcp_discovery_tools_lowlevel(dbus_manager) -> List[tuple[Tool, callable]]:
    """Create tools for MCP instance discovery and communication."""
    
    async def discover_mcp_servers(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover other MCP server instances on D-Bus."""
        bus = arguments.get("bus", "session")
        
        try:
            from pydbus import SessionBus, SystemBus
            
            bus_obj = SessionBus() if bus == "session" else SystemBus()
            
            # Get all services
            dbus_obj = bus_obj.get("org.freedesktop.DBus", "/org/freedesktop/DBus")
            services = dbus_obj.ListNames()
            
            # Filter for MCP services
            mcp_services = []
            for service in services:
                if service.startswith("org.mcp."):
                    try:
                        # Try to get info from the service
                        mcp_obj = bus_obj.get(service, "/org/mcp/DBusServer")
                        info = json.loads(mcp_obj.GetInfo())
                        
                        mcp_services.append({
                            "service_name": service,
                            "info": info
                        })
                    except Exception as e:
                        logger.debug(f"Could not query {service}: {e}")
                        mcp_services.append({
                            "service_name": service,
                            "info": {"error": str(e)}
                        })
            
            return mcp_services
            
        except Exception as e:
            logger.error(f"Error discovering MCP servers: {e}")
            return []
    
    async def get_mcp_server_info(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information from a specific MCP server."""
        service_name = arguments.get("service_name", "")
        
        try:
            from pydbus import SessionBus
            
            bus = SessionBus()
            mcp_obj = bus.get(service_name, "/org/mcp/DBusServer")
            
            # Get basic info
            info = json.loads(mcp_obj.GetInfo())
            
            # Get status
            status = mcp_obj.GetStatus()
            
            # Get connected clients
            clients = mcp_obj.GetConnectedClients()
            
            # Get peers
            peers = mcp_obj.GetPeers()
            
            return {
                "info": info,
                "status": dict(status),
                "connected_clients": clients,
                "registered_peers": peers
            }
            
        except Exception as e:
            logger.error(f"Error getting MCP server info: {e}")
            return {"error": str(e)}
    
    async def send_mcp_notification(arguments: Dict[str, Any]) -> str:
        """Send a notification to another MCP instance."""
        service_name = arguments.get("service_name", "")
        message = arguments.get("message", "")
        
        try:
            from pydbus import SessionBus
            
            bus = SessionBus()
            mcp_obj = bus.get(service_name, "/org/mcp/DBusServer")
            
            # Get our own service name (if we have one)
            source = "org.mcp.DBusServer.unknown"
            try:
                # Try to find our own service name
                dbus_obj = bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus")
                our_name = dbus_obj.GetNameOwner("org.mcp.DBusServer")
                source = "org.mcp.DBusServer"
            except:
                pass
            
            response = mcp_obj.SendNotification(source, message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending MCP notification: {e}")
            return f"Error: {str(e)}"
    
    # Create tool definitions
    discover_tool = Tool(
        name="discover_mcp_servers",
        description="Discover other MCP server instances on D-Bus",
        inputSchema={
            "type": "object",
            "properties": {
                "bus": {
                    "type": "string",
                    "enum": ["session", "system"],
                    "default": "session",
                    "description": "D-Bus bus to search"
                }
            }
        }
    )
    
    info_tool = Tool(
        name="get_mcp_server_info",
        description="Get detailed information from a specific MCP server",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "D-Bus service name of the MCP server"
                }
            },
            "required": ["service_name"]
        }
    )
    
    notify_tool = Tool(
        name="send_mcp_notification",
        description="Send a notification to another MCP instance",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Target MCP server D-Bus service name"
                },
                "message": {
                    "type": "string",
                    "description": "Message to send"
                }
            },
            "required": ["service_name", "message"]
        }
    )
    
    return [
        (discover_tool, discover_mcp_servers),
        (info_tool, get_mcp_server_info),
        (notify_tool, send_mcp_notification)
    ]