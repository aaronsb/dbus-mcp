# D-Bus MCP Server - Architecture Overview

## Two Primary Linux System Roles

```mermaid
graph TB
    subgraph "AI Assistant Layer"
        AI[fa:fa-brain AI Assistant<br/>Claude, GPT, Gemini]
    end
    
    subgraph "MCP Server" 
        MCP[fa:fa-server D-Bus MCP Server]
        subgraph "System Roles"
            WS[fa:fa-desktop Workstation Role<br/>Interactive Desktop]
            DS[fa:fa-database Dedicated System Role<br/>Servers, Appliances]
        end
    end
    
    subgraph "D-Bus Layer"
        subgraph "Session Bus"
            CB[fa:fa-clipboard Clipboard]
            NT[fa:fa-bell Notifications]
            MD[fa:fa-play Media]
            SS[fa:fa-camera Screenshot]
            FD[fa:fa-folder File Dialogs]
        end
        
        subgraph "System Bus"
            SD[fa:fa-cogs SystemD]
            JL[fa:fa-file-alt Journal Logs]
            NW[fa:fa-network-wired Network Manager]
            UP[fa:fa-battery-half UPower]
        end
    end
    
    AI -->|"MCP Protocol"| MCP
    MCP --> WS
    MCP --> DS
    
    WS -->|"User Context"| CB
    WS --> NT
    WS --> MD
    WS --> SS
    WS --> FD
    
    DS -->|"System Context"| SD
    DS --> JL
    DS --> NW
    DS --> UP
    
    style AI fill:#e3f2fd,stroke:#1565c0,stroke-width:3px,color:#000
    style MCP fill:#f3e5f5,stroke:#6a1b9a,stroke-width:3px,color:#000
    style WS fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000
    style DS fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000
    
    classDef sessionService fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef systemService fill:#ffccbc,stroke:#d84315,stroke-width:2px,color:#000
    
    class CB,NT,MD,SS,FD sessionService
    class SD,JL,NW,UP systemService
```

## Workstation Role: Desktop Collaboration Flow

```mermaid
sequenceDiagram
    participant U as User
    participant AI as AI Assistant
    participant MCP as D-Bus MCP
    participant D as Desktop Services
    
    U->>AI: "Help me debug this error"
    AI->>MCP: clipboard_read()
    MCP->>D: Get clipboard content
    D-->>MCP: Error message text
    MCP-->>AI: Context understood
    
    AI->>MCP: notify("Starting task...")
    MCP->>D: Show notification
    
    U->>AI: Shares screenshot
    AI->>MCP: analyze_screenshot()
    MCP->>D: Process image
    
    AI->>MCP: clipboard_write(solution)
    MCP->>D: Set clipboard
    
    AI->>MCP: media_pause()
    MCP->>D: Pause media players
    Note over U,D: Focus work time
    
    AI->>MCP: notify("Task complete!")
    MCP->>D: Show notification
    
    style U fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#000
    style AI fill:#e0f2f1,stroke:#00796b,stroke-width:2px,color:#000
    style MCP fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
    style D fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
```

## Dedicated System Role: Remote Management Flow

```mermaid
flowchart TD
    Start([AI Fleet Manager]) --> Connect[Connect to server-prod-03]
    Connect --> Discover[Discover D-Bus services]
    Discover --> Introspect[Introspect custom interfaces]
    Introspect --> Query[Query systemd status]
    Query --> Analyze[Analyze journal logs]
    Analyze --> Identify{Failed<br/>process?}
    
    Identify -->|Yes| Auth[Request PolicyKit auth]
    Identify -->|No| Next[Move to next server]
    
    Auth --> Restart[Restart service]
    Restart --> Verify[Verify health]
    Verify --> Log[Log actions]
    Log --> Next
    
    Next --> End([Continue fleet scan])
    
    style Start fill:#e1bee7,stroke:#6a1b9a,stroke-width:3px,color:#000
    style End fill:#e1bee7,stroke:#6a1b9a,stroke-width:3px,color:#000
    style Identify fill:#ffecb3,stroke:#ff6f00,stroke-width:2px,color:#000
    style Auth fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    
    classDef action fill:#c5e1a5,stroke:#558b2f,stroke-width:2px,color:#000
    classDef check fill:#b3e5fc,stroke:#0277bd,stroke-width:2px,color:#000
    
    class Connect,Discover,Introspect,Query,Analyze,Restart,Verify,Log action
    class Identify check
```

## Security Zones

```mermaid
graph TB
    subgraph "Security Zones"
        subgraph "Zone 1: Green - Interactive Session"
            G1[fa:fa-clipboard Clipboard R/W]
            G2[fa:fa-bell Notifications]
            G3[fa:fa-camera Screenshots]
            G4[fa:fa-music Media Control]
        end
        
        subgraph "Zone 2: Yellow - System Read"
            Y1[fa:fa-battery-three-quarters Battery Status]
            Y2[fa:fa-wifi Network State]
            Y3[fa:fa-info-circle Service Info]
            Y4[fa:fa-chart-line System Metrics]
        end
        
        subgraph "Zone 3: Red - Privileged"
            R1[fa:fa-sync Service Restart]
            R2[fa:fa-network-wired Network Toggle]
            R3[fa:fa-cog Config Changes]
        end
        
        subgraph "Zone 4: Black - Forbidden"
            B1[fa:fa-power-off Shutdown/Reboot]
            B2[fa:fa-hdd Disk Format]
            B3[fa:fa-download Package Install]
            B4[fa:fa-key Password Changes]
        end
    end
    
    AI[fa:fa-robot AI Assistant] -->|"High Trust"| G1
    AI -->|"High Trust"| G2
    AI -->|"High Trust"| G3
    AI -->|"High Trust"| G4
    
    AI -->|"Medium Trust"| Y1
    AI -->|"Medium Trust"| Y2
    AI -->|"Medium Trust"| Y3
    AI -->|"Medium Trust"| Y4
    
    AI -->|"Auth Required"| R1
    AI -->|"Auth Required"| R2
    AI -->|"Auth Required"| R3
    
    AI -.->|"Always Denied"| B1
    AI -.->|"Always Denied"| B2
    AI -.->|"Always Denied"| B3
    AI -.->|"Always Denied"| B4
    
    style AI fill:#e1f5fe,stroke:#01579b,stroke-width:3px,color:#000
    
    classDef green fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef yellow fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000
    classDef red fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    classDef black fill:#424242,stroke:#000000,stroke-width:3px,color:#fff
    
    class G1,G2,G3,G4 green
    class Y1,Y2,Y3,Y4 yellow
    class R1,R2,R3 red
    class B1,B2,B3,B4 black
```

### Zone Details

| Zone | Trust Level | Examples | Restrictions |
|------|------------|----------|--------------|
| 🟢 **Green** | High | Clipboard, notifications, screenshots | Rate limiting only |
| 🟡 **Yellow** | Medium | Battery status, network state, service info | Read-only access |
| 🔴 **Red** | Low | Service restart, network toggle | PolicyKit auth required |
| ⚫ **Black** | None | Shutdown, disk format, package install | Always denied |

## Implementation Layers

```mermaid
graph TD
    subgraph "Application Layer"
        A1[MCP Protocol Handler<br/>JSON-RPC Processing]
        A2[Tool Registry<br/>Dynamic Tool Discovery]
    end
    
    subgraph "Security Layer"
        S1[Security Policy Engine<br/>Rate Limiting & Permissions]
        S2[Audit Logger<br/>Action Tracking]
    end
    
    subgraph "Integration Layer"
        I1[D-Bus Connection Manager<br/>Session & System Bus]
        I2[System Profile Adapter<br/>KDE, GNOME, etc.]
    end
    
    subgraph "Tool Implementation Layer"
        T1[Desktop Tools<br/>Clipboard, Notify, Media]
        T2[System Tools<br/>SystemD, Network, Logs]
        T3[Profile Tools<br/>KDE, GNOME Specific]
    end
    
    A1 --> A2
    A2 --> S1
    S1 --> S2
    S1 --> I1
    I1 --> I2
    I2 --> T1
    I2 --> T2
    I2 --> T3
    
    style A1 fill:#e8eaf6,stroke:#5e35b1,stroke-width:2px,color:#000
    style A2 fill:#e8eaf6,stroke:#5e35b1,stroke-width:2px,color:#000
    style S1 fill:#ffebee,stroke:#c62828,stroke-width:3px,color:#000
    style S2 fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000
    style I1 fill:#e0f7fa,stroke:#00695c,stroke-width:2px,color:#000
    style I2 fill:#e0f7fa,stroke:#00695c,stroke-width:2px,color:#000
    style T1 fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#000
    style T2 fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    style T3 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000
```

## Connection Modes

### Workstation Role
- Long-lived connection
- Stateful session
- User authentication
- Interactive operations
- Desktop environment integration

### Dedicated System Role
- Ephemeral connections
- Stateless operations
- Service authentication
- Batch processing
- Works on servers, routers, NAS, IoT devices, etc.

## Tool Categories

### Universal Tools
- `list_services` - Available on both buses
- `introspect` - Discover interfaces
- `call_method` - Generic invocation

### Desktop-Specific Tools
- `clipboard_*` - Session bus only
- `screenshot` - Requires display
- `media_control` - User media players

### Server-Specific Tools
- `systemd_*` - Service management
- `journal_*` - Log analysis
- `network_config` - Network state

This architecture enables the D-Bus MCP server to adapt to different Linux system roles - from interactive workstations where users need productivity tools, to dedicated systems (servers, appliances, embedded devices) that require remote monitoring and management. The same core technology serves vastly different purposes based on the system's role.