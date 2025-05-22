# System Profile Auto-Detection
"""Automatically detect the best system profile for the current environment."""

import os
import subprocess
from typing import Optional, List, Dict, Type
from .base import SystemProfile


class ProfileDetector:
    """
    Detects the appropriate system profile based on:
    - Distribution (Arch, Ubuntu, Fedora, etc.)
    - Desktop Environment (KDE, GNOME, XFCE, etc.)
    - Display Server (X11, Wayland)
    - System Type (Desktop, Server, Embedded)
    """
    
    @staticmethod
    def detect() -> str:
        """
        Detect the best profile name for current system.
        Returns profile name string (e.g., 'kde-arch', 'gnome-ubuntu').
        """
        # Get system information
        distro = ProfileDetector._detect_distro()
        desktop = ProfileDetector._detect_desktop()
        is_server = ProfileDetector._is_server()
        
        # Build profile name
        if is_server:
            return f"server-{distro}" if distro else "server-generic"
        
        if desktop and distro:
            return f"{desktop}-{distro}"
        elif desktop:
            return f"{desktop}-generic"
        elif distro:
            return f"minimal-{distro}"
        
        return "generic"
    
    @staticmethod
    def detect_all_compatible() -> List[str]:
        """
        Return all compatible profiles, ordered by preference.
        This allows fallback if primary profile isn't available.
        """
        profiles = []
        
        distro = ProfileDetector._detect_distro()
        desktop = ProfileDetector._detect_desktop()
        is_server = ProfileDetector._is_server()
        
        # Most specific first
        if desktop and distro:
            profiles.append(f"{desktop}-{distro}")
        
        # Desktop-specific fallback
        if desktop:
            profiles.append(f"{desktop}-generic")
        
        # Distro-specific fallback
        if distro:
            if is_server:
                profiles.append(f"server-{distro}")
            else:
                profiles.append(f"minimal-{distro}")
        
        # Generic fallbacks
        if is_server:
            profiles.append("server-generic")
        else:
            profiles.append("generic")
        
        return profiles
    
    @staticmethod
    def _detect_distro() -> Optional[str]:
        """Detect Linux distribution."""
        # Try /etc/os-release first (systemd standard)
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('ID='):
                        distro_id = line.split('=')[1].strip().strip('"')
                        # Normalize common distros
                        if distro_id in ['arch', 'archlinux']:
                            return 'arch'
                        elif distro_id == 'ubuntu':
                            return 'ubuntu'
                        elif distro_id == 'debian':
                            return 'debian'
                        elif distro_id in ['fedora', 'rhel', 'centos']:
                            return 'fedora'
                        elif distro_id == 'opensuse':
                            return 'suse'
                        elif distro_id == 'nixos':
                            return 'nixos'
                        return distro_id
        
        # Fallback to checking specific files
        if os.path.exists('/etc/arch-release'):
            return 'arch'
        elif os.path.exists('/etc/debian_version'):
            return 'debian'
        elif os.path.exists('/etc/fedora-release'):
            return 'fedora'
        
        return None
    
    @staticmethod
    def _detect_desktop() -> Optional[str]:
        """Detect desktop environment."""
        # XDG_CURRENT_DESKTOP is the standard
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        # Normalize desktop names
        if 'kde' in desktop or 'plasma' in desktop:
            return 'kde'
        elif 'gnome' in desktop:
            return 'gnome'
        elif 'xfce' in desktop:
            return 'xfce'
        elif 'lxde' in desktop or 'lxqt' in desktop:
            return 'lxde'
        elif 'mate' in desktop:
            return 'mate'
        elif 'cinnamon' in desktop:
            return 'cinnamon'
        elif 'unity' in desktop:
            return 'unity'
        elif 'deepin' in desktop:
            return 'deepin'
        elif 'pantheon' in desktop:
            return 'pantheon'
        elif 'budgie' in desktop:
            return 'budgie'
        
        # Check for window managers
        if 'sway' in desktop or os.environ.get('SWAYSOCK'):
            return 'sway'
        elif 'i3' in desktop:
            return 'i3'
        elif 'awesome' in desktop:
            return 'awesome'
        elif 'hyprland' in desktop:
            return 'hyprland'
        
        # Fallback checks
        if os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            return 'gnome'
        elif os.environ.get('KDE_FULL_SESSION'):
            return 'kde'
        
        return None
    
    @staticmethod
    def _is_server() -> bool:
        """Detect if running on a server (headless) system."""
        # No display = likely server
        if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
            return True
        
        # Check systemd target
        try:
            result = subprocess.run(
                ['systemctl', 'get-default'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if 'multi-user.target' in result.stdout:
                return True
            elif 'graphical.target' in result.stdout:
                return False
        except:
            pass
        
        # Check for common server indicators
        if os.path.exists('/etc/server-release'):
            return True
        
        return False
    
    @staticmethod
    def get_environment_info() -> Dict[str, any]:
        """Get comprehensive environment information for debugging."""
        return {
            'distro': ProfileDetector._detect_distro(),
            'desktop': ProfileDetector._detect_desktop(),
            'is_server': ProfileDetector._is_server(),
            'display_server': 'wayland' if os.environ.get('WAYLAND_DISPLAY') 
                            else 'x11' if os.environ.get('DISPLAY')
                            else 'none',
            'session_type': os.environ.get('XDG_SESSION_TYPE', 'unknown'),
            'detected_profile': ProfileDetector.detect(),
            'compatible_profiles': ProfileDetector.detect_all_compatible(),
            'env_vars': {
                'XDG_CURRENT_DESKTOP': os.environ.get('XDG_CURRENT_DESKTOP'),
                'XDG_SESSION_TYPE': os.environ.get('XDG_SESSION_TYPE'),
                'DESKTOP_SESSION': os.environ.get('DESKTOP_SESSION'),
                'DISPLAY': bool(os.environ.get('DISPLAY')),
                'WAYLAND_DISPLAY': bool(os.environ.get('WAYLAND_DISPLAY'))
            }
        }