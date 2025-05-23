# Base System Profile
"""Base class for all system profiles."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import os
import subprocess


class SystemProfile(ABC):
    """
    Base class for system profiles.
    
    Each profile adapts D-Bus MCP to a specific Linux environment,
    handling differences in:
    - Desktop environments (KDE, GNOME, XFCE)
    - Distributions (Arch, Ubuntu, Fedora)
    - Display servers (X11, Wayland)
    - System services and tools
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this profile."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this profile."""
        pass
    
    @property
    def priority(self) -> int:
        """Priority for auto-detection (higher = preferred)."""
        return 0
    
    # Service Adapters
    
    def get_clipboard_config(self) -> Dict[str, Any]:
        """Get clipboard service configuration."""
        return {
            'service': 'org.freedesktop.portal.Desktop',
            'interface': 'org.freedesktop.portal.Clipboard',
            'adapter': 'portal'
        }
    
    def get_screenshot_config(self) -> Dict[str, Any]:
        """Get screenshot service configuration."""
        return {
            'service': 'org.freedesktop.portal.Desktop',
            'interface': 'org.freedesktop.portal.Screenshot',
            'adapter': 'portal'
        }
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification service configuration."""
        return {
            'service': 'org.freedesktop.Notifications',
            'interface': 'org.freedesktop.Notifications',
            'adapter': 'freedesktop'
        }
    
    def get_media_player_pattern(self) -> str:
        """Get D-Bus pattern for media players."""
        return "org.mpris.MediaPlayer2.*"  # MPRIS2 standard
    
    def process_screenshot_data(self, raw_data: bytes, metadata: Dict[str, Any]) -> Optional[bytes]:
        """
        Process raw screenshot data into a standard format.
        
        Different desktop environments may provide screenshot data in different formats.
        This method allows profiles to handle their specific format.
        
        Args:
            raw_data: The raw bytes from the screenshot
            metadata: Any metadata returned by the D-Bus call
            
        Returns:
            Processed image data in PNG format, or None if cannot process
        """
        # Default implementation assumes data is already in correct format
        return raw_data
    
    # Tool Availability
    
    def get_available_tools(self) -> Dict[str, bool]:
        """Return which tool categories are available."""
        return {
            'clipboard': True,
            'screenshot': True,
            'notifications': True,
            'media': True,
            'system': True,
            'desktop': self.has_display(),
        }
    
    def get_profile_specific_tools(self) -> List[str]:
        """Return list of profile-specific tool names."""
        return []
    
    # Environment Detection
    
    def has_display(self) -> bool:
        """Check if running with display server."""
        return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
    
    def is_wayland(self) -> bool:
        """Check if running under Wayland."""
        return bool(os.environ.get('WAYLAND_DISPLAY'))
    
    def is_x11(self) -> bool:
        """Check if running under X11."""
        return bool(os.environ.get('DISPLAY')) and not self.is_wayland()
    
    def detect_init_system(self) -> str:
        """Detect init system (systemd, openrc, etc)."""
        if os.path.exists('/run/systemd/system'):
            return 'systemd'
        elif os.path.exists('/run/openrc'):
            return 'openrc'
        return 'unknown'
    
    def detect_environment(self) -> Dict[str, Any]:
        """Detect comprehensive environment information."""
        env = {
            'profile': self.name,
            'display_server': self._detect_display_server(),
            'init_system': self.detect_init_system(),
            'has_display': self.has_display(),
            'desktop': os.environ.get('XDG_CURRENT_DESKTOP', 'unknown'),
            'session_type': os.environ.get('XDG_SESSION_TYPE', 'unknown'),
        }
        
        # Try to get distro info
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('ID='):
                        env['distro_id'] = line.split('=')[1].strip().strip('"')
                    elif line.startswith('NAME='):
                        env['distro_name'] = line.split('=')[1].strip().strip('"')
        
        return env
    
    def _detect_display_server(self) -> str:
        """Detect display server type."""
        if self.is_wayland():
            return 'wayland'
        elif self.is_x11():
            return 'x11'
        elif not self.has_display():
            return 'none'
        return 'unknown'
    
    # Validation
    
    def validate_environment(self) -> List[str]:
        """
        Validate that this profile can run in current environment.
        Returns list of issues (empty = valid).
        """
        issues = []
        
        if self.get_available_tools()['desktop'] and not self.has_display():
            issues.append("Desktop tools require display server")
        
        if self.detect_init_system() != 'systemd' and self.get_available_tools()['system']:
            issues.append("System tools require systemd")
        
        return issues
    
    # Hooks
    
    def on_load(self):
        """Called when profile is loaded."""
        pass
    
    def on_unload(self):
        """Called when profile is unloaded."""
        pass