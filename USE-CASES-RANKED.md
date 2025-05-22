# D-Bus MCP Server - Ranked Capabilities by System Role

## Workstation Role: Interactive Desktop Systems
*AI assistant collaborating with users on their Linux desktop/laptop*

### Tier 1: Essential Daily Collaboration
1. **Clipboard Integration** (Score: 10/10)
   - Read/write clipboard for seamless data exchange
   - Access clipboard history for context recovery
   - Critical for code snippets, URLs, data transfer

2. **Desktop Notifications** (Score: 9/10)
   - Alert user to completed tasks
   - Remind about meetings/deadlines
   - Report async operation results
   - Non-intrusive communication channel

3. **Screenshot Capture** (Score: 9/10)
   - Capture errors for debugging
   - Document UI states
   - Share visual context with AI
   - Interactive area selection

4. **File Dialog Integration** (Score: 8/10)
   - Open/save file dialogs
   - Navigate filesystem with user
   - Respect user's file organization

### Tier 2: Productivity Enhancement
5. **Media Control** (Score: 7/10)
   - Pause during meetings
   - Control podcasts/music while working
   - Manage distractions automatically

6. **Window/Application Management** (Score: 7/10)
   - List running applications
   - Focus specific windows
   - Organize workspace layouts

7. **System Status Monitoring** (Score: 6/10)
   - Battery warnings
   - Network connectivity checks
   - Performance monitoring
   - Disk space alerts

8. **Browser Integration** (Score: 6/10)
   - Open URLs in preferred browser
   - Extract current tab information
   - Coordinate research tasks

### Tier 3: Advanced Integration
9. **Power Management** (Score: 5/10)
   - Prevent sleep during long operations
   - Adjust screen brightness
   - Manage power profiles

10. **Settings Access** (Score: 4/10)
    - Read theme preferences
    - Understand user environment
    - Adapt to accessibility needs

11. **Activity/Workspace Control** (Score: 4/10)
    - Switch virtual desktops
    - Manage KDE activities
    - Context-aware workspace organization

12. **Hardware Device Monitoring** (Score: 3/10)
    - USB device notifications
    - Bluetooth device management
    - External display detection

## Dedicated System Role: Purpose-Built Linux Systems
*AI as maintenance robot for servers, embedded devices, appliances, routers, NAS, etc.*

### Tier 1: Core Investigation Tools
1. **Service Discovery & Introspection** (Score: 10/10)
   - List all available D-Bus services
   - Introspect interfaces and methods
   - Map the "internal wiring" of each machine
   - Understand capabilities before acting

2. **System Service Status** (Score: 10/10)
   - Query systemd unit states
   - Check critical service health
   - Monitor daemon status
   - Identify failed/degraded services

3. **Log Access & Monitoring** (Score: 9/10)
   - Read systemd journal entries
   - Filter logs by service/time/severity
   - Track error patterns
   - Real-time log following

4. **Network Configuration Discovery** (Score: 9/10)
   - Current network state
   - Interface configurations
   - Connection profiles
   - DNS/routing information

### Tier 2: Diagnostic Capabilities
5. **Resource Monitoring** (Score: 8/10)
   - CPU/memory usage via D-Bus interfaces
   - Disk usage and mount points
   - Process information
   - System load metrics

6. **Container/VM Discovery** (Score: 8/10)
   - List running containers
   - Query container states
   - Discover virtualization
   - Understand workload distribution

7. **Security State Assessment** (Score: 7/10)
   - Firewall status
   - SELinux/AppArmor state
   - Failed login attempts
   - Security service status

8. **Application-Specific Interfaces** (Score: 7/10)
   - Database service status
   - Web server health
   - Custom application D-Bus APIs
   - Middleware services

### Tier 3: Remediation Tools
9. **Service Control** (Score: 6/10)
   - Restart failed services (with auth)
   - Reload configurations
   - Enable/disable units
   - Clear service failures

10. **Configuration Updates** (Score: 5/10)
    - Update network settings
    - Modify service parameters
    - Apply security policies
    - Tune performance settings

11. **Package/Update Status** (Score: 4/10)
    - Check for pending updates
    - Query package versions
    - Verify system integrity
    - Update scheduling

12. **Hardware Monitoring** (Score: 3/10)
    - Temperature sensors
    - Fan speeds
    - Power supply status
    - Hardware error logs

## Key Differences Between System Roles

### Workstation Systems
- **Focus**: User productivity and convenience
- **Interaction**: Real-time, interactive
- **Permissions**: User-level operations
- **State**: Long-running, stateful
- **Safety**: Must not disrupt user workflow

### Dedicated Systems
- **Focus**: Discovery, diagnosis, remediation
- **Interaction**: Automated, systematic
- **Permissions**: May need elevated privileges
- **State**: Ephemeral connections
- **Safety**: Must not break production services

## Implementation Priority Matrix

```
                    Workstation Priority
                    High           Low
Dedicated   High │ Svc Discovery │ Log Access    │
System           │ Introspection │ Network State │
Priority         │ Notifications │ Health Checks │
                 ├───────────────┼───────────────┤
            Low  │ Clipboard     │ Media Control │
                 │ Screenshots   │ Power Mgmt    │
                 │ File Dialogs  │ Settings      │
```

## Recommended Initial Implementation

### Phase 1: Common Core
1. Service discovery and introspection
2. Basic notification system
3. Read-only status queries

### Phase 2A: Workstation Focus
- Clipboard integration
- Screenshot tools
- File chooser dialogs
- Media control

### Phase 2B: Dedicated System Focus
- Systemd integration
- Log access
- Network status
- Service health monitoring

This approach ensures the D-Bus MCP server can adapt to different Linux system roles - from interactive workstations to purpose-built systems like servers, routers, embedded devices, and appliances - while maintaining appropriate security boundaries for each context.