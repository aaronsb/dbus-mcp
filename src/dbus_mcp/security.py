"""
Security Policy Engine

Enforces security policies for D-Bus operations.
"""

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
    """
    
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
    
    def __init__(self):
        """Initialize the security policy."""
        # Rate limiting tracking
        self.operation_history: Dict[str, list] = defaultdict(list)
        
        # Audit log
        self.audit_log = []
        
        logger.info("Security policy initialized")
    
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