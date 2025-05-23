# KDE Plasma on Arch Linux Profile
"""System profile for KDE Plasma desktop environment on Arch Linux."""

from typing import Dict, Any, List
import os
from .base import SystemProfile


class KDEArchProfile(SystemProfile):
    """
    Profile optimized for KDE Plasma on Arch Linux.
    
    Handles KDE-specific services:
    - Klipper for clipboard management
    - KWin/Spectacle for screenshots  
    - PowerDevil for power management
    - KDE Connect integration
    - Plasma-specific D-Bus interfaces
    """
    
    @property
    def name(self) -> str:
        return "kde-arch"
    
    @property
    def description(self) -> str:
        return "KDE Plasma 6 on Arch Linux"
    
    @property
    def priority(self) -> int:
        return 10  # High priority for specific match
    
    def get_clipboard_config(self) -> Dict[str, Any]:
        """KDE uses Klipper for clipboard management."""
        return {
            'service': 'org.kde.klipper',
            'path': '/klipper',
            'interface': 'org.kde.klipper.klipper',
            'adapter': 'klipper',
            'methods': {
                'read': 'getClipboardContents',
                'write': 'setClipboardContents',
                'history': 'getClipboardHistoryMenu',
                'clear': 'clearClipboardContents'
            }
        }
    
    def get_screenshot_config(self) -> Dict[str, Any]:
        """KDE screenshot tools vary by Wayland/X11."""
        if self.is_wayland():
            # Spectacle on Wayland or KWin built-in
            return {
                'service': 'org.kde.KWin.ScreenShot2',
                'path': '/org/kde/KWin/ScreenShot2',
                'interface': 'org.kde.KWin.ScreenShot2',
                'adapter': 'kwin',
                'methods': {
                    'screen': 'CaptureActiveScreen',
                    'window': 'CaptureActiveWindow',
                    'area': 'CaptureArea',
                    'interactive': 'CaptureInteractive'
                }
            }
        else:
            # X11 can use more options
            return {
                'service': 'org.kde.spectacle',
                'interface': 'org.kde.spectacle',
                'adapter': 'spectacle',
                'fallback': super().get_screenshot_config()
            }
    
    def get_profile_specific_tools(self) -> List[str]:
        """KDE-specific tools available."""
        tools = [
            'kde.activities',      # Virtual desktop activities
            'kde.krunner',        # KRunner launcher
            'kde.powerdevil',     # Power management
            'kde.kwin',           # Window manager control
            'kde.plasma_vault',   # Encrypted folders
        ]
        
        # Check for optional KDE tools
        if self._has_kde_connect():
            tools.append('kde.connect')  # Phone integration
            
        if self._has_kate():
            tools.append('kde.kate')  # Text editor integration
            
        return tools
    
    def get_safety_level_capabilities(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Describe what capabilities are available at each safety level.
        
        Returns a clear, user-friendly description of what can be done.
        """
        return {
            'high': {
                'description': '🟢 Read-only operations and user notifications',
                'capabilities': [
                    '📋 Read/write clipboard text',
                    '🔔 Send desktop notifications', 
                    '🎵 Control media playback',
                    '📊 Read system status (battery, network)',
                    '🔍 Discover available services',
                    '📖 Read application states'
                ],
                'examples': [
                    'Get clipboard contents',
                    'Show notification "Task completed"',
                    'Pause currently playing media'
                ]
            },
            'medium': {
                'description': '🟡 Productivity operations (recommended for development)',
                'capabilities': [
                    '✏️ Send text to editors (Kate, KWrite)',
                    '📁 Open files/folders in Dolphin',
                    '🌐 Open URLs in browser',
                    '🪟 Focus and activate windows',
                    '📸 Take screenshots (with user consent)',
                    '⌨️ Simulate keyboard input to active window'
                ],
                'examples': [
                    'Write code directly to Kate',
                    'Show project folder in file manager',
                    'Open documentation in browser'
                ]
            },
            'low': {
                'description': '🔴 System administration (use with caution)',
                'capabilities': [
                    '⚙️ Start/stop/restart services',
                    '🔧 Modify system settings',
                    '📦 Query package information',
                    '🖥️ Control display settings',
                    '🔐 Manage system connections'
                ],
                'examples': [
                    'Restart a crashed service',
                    'Change display brightness',
                    'Check for system updates'
                ]
            }
        }
    
    def get_power_management_config(self) -> Dict[str, Any]:
        """KDE uses PowerDevil for power management."""
        return {
            'service': 'org.kde.Solid.PowerManagement',
            'interface': 'org.kde.Solid.PowerManagement',
            'adapter': 'powerdevil',
            'features': [
                'brightness_control',
                'power_profiles',
                'inhibit_sleep',
                'battery_conservation'
            ]
        }
    
    def get_package_manager_config(self) -> Dict[str, Any]:
        """Arch uses pacman/yay."""
        return {
            'system': 'pacman',
            'aur_helper': self._detect_aur_helper(),
            'commands': {
                'search': 'pacman -Ss',
                'info': 'pacman -Si',
                'list_installed': 'pacman -Q',
                'check_updates': 'checkupdates'
            }
        }
    
    def get_media_player_pattern(self) -> str:
        """KDE apps often use specific patterns."""
        # Include both standard MPRIS and KDE-specific patterns
        return "org.mpris.MediaPlayer2.*|org.kde.plasma-browser-integration"
    
    def validate_environment(self) -> List[str]:
        """Validate KDE/Arch environment."""
        issues = super().validate_environment()
        
        # Check for KDE
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        if 'kde' not in desktop:
            issues.append("KDE desktop environment not detected")
        
        # Check for Arch
        if not os.path.exists('/etc/arch-release'):
            issues.append("Arch Linux not detected")
        
        # Check for critical KDE services
        if self.has_display():
            # Would check D-Bus for these services
            required_services = [
                'org.kde.plasmashell',
                'org.kde.kwin',
                'org.kde.kded6'
            ]
            # Note: Actual implementation would check via D-Bus
        
        return issues
    
    def _has_kde_connect(self) -> bool:
        """Check if KDE Connect is available."""
        # Would check D-Bus for org.kde.kdeconnect
        return os.path.exists('/usr/bin/kdeconnect-cli')
    
    def _has_kate(self) -> bool:
        """Check if Kate editor is available."""
        return os.path.exists('/usr/bin/kate')
    
    def _detect_aur_helper(self) -> str:
        """Detect which AUR helper is installed."""
        helpers = ['yay', 'paru', 'aurman', 'trizen']
        for helper in helpers:
            if os.path.exists(f'/usr/bin/{helper}'):
                return helper
        return None
    
    def get_desktop_integration_features(self) -> Dict[str, bool]:
        """KDE-specific desktop integration features."""
        return {
            'global_menu': True,          # KDE supports global menu
            'system_tray': True,          # Full system tray support
            'thumbnails': True,           # File manager thumbnails
            'file_indexing': True,        # Baloo file indexing
            'desktop_widgets': True,      # Plasma widgets
            'window_rules': True,         # KWin window rules
            'color_schemes': True,        # System color schemes
            'virtual_desktops': True,     # Multiple desktops
            'activities': True,           # KDE Activities
        }
    
    def on_load(self):
        """Initialize KDE-specific features."""
        # Set KDE-specific environment if needed
        if not os.environ.get('KDE_FULL_SESSION'):
            os.environ['KDE_FULL_SESSION'] = 'true'