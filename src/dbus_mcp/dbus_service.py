#!/usr/bin/env python3
"""
D-Bus service exposure for MCP server.

This module exposes the MCP server itself as a D-Bus service, enabling:
- Discovery by other MCP instances
- Inter-MCP communication
- Status monitoring
- Coordination between multiple AI agents
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from pydbus import SessionBus
from gi.repository import GLib

logger = logging.getLogger(__name__)

# D-Bus service interface definition
DBUS_MCP_INTERFACE = """
<node>
  <interface name='org.mcp.DBusServer'>
    <method name='GetInfo'>
      <arg type='s' name='info' direction='out'/>
    </method>
    
    <method name='GetStatus'>
      <arg type='a{sv}' name='status' direction='out'/>
    </method>
    
    <method name='GetConnectedClients'>
      <arg type='as' name='clients' direction='out'/>
    </method>
    
    <method name='SendNotification'>
      <arg type='s' name='source' direction='in'/>
      <arg type='s' name='message' direction='in'/>
      <arg type='s' name='response' direction='out'/>
    </method>
    
    <method name='RegisterPeer'>
      <arg type='s' name='peer_id' direction='in'/>
      <arg type='s' name='peer_info' direction='in'/>
      <arg type='b' name='success' direction='out'/>
    </method>
    
    <method name='GetPeers'>
      <arg type='a{ss}' name='peers' direction='out'/>
    </method>
    
    <property name='Version' type='s' access='read'/>
    <property name='Profile' type='s' access='read'/>
    <property name='SafetyLevel' type='s' access='read'/>
    <property name='StartTime' type='s' access='read'/>
    <property name='ClientCount' type='u' access='read'/>
    
    <signal name='ClientConnected'>
      <arg type='s' name='client_id'/>
    </signal>
    
    <signal name='ClientDisconnected'>
      <arg type='s' name='client_id'/>
    </signal>
    
    <signal name='PeerMessage'>
      <arg type='s' name='source'/>
      <arg type='s' name='message'/>
    </signal>
  </interface>
</node>
"""


class DBusMCPService:
    """D-Bus service for MCP server self-exposure."""
    
    dbus = DBUS_MCP_INTERFACE
    
    def __init__(self, server_config):
        """Initialize D-Bus service."""
        self.config = server_config
        self.start_time = datetime.now().isoformat()
        self.connected_clients: List[str] = []
        self.registered_peers: Dict[str, str] = {}
        self._version = "0.1.0"
        self._profile = getattr(server_config, 'profile_name', 'unknown')
        self._safety_level = server_config.safety_level
        
        logger.info("Initializing D-Bus MCP service")
    
    # Properties
    @property
    def Version(self) -> str:
        """Return server version."""
        return self._version
    
    @property
    def Profile(self) -> str:
        """Return active system profile."""
        return self._profile
    
    @property
    def SafetyLevel(self) -> str:
        """Return current safety level."""
        return self._safety_level
    
    @property
    def StartTime(self) -> str:
        """Return server start time."""
        return self.start_time
    
    @property
    def ClientCount(self) -> int:
        """Return number of connected clients."""
        return len(self.connected_clients)
    
    # Methods
    def GetInfo(self) -> str:
        """Get server information as JSON."""
        info = {
            "version": self._version,
            "profile": self._profile,
            "safety_level": self._safety_level,
            "start_time": self.start_time,
            "client_count": len(self.connected_clients),
            "peer_count": len(self.registered_peers)
        }
        return json.dumps(info)
    
    def GetStatus(self) -> Dict[str, Any]:
        """Get detailed server status."""
        return {
            "running": GLib.Variant('b', True),
            "uptime": GLib.Variant('s', str(datetime.now() - datetime.fromisoformat(self.start_time))),
            "memory_usage": GLib.Variant('s', "N/A"),  # Could implement actual memory tracking
            "total_requests": GLib.Variant('u', 0),  # Could implement request counting
        }
    
    def GetConnectedClients(self) -> List[str]:
        """Get list of connected client IDs."""
        return self.connected_clients
    
    def SendNotification(self, source: str, message: str) -> str:
        """Receive notification from another MCP instance."""
        logger.info(f"Received notification from {source}: {message}")
        
        # Emit signal for other listeners
        self.PeerMessage(source, message)
        
        return f"Acknowledged: {message[:50]}..."
    
    def RegisterPeer(self, peer_id: str, peer_info: str) -> bool:
        """Register another MCP instance as a peer."""
        logger.info(f"Registering peer: {peer_id}")
        self.registered_peers[peer_id] = peer_info
        return True
    
    def GetPeers(self) -> Dict[str, str]:
        """Get registered peer MCP instances."""
        return self.registered_peers
    
    # Client tracking (called by main server)
    def add_client(self, client_id: str):
        """Track new client connection."""
        if client_id not in self.connected_clients:
            self.connected_clients.append(client_id)
            self.ClientConnected(client_id)
            logger.info(f"Client connected: {client_id}")
    
    def remove_client(self, client_id: str):
        """Track client disconnection."""
        if client_id in self.connected_clients:
            self.connected_clients.remove(client_id)
            self.ClientDisconnected(client_id)
            logger.info(f"Client disconnected: {client_id}")
    
    # Signals (defined by interface, implemented by pydbus)
    ClientConnected = None
    ClientDisconnected = None
    PeerMessage = None


def publish_dbus_service(server_config) -> Optional[DBusMCPService]:
    """Publish MCP server on D-Bus session bus."""
    try:
        bus = SessionBus()
        service = DBusMCPService(server_config)
        
        # Try to publish with a unique name if primary is taken
        service_names = [
            "org.mcp.DBusServer",
            f"org.mcp.DBusServer.{server_config.safety_level}",
            f"org.mcp.DBusServer.instance{datetime.now().timestamp()}"
        ]
        
        published = False
        for name in service_names:
            try:
                bus.publish(name, service)
                logger.info(f"Published D-Bus service as: {name}")
                published = True
                break
            except Exception as e:
                logger.debug(f"Could not publish as {name}: {e}")
        
        if not published:
            logger.warning("Could not publish D-Bus service under any name")
            return None
            
        return service
        
    except Exception as e:
        logger.error(f"Failed to publish D-Bus service: {e}")
        return None