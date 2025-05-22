# D-Bus MCP Server - Discovered Capabilities

## Live System Exploration Results

Based on exploration of a live Arch Linux KDE Plasma system, here are the actual D-Bus services and capabilities discovered:

## Session Bus Services

### 1. Desktop Notifications (org.freedesktop.Notifications)
**Available on**: KDE Plasma via plasmashell
**Key Methods**:
- `Notify(app_name, replaces_id, icon, summary, body, actions, hints, timeout)` - Send notifications
- `CloseNotification(id)` - Close a notification
- `GetCapabilities()` - Query notification capabilities
- `Inhibit()` - Prevent notifications temporarily

### 2. Screenshot Services

#### KDE KWin Screenshot (org.kde.KWin.ScreenShot2)
**Key Methods**:
- `CaptureActiveScreen()` - Screenshot of current screen
- `CaptureActiveWindow()` - Screenshot of active window
- `CaptureArea(x, y, width, height)` - Screenshot of specific area
- `CaptureInteractive()` - User selects area
- `CaptureWorkspace()` - Full workspace screenshot

#### Portal Screenshot (org.freedesktop.portal.Screenshot)
**Key Methods**:
- `Screenshot()` - Take a screenshot
- `PickColor()` - Color picker tool

### 3. Clipboard Management

#### KDE Klipper (org.kde.klipper)
**Key Methods**:
- `getClipboardContents()` - Read clipboard
- `setClipboardContents(text)` - Write to clipboard
- `getClipboardHistoryMenu()` - Get clipboard history
- `clearClipboardContents()` - Clear clipboard
- `getClipboardHistoryItem(index)` - Get specific history item

### 4. Media Player Control

**Pattern**: `org.mpris.MediaPlayer2.*`
**Discovered Players**:
- Chrome browser media (`org.mpris.MediaPlayer2.chromium.instance*`)
- Plasma browser integration

**Standard MPRIS2 Interface** (when properly exposed):
- Play/Pause/Stop
- Next/Previous
- Seek
- Volume control
- Metadata access

### 5. File Management

#### File Manager (org.freedesktop.FileManager1)
**Available via**: Dolphin file manager
- Open folders
- Show items
- Expose file operations

### 6. Desktop Portals (org.freedesktop.portal.Desktop)

**Available Portals**:
- **FileChooser**: Open/Save file dialogs
- **OpenURI**: Open URLs and files safely
- **Email**: Compose emails
- **Settings**: Read desktop settings
- **Background**: Background app permissions
- **Notification**: Alternative notification API
- **Inhibit**: Prevent sleep/screensaver
- **Location**: Location services
- **Camera**: Camera access
- **ScreenCast**: Screen recording
- **RemoteDesktop**: Remote control capabilities

### 7. Power Management

#### KDE PowerDevil (org.freedesktop.PowerManagement)
**Session Bus Access**:
- Screen brightness queries
- Inhibit sleep/screensaver
- Power profile status

### 8. Desktop Environment Services

#### KDE Services:
- `org.kde.ActivityManager` - Virtual desktop activities
- `org.kde.kwalletd6` - Password/secret storage
- `org.kde.JobViewServer` - Progress notifications
- `org.kde.GtkConfig` - GTK theme integration
- `org.kde.KScreen` - Display configuration

## System Bus Services (Read-Only Access)

### 1. Power Information (org.freedesktop.UPower)
**Safe Read Properties**:
- Battery percentage, state, time to empty/full
- AC adapter status
- Lid state (laptop)
- Overall power state

**Example Query**:
```python
# Get battery status
upower.Get('org.freedesktop.UPower.Device', 'Percentage')
upower.Get('org.freedesktop.UPower.Device', 'State')
```

### 2. Network Status (org.freedesktop.NetworkManager)
**Safe Read Properties**:
- Connection state (disconnected/connecting/connected)
- WiFi enabled/disabled status
- Available networks (read-only)
- Active connections
- Network devices

**Writable (requires privilege)**:
- `WirelessEnabled` - Toggle WiFi
- `Enable(bool)` - Enable/disable networking

### 3. Bluetooth (org.bluez)
**Safe Read Operations**:
- List adapters and devices
- Device properties (name, paired, connected)
- Adapter state

### 4. System Information
- `org.freedesktop.hostname1` - Hostname, kernel info
- `org.freedesktop.timedate1` - Time, timezone
- `org.freedesktop.login1` - User sessions, seat info

### 5. Hardware Monitoring
- `org.freedesktop.UDisks2` - Disk information (read-only)
- Various sensor services (temperature, fan speed)

## Discovered Patterns

### 1. Service Naming Conventions
- System services: `org.freedesktop.*`
- KDE services: `org.kde.*`
- Media players: `org.mpris.MediaPlayer2.*`
- Application-specific: Varies widely

### 2. Portal vs Direct Access
Many operations have two paths:
- **Direct**: Application-specific D-Bus interface
- **Portal**: Standardized `org.freedesktop.portal.*` interface

Portals are preferred for:
- Better security (built-in sandboxing support)
- Cross-desktop compatibility
- Standardized APIs

### 3. Permission Models

**No Permission Required** (Session Bus):
- Reading own clipboard
- Sending notifications
- Controlling own media
- Taking screenshots (may show user dialog)

**System Read-Only** (System Bus):
- Battery status
- Network state
- System information

**Requires Privilege**:
- Changing network settings
- Power management actions
- System service control

## Implementation Recommendations

### 1. Priority Tools to Implement

**High Priority** (Most Useful):
- `dbus.notify` - Desktop notifications
- `dbus.screenshot` - Screenshot capture
- `dbus.clipboard_read/write` - Clipboard access
- `dbus.battery_status` - Power information
- `dbus.network_status` - Network state

**Medium Priority**:
- `dbus.media_control` - Media player control
- `dbus.open_uri` - Open URLs/files
- `dbus.file_chooser` - File dialogs
- `dbus.inhibit` - Prevent sleep

**Low Priority**:
- `dbus.activities` - KDE activities
- `dbus.color_picker` - Pick colors
- `dbus.settings_read` - Desktop settings

### 2. Desktop-Specific Considerations

**KDE Plasma** (discovered):
- Rich D-Bus integration
- KWin for screenshots
- Klipper for clipboard
- PowerDevil for power management

**GNOME** (would have):
- GNOME Shell for screenshots
- Different clipboard mechanism
- Different power management

**Recommendation**: Use portals when available for cross-desktop compatibility.

### 3. Security Insights

**Observed Permission Model**:
- Session bus: Generally permissive for user operations
- System bus: Restricted, mostly read-only
- No built-in rate limiting (must implement)
- Some operations show user dialogs (screenshots)

### 4. Real-World Limitations

**Cannot Access**:
- Other users' sessions
- System services without PolicyKit
- Root-only operations
- Direct hardware access

**Unexpected Findings**:
- Many browsers expose MPRIS media control
- Screenshot services vary by compositor
- Clipboard has history in KDE
- Portal interfaces are widely available

## Testing Commands Used

```bash
# List all services
busctl list
busctl --user list

# Introspect services
busctl --user introspect org.freedesktop.Notifications /org/freedesktop/Notifications
busctl introspect org.freedesktop.UPower /org/freedesktop/UPower

# Find specific services
busctl --user list | grep -i screenshot
busctl --user list | grep -i mpris

# Test method calls (examples)
busctl --user call org.freedesktop.Notifications /org/freedesktop/Notifications \
    org.freedesktop.Notifications Notify \
    susssasa{sv}i "test" 0 "" "Test" "Hello from busctl" 0 0 5000
```

## Conclusions

1. **Rich Ecosystem**: Modern Linux desktops expose extensive D-Bus APIs
2. **Portal Adoption**: Freedesktop portals provide good standardization
3. **Security by Default**: System bus properly restricts dangerous operations
4. **Desktop Variance**: Significant differences between KDE/GNOME/others
5. **Practical Focus**: Most useful operations are on session bus