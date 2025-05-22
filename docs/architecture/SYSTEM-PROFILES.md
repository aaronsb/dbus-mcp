# D-Bus MCP Server - System Profiles Architecture

## Concept

System profiles act as an abstraction layer between the pure D-Bus implementation and the specific Linux environment. This allows the MCP server to adapt to different distributions, desktop environments, and system configurations without modifying core code.

## Problem Space

Linux diversity means:
- **KDE Plasma** uses Klipper for clipboard, KWin for screenshots
- **GNOME** uses Mutter for screenshots, different clipboard mechanism  
- **Arch** has different service names than Ubuntu
- **Wayland vs X11** changes available interfaces
- **Embedded systems** have completely different services

## Architecture

```
┌─────────────────────────────────────────────┐
│             MCP Client (AI)                 │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│           D-Bus MCP Server Core             │
│  ┌─────────────────────────────────────┐   │
│  │        Profile Manager               │   │
│  │  ┌─────────┐ ┌─────────┐ ┌────────┐│   │
│  │  │ KDE/Arch│ │GNOME/   │ │Server/ ││   │
│  │  │ Profile │ │Ubuntu   │ │Generic ││   │
│  │  └─────────┘ └─────────┘ └────────┘│   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│        Actual D-Bus Services                │
└─────────────────────────────────────────────┘
```

## Profile Structure

```python
# profiles/base.py
class SystemProfile:
    """Base class for system profiles"""
    
    @property
    def name(self) -> str:
        return "base"
    
    @property
    def description(self) -> str:
        return "Base system profile"
    
    def get_clipboard_service(self) -> ClipboardAdapter:
        """Return clipboard adapter for this system"""
        raise NotImplementedError
        
    def get_screenshot_service(self) -> ScreenshotAdapter:
        """Return screenshot adapter for this system"""
        raise NotImplementedError
        
    def get_notification_service(self) -> NotificationAdapter:
        """Return notification adapter for this system"""
        return FreedesktopNotificationAdapter()  # Common standard
        
    def get_media_pattern(self) -> str:
        """Return D-Bus pattern for media players"""
        return "org.mpris.MediaPlayer2.*"  # Standard MPRIS
        
    def detect_environment(self) -> Dict[str, Any]:
        """Detect system environment details"""
        return {
            "distro": self._detect_distro(),
            "desktop": self._detect_desktop(),
            "display_server": self._detect_display_server(),
            "init_system": self._detect_init_system()
        }
```

## Example Profiles

### KDE/Arch Profile
```python
# profiles/kde_arch.py
class KDEArchProfile(SystemProfile):
    """Profile for KDE Plasma on Arch Linux"""
    
    @property
    def name(self) -> str:
        return "kde-arch"
        
    def get_clipboard_service(self) -> ClipboardAdapter:
        return KlipperAdapter()
        
    def get_screenshot_service(self) -> ScreenshotAdapter:
        if self.is_wayland():
            return SpectacleAdapter()  # KDE's screenshot tool
        else:
            return KWinScreenshotAdapter()
            
    def get_system_packages_tool(self) -> Optional[PackageAdapter]:
        return PacmanAdapter()  # Arch-specific
        
    def get_desktop_specific_tools(self) -> List[Tool]:
        """KDE-specific tools"""
        return [
            KDEActivitiesTools(),
            KDEVaultsTools(),
            PowerDevilTools(),
            KRunnerTools()
        ]
```

### GNOME/Ubuntu Profile
```python
# profiles/gnome_ubuntu.py
class GNOMEUbuntuProfile(SystemProfile):
    """Profile for GNOME on Ubuntu"""
    
    @property
    def name(self) -> str:
        return "gnome-ubuntu"
        
    def get_clipboard_service(self) -> ClipboardAdapter:
        return GNOMEClipboardAdapter()
        
    def get_screenshot_service(self) -> ScreenshotAdapter:
        return GNOMEScreenshotAdapter()
        
    def get_system_packages_tool(self) -> Optional[PackageAdapter]:
        return AptAdapter()  # Debian/Ubuntu specific
        
    def get_desktop_specific_tools(self) -> List[Tool]:
        return [
            GNOMEExtensionsTools(),
            GSettingsTools(),
            TrackerTools()  # GNOME's search
        ]
```

### Server/Headless Profile
```python
# profiles/server.py
class ServerProfile(SystemProfile):
    """Profile for headless servers"""
    
    @property
    def name(self) -> str:
        return "server"
        
    def get_clipboard_service(self) -> ClipboardAdapter:
        return None  # No clipboard on headless
        
    def get_screenshot_service(self) -> ScreenshotAdapter:
        return None  # No screenshots on headless
        
    def get_server_specific_tools(self) -> List[Tool]:
        return [
            SystemdToolsEnhanced(),
            JournaldTools(),
            NetworkManagerCLITools(),
            ContainerTools()  # Docker/Podman if present
        ]
```

## Adapters Pattern

Each service has an adapter interface:

```python
# adapters/clipboard.py
class ClipboardAdapter(ABC):
    """Abstract base for clipboard implementations"""
    
    @abstractmethod
    async def read(self) -> str:
        """Read clipboard contents"""
        pass
        
    @abstractmethod
    async def write(self, content: str) -> bool:
        """Write to clipboard"""
        pass
        
    @abstractmethod
    async def get_history(self) -> List[str]:
        """Get clipboard history if available"""
        pass

class KlipperAdapter(ClipboardAdapter):
    """KDE's Klipper clipboard manager"""
    
    def __init__(self):
        self.bus = SessionBus()
        self.klipper = self.bus.get('org.kde.klipper', '/klipper')
        
    async def read(self) -> str:
        return self.klipper.getClipboardContents()
        
    async def write(self, content: str) -> bool:
        self.klipper.setClipboardContents(content)
        return True
        
    async def get_history(self) -> List[str]:
        return self.klipper.getClipboardHistoryMenu()

class GNOMEClipboardAdapter(ClipboardAdapter):
    """GNOME clipboard (via Mutter or portal)"""
    
    async def read(self) -> str:
        # Different D-Bus path/interface
        portal = self.bus.get('org.freedesktop.portal.Desktop')
        # ... implementation
```

## Profile Detection

```python
class ProfileDetector:
    """Auto-detect the best profile for current system"""
    
    @staticmethod
    def detect() -> SystemProfile:
        # Check environment variables
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        # Check for desktop environment
        if 'kde' in desktop:
            if ProfileDetector._is_arch():
                return KDEArchProfile()
            elif ProfileDetector._is_fedora():
                return KDEFedoraProfile()
            else:
                return KDEGenericProfile()
                
        elif 'gnome' in desktop:
            if ProfileDetector._is_ubuntu():
                return GNOMEUbuntuProfile()
            else:
                return GNOMEGenericProfile()
                
        elif 'xfce' in desktop:
            return XFCEProfile()
            
        # Check if headless
        elif not os.environ.get('DISPLAY'):
            return ServerProfile()
            
        # Fallback
        return GenericProfile()
    
    @staticmethod
    def _is_arch() -> bool:
        return os.path.exists('/etc/arch-release')
        
    @staticmethod
    def _is_ubuntu() -> bool:
        return 'ubuntu' in open('/etc/os-release').read().lower()
```

## Configuration Override

Users can specify their profile:

```yaml
# ~/.config/dbus-mcp/config.yaml
profile: kde-arch  # Force specific profile

# Or customize
profile:
  base: kde-arch
  overrides:
    screenshot_tool: flameshot  # Use flameshot instead of spectacle
    clipboard_history: false    # Disable history access
```

## Profile Registry

```python
# profiles/registry.py
PROFILE_REGISTRY = {
    'kde-arch': KDEArchProfile,
    'kde-fedora': KDEFedoraProfile,
    'gnome-ubuntu': GNOMEUbuntuProfile,
    'gnome-fedora': GNOMEFedoraProfile,
    'xfce': XFCEProfile,
    'server': ServerProfile,
    'embedded': EmbeddedProfile,
    'custom': CustomProfile
}

def load_profile(name: str = None) -> SystemProfile:
    """Load a profile by name or auto-detect"""
    if name and name in PROFILE_REGISTRY:
        return PROFILE_REGISTRY[name]()
    return ProfileDetector.detect()
```

## Benefits

1. **Maintainability**: Each distro/DE combination is isolated
2. **Extensibility**: Easy to add new profiles
3. **User Choice**: Can override auto-detection
4. **Community Driven**: Users can contribute profiles
5. **Clean Core**: Core code doesn't have distro-specific hacks
6. **Testing**: Can test each profile independently

## Usage in Tools

```python
class ClipboardTool(Tool):
    def __init__(self, profile: SystemProfile):
        self.profile = profile
        self.adapter = profile.get_clipboard_service()
        
    async def read_clipboard(self) -> str:
        if not self.adapter:
            raise ToolError("Clipboard not available in this environment")
        return await self.adapter.read()
```

## Future Profiles

- `sway` - Sway compositor  
- `hyprland` - Hyprland compositor
- `steamdeck` - Steam Deck's custom environment
- `raspbian` - Raspberry Pi specific
- `nixos` - NixOS with unique paths
- `alpine` - Minimal Alpine Linux
- `wsl` - Windows Subsystem for Linux

This modular approach ensures D-Bus MCP can adapt to any Linux environment while keeping the core implementation clean and maintainable.