#!/usr/bin/env python3
"""
MCP instance discovery tools.

These tools enable discovery and communication between multiple MCP instances.
"""

import logging
import json
from typing import Dict, List, Any

from mcp import Tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DiscoverMCPServersInput(BaseModel):
    """Input for discovering MCP servers."""
    bus: str = Field(
        default="session",
        description="D-Bus bus to search (session or system)"
    )


class MCPServerInfoInput(BaseModel):
    """Input for getting MCP server info."""
    service_name: str = Field(
        description="D-Bus service name of the MCP server"
    )


class SendMCPNotificationInput(BaseModel):
    """Input for sending notification to another MCP instance."""
    service_name: str = Field(
        description="Target MCP server D-Bus service name"
    )
    message: str = Field(
        description="Message to send"
    )


def create_mcp_discovery_tools(dbus_manager) -> List[Tool]:
    """Create tools for MCP instance discovery and communication."""
    
    async def discover_mcp_servers(arguments: DiscoverMCPServersInput) -> List[Dict[str, Any]]:
        """Discover other MCP server instances on D-Bus."""
        try:
            from pydbus import SessionBus, SystemBus
            
            bus = SessionBus() if arguments.bus == "session" else SystemBus()
            
            # Get all services
            dbus_obj = bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus")
            services = dbus_obj.ListNames()
            
            # Filter for MCP services
            mcp_services = []
            for service in services:
                if service.startswith("org.mcp."):
                    try:
                        # Try to get info from the service
                        mcp_obj = bus.get(service, "/org/mcp/DBusServer")
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
    
    async def get_mcp_server_info(arguments: MCPServerInfoInput) -> Dict[str, Any]:
        """Get detailed information from a specific MCP server."""
        try:
            from pydbus import SessionBus
            
            bus = SessionBus()
            mcp_obj = bus.get(arguments.service_name, "/org/mcp/DBusServer")
            
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
    
    async def send_mcp_notification(arguments: SendMCPNotificationInput) -> str:
        """Send a notification to another MCP instance."""
        try:
            from pydbus import SessionBus
            
            bus = SessionBus()
            mcp_obj = bus.get(arguments.service_name, "/org/mcp/DBusServer")
            
            # Get our own service name (if we have one)
            source = "org.mcp.DBusServer.unknown"
            try:
                # Try to find our own service name
                dbus_obj = bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus")
                our_name = dbus_obj.GetNameOwner("org.mcp.DBusServer")
                source = "org.mcp.DBusServer"
            except:
                pass
            
            response = mcp_obj.SendNotification(source, arguments.message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending MCP notification: {e}")
            return f"Error: {str(e)}"
    
    return [
        Tool(
            name="discover_mcp_servers",
            description="Discover other MCP server instances on D-Bus",
            inputSchema=DiscoverMCPServersInput.model_json_schema(),
            fn=discover_mcp_servers
        ),
        Tool(
            name="get_mcp_server_info",
            description="Get detailed information from a specific MCP server",
            inputSchema=MCPServerInfoInput.model_json_schema(),
            fn=get_mcp_server_info
        ),
        Tool(
            name="send_mcp_notification",
            description="Send a notification to another MCP instance",
            inputSchema=SendMCPNotificationInput.model_json_schema(),
            fn=send_mcp_notification
        )
    ]