"""
D-Bus MCP Server Core Implementation using low-level MCP API

This module contains the main MCP server that bridges between
AI clients and D-Bus services on Linux systems, using the 
low-level MCP library for maximum control.
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import json

from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp import Tool
from mcp.types import TextContent
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
    Main D-Bus MCP Server implementation using low-level API.
    
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
        self.server = Server(self.config.name)
        
        # Initialize components
        self.dbus_manager = DBusManager(
            enable_system_bus=self.config.enable_system_bus
        )
        self.security = SecurityPolicy(safety_level=self.config.safety_level)
        
        # Initialize file manager for operations that create files
        from .file_manager import FilePipeManager
        
        # D-Bus service exposure (optional)
        self.dbus_service = None
        self.file_manager = FilePipeManager(profile=profile)
        
        # Tool registry
        self.tools: Dict[str, Tool] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        
        # Statistics
        self.stats = {
            "start_time": datetime.now(),
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "requests_by_tool": {}
        }
        
        # Set up server handlers
        self._setup_handlers()
        
        logger.info(
            f"Initialized {self.config.name} v{self.config.version} "
            f"with profile: {profile.name}"
        )
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Return available tools."""
            return list(self.tools.values())
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[Any]:
            """Handle tool execution."""
            if name not in self.tool_handlers:
                raise ValueError(f"Unknown tool: {name}")
            
            # Update statistics
            self.stats["total_requests"] += 1
            self.stats["requests_by_tool"][name] = \
                self.stats["requests_by_tool"].get(name, 0) + 1
            
            try:
                # Execute the tool handler
                handler = self.tool_handlers[name]
                result = await handler(arguments)
                
                self.stats["successful_requests"] += 1
                
                # Ensure result is a list of content items
                if isinstance(result, dict):
                    # Convert dict to text content
                    import json
                    from mcp.types import TextContent
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
                elif isinstance(result, str):
                    from mcp.types import TextContent
                    return [TextContent(
                        type="text",
                        text=result
                    )]
                elif isinstance(result, list):
                    return result
                else:
                    # Fallback
                    from mcp.types import TextContent
                    return [TextContent(
                        type="text",
                        text=str(result)
                    )]
                
            except Exception as e:
                self.stats["failed_requests"] += 1
                logger.error(f"Tool {name} failed: {e}")
                raise
    
    def add_tool(self, tool: Tool, handler: Callable):
        """
        Add a tool to the server.
        
        Args:
            tool: Tool definition
            handler: Async function to handle tool execution
        """
        self.tools[tool.name] = tool
        self.tool_handlers[tool.name] = handler
        logger.debug(f"Registered tool: {tool.name}")
    
    def remove_tool(self, name: str):
        """Remove a tool from the server."""
        if name in self.tools:
            del self.tools[name]
            del self.tool_handlers[name]
            logger.debug(f"Removed tool: {name}")
    
    def publish_on_dbus(self):
        """Publish this MCP server as a D-Bus service for discovery."""
        try:
            from .dbus_service import publish_dbus_service
            
            # Add profile name to config for the service
            self.config.profile_name = self.profile.name
            
            self.dbus_service = publish_dbus_service(self.config)
            if self.dbus_service:
                logger.info("MCP server published on D-Bus for discovery")
                return True
            else:
                logger.warning("Could not publish MCP server on D-Bus")
                return False
        except Exception as e:
            logger.error(f"Error publishing D-Bus service: {e}")
            return False
    
    async def run_stdio(self):
        """Run the server with stdio transport."""
        from mcp import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=self.config.name,
                    server_version=self.config.version,
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    ),
                    instructions=self.config.description
                )
            )