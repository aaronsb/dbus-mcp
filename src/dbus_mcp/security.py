"""
Security Policy Engine

Enforces security policies for D-Bus operations.
"""

import os
import logging
from typing import Dict, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict

from .profiles.base import SystemProfile

logger = logging.getLogger(__name__)


class SecurityPolicy:
    """
    Enforces security policies for D-Bus operations.
    
    Features:
    - Operation whitelisting
    - Rate limiting
    - Dangerous operation blocking
    - Audit logging
    - Configurable safety levels
    """
    
    # Safety levels
    SAFETY_HIGH = "high"      # Very restrictive (default)
    SAFETY_MEDIUM = "medium"  # Allow productivity operations
    SAFETY_LOW = "low"        # More permissive (future)
    
    # Operations that are ALWAYS forbidden
    FORBIDDEN_OPERATIONS = {
        'system.shutdown',
        'system.reboot',
        'system.poweroff',
        'system.format_disk',
        'system.install_package',
        'system.remove_package',
    }
    
    # Default rate limits (operations per minute)
    DEFAULT_RATE_LIMITS = {
        'default': 60,
        'notify': 10,
        'clipboard.write': 30,
        'screenshot': 5,
        'system.service_restart': 5,
    }
    
    def __init__(self, safety_level: str = None):
        """
        Initialize the security policy.
        
        Args:
            safety_level: One of SAFETY_HIGH, SAFETY_MEDIUM, SAFETY_LOW
        """
        # Rate limiting tracking
        self.operation_history: Dict[str, list] = defaultdict(list)
        
        # Audit log
        self.audit_log = []
        
        # Set safety level with default
        if safety_level is None:
            safety_level = self.SAFETY_HIGH
            
        self.safety_level = safety_level
        if safety_level not in [self.SAFETY_HIGH, self.SAFETY_MEDIUM, self.SAFETY_LOW]:
            logger.warning(f"Unknown safety level: {safety_level}, defaulting to HIGH")
            self.safety_level = self.SAFETY_HIGH
        
        logger.info(f"Security policy initialized with safety level: {self.safety_level}")
    
    def check_operation(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        profile: SystemProfile
    ) -> Tuple[bool, str]:
        """
        Check if an operation is allowed.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Arguments passed to the tool
            profile: Current system profile
            
        Returns:
            Tuple of (allowed, reason)
        """
        # Log the check
        self._audit_log(tool_name, arguments, "check_started")
        
        # Check if operation is forbidden
        if self._is_forbidden(tool_name):
            self._audit_log(tool_name, arguments, "forbidden")
            return False, f"Operation '{tool_name}' is forbidden"
        
        # Check rate limits
        if not self._check_rate_limit(tool_name):
            self._audit_log(tool_name, arguments, "rate_limited")
            return False, f"Rate limit exceeded for '{tool_name}'"
        
        # Check profile-specific restrictions
        available_tools = profile.get_available_tools()
        tool_category = tool_name.split('.')[0]
        
        if tool_category in available_tools and not available_tools[tool_category]:
            self._audit_log(tool_name, arguments, "not_available_in_profile")
            return False, f"Tool category '{tool_category}' not available in profile {profile.name}"
        
        # Additional checks based on tool
        if tool_name.startswith('system.') and not profile.detect_init_system() == 'systemd':
            return False, "System tools require systemd"
        
        # All checks passed
        self._audit_log(tool_name, arguments, "allowed")
        return True, "Operation allowed"
    
    def _is_forbidden(self, tool_name: str) -> bool:
        """Check if an operation is in the forbidden list."""
        return tool_name in self.FORBIDDEN_OPERATIONS
    
    def _check_rate_limit(self, tool_name: str) -> bool:
        """
        Check if operation is within rate limits.
        
        Returns True if allowed, False if rate limited.
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        self.operation_history[tool_name] = [
            timestamp for timestamp in self.operation_history[tool_name]
            if timestamp > one_minute_ago
        ]
        
        # Get rate limit for this operation
        if tool_name in self.DEFAULT_RATE_LIMITS:
            limit = self.DEFAULT_RATE_LIMITS[tool_name]
        else:
            limit = self.DEFAULT_RATE_LIMITS['default']
        
        # Check if under limit
        if len(self.operation_history[tool_name]) >= limit:
            return False
        
        # Record this operation
        self.operation_history[tool_name].append(now)
        return True
    
    def _audit_log(self, tool_name: str, arguments: Dict[str, Any], result: str):
        """Add entry to audit log."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'tool': tool_name,
            'arguments': self._sanitize_arguments(arguments),
            'result': result
        }
        
        self.audit_log.append(entry)
        
        # Log significant events
        if result in ['forbidden', 'rate_limited']:
            logger.warning(f"Security event: {result} for {tool_name}")
        
        # Keep audit log size manageable
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
    
    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize arguments for logging (remove sensitive data)."""
        # Create a copy
        sanitized = arguments.copy()
        
        # Remove potentially sensitive fields
        sensitive_fields = {'password', 'token', 'secret', 'key'}
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '<redacted>'
        
        return sanitized
    
    def get_audit_log(self, limit: int = 100) -> list:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]
    
    def get_rate_limit_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current rate limit status for all operations."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        status = {}
        for tool_name, timestamps in self.operation_history.items():
            recent_count = len([t for t in timestamps if t > one_minute_ago])
            
            if tool_name in self.DEFAULT_RATE_LIMITS:
                limit = self.DEFAULT_RATE_LIMITS[tool_name]
            else:
                limit = self.DEFAULT_RATE_LIMITS['default']
            
            status[tool_name] = {
                'current': recent_count,
                'limit': limit,
                'percentage': (recent_count / limit) * 100
            }
        
        return status
    
    def is_method_allowed(self, service: str, interface: str, method: str) -> bool:
        """
        Check if a specific D-Bus method call is allowed.
        
        This is used by the call_method tool to enforce security policies
        on arbitrary D-Bus method calls.
        
        Args:
            service: D-Bus service name
            interface: D-Bus interface name
            method: Method name
            
        Returns:
            True if the method call is allowed, False otherwise
        """
        # Block dangerous system operations
        dangerous_patterns = [
            # Power management
            ('org.freedesktop.login1', 'PowerOff'),
            ('org.freedesktop.login1', 'Reboot'),
            ('org.freedesktop.login1', 'Suspend'),
            ('org.freedesktop.login1', 'Hibernate'),
            
            # Package management
            ('org.freedesktop.PackageKit', 'InstallPackages'),
            ('org.freedesktop.PackageKit', 'RemovePackages'),
            ('org.freedesktop.PackageKit', 'UpdatePackages'),
            
            # Systemd dangerous operations
            ('org.freedesktop.systemd1', 'PowerOff'),
            ('org.freedesktop.systemd1', 'Reboot'),
            ('org.freedesktop.systemd1', 'Halt'),
            ('org.freedesktop.systemd1', 'KExec'),
            
            # Disk operations
            ('org.freedesktop.UDisks2', 'Format'),
            ('org.freedesktop.UDisks2', 'Delete'),
            
            # PolicyKit operations (prevent privilege escalation)
            ('org.freedesktop.PolicyKit1', 'AuthenticationAgentResponse'),
        ]
        
        # Check against dangerous patterns
        for pattern_service, pattern_method in dangerous_patterns:
            if service.startswith(pattern_service) and method == pattern_method:
                logger.warning(f"Blocked dangerous method: {service}.{interface}.{method}")
                return False
        
        # Block all methods that could modify critical system state
        dangerous_method_names = {
            'PowerOff', 'Reboot', 'Halt', 'Shutdown', 'Suspend', 'Hibernate',
            'Format', 'Delete', 'Destroy', 'Remove', 'Uninstall',
            'Install', 'Update', 'Upgrade',
            'SetPassword', 'ChangePassword',
            'ExecuteCommand', 'RunScript',
        }
        
        if method in dangerous_method_names:
            logger.warning(f"Blocked dangerous method name: {method}")
            return False
        
        # Allow read-only operations by default
        read_only_prefixes = ['Get', 'List', 'Is', 'Has', 'Can', 'Query']
        for prefix in read_only_prefixes:
            if method.startswith(prefix):
                return True
        
        # High safety operations (always allowed)
        high_safety_operations = [
            # Clipboard operations
            ('org.kde.klipper', 'getClipboardContents'),
            ('org.kde.klipper', 'setClipboardContents'),
            
            # Notification operations
            ('org.freedesktop.Notifications', 'Notify'),
            ('org.freedesktop.Notifications', 'CloseNotification'),
            
            # Media player operations
            ('org.mpris.MediaPlayer2', 'Play'),
            ('org.mpris.MediaPlayer2', 'Pause'),
            ('org.mpris.MediaPlayer2', 'Next'),
            ('org.mpris.MediaPlayer2', 'Previous'),
            
            # Screenshot operations
            ('org.freedesktop.portal.Screenshot', 'Screenshot'),
            ('org.kde.kwin.Screenshot', 'screenshotArea'),
            ('org.kde.kwin.Screenshot', 'screenshotFullscreen'),
        ]
        
        for safe_service, safe_method in high_safety_operations:
            if service.endswith(safe_service) and method == safe_method:
                return True
        
        # Medium safety operations (allowed in MEDIUM or LOW safety)
        if self.safety_level in [self.SAFETY_MEDIUM, self.SAFETY_LOW]:
            medium_safety_operations = [
                # Text editor operations (Kate)
                ('org.kde.kate', 'org.kde.Kate.Application', 'openInput'),
                ('org.kde.kate', 'org.kde.Kate.Application', 'openUrl'),
                ('org.kde.kate', 'org.kde.Kate.Application', 'setCursor'),
                ('org.kde.kate', 'org.kde.Kate.Application', 'activateSession'),
                ('org.kde.kate', 'org.kde.Kate.Application', 'activate'),
                
                # File manager operations
                ('org.freedesktop.FileManager1', 'org.freedesktop.FileManager1', 'ShowItems'),
                ('org.freedesktop.FileManager1', 'org.freedesktop.FileManager1', 'ShowFolders'),
                ('org.freedesktop.FileManager1', 'org.freedesktop.FileManager1', 'ShowItemProperties'),
                
                # Browser operations (opening URLs)
                ('org.freedesktop.portal.OpenURI', 'org.freedesktop.portal.OpenURI', 'OpenURI'),
                
                # Window manager operations
                ('org.kde.KWin', 'org.kde.KWin', 'setActiveWindow'),
            ]
            
            for safe_service, safe_interface, safe_method in medium_safety_operations:
                if service.startswith(safe_service) and interface == safe_interface and method == safe_method:
                    return True
        
        # Log and deny by default
        logger.info(f"Method not explicitly allowed: {service}.{interface}.{method}")
        return False