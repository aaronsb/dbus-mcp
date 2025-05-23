# D-Bus Application Support Guide

Based on comprehensive research of Linux applications with D-Bus support, this guide maps applications to our security categories and helps expand our pattern-based security model.

## Security Category Mappings

### 🟢 HIGH Safety - Read Operations & Notifications

**Media Control** (`media_control` category):
- Amarok, Rhythmbox, Banshee, Clementine, VLC
- Pattern matches: `Play`, `Pause`, `Next`, `Previous`, `Stop`
- Examples: Control music playback without system changes

**Status Reading** (`read_state` category):
- All KDE/GNOME apps status queries
- Pattern matches: `Get*`, `List*`, `Query*`, `Is*`, `Has*`
- Examples: Get current song, check email count, list open documents

**Desktop Notifications** (`user_notification` category):
- All apps using org.freedesktop.Notifications
- Pattern matches: `Notify`, `ShowNotification`
- Safe for all applications

### 🟡 MEDIUM Safety - Productivity Operations

**Text Input** (`text_input` category):
Applications:
- Kate, KWrite, Gedit, Emacs
- Konsole, GNOME Terminal, Terminator
- Pidgin, Kopete (chat messages)
- KMail (compose emails)

Enhanced patterns:
```python
'text_input': {
    'patterns': ['*Input*', 'InsertText', 'TypeText', 'SendKeys', 
                 'SetText*', 'sendText', 'runCommand', 'SendMessage',
                 'ComposeEmail', 'WriteDocument'],
    'safety_level': 'medium'
}
```

**File Navigation** (`file_navigation` category):
Applications:
- Dolphin, Nautilus, Konqueror, Thunar, Krusader
- Okular, Evince (open documents)
- Gwenview, digiKam (browse photos)

Enhanced patterns:
```python
'file_navigation': {
    'patterns': ['Open*', 'Show*', 'Navigate*', 'Browse*', 
                 'Reveal*', 'Display*', 'Load*', 'View*'],
    'safety_level': 'medium'
}
```

**Window Management** (`window_management` category):
Applications:
- KWin, Compiz, GNOME Shell
- All KDE/GNOME applications with window control

### 🔴 LOW Safety - System Administration

**Process Control** (`process_control` category):
- systemd services
- GNOME System Monitor
- KSysGuard

**Network Configuration** (`network_config` category):
- NetworkManager
- wpa_supplicant
- Network configuration tools

## Application-Specific Patterns

### KDE Applications (org.kde.*)
Most comprehensive D-Bus support. Standard patterns:
- `openUrl()` - Open files/URLs
- `activate()` - Focus window
- `saveDocument()` - Save changes
- `quit()` - Close application

### GNOME Applications (org.gnome.*)
More limited but consistent:
- Basic window management
- File operations
- Status queries

### Media Players (org.mpris.MediaPlayer2.*)
Standardized MPRIS2 interface:
- `/org/mpris/MediaPlayer2` - Player control
- Consistent across all players

## Expanding Security Categories

Based on the application survey, we should add these categories:

```python
# Additional categories for comprehensive support

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

'archive_operations': {
    'description': 'Compress and extract files',
    'patterns': ['Extract*', 'Compress*', 'AddToArchive'],
    'safety_level': 'medium'
},

'search_operations': {
    'description': 'Search for files and content',
    'patterns': ['Search*', 'Find*', 'Locate*', 'QueryIndex'],
    'safety_level': 'high'  # Read-only searching
},

'session_management': {
    'description': 'Desktop session control',
    'patterns': ['LockScreen', 'Logout', 'SwitchUser', 'StartScreensaver'],
    'safety_level': 'low'
}
```

## Implementation Guidelines

### 1. Service Name Patterns
Many KDE apps use dynamic service names with PIDs:
- `org.kde.kate-1234` → Check prefix `org.kde.kate`
- `org.mpris.MediaPlayer2.app_name` → Check prefix

### 2. Interface Naming Conventions
- KDE: `org.kde.AppName.Interface`
- GNOME: `org.gnome.AppName`
- FreeDesktop: `org.freedesktop.StandardName`

### 3. Method Naming Patterns
Consistent patterns across ecosystems:
- **KDE**: `openUrl()`, `saveDocument()`, `quit()`
- **GNOME**: `Open()`, `Save()`, `Close()`
- **FreeDesktop**: Standardized interfaces

## Testing Application Support

To test if an application is supported:

1. Check if service is running:
   ```bash
   busctl list | grep appname
   ```

2. Introspect to find methods:
   ```bash
   busctl introspect org.kde.appname /
   ```

3. Match methods against our categories:
   - Does `openFile()` match `Open*`? → Yes, `file_navigation`
   - Does `sendText()` match any pattern? → No, needs special case

## Recommendations

1. **Prioritize KDE Apps**: They have the richest D-Bus interfaces
2. **Use Standard Interfaces**: MPRIS2 for media, org.freedesktop.* for system
3. **Add Special Cases**: For valuable operations that don't match patterns
4. **Test Real Apps**: Validate patterns against actual D-Bus methods

## Common Application Examples

### Text Editor (Kate)
- ✅ `openInput()` → Matches `*Input*` → `text_input` category
- ✅ `openUrl()` → Matches `Open*` → `file_navigation` category
- ❌ `activate()` → Doesn't match patterns → Needs special case

### File Manager (Dolphin)
- ✅ `ShowFolders()` → Matches `Show*` → `file_navigation` category
- ✅ `ShowItems()` → Matches `Show*` → `file_navigation` category

### Terminal (Konsole)
- ❌ `sendText()` → Doesn't match `*Input*` → Needs pattern update
- ✅ `runCommand()` → Could match `run*` → Needs new category?

This mapping helps us support the rich ecosystem of Linux applications while maintaining security through categorical permissions.