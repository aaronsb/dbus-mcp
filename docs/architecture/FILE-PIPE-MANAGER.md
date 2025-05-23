# File Pipe Manager Architecture

## Problem Statement

Many D-Bus methods (screenshots, exports, renders) write output to file descriptors rather than returning data directly. This is due to:
- D-Bus message size limits (~134MB)
- Efficiency for binary data
- Legacy API design

Currently, we cannot use these methods effectively through MCP.

## Proposed Solution: File Pipe Manager

A managed temporary file system that:
1. Creates file descriptors for D-Bus methods
2. Tracks metadata about created files
3. Returns file references to the AI agent
4. Cleans up automatically

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AI Agent      │     │  D-Bus MCP       │     │  File System    │
│                 │────▶│  Server          │────▶│  /tmp/dbus-mcp/ │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                      │                          │
         │ call_method()        │ 1. Create pipe          │
         │                      │────────────────────────▶│
         │                      │                          │
         │                      │ 2. Call D-Bus method    │
         │                      │    with pipe fd         │
         │                      │                          │
         │                      │ 3. Track metadata       │
         │                      │                          │
         │◀─────────────────────│ 4. Return reference     │
         │ {ref: "abc123",      │                          │
         │  path: "/tmp/...",   │                          │
         │  type: "image/png"}  │                          │
```

## Implementation

### File Pipe Manager Class

```python
class FilePipeManager:
    """Manages temporary files for D-Bus operations."""
    
    def __init__(self, base_dir: str = "/tmp/dbus-mcp"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True, mode=0o700)
        self.files: Dict[str, FileInfo] = {}
        
    def create_pipe(self, purpose: str) -> Tuple[int, str]:
        """
        Create a file descriptor for D-Bus method.
        Returns (fd, reference_id).
        """
        ref_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        # Create file path
        file_path = self.base_dir / f"{purpose}_{ref_id}.tmp"
        
        # Open file and get descriptor
        fd = os.open(str(file_path), os.O_CREAT | os.O_WRONLY, 0o600)
        
        # Track metadata
        self.files[ref_id] = FileInfo(
            reference=ref_id,
            path=str(file_path),
            purpose=purpose,
            created=timestamp,
            fd=fd,
            status='pending'
        )
        
        return fd, ref_id
        
    def finalize_file(self, ref_id: str, metadata: Dict[str, Any]):
        """Mark file as complete and add metadata."""
        if ref_id in self.files:
            self.files[ref_id].status = 'complete'
            self.files[ref_id].metadata = metadata
            os.close(self.files[ref_id].fd)
            
    def get_file_info(self, ref_id: str) -> Optional[FileInfo]:
        """Get information about a file."""
        return self.files.get(ref_id)
        
    def cleanup_old_files(self, max_age_minutes: int = 30):
        """Remove files older than max_age."""
        # Implementation here
```

### Enhanced Tool Methods

```python
@server.tool()
async def capture_window_screenshot(
    window_id: Optional[str] = None,
    include_decorations: bool = True,
    include_cursor: bool = False
) -> Dict[str, Any]:
    """
    Capture a screenshot of a window.
    
    Returns reference to the captured image file.
    """
    # Create pipe
    fd, ref_id = file_manager.create_pipe("screenshot")
    
    try:
        # Call D-Bus method with pipe
        if window_id:
            result = await call_dbus_method(
                'org.kde.KWin.ScreenShot2',
                '/org/kde/KWin/ScreenShot2',
                'CaptureWindow',
                [window_id, {'include-decoration': include_decorations}, fd]
            )
        else:
            result = await call_dbus_method(
                'org.kde.KWin.ScreenShot2',
                '/org/kde/KWin/ScreenShot2',
                'CaptureActiveWindow',
                [{'include-cursor': include_cursor}, fd]
            )
        
        # Finalize with metadata
        file_manager.finalize_file(ref_id, {
            'type': 'image/png',
            'window': window_id or 'active',
            'size': os.path.getsize(file_path)
        })
        
        return {
            'reference': ref_id,
            'path': file_manager.files[ref_id].path,
            'type': 'image/png',
            'purpose': 'screenshot',
            'metadata': result
        }
        
    except Exception as e:
        file_manager.cleanup_file(ref_id)
        raise
```

### New Tool Categories

```python
# Tools that create files
@server.tool()
async def export_document(
    service: str,
    format: str = "pdf"
) -> Dict[str, Any]:
    """Export document to file."""
    # Implementation

@server.tool()
async def render_graph(
    data: Dict,
    format: str = "svg"
) -> Dict[str, Any]:
    """Render graph visualization."""
    # Implementation

@server.tool() 
async def list_file_references() -> List[Dict[str, Any]]:
    """List all file references created in this session."""
    return [
        {
            'reference': ref,
            'purpose': info.purpose,
            'created': info.created,
            'size': os.path.getsize(info.path) if os.path.exists(info.path) else 0,
            'type': info.metadata.get('type', 'unknown')
        }
        for ref, info in file_manager.files.items()
        if info.status == 'complete'
    ]

@server.tool()
async def get_file_content(reference: str) -> str:
    """Get content of a file by reference (text files only)."""
    info = file_manager.get_file_info(reference)
    if not info:
        return f"No file found with reference: {reference}"
    
    # Security: Only allow reading files we created
    if not str(info.path).startswith(str(file_manager.base_dir)):
        return "Security: Can only read managed files"
    
    # Check if text file
    mime_type = info.metadata.get('type', '')
    if not mime_type.startswith('text/'):
        return f"File is binary ({mime_type}), cannot display as text"
    
    with open(info.path, 'r') as f:
        return f.read()
```

## Usage Example

```python
# AI Agent flow:
1. screenshot = capture_window_screenshot()
   → Returns: {"reference": "abc123", "path": "/tmp/dbus-mcp/screenshot_abc123.tmp"}

2. files = list_file_references()
   → Returns: [{"reference": "abc123", "purpose": "screenshot", "size": 250000}]

3. # AI can now reference these files for further operations
   upload_to_service(screenshot['reference'])
```

## Security Considerations

1. **Temporary Directory**: Use mode 0700 (owner only)
2. **File Permissions**: Create files with 0600 (owner read/write only)
3. **Path Validation**: Never allow reading outside managed directory
4. **Automatic Cleanup**: Delete files after 30 minutes
5. **Size Limits**: Enforce maximum file sizes
6. **Type Validation**: Verify MIME types match expected formats

## Benefits

1. **Enables Rich Operations**: Screenshots, exports, renders
2. **Clean API**: Simple reference system for AI agents
3. **Memory Efficient**: No large data in D-Bus messages
4. **Reusable**: Same system for all file-producing operations
5. **Traceable**: Full metadata and audit trail

## Implementation Priority

1. **Phase 1**: Basic file manager and screenshot support
2. **Phase 2**: Document export operations
3. **Phase 3**: Advanced rendering (graphs, diagrams)
4. **Phase 4**: Batch operations and archives