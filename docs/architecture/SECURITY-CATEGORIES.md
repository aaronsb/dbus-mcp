# Security Categories Architecture

## Problem with Current Approach

The current security implementation hardcodes specific D-Bus service/interface/method combinations:

```python
medium_safety_operations = [
    ('org.kde.kate', 'org.kde.Kate.Application', 'openInput'),
    ('org.kde.kate', 'org.kde.Kate.Application', 'openUrl'),
    # ... hundreds more specific endpoints
]
```

This approach has several problems:
1. **Not scalable** - Every new application needs explicit rules
2. **Version fragile** - Service names change (e.g., `org.kde.kate-1157225`)
3. **Encourages bypass** - Users set safety to "low" to "just make it work"
4. **Maintenance burden** - Constant updates for new applications

## Proposed: Category-Based Security Model

Instead of specific endpoints, define **operation categories** based on what they do:

### Operation Categories

```python
# Define what operations do, not which specific D-Bus methods
OPERATION_CATEGORIES = {
    # 🟢 HIGH Safety - Always allowed
    'read_state': {
        'description': 'Read application or system state',
        'patterns': ['Get*', 'List*', 'Query*', 'Is*', 'Has*'],
        'examples': ['GetClipboardContents', 'ListWindows', 'QueryStatus']
    },
    
    'user_notification': {
        'description': 'Notify user without side effects',
        'patterns': ['Notify', 'ShowNotification', 'Alert'],
        'risk': 'minimal'
    },
    
    'media_control': {
        'description': 'Control media playback',
        'patterns': ['Play', 'Pause', 'Next', 'Previous', 'Stop'],
        'risk': 'minimal'
    },
    
    # 🟡 MEDIUM Safety - Productivity operations
    'text_input': {
        'description': 'Send text to applications',
        'patterns': ['*Input*', 'InsertText', 'TypeText', 'SendKeys'],
        'risk': 'moderate',
        'examples': ['openInput', 'insertText', 'sendTextToEditor']
    },
    
    'file_navigation': {
        'description': 'Open files/folders in applications',
        'patterns': ['Open*', 'Show*', 'Navigate*', 'Browse*'],
        'risk': 'moderate',
        'examples': ['OpenFile', 'ShowInFileManager', 'NavigateToFolder']
    },
    
    'window_management': {
        'description': 'Focus and arrange windows',
        'patterns': ['Activate*', 'Focus*', 'Raise*', 'Minimize*'],
        'risk': 'moderate'
    },
    
    # 🔴 LOW Safety - System modifications
    'process_control': {
        'description': 'Start/stop processes and services',
        'patterns': ['Start*', 'Stop*', 'Restart*', 'Kill*'],
        'risk': 'high',
        'audit': True
    },
    
    'system_config': {
        'description': 'Modify system configuration',
        'patterns': ['Set*', 'Configure*', 'Update*', 'Change*'],
        'risk': 'high',
        'audit': True
    },
    
    # ⚫ NEVER Allowed - Destructive operations
    'system_power': {
        'description': 'Power management operations',
        'patterns': ['PowerOff', 'Reboot', 'Shutdown', 'Suspend'],
        'forbidden': True
    },
    
    'data_destruction': {
        'description': 'Delete or format data',
        'patterns': ['Delete*', 'Remove*', 'Format*', 'Destroy*'],
        'forbidden': True
    }
}
```

### Implementation Pattern

```python
class SecurityPolicy:
    def is_method_allowed(self, service: str, interface: str, method: str) -> bool:
        # First check forbidden categories
        category = self._categorize_method(method)
        if category and OPERATION_CATEGORIES[category].get('forbidden'):
            return False
            
        # Check safety level requirements
        if self.safety_level == 'high':
            allowed_categories = ['read_state', 'user_notification', 'media_control']
        elif self.safety_level == 'medium':
            allowed_categories = ['read_state', 'user_notification', 'media_control',
                                'text_input', 'file_navigation', 'window_management']
        else:  # low
            allowed_categories = list(OPERATION_CATEGORIES.keys())
            allowed_categories = [c for c in allowed_categories 
                                 if not OPERATION_CATEGORIES[c].get('forbidden')]
        
        return category in allowed_categories
```

## Profile Integration

Profiles should declare their capabilities in terms of categories:

```python
class KDEArchProfile(SystemProfile):
    def get_safety_capabilities(self) -> Dict[str, List[str]]:
        """Return available operation categories by safety level."""
        return {
            'high': [
                'read_state',      # Read any application state
                'user_notification', # Desktop notifications
                'media_control',    # Media player control
            ],
            'medium': [
                'text_input',       # ✨ Kate, KWrite, etc.
                'file_navigation',  # Dolphin file manager
                'window_management', # KWin window control
            ],
            'low': [
                'process_control',  # systemctl operations
                'system_config',    # KDE settings
            ]
        }
```

## Benefits

1. **Scalable** - New applications automatically work if they follow patterns
2. **Intuitive** - Users understand "text_input" vs specific D-Bus methods  
3. **Maintainable** - Add new categories, not hundreds of endpoints
4. **Discoverable** - Profiles can list their capabilities clearly
5. **Audit-friendly** - Log by category for better security monitoring

## Migration Path

1. Keep existing specific rules for compatibility
2. Add category detection as primary mechanism
3. Fall back to specific rules if no category matches
4. Gradually phase out specific rules