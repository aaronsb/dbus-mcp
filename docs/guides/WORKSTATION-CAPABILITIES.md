# Workstation Capabilities Guide

This guide documents the capabilities available for workstation (desktop/laptop) systems at different safety levels.

## 🟡 MEDIUM Safety Level Capabilities

### Text Editor Integration (Kate)

**What it does**: Send text directly to the Kate text editor

**How to enable**: 
```bash
# Configure Claude Code
claude mcp add dbus-mcp /path/to/venv/bin/python -- -m dbus_mcp --safety-level medium

# Or run directly
python -m dbus_mcp --safety-level medium
```

**Example usage**:
```python
# The AI can now write text to Kate
await call_method(
    service="org.kde.kate-1157225",  # Note: PID suffix varies
    path="/MainApplication",
    interface="org.kde.Kate.Application",
    method="openInput",
    args=["Hello from Claude!", "utf-8"]
)
```

**Current implementation** (to be replaced with category-based):
```python
# In security.py - matches any Kate instance
('org.kde.kate', 'org.kde.Kate.Application', 'openInput'),
('org.kde.kate', 'org.kde.Kate.Application', 'activate'),
```

### Other MEDIUM Safety Operations

- **File Manager** - Show files/folders in Dolphin
- **Browser** - Open URLs in default browser  
- **Window Management** - Focus/activate application windows

## 🟢 HIGH Safety Level Capabilities (Default)

These are always available:

### Clipboard Operations
- Read clipboard contents
- Write text to clipboard
- Detect non-text content

### Desktop Notifications
- Send desktop notifications with urgency levels
- Close notifications

### Media Control
- Play/pause media
- Next/previous track

### System Status
- Read battery level
- Check network status
- Query system information

## Architecture Notes

### Why Safety Levels Matter

Safety levels prevent accidental or malicious:
- Data loss (no delete operations at HIGH/MEDIUM)
- Privacy breaches (no screenshot at HIGH)
- System disruption (no service restart at HIGH)
- Unwanted automation (no arbitrary text input at HIGH)

### Current Pattern (Being Improved)

The current implementation uses explicit endpoint matching:

```python
def is_method_allowed(self, service: str, interface: str, method: str) -> bool:
    # Check against specific operations
    medium_safety_operations = [
        ('org.kde.kate', 'org.kde.Kate.Application', 'openInput'),
        # ... more specific endpoints
    ]
    
    for safe_service, safe_interface, safe_method in medium_safety_operations:
        if service.startswith(safe_service) and \
           interface == safe_interface and \
           method == safe_method:
            return True
```

**Problems with this approach**:
- Requires updating for every new application
- Service names include PIDs (e.g., `org.kde.kate-1157225`)
- Not discoverable - users don't know what's allowed

### Future: Category-Based Security

See [SECURITY-CATEGORIES.md](../architecture/SECURITY-CATEGORIES.md) for the proposed improvement that will:
- Automatically allow operations based on patterns
- Make capabilities discoverable
- Reduce maintenance burden