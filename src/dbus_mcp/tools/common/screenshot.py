"""
Screenshot tools for D-Bus MCP server using low-level API.
"""

import logging
from typing import Dict, Any, List
import os

from mcp import Tool

logger = logging.getLogger(__name__)


def create_screenshot_tools(profile, security, dbus_manager, file_manager) -> List[tuple[Tool, callable]]:
    """Create screenshot-related tools."""
    
    async def capture_screen(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Capture a screenshot of the entire screen."""
        try:
            # Security check
            allowed, reason = security.check_operation('capture_screenshot', {
                'type': 'screen',
                'target': 'full_screen'
            })
            
            if not allowed:
                return {"error": f"Operation blocked: {reason}"}
            
            # Get screenshot config from profile
            config = profile.get_screenshot_config()
            if not config:
                return {"error": "Screenshot not supported on this profile"}
            
            # Call D-Bus method to capture screenshot
            service = dbus_manager.get_service(
                'session',
                config['service'],
                config['path']
            )
            
            # Different desktop environments have different interfaces
            if 'kde' in profile.name.lower():
                # KDE uses ScreenShot2 interface
                result = service.CaptureImage(
                    0,  # x
                    0,  # y
                    0,  # width (0 = full screen)
                    0,  # height (0 = full screen)
                    False,  # include_cursor
                    False   # include_decoration
                )
                
                # Process the screenshot data
                screenshot_data = profile.process_screenshot_data(result, file_manager)
                
            else:
                # GNOME/Generic interface
                filename = service.Screenshot(False, True, "/tmp/screenshot.png")
                screenshot_data = {
                    'filename': filename,
                    'id': os.path.basename(filename)
                }
            
            return {
                "id": screenshot_data.get('id'),
                "filename": screenshot_data.get('filename'),
                "message": "Screenshot captured successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return {"error": f"Failed to capture screenshot: {str(e)}"}
    
    async def capture_active_window(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Capture a screenshot of the active window."""
        try:
            # Security check
            allowed, reason = security.check_operation('capture_screenshot', {
                'type': 'window',
                'target': 'active_window'
            })
            
            if not allowed:
                return {"error": f"Operation blocked: {reason}"}
            
            # Get screenshot config from profile
            config = profile.get_screenshot_config()
            if not config:
                return {"error": "Screenshot not supported on this profile"}
            
            # Call D-Bus method to capture active window
            service = dbus_manager.get_service(
                'session',
                config['service'],
                config['path']
            )
            
            # Different desktop environments have different interfaces
            if 'kde' in profile.name.lower():
                # KDE uses CaptureActiveWindow
                result = service.CaptureActiveWindow(
                    False,  # include_decoration
                    False   # include_cursor
                )
                
                # Process the screenshot data
                screenshot_data = profile.process_screenshot_data(result, file_manager)
                
            else:
                # GNOME/Generic interface
                filename = service.ScreenshotWindow(True, True, "/tmp/screenshot.png")
                screenshot_data = {
                    'filename': filename,
                    'id': os.path.basename(filename)
                }
            
            return {
                "id": screenshot_data.get('id'),
                "filename": screenshot_data.get('filename'),
                "message": "Active window screenshot captured successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to capture active window: {e}")
            return {"error": f"Failed to capture active window: {str(e)}"}
    
    async def list_screenshot_files(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List available screenshot files."""
        try:
            files = file_manager.list_files()
            return [
                {
                    "id": f["id"],
                    "filename": f["filename"],
                    "size": f["size"],
                    "created": f["created"].isoformat() if hasattr(f["created"], 'isoformat') else str(f["created"])
                }
                for f in files
            ]
        except Exception as e:
            logger.error(f"Failed to list screenshot files: {e}")
            return []
    
    # Create tool definitions
    capture_screen_tool = Tool(
        name="capture_screen",
        description="Capture a screenshot of the entire screen",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
    
    capture_window_tool = Tool(
        name="capture_active_window",
        description="Capture a screenshot of the currently active window",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
    
    list_files_tool = Tool(
        name="list_screenshot_files",
        description="List captured screenshot files",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
    
    return [
        (capture_screen_tool, capture_screen),
        (capture_window_tool, capture_active_window),
        (list_files_tool, list_screenshot_files)
    ]