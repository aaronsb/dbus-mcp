"""
Security Policy Engine

Enforces security policies for D-Bus operations.
"""

import os
import logging
from typing import Dict, Any, Tuple, Set, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import fnmatch

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
    
    # Operation categories - Pattern-based security model
    # Categories can have 'requires_interaction' flag for operations needing human collaboration
    OPERATION_CATEGORIES = {
        # 🟢 HIGH Safety - Always allowed
        'read_state': {
            'description': 'Read application or system state',
            'patterns': ['Get*', 'List*', 'Query*', 'Is*', 'Has*', 'Read*'],
            'safety_level': 'high'
        },
        'user_notification': {
            'description': 'Notify user without side effects',
            'patterns': ['Notify', 'ShowNotification', 'Alert', 'CloseNotification'],
            'safety_level': 'high'
        },
        'clipboard_read': {
            'description': 'Read clipboard contents',
            'patterns': ['*ClipboardContents', 'GetClipboard*', 'ReadClipboard*'],
            'safety_level': 'high'
        },
        'media_control': {
            'description': 'Control media playback',
            'patterns': ['Play', 'Pause', 'Next', 'Previous', 'Stop', 'PlayPause'],
            'safety_level': 'high'
        },
        
        # 🟡 MEDIUM Safety - Productivity operations
        'text_input': {
            'description': 'Send text to applications',
            'patterns': ['*Input*', 'InsertText', 'TypeText', 'SendKeys', 'SetText*',
                        'sendText', 'SendMessage', 'ComposeEmail', 'WriteDocument'],
            'safety_level': 'medium'
        },
        'clipboard_write': {
            'description': 'Write to clipboard',
            'patterns': ['SetClipboard*', 'WriteClipboard*', 'CopyTo*'],
            'safety_level': 'medium'
        },
        'file_navigation': {
            'description': 'Open files/folders in applications',
            'patterns': ['Open*', 'Show*', 'Navigate*', 'Browse*', 'Reveal*',
                        'Display*', 'Load*', 'View*'],
            'safety_level': 'medium'
        },
        'window_management': {
            'description': 'Focus and arrange windows (non-destructive)',
            'patterns': ['Activate*', 'Focus*', 'Raise*', 'Minimize*', 'SetActive*',
                        'activate', 'focus', 'raise', 'lower', 'show', 'hide',
                        'cascadeDesktop', 'unclutterDesktop', 'showDesktop',
                        'nextDesktop', 'previousDesktop', 'highlightWindows'],
            'safety_level': 'medium'
        },
        'desktop_navigation': {
            'description': 'Switch between virtual desktops',
            'patterns': ['*Desktop', 'switchTo*', 'moveToDesktop*'],
            'safety_level': 'medium'
        },
        'screenshot': {
            'description': 'Capture screen content',
            'patterns': ['Screenshot*', 'Capture*', 'Grab*'],
            'safety_level': 'medium'
        },
        'screen_brightness': {
            'description': 'Adjust display brightness',
            'patterns': ['*Brightness*', 'SetBrightness', 'AdjustBrightness*'],
            'safety_level': 'medium'
        },
        
        # 🤝 INTERACTIVE - Requires human collaboration
        'interactive_selection': {
            'description': 'Operations requiring user to click/select',
            'patterns': ['query*', '*Interactive*', 'pick*', 'select*'],
            'safety_level': 'medium',
            'requires_interaction': True,
            'interaction_type': 'user_selection'
        },
        'interactive_confirmation': {
            'description': 'Operations requiring user confirmation',
            'patterns': ['confirm*', 'approve*', 'authenticate*'],
            'safety_level': 'medium',
            'requires_interaction': True,
            'interaction_type': 'user_confirmation'
        },
        
        # 🔴 LOW Safety - System modifications
        'window_close': {
            'description': 'Close windows (potential data loss)',
            'patterns': ['Close*', 'Quit*', 'Exit*', 'killWindow', 'terminate*'],
            'safety_level': 'low'
        },
        'process_control': {
            'description': 'Start/stop processes and services',
            'patterns': ['Start*', 'Stop*', 'Restart*', 'Kill*', 'Terminate*'],
            'safety_level': 'low'
        },
        'system_config': {
            'description': 'Modify system configuration',
            'patterns': ['Set*', 'Configure*', 'Update*', 'Change*', 'Apply*'],
            'safety_level': 'low'
        },
        
        # Additional categories for comprehensive application support
        'document_operations': {
            'description': 'Save documents and export files',
            'patterns': ['Save*', 'Export*', 'Print*', 'Convert*'],
            'safety_level': 'medium'
        },
        'communication': {
            'description': 'Send messages and emails',
            'patterns': ['SendMessage', 'SendEmail', 'SendIM', 'PostStatus'],
            'safety_level': 'medium'
        },
        'media_management': {
            'description': 'Organize media files',
            'patterns': ['AddToPlaylist', 'ImportMedia', 'TagFile', 'OrganizePhotos'],
            'safety_level': 'medium'
        },
        'search_operations': {
            'description': 'Search for files and content',
            'patterns': ['Search*', 'Find*', 'Locate*', 'QueryIndex'],
            'safety_level': 'high'  # Read-only searching
        },
        'window_info': {
            'description': 'Query window and desktop information',
            'patterns': ['queryWindowInfo', 'getWindowInfo', 'currentDesktop',
                        'supportInformation', 'activeOutputName'],
            'safety_level': 'high'  # Read-only window queries
        },
        
        # ⚫ NEVER Allowed - Destructive operations
        'system_power': {
            'description': 'Power management operations',
            'patterns': ['PowerOff', 'Reboot', 'Shutdown', 'Suspend', 'Hibernate'],
            'forbidden': True
        },
        'data_destruction': {
            'description': 'Delete or format data',
            'patterns': ['Delete*', 'Remove*', 'Format*', 'Destroy*', 'Wipe*'],
            'forbidden': True
        },
        'package_management': {
            'description': 'Install or remove software',
            'patterns': ['Install*', 'Uninstall*', 'RemovePackage*', 'UpdatePackage*'],
            'forbidden': True
        }
    }
    
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
    
    def _categorize_method(self, method: str) -> Optional[str]:
        """
        Categorize a method based on pattern matching.
        
        Returns the category name if matched, None otherwise.
        """
        for category_name, category_info in self.OPERATION_CATEGORIES.items():
            patterns = category_info.get('patterns', [])
            for pattern in patterns:
                if fnmatch.fnmatch(method, pattern):
                    return category_name
        return None
    
    def get_method_interaction_info(self, method: str) -> Optional[Dict[str, Any]]:
        """
        Get interaction requirements for a method.
        
        Returns dict with 'requires_interaction' and 'interaction_type' if applicable.
        """
        category = self._categorize_method(method)
        if category:
            category_info = self.OPERATION_CATEGORIES[category]
            if category_info.get('requires_interaction', False):
                return {
                    'requires_interaction': True,
                    'interaction_type': category_info.get('interaction_type', 'unknown'),
                    'category': category,
                    'description': category_info.get('description', '')
                }
        return None
    
    def is_method_allowed(self, service: str, interface: str, method: str) -> bool:
        """
        Check if a specific D-Bus method call is allowed using category-based security.
        
        This uses pattern matching to categorize operations rather than maintaining
        lists of specific endpoints.
        
        Args:
            service: D-Bus service name
            interface: D-Bus interface name
            method: Method name
            
        Returns:
            True if the method call is allowed, False otherwise
        """
        # First, try to categorize the method
        category = self._categorize_method(method)
        
        if category:
            category_info = self.OPERATION_CATEGORIES[category]
            
            # Check if forbidden
            if category_info.get('forbidden', False):
                logger.warning(f"Blocked forbidden category '{category}': {service}.{interface}.{method}")
                return False
            
            # Check safety level requirement
            required_level = category_info.get('safety_level')
            
            if required_level == 'high':
                # Always allowed
                logger.debug(f"Allowed '{category}' (high safety): {method}")
                return True
            elif required_level == 'medium' and self.safety_level in ['medium', 'low']:
                logger.debug(f"Allowed '{category}' (medium safety): {method}")
                return True
            elif required_level == 'low' and self.safety_level == 'low':
                logger.debug(f"Allowed '{category}' (low safety): {method}")
                return True
            else:
                logger.info(f"Blocked '{category}' - requires {required_level} safety, current: {self.safety_level}")
                return False
        
        # Special handling for clipboard write at medium safety
        # (since setClipboardContents doesn't match our write patterns)
        if self.safety_level in ['medium', 'low']:
            if method == 'setClipboardContents' and 'klipper' in service:
                logger.debug(f"Allowed clipboard write (special case): {method}")
                return True
            
            # Also handle window activation methods that don't match patterns
            if method == 'activate' and interface == 'org.kde.Kate.Application':
                logger.debug(f"Allowed window activation (special case): {method}")
                return True
        
        # If no category matched, deny by default
        logger.info(f"Method not categorized, denying: {service}.{interface}.{method}")
        return False