# D-Bus MCP Server - Usage Examples

## Example Use Cases

### 1. Desktop Automation Workflow

**Scenario**: AI assistant helps manage daily tasks

```typescript
// AI Assistant interacting with D-Bus MCP

// Check what music is playing
const currentMedia = await mcp.use("dbus.media_control", {
  action: "get_metadata",
  player: "spotify"
});

// Send a notification
await mcp.use("dbus.notify", {
  summary: "Daily Standup",
  body: "Your daily standup meeting starts in 5 minutes",
  icon: "appointment-reminder",
  urgency: 2
});

// Take a screenshot of current work
const screenshot = await mcp.use("dbus.screenshot", {
  area: "window",
  save_to: "/tmp/work-progress.png"
});

// Copy meeting link to clipboard
await mcp.use("dbus.clipboard_write", {
  text: "https://meet.company.com/daily-standup",
  type: "text/plain"
});
```

### 2. System Monitoring Assistant

**Scenario**: AI monitors system health and alerts

```python
# List system services
services = await mcp.use("dbus.list_services", {
    "bus": "system",
    "filter": "org.freedesktop.systemd1.*"
})

# Check NetworkManager status
network_status = await mcp.use("dbus.get_property", {
    "bus": "system",
    "service": "org.freedesktop.NetworkManager",
    "object": "/org/freedesktop/NetworkManager",
    "interface": "org.freedesktop.NetworkManager",
    "property": "State"
})

# Monitor battery level
battery = await mcp.use("dbus.get_property", {
    "bus": "system", 
    "service": "org.freedesktop.UPower",
    "object": "/org/freedesktop/UPower/devices/battery_BAT0",
    "interface": "org.freedesktop.UPower.Device",
    "property": "Percentage"
})

if battery["value"] < 20:
    await mcp.use("dbus.notify", {
        "summary": "Low Battery Warning",
        "body": f"Battery at {battery['value']}%. Please connect charger.",
        "urgency": 2,
        "icon": "battery-low"
    })
```

### 3. Development Workflow Integration

**Scenario**: AI assists with development tasks

```javascript
// Get list of running development tools
const apps = await mcp.use("dbus.list_applications", {
  filter: ["code", "terminal", "firefox"]
});

// Copy error message from terminal
const terminalContent = await mcp.use("dbus.call_method", {
  bus: "session",
  service: "org.gnome.Terminal",
  object: "/org/gnome/Terminal/window/1",
  interface: "org.gnome.Terminal.Window",
  method: "GetSelectedText"
});

// Search for the error
const searchUrl = `https://stackoverflow.com/search?q=${encodeURIComponent(terminalContent)}`;
await mcp.use("dbus.clipboard_write", {
  text: searchUrl
});

// Notify when build completes
await mcp.use("dbus.notify", {
  summary: "Build Complete",
  body: "Your project build finished successfully",
  icon: "emblem-default",
  actions: [
    { id: "open", label: "Open Project" },
    { id: "test", label: "Run Tests" }
  ]
});
```

### 4. Media Control Automation

**Scenario**: Smart media management

```python
# Get all media players
players = await mcp.use("dbus.list_services", {
    "bus": "session",
    "filter": "org.mpris.MediaPlayer2.*"
})

# Check what's playing
for player in players:
    metadata = await mcp.use("dbus.media_control", {
        "player": player,
        "action": "get_metadata"
    })
    
    if metadata["PlaybackStatus"] == "Playing":
        # Pause during meeting
        await mcp.use("dbus.media_control", {
            "player": player,
            "action": "pause"
        })
        
        await mcp.use("dbus.notify", {
            "summary": "Media Paused",
            "body": f"Paused {metadata['title']} for your meeting"
        })
```

### 5. Clipboard History Manager

**Scenario**: AI helps manage clipboard content

```typescript
// Read current clipboard
const current = await mcp.use("dbus.clipboard_read", {
  type: "text/plain"
});

// Store in history
clipboardHistory.push({
  content: current.text,
  timestamp: new Date(),
  application: current.source_application
});

// Smart paste based on context
if (context.includes("email")) {
  // Find email addresses in history
  const emails = clipboardHistory.filter(item => 
    item.content.match(/[\w._%+-]+@[\w.-]+\.[A-Z]{2,}/i)
  );
  
  if (emails.length > 0) {
    await mcp.use("dbus.clipboard_write", {
      text: emails[0].content
    });
  }
}
```

### 6. Window Management

**Scenario**: Organize desktop workspace

```python
# Get window list
windows = await mcp.use("dbus.call_method", {
    "bus": "session",
    "service": "org.gnome.Shell",
    "object": "/org/gnome/Shell",
    "interface": "org.gnome.Shell",
    "method": "GetWindows"
})

# Find browser windows
browser_windows = [w for w in windows if "firefox" in w["app_id"].lower()]

# Move to specific workspace
for window in browser_windows:
    await mcp.use("dbus.call_method", {
        "bus": "session",
        "service": "org.gnome.Shell",
        "object": "/org/gnome/Shell",
        "interface": "org.gnome.Shell.Window",
        "method": "MoveToWorkspace",
        "args": [window["id"], 2]  # Move to workspace 2
    })
```

## Error Handling Examples

```typescript
try {
  await mcp.use("dbus.call_method", {
    bus: "system",
    service: "org.freedesktop.NetworkManager",
    method: "Enable",
    args: [true]
  });
} catch (error) {
  if (error.code === "PERMISSION_DENIED") {
    await mcp.use("dbus.notify", {
      summary: "Permission Required",
      body: "This operation requires administrator privileges",
      icon: "dialog-password"
    });
  } else if (error.code === "SERVICE_NOT_FOUND") {
    console.log("NetworkManager is not running");
  }
}
```

## Best Practices

1. **Always check service availability**
   ```typescript
   const services = await mcp.use("dbus.list_services");
   if (services.includes("org.mpris.MediaPlayer2.spotify")) {
     // Safe to use Spotify controls
   }
   ```

2. **Handle async signals properly**
   ```typescript
   const subscription = await mcp.use("dbus.subscribe_signal", {
     bus: "session",
     interface: "org.freedesktop.Notifications",
     signal: "NotificationClosed",
     callback: (id, reason) => {
       console.log(`Notification ${id} closed: ${reason}`);
     }
   });
   ```

3. **Use introspection for discovery**
   ```typescript
   const introspection = await mcp.use("dbus.introspect", {
     bus: "session",
     service: "org.gnome.Calculator",
     object: "/org/gnome/Calculator"
   });
   // Use introspection data to understand available methods
   ```

4. **Batch operations when possible**
   ```typescript
   const batch = await mcp.use("dbus.batch", {
     operations: [
       { tool: "dbus.notify", args: { summary: "Task 1 Complete" } },
       { tool: "dbus.notify", args: { summary: "Task 2 Complete" } },
       { tool: "dbus.notify", args: { summary: "All Tasks Done!" } }
     ],
     delay: 1000  // 1 second between operations
   });
   ```