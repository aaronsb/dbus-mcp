#!/usr/bin/env python3
"""
Socket bridge for systemd socket activation.

This module bridges systemd socket activation to FastMCP's stdio-based transport.
When systemd passes a socket, we accept connections and proxy them to/from stdio.
"""

import os
import sys
import asyncio
import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def socket_to_stdio_bridge():
    """Bridge systemd socket to stdio for FastMCP compatibility."""
    # Check for systemd socket activation
    listen_fds = int(os.environ.get('LISTEN_FDS', '0'))
    
    if listen_fds == 0:
        # No socket activation - just exec the regular server
        logger.info("No systemd socket activation detected, running in direct mode")
        os.execvp(sys.executable, [sys.executable, '-m', 'dbus_mcp'] + sys.argv[1:])
        return
    
    if listen_fds > 1:
        logger.warning(f"Multiple sockets passed ({listen_fds}), using first one")
    
    # Get the socket from systemd (always starts at FD 3)
    sock_fd = 3
    
    try:
        # Create socket from file descriptor
        sock = socket.socket(fileno=sock_fd)
        sock.setblocking(False)
        
        logger.info(f"Using systemd socket activation (FD={sock_fd})")
        
        # For Unix domain sockets with Accept=no, we need to handle a single connection
        # The socket is already connected when passed by systemd
        
        # Create async streams from the socket
        reader, writer = await asyncio.open_connection(sock=sock)
        
        # Create pipes for subprocess stdio
        stdin_r, stdin_w = os.pipe()
        stdout_r, stdout_w = os.pipe()
        
        # Start the actual MCP server as subprocess with piped stdio
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'dbus_mcp', *sys.argv[1:],
            stdin=stdin_r,
            stdout=stdout_w,
            stderr=sys.stderr.fileno()
        )
        
        # Close unused pipe ends
        os.close(stdin_r)
        os.close(stdout_w)
        
        # Create tasks for bidirectional proxying
        async def proxy_socket_to_stdin():
            """Copy data from socket to MCP server stdin."""
            stdin_stream = os.fdopen(stdin_w, 'wb')
            try:
                while True:
                    data = await reader.read(4096)
                    if not data:
                        break
                    stdin_stream.write(data)
                    stdin_stream.flush()
            except Exception as e:
                logger.error(f"Error proxying socket to stdin: {e}")
            finally:
                stdin_stream.close()
        
        async def proxy_stdout_to_socket():
            """Copy data from MCP server stdout to socket."""
            stdout_stream = os.fdopen(stdout_r, 'rb')
            try:
                while True:
                    data = await asyncio.get_event_loop().run_in_executor(
                        None, stdout_stream.read, 4096
                    )
                    if not data:
                        break
                    writer.write(data)
                    await writer.drain()
            except Exception as e:
                logger.error(f"Error proxying stdout to socket: {e}")
            finally:
                stdout_stream.close()
                writer.close()
                await writer.wait_closed()
        
        # Run proxy tasks concurrently
        await asyncio.gather(
            proxy_socket_to_stdin(),
            proxy_stdout_to_socket(),
            proc.wait()
        )
        
    except Exception as e:
        logger.error(f"Socket bridge error: {e}")
        raise


async def main():
    """Main entry point for socket bridge."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        await socket_to_stdio_bridge()
    except KeyboardInterrupt:
        logger.info("Socket bridge interrupted")
    except Exception as e:
        logger.error(f"Fatal error in socket bridge: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())