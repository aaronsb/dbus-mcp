#!/usr/bin/env python3
"""
SystemD socket activation support for D-Bus MCP server.

This module provides a custom stdio transport that works with systemd socket activation.
It wraps the socket file descriptors to make them compatible with FastMCP's stdio expectations.
"""

import os
import sys
import socket
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SystemdSocketWrapper:
    """Wraps systemd socket to provide file-like interface for FastMCP."""
    
    def __init__(self, sock: socket.socket, mode: str):
        self.socket = sock
        self.mode = mode
        self._buffer = b''
        
    def fileno(self):
        """Return the socket's file descriptor."""
        return self.socket.fileno()
    
    def readable(self):
        """Check if socket is readable."""
        return 'r' in self.mode
    
    def writable(self):
        """Check if socket is writable."""
        return 'w' in self.mode
    
    def read(self, size: int = -1) -> bytes:
        """Read from socket."""
        if size == -1:
            size = 65536  # Read in chunks
        try:
            data = self.socket.recv(size)
            return data
        except BlockingIOError:
            return b''
    
    def write(self, data: bytes) -> int:
        """Write to socket."""
        try:
            return self.socket.send(data)
        except BlockingIOError:
            return 0
    
    def flush(self):
        """No-op for compatibility."""
        pass
    
    def close(self):
        """Close the socket."""
        self.socket.close()


def setup_systemd_stdio():
    """Set up stdio using systemd socket activation."""
    # Check for systemd socket activation
    listen_fds = int(os.environ.get('LISTEN_FDS', '0'))
    
    if listen_fds == 0:
        # No socket activation, use regular stdio
        return False
    
    if listen_fds > 1:
        logger.warning(f"Multiple sockets passed ({listen_fds}), using first one")
    
    # Get the socket from systemd (always starts at FD 3)
    sock_fd = 3
    
    try:
        # Create socket from file descriptor
        sock = socket.fromfd(sock_fd, socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(False)
        
        logger.info(f"Using systemd socket activation (FD={sock_fd})")
        
        # Create wrapped file objects
        stdin_wrapper = SystemdSocketWrapper(sock, 'rb')
        stdout_wrapper = SystemdSocketWrapper(sock, 'wb')
        
        # Replace sys.stdin and sys.stdout with our wrappers
        # Save originals first
        sys._orig_stdin = sys.stdin
        sys._orig_stdout = sys.stdout
        sys._orig_stdin_buffer = sys.stdin.buffer
        sys._orig_stdout_buffer = sys.stdout.buffer
        
        # Create TextIOWrapper around our socket wrappers
        import io
        sys.stdin = io.TextIOWrapper(io.BufferedReader(stdin_wrapper), encoding='utf-8')
        sys.stdout = io.TextIOWrapper(io.BufferedWriter(stdout_wrapper), encoding='utf-8', line_buffering=True)
        
        # Also update the buffer attributes
        sys.stdin.buffer = io.BufferedReader(stdin_wrapper)
        sys.stdout.buffer = io.BufferedWriter(stdout_wrapper)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to set up systemd socket: {e}")
        raise


def restore_stdio():
    """Restore original stdio if needed."""
    if hasattr(sys, '_orig_stdin'):
        sys.stdin = sys._orig_stdin
        sys.stdout = sys._orig_stdout
        delattr(sys, '_orig_stdin')
        delattr(sys, '_orig_stdout')
        delattr(sys, '_orig_stdin_buffer')
        delattr(sys, '_orig_stdout_buffer')