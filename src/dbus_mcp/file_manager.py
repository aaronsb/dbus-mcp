"""
File Pipe Manager

Manages temporary files for D-Bus operations that require file descriptors.
"""

import os
import logging
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a managed file."""
    reference: str
    path: str
    purpose: str
    created: str
    fd: Optional[int] = None
    status: str = 'pending'  # pending, complete, error
    metadata: Dict[str, Any] = field(default_factory=dict)
    

class FilePipeManager:
    """
    Manages temporary files for D-Bus operations.
    
    Many D-Bus methods write output to file descriptors rather than
    returning data directly. This manager handles creating, tracking,
    and cleaning up these temporary files.
    """
    
    def __init__(self, base_dir: str = None, profile=None):
        """Initialize the file manager with a base directory."""
        if base_dir is None:
            # Use XDG cache directory for user-specific storage
            cache_home = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
            base_dir = os.path.join(cache_home, 'dbus-mcp', 'screenshots')
        
        self.base_dir = Path(base_dir)
        self.profile = profile
        try:
            # Create base directory with restrictive permissions
            # Use parents=True to create intermediate directories
            self.base_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            logger.info(f"File manager initialized with base directory: {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to create base directory: {e}")
            raise
            
        self.files: Dict[str, FileInfo] = {}
        
        # Clean up old files on startup
        self._cleanup_existing_files()
        
    def _cleanup_existing_files(self):
        """Clean up any leftover files from previous sessions."""
        try:
            if self.base_dir.exists():
                for file_path in self.base_dir.glob("*.tmp"):
                    try:
                        file_path.unlink()
                        logger.debug(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def create_pipe(self, purpose: str, extension: str = "tmp") -> Tuple[int, str]:
        """
        Create a file descriptor for D-Bus method.
        
        Args:
            purpose: What this file is for (e.g., "screenshot", "export")
            extension: File extension (without dot)
            
        Returns:
            Tuple of (file_descriptor, reference_id)
        """
        ref_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        # Create file path
        file_path = self.base_dir / f"{purpose}_{ref_id}.{extension}"
        
        try:
            # Open file and get descriptor
            # O_CREAT: Create if doesn't exist
            # O_WRONLY: Write only (D-Bus methods will write to it)
            # O_EXCL: Exclusive creation (fail if exists)
            fd = os.open(str(file_path), os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
            
            # Track metadata
            self.files[ref_id] = FileInfo(
                reference=ref_id,
                path=str(file_path),
                purpose=purpose,
                created=timestamp,
                fd=fd,
                status='pending'
            )
            
            logger.info(f"Created pipe for {purpose}: {ref_id} -> {file_path}")
            return fd, ref_id
            
        except Exception as e:
            logger.error(f"Failed to create pipe for {purpose}: {e}")
            raise
    
    def finalize_file(self, ref_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Mark file as complete and add metadata.
        
        Args:
            ref_id: Reference ID from create_pipe
            metadata: Additional metadata about the file
        """
        if ref_id not in self.files:
            logger.warning(f"Unknown reference ID: {ref_id}")
            return
            
        file_info = self.files[ref_id]
        
        # Close file descriptor if still open
        if file_info.fd is not None:
            try:
                os.close(file_info.fd)
                file_info.fd = None
            except OSError:
                pass  # Already closed
        
        # Update metadata first so conversion has access to it
        if metadata:
            file_info.metadata.update(metadata)
            
        # Check if this is a screenshot that needs conversion
        if file_info.purpose == 'screenshot' and file_info.path.endswith('.png'):
            logger.info(f"Processing screenshot {ref_id} with metadata: {file_info.metadata}")
            self._convert_screenshot_if_needed(file_info)
        
        # Update status
        file_info.status = 'complete'
            
        # Add file size
        try:
            file_size = os.path.getsize(file_info.path)
            file_info.metadata['size'] = file_size
            logger.info(f"Finalized {file_info.purpose} file {ref_id}: {file_size} bytes")
        except Exception as e:
            logger.warning(f"Could not get file size for {ref_id}: {e}")
    
    def _convert_screenshot_if_needed(self, file_info: FileInfo):
        """
        Convert screenshot data to PNG if needed using profile-specific processing.
        
        This delegates to the system profile to handle format conversion,
        as different desktop environments may provide data in different formats.
        """
        if file_info.purpose != 'screenshot':
            return
            
        try:
            # Read the raw data
            with open(file_info.path, 'rb') as f:
                raw_data = f.read()
            
            # Check if already PNG
            if raw_data[:8] == b'\x89PNG\r\n\x1a\n':
                logger.debug(f"File {file_info.reference} is already PNG format")
                return
            
            # Get the profile to process the data
            if hasattr(self, 'profile') and self.profile:
                logger.info(f"Using {self.profile.name} profile to process screenshot")
                processed_data = self.profile.process_screenshot_data(raw_data, file_info.metadata)
                
                if processed_data and processed_data != raw_data:
                    # Write the processed data back
                    with open(file_info.path, 'wb') as f:
                        f.write(processed_data)
                    logger.info(f"Successfully processed screenshot with {self.profile.name} profile")
                elif not processed_data:
                    logger.error("Profile failed to process screenshot data")
            else:
                logger.warning("No profile available for screenshot processing")
                
        except Exception as e:
            logger.error(f"Error during screenshot conversion: {e}")
    
    def mark_error(self, ref_id: str, error: str):
        """Mark a file as having an error."""
        if ref_id in self.files:
            file_info = self.files[ref_id]
            file_info.status = 'error'
            file_info.metadata['error'] = error
            
            # Close fd if open
            if file_info.fd is not None:
                try:
                    os.close(file_info.fd)
                    file_info.fd = None
                except OSError:
                    pass
                    
            # Remove the file
            try:
                Path(file_info.path).unlink()
            except Exception:
                pass
    
    def get_file_info(self, ref_id: str) -> Optional[FileInfo]:
        """Get information about a file by reference."""
        return self.files.get(ref_id)
    
    def list_files(self, purpose: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all managed files.
        
        Args:
            purpose: Filter by purpose (optional)
            
        Returns:
            List of file information dictionaries
        """
        results = []
        for ref_id, info in self.files.items():
            if purpose and info.purpose != purpose:
                continue
                
            if info.status != 'complete':
                continue
                
            results.append({
                'reference': ref_id,
                'purpose': info.purpose,
                'created': info.created,
                'size': info.metadata.get('size', 0),
                'type': info.metadata.get('type', 'unknown'),
                'path': info.path
            })
            
        return sorted(results, key=lambda x: x['created'], reverse=True)
    
    def cleanup_old_files(self, max_age_minutes: int = 30):
        """Remove files older than max_age."""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        refs_to_remove = []
        for ref_id, info in self.files.items():
            try:
                created_time = datetime.fromisoformat(info.created)
                if created_time < cutoff_time:
                    refs_to_remove.append(ref_id)
            except Exception as e:
                logger.warning(f"Error checking age of {ref_id}: {e}")
        
        for ref_id in refs_to_remove:
            self.cleanup_file(ref_id)
    
    def cleanup_file(self, ref_id: str):
        """Clean up a specific file."""
        if ref_id not in self.files:
            return
            
        file_info = self.files[ref_id]
        
        # Close fd if open
        if file_info.fd is not None:
            try:
                os.close(file_info.fd)
            except OSError:
                pass
        
        # Remove file
        try:
            Path(file_info.path).unlink()
            logger.debug(f"Removed file {ref_id}: {file_info.path}")
        except Exception as e:
            logger.warning(f"Failed to remove file {ref_id}: {e}")
        
        # Remove from tracking
        del self.files[ref_id]
    
    def cleanup_all(self):
        """Clean up all managed files."""
        refs = list(self.files.keys())
        for ref_id in refs:
            self.cleanup_file(ref_id)