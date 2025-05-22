# System Profiles for D-Bus MCP Server
"""
System profiles provide abstraction between D-Bus implementations
and specific Linux distributions/desktop environments.
"""

from .base import SystemProfile
from .detector import ProfileDetector
from .registry import load_profile, register_profile, PROFILE_REGISTRY

__all__ = [
    'SystemProfile',
    'ProfileDetector', 
    'load_profile',
    'register_profile',
    'PROFILE_REGISTRY'
]