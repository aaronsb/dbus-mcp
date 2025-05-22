# D-Bus MCP Server - Context Examples

## Real-World Context Scenarios

### Scenario 1: Media Control (Session Bus Only)

**Context**: User wants AI to pause music during a meeting

```python
# ✅ SAFE - Entirely in user session context
async def handle_media_pause(mcp_request):
    """Runs as regular user, affects only their media"""
    
    # No special privileges needed
    session_bus = SessionBus()
    
    # Find all media players
    players = [
        name for name in session_bus.list_names()
        if name.startswith('org.mpris.MediaPlayer2.')
    ]
    
    # Pause each one
    for player in players:
        try:
            player_obj = session_bus.get(player, '/org/mpris/MediaPlayer2')
            player_obj.Pause()
        except:
            # Player might have disappeared
            pass
    
    return {"paused_players": len(players)}
```

### Scenario 2: Battery Monitoring (System Bus Read-Only)

**Context**: AI monitors battery and alerts user

```python
# ✅ SAFE - Read-only system information
async def handle_battery_check(mcp_request):
    """Runs as regular user, reads system info"""
    
    # Connect to system bus (no special privileges)
    system_bus = SystemBus()
    
    try:
        # Read-only access to UPower
        upower = system_bus.get(
            'org.freedesktop.UPower',
            '/org/freedesktop/UPower/devices/DisplayDevice'
        )
        
        # These are read-only properties
        battery_info = {
            'percentage': upower.Percentage,
            'is_charging': upower.State == 1,
            'time_to_empty': upower.TimeToEmpty,
            'time_to_full': upower.TimeToFull
        }
        
        # Send notification if low (via session bus)
        if battery_info['percentage'] < 20 and not battery_info['is_charging']:
            session_bus = SessionBus()
            notifier = session_bus.get('org.freedesktop.Notifications')
            notifier.Notify(
                'dbus-mcp', 0, 'battery-low',
                'Low Battery Warning',
                f"Battery at {battery_info['percentage']}%",
                [], {}, -1
            )
        
        return battery_info
        
    except Exception as e:
        # Never expose system errors
        return {"error": "Unable to read battery status"}
```

### Scenario 3: Network Status (Mixed Context)

**Context**: Check network status (read) and toggle WiFi (privileged)

```python
# Part 1: ✅ SAFE - Read network status
async def handle_network_status(mcp_request):
    """Read-only network information"""
    
    system_bus = SystemBus()
    
    try:
        nm = system_bus.get('org.freedesktop.NetworkManager')
        
        # All read-only properties
        return {
            'state': nm.State,  # 70 = connected
            'connectivity': nm.Connectivity,  # 4 = full
            'wifi_enabled': nm.WirelessEnabled,
            'wifi_hardware_enabled': nm.WirelessHardwareEnabled,
            'networking_enabled': nm.NetworkingEnabled
        }
    except:
        return {"error": "Unable to read network status"}

# Part 2: ⚠️  PRIVILEGED - Toggle WiFi
async def handle_wifi_toggle(mcp_request, enable: bool):
    """Requires privileged helper"""
    
    # First, check if we even need to change it
    current_status = await handle_network_status(mcp_request)
    if current_status.get('wifi_enabled') == enable:
        return {"status": "already_set", "wifi_enabled": enable}
    
    # Request privileged operation via helper
    async with connect_to_helper() as helper:
        try:
            # Helper will check PolicyKit authorization
            result = await helper.request({
                'action': 'toggle_wifi',
                'params': {'enable': enable},
                'user': mcp_request.user,
                'request_id': mcp_request.id
            })
            
            if result['authorized']:
                return {"status": "success", "wifi_enabled": enable}
            else:
                return {"status": "unauthorized", "message": "User denied permission"}
                
        except HelperTimeout:
            return {"status": "error", "message": "Operation timed out"}
```

### Scenario 4: Screenshot (Session Bus with Filesystem Access)

**Context**: Take screenshot and provide to AI

```python
# ✅ SAFE - Session bus operation with controlled file access
async def handle_screenshot(mcp_request, area='full'):
    """Takes screenshot via session bus"""
    
    session_bus = SessionBus()
    
    # Use desktop portal (safer than direct X11 access)
    portal = session_bus.get(
        'org.freedesktop.portal.Desktop',
        '/org/freedesktop/portal/desktop'
    )
    
    # Create unique filename in allowed directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"/tmp/dbus-mcp/screenshot_{timestamp}.png"
    
    # Ensure directory exists (created at startup with proper permissions)
    os.makedirs('/tmp/dbus-mcp', exist_ok=True, mode=0o700)
    
    try:
        if area == 'full':
            portal.Screenshot('', {'interactive': False})
        elif area == 'selection':
            portal.Screenshot('', {'interactive': True})
        
        # Move portal's screenshot to our location
        # Portal saves to XDG_PICTURES_DIR by default
        import shutil
        portal_file = f"{os.environ['HOME']}/Pictures/Screenshot.png"
        shutil.move(portal_file, filename)
        
        # Set restrictive permissions
        os.chmod(filename, 0o600)
        
        return {
            "status": "success",
            "filename": filename,
            "size": os.path.getsize(filename)
        }
        
    except Exception as e:
        return {"status": "error", "message": "Screenshot failed"}
```

### Scenario 5: Forbidden Operations (Always Denied)

**Context**: Various dangerous operations that must be rejected

```python
# ❌ FORBIDDEN - System shutdown
async def handle_shutdown_request(mcp_request):
    """NEVER ALLOWED - Hard-coded rejection"""
    
    # Log attempt for security monitoring
    security_logger.warning(
        f"Shutdown attempt from user {mcp_request.user} "
        f"via request {mcp_request.id}"
    )
    
    # Always return error
    return {
        "status": "forbidden",
        "message": "System power operations are not permitted",
        "suggestion": "Use your desktop environment's shutdown dialog"
    }

# ❌ FORBIDDEN - Package installation
async def handle_package_install(mcp_request, package_name):
    """NEVER ALLOWED - No package management"""
    
    security_logger.warning(
        f"Package install attempt: {package_name} from {mcp_request.user}"
    )
    
    return {
        "status": "forbidden",
        "message": "Package management operations are not permitted",
        "suggestion": "Install packages using your system's package manager"
    }

# ❌ FORBIDDEN - Disk operations
async def handle_disk_format(mcp_request, device):
    """NEVER ALLOWED - No disk operations"""
    
    # This is a critical security event
    security_logger.critical(
        f"DISK FORMAT ATTEMPT: {device} from {mcp_request.user}"
    )
    
    # Alert system administrator
    await send_security_alert(
        level="CRITICAL",
        message=f"Disk format attempt blocked for device {device}"
    )
    
    return {
        "status": "forbidden",
        "message": "Disk operations are strictly forbidden",
        "security_event": "logged_and_reported"
    }
```

## Context Decision Tree

```python
def determine_context_requirements(service, interface, method):
    """Determine what context/privileges are needed"""
    
    # Level 0: User context (session bus)
    if service.startswith('org.mpris.'):
        return ContextLevel.USER
    if service == 'org.freedesktop.Notifications':
        return ContextLevel.USER
    if service == 'org.freedesktop.portal.':
        return ContextLevel.USER
    
    # Level 1: System read-only
    if service == 'org.freedesktop.UPower' and method.startswith('Get'):
        return ContextLevel.SYSTEM_READ
    if service == 'org.freedesktop.NetworkManager' and method == 'GetDevices':
        return ContextLevel.SYSTEM_READ
    
    # Level 2: Privileged (via helper)
    if service == 'org.freedesktop.NetworkManager' and method in ['Enable', 'Sleep']:
        return ContextLevel.PRIVILEGED
    if 'brightness' in method.lower():
        return ContextLevel.PRIVILEGED
    
    # Level 3: Forbidden
    if method in ['Shutdown', 'Reboot', 'PowerOff', 'Suspend']:
        return ContextLevel.FORBIDDEN
    if 'Format' in method or 'Delete' in method:
        return ContextLevel.FORBIDDEN
    if service == 'org.freedesktop.PackageKit':
        return ContextLevel.FORBIDDEN
    
    # Default: Deny
    return ContextLevel.FORBIDDEN
```

## Testing Different Contexts

```bash
# Test user context operations
$ dbus-mcp-client call media.pause
✅ Success: All media players paused

# Test system read operations  
$ dbus-mcp-client call battery.status
✅ Success: Battery at 67%, charging

# Test privileged operation (will prompt for auth)
$ dbus-mcp-client call wifi.toggle --enable=false
🔐 Authentication required...
✅ Success: WiFi disabled

# Test forbidden operation
$ dbus-mcp-client call system.shutdown
❌ Forbidden: System power operations are not permitted
```

## Key Takeaways

1. **Most operations run in user context** - No special privileges needed
2. **System bus access is read-only** - Information gathering only
3. **Privileged operations use PolicyKit** - User must authorize
4. **Dangerous operations are hard-blocked** - No amount of authorization allows them
5. **Each context has specific safeguards** - Rate limits, timeouts, validation
6. **Errors never expose system details** - Generic messages for security