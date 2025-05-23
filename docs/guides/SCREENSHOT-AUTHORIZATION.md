# Screenshot Authorization on KDE

## The Problem

When trying to capture screenshots on KDE Plasma, you may encounter:
```
GDBus.Error:org.kde.KWin.ScreenShot2.Error.NoAuthorized: The process is not authorized to take a screenshot
```

This is KDE's security mechanism to prevent unauthorized screenshot access.

## The Solution

KDE uses desktop entries to authorize applications for screenshot access. Applications need a desktop entry with the `X-KDE-DBUS-Restricted-Interfaces` field.

### Quick Fix (Current Session)

For immediate testing, you can manually authorize the Python process:

1. Install the desktop entry:
```bash
sudo tee /usr/share/applications/dbus-mcp-screenshot.desktop << EOF
[Desktop Entry]
Type=Application
Name=D-Bus MCP Server
Comment=Model Context Protocol server for D-Bus integration
Exec=$(which python) -m dbus_mcp
NoDisplay=true
X-KDE-DBUS-Restricted-Interfaces=org.kde.kwin.Screenshot,org.kde.KWin.ScreenShot2
EOF
```

2. Update KDE's desktop database:
```bash
kbuildsycoca6
```

3. Restart the D-Bus MCP server (restart Claude Code)

### Permanent Solution

The `install-service.sh` script will show instructions for KDE systems to set up proper authorization.

## How It Works

The `X-KDE-DBUS-Restricted-Interfaces` field in the desktop entry tells KDE which D-Bus interfaces this application is allowed to use. In our case:
- `org.kde.kwin.Screenshot` - Legacy screenshot interface
- `org.kde.KWin.ScreenShot2` - Modern screenshot interface

## Alternative: Portal API

The freedesktop portal API (`org.freedesktop.portal.Screenshot`) provides a cross-desktop way to take screenshots with user permission dialogs, but it's interactive and less suitable for automation.

## Security Note

This authorization grants the application permission to take screenshots at any time. Only authorize trusted applications.