"""
D-Bus MCP Server Core Implementation

This module contains the main MCP server that bridges between
AI clients and D-Bus services on Linux systems.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from mcp.server import FastMCP
from pydantic import BaseModel

from .profiles.base import SystemProfile
from .dbus_manager import DBusManager
from .security import SecurityPolicy


logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """Configuration for the D-Bus MCP server."""
    name: str = "dbus-mcp"
    version: str = "0.1.0"
    description: str = "D-Bus bridge for AI assistants - from vacuum cleaners to supercomputers"
    
    # Security settings
    safety_level: str = "high"  # "high", "medium", or "low"
    rate_limit_per_minute: int = 60
    enable_system_bus: bool = True
    enable_audit_log: bool = True
    
    # Feature flags
    enable_discovery_tools: bool = True
    enable_raw_dbus_tools: bool = False  # Advanced tools
    
    class Config:
        extra = "allow"


class DBusMCPServer:
    """
    Main D-Bus MCP Server implementation.
    
    This server:
    1. Accepts requests from AI clients via MCP protocol
    2. Translates them to D-Bus operations
    3. Enforces security policies
    4. Returns responses to the AI client
    """
    
    def __init__(
        self,
        profile: SystemProfile,
        config: Optional[ServerConfig] = None
    ):
        """
        Initialize the D-Bus MCP server.
        
        Args:
            profile: System profile for adapting to the environment
            config: Server configuration
        """
        self.profile = profile
        self.config = config or ServerConfig()
        
        # Create the MCP server
        self.server = FastMCP(self.config.name)
        
        # Initialize components
        self.dbus_manager = DBusManager(
            enable_system_bus=self.config.enable_system_bus
        )
        self.security = SecurityPolicy(safety_level=self.config.safety_level)
        
        # Statistics
        self.stats = {
            "start_time": datetime.now(),
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "requests_by_tool": {}
        }
        
        # Initialize server information
        self._setup_server_info()
        
        logger.info(
            f"Initialized {self.config.name} v{self.config.version} "
            f"with profile: {profile.name}"
        )
    
    def _setup_server_info(self):
        """Setup server information for MCP."""
        # This would be exposed to MCP clients
        self.server_info = {
            "name": self.config.name,
            "version": self.config.version,
            "description": self.config.description,
            "profile": {
                "name": self.profile.name,
                "description": self.profile.description,
                "capabilities": self.profile.get_available_tools()
            },
            "environment": self.profile.detect_environment()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get server statistics."""
        uptime = datetime.now() - self.stats["start_time"]
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate": (
                self.stats["successful_requests"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0 else 0
            ),
            "requests_by_tool": self.stats["requests_by_tool"],
            "profile": self.profile.name,
            "dbus_connections": {
                "session": self.dbus_manager.session_bus is not None,
                "system": self.dbus_manager.system_bus is not None
            }
        }
    
    def track_request(self, tool_name: str, success: bool):
        """Track a tool request for statistics."""
        self.stats["total_requests"] += 1
        
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        if tool_name not in self.stats["requests_by_tool"]:
            self.stats["requests_by_tool"][tool_name] = {
                "total": 0,
                "successful": 0,
                "failed": 0
            }
        
        self.stats["requests_by_tool"][tool_name]["total"] += 1
        if success:
            self.stats["requests_by_tool"][tool_name]["successful"] += 1
        else:
            self.stats["requests_by_tool"][tool_name]["failed"] += 1
    
    async def handle_tool_request(self, tool_name: str, arguments: Dict[str, Any]):
        """
        Handle a tool request from the MCP client.
        
        This is called by individual tools to track requests and
        enforce security policies.
        """
        # Check security policy
        allowed, reason = self.security.check_operation(
            tool_name,
            arguments,
            self.profile
        )
        
        if not allowed:
            self.track_request(tool_name, False)
            raise PermissionError(f"Operation denied: {reason}")
        
        # Rate limiting would be checked here
        
        # Tool executes the request
        # (actual execution happens in the tool implementation)
        
        # Track successful request
        self.track_request(tool_name, True)
    
    def cleanup(self):
        """Cleanup resources when shutting down."""
        logger.info("Shutting down D-Bus MCP Server")
        
        # Close D-Bus connections
        self.dbus_manager.cleanup()
        
        # Log final statistics
        stats = self.get_statistics()
        logger.info(f"Final statistics: {stats}")
        
        # Profile cleanup
        self.profile.on_unload()