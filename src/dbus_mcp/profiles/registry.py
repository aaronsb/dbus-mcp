"""
Profile Registry

Central registry for system profiles.
"""

import logging
from typing import Dict, Type, Optional

from .base import SystemProfile
from .kde_arch import KDEArchProfile
from .detector import ProfileDetector

logger = logging.getLogger(__name__)


# Global profile registry
PROFILE_REGISTRY: Dict[str, Type[SystemProfile]] = {
    'kde-arch': KDEArchProfile,
    # Add more profiles as they're implemented:
    # 'gnome-ubuntu': GNOMEUbuntuProfile,
    # 'server-generic': ServerGenericProfile,
    # 'sway-arch': SwayArchProfile,
}


def register_profile(name: str, profile_class: Type[SystemProfile]):
    """
    Register a custom profile.
    
    Args:
        name: Profile identifier
        profile_class: Profile class (must inherit from SystemProfile)
    """
    if not issubclass(profile_class, SystemProfile):
        raise ValueError(f"Profile class must inherit from SystemProfile")
    
    PROFILE_REGISTRY[name] = profile_class
    logger.info(f"Registered profile: {name}")


def load_profile(name: Optional[str] = None) -> SystemProfile:
    """
    Load a system profile by name or auto-detect.
    
    Args:
        name: Profile name (optional, will auto-detect if not provided)
        
    Returns:
        Instantiated system profile
    """
    if name:
        # Try to load specific profile
        if name in PROFILE_REGISTRY:
            profile_class = PROFILE_REGISTRY[name]
            profile = profile_class()
            logger.info(f"Loaded profile: {name}")
            return profile
        else:
            logger.warning(f"Profile '{name}' not found, falling back to auto-detection")
    
    # Auto-detect profile
    detected_profiles = ProfileDetector.detect_all_compatible()
    logger.info(f"Auto-detected compatible profiles: {detected_profiles}")
    
    # Try each detected profile in order
    for profile_name in detected_profiles:
        if profile_name in PROFILE_REGISTRY:
            profile_class = PROFILE_REGISTRY[profile_name]
            profile = profile_class()
            logger.info(f"Loaded auto-detected profile: {profile_name}")
            return profile
    
    # Last resort - create a generic profile
    logger.warning("No suitable profile found, using generic fallback")
    return GenericProfile()


class GenericProfile(SystemProfile):
    """Fallback generic profile for unknown systems."""
    
    @property
    def name(self) -> str:
        return "generic"
    
    @property
    def description(self) -> str:
        return "Generic Linux system (fallback)"
    
    def get_available_tools(self) -> Dict[str, bool]:
        """Conservative tool availability for generic systems."""
        return {
            'clipboard': False,  # Can't assume clipboard access
            'screenshot': False,  # Can't assume display
            'notifications': True,  # Try freedesktop standard
            'media': True,  # MPRIS is fairly standard
            'system': False,  # Can't assume systemd
            'desktop': self.has_display(),
        }