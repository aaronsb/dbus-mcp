# D-Bus MCP Server - Tool Presentation Strategy

## The Challenge

D-Bus is vast. A typical Linux desktop has 100+ services exposing thousands of methods. We could create tools for everything, but this would overwhelm AI clients with choices, leading to:
- Decision paralysis
- Incorrect tool selection
- Poor performance (too many tools to consider)
- Confusion about similar tools

## Design Principles

### 1. Progressive Disclosure
Start minimal, expand based on need:
```
Core Tools (5-10) → Common Tools (20-30) → Specialized Tools (on demand)
```

### 2. Semantic Tool Names
Tools should be self-documenting through their names:
```
❌ Bad:  "dbus.call"
✅ Good: "dbus.clipboard.read"
✅ Good: "dbus.notify.send"
✅ Good: "dbus.system.service.status"
```

### 3. Tool Categories
Organize tools into logical groups:

```python
TOOL_CATEGORIES = {
    "discovery": {
        "description": "Explore available D-Bus services",
        "tools": ["list_services", "introspect", "find_interface"]
    },
    "desktop": {
        "description": "Interact with desktop environment",
        "tools": ["notify", "clipboard.read", "clipboard.write", "screenshot"]
    },
    "media": {
        "description": "Control media playback",
        "tools": ["media.list_players", "media.control", "media.get_info"]
    },
    "system": {
        "description": "Monitor system state (read-only)",
        "tools": ["power.battery_status", "network.get_state", "system.load_average"]
    },
    "services": {
        "description": "Manage system services",
        "tools": ["systemd.list_units", "systemd.get_status", "journal.query"]
    }
}
```

## Tool Presentation Strategies

### Strategy 1: Minimal Core Set
Start with only the most essential tools:

```json
{
  "tools": [
    {
      "name": "dbus.discover",
      "description": "Discover available D-Bus capabilities on this system",
      "inputSchema": {
        "type": "object",
        "properties": {
          "category": {
            "type": "string",
            "enum": ["desktop", "media", "system", "services"],
            "description": "Category to explore, or omit for all"
          }
        }
      }
    },
    {
      "name": "dbus.notify",
      "description": "Send desktop notification to user",
      "inputSchema": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "message": {"type": "string"},
          "urgency": {"type": "string", "enum": ["low", "normal", "critical"]}
        },
        "required": ["title", "message"]
      }
    },
    {
      "name": "dbus.clipboard.read",
      "description": "Read current clipboard contents"
    },
    {
      "name": "dbus.system.status",
      "description": "Get system status overview (battery, network, load)"
    },
    {
      "name": "dbus.help",
      "description": "Get help about available D-Bus tools and categories"
    }
  ]
}
```

### Strategy 2: Dynamic Tool Loading
Load tools based on discovered services:

```python
class DynamicToolLoader:
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        self.base_tools = ["discover", "help", "list_services"]
        
    async def load_tools_for_context(self):
        """Load tools based on what's actually available"""
        
        # Always load base tools
        for tool in self.base_tools:
            self.mcp_server.add_tool(tool)
        
        # Check what's available and load accordingly
        if await self.has_desktop_session():
            self.load_desktop_tools()
            
        if await self.has_media_players():
            self.load_media_tools()
            
        if await self.has_systemd():
            self.load_system_tools()
```

### Strategy 3: Hierarchical Tool Structure
Present tools in a hierarchy to reduce cognitive load:

```json
{
  "name": "dbus",
  "description": "Interact with D-Bus services",
  "subcommands": {
    "clipboard": {
      "description": "Clipboard operations",
      "subcommands": {
        "read": {"description": "Read clipboard contents"},
        "write": {"description": "Write to clipboard"},
        "history": {"description": "Get clipboard history"}
      }
    },
    "notify": {
      "description": "Send desktop notification",
      "parameters": ["title", "message", "urgency"]
    },
    "system": {
      "description": "System information",
      "subcommands": {
        "battery": {"description": "Battery status"},
        "network": {"description": "Network status"},
        "services": {"description": "Service management"}
      }
    }
  }
}
```

### Strategy 4: Context-Aware Tool Filtering
Only show tools relevant to current context:

```python
class ContextAwareToolFilter:
    def get_tools_for_prompt(self, prompt: str) -> List[Tool]:
        """Return only tools relevant to the user's request"""
        
        keywords = self.extract_keywords(prompt)
        
        if any(word in keywords for word in ["clipboard", "copy", "paste"]):
            return self.clipboard_tools
            
        if any(word in keywords for word in ["notify", "alert", "remind"]):
            return self.notification_tools
            
        if any(word in keywords for word in ["battery", "power", "charging"]):
            return self.power_tools
            
        # Default to discovery tools
        return self.discovery_tools
```

## Recommended Approach: Hybrid Model

### 1. Core Tools (Always Available)
```python
CORE_TOOLS = {
    "dbus.discover": "Explore available D-Bus capabilities",
    "dbus.notify": "Send desktop notifications", 
    "dbus.clipboard.read": "Read clipboard contents",
    "dbus.clipboard.write": "Write to clipboard",
    "dbus.system.quick_status": "Get battery, network, and system status"
}
```

### 2. Category-Based Expansion
```python
TOOL_CATEGORIES = {
    "desktop": ["screenshot", "media_control", "open_uri"],
    "system": ["service_status", "journal_query", "network_details"],
    "advanced": ["call_method", "introspect", "monitor_signals"]
}
```

### 3. Smart Tool Descriptions
Include usage hints in descriptions:

```python
tools = [
    {
        "name": "dbus.clipboard.read",
        "description": "Read current clipboard contents. Use this when user asks to 'get what I copied' or needs clipboard data.",
        "examples": ["What's in my clipboard?", "Use what I just copied"]
    },
    {
        "name": "dbus.notify",
        "description": "Send desktop notification. Use for alerts, reminders, or important status updates.",
        "examples": ["Remind me in 5 minutes", "Alert when build completes"]
    }
]
```

### 4. Tool Discovery Flow
```
User: "Help me manage my system"
  ↓
AI uses: dbus.discover(category="system")
  ↓
Returns: Available system tools for this specific machine
  ↓
AI can now use: systemd.*, journal.*, network.* tools
```

## Anti-Patterns to Avoid

### 1. Tool Explosion
❌ Don't create a tool for every D-Bus method:
```
dbus.org_freedesktop_NetworkManager_GetDevices
dbus.org_freedesktop_NetworkManager_GetActiveConnections
dbus.org_freedesktop_NetworkManager_GetConnectivity
```

✅ Do create logical tools:
```
dbus.network.get_status (combines multiple calls)
```

### 2. Over-Generic Tools
❌ Don't make tools too generic:
```
dbus.call(service, object, interface, method, args)
```

✅ Do make tools specific to use cases:
```
dbus.notify.send(title, message)
dbus.clipboard.read()
```

### 3. Unclear Tool Boundaries
❌ Don't have overlapping tools:
```
dbus.get_clipboard
dbus.read_clipboard  
dbus.clipboard_contents
```

✅ Do have clear, single-purpose tools:
```
dbus.clipboard.read
dbus.clipboard.write
```

## Implementation Example

```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.categories = defaultdict(list)
        
    def register_tool(self, tool, category="general", requires=None):
        """Register a tool with metadata"""
        self.tools[tool.name] = {
            "tool": tool,
            "category": category,
            "requires": requires or [],
            "usage_count": 0
        }
        self.categories[category].append(tool.name)
        
    def get_initial_tools(self):
        """Get minimal set of tools for AI"""
        return [
            self.tools["dbus.discover"]["tool"],
            self.tools["dbus.notify"]["tool"],
            self.tools["dbus.clipboard.read"]["tool"],
            self.tools["dbus.help"]["tool"]
        ]
        
    def get_tools_for_category(self, category):
        """Get all tools in a category"""
        return [self.tools[name]["tool"] for name in self.categories[category]]
        
    def track_usage(self, tool_name):
        """Track tool usage for adaptive loading"""
        self.tools[tool_name]["usage_count"] += 1
```

## Conclusion

The key to good tool presentation is:
1. Start minimal (5-10 core tools)
2. Use clear, hierarchical naming
3. Provide excellent descriptions with examples
4. Allow progressive discovery
5. Group related functionality
6. Track usage patterns

This approach prevents overwhelming the AI while still providing access to D-Bus's full power when needed.