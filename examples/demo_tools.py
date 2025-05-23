#!/usr/bin/env python3
"""
D-Bus MCP Tools Demo

This script demonstrates how to interact with the D-Bus MCP server
using the MCP protocol. It shows examples of calling each core tool.
"""

import json
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))


async def send_request(writer, reader, request):
    """Send a JSON-RPC request and get the response."""
    # Send request
    writer.write((json.dumps(request) + '\n').encode())
    await writer.drain()
    
    # Read response
    response_line = await reader.readline()
    return json.loads(response_line.decode())


async def demo_tools():
    """Demonstrate the core D-Bus MCP tools."""
    # Start the server
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'dbus_mcp',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    reader = proc.stdout
    writer = proc.stdin
    
    print("D-Bus MCP Tools Demo")
    print("=" * 50)
    
    try:
        # 1. Initialize the connection
        print("\n1. Initializing MCP connection...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "demo-client",
                    "version": "1.0"
                }
            }
        }
        response = await send_request(writer, reader, init_request)
        print(f"   Server: {response['result']['serverInfo']['name']} v{response['result']['serverInfo']['version']}")
        
        # Send initialized notification
        writer.write((json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + '\n').encode())
        await writer.drain()
        
        # 2. List available tools
        print("\n2. Listing available tools...")
        list_tools = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        response = await send_request(writer, reader, list_tools)
        tools = response['result']['tools']
        print(f"   Found {len(tools)} tools:")
        for tool in tools[:7]:  # Show first 7 core tools
            print(f"   - {tool['name']}")
        
        # 3. Call help tool
        print("\n3. Getting help...")
        help_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "help",
                "arguments": {}
            }
        }
        response = await send_request(writer, reader, help_request)
        help_text = response['result']['content'][0]['text']
        print("   " + "\n   ".join(help_text.split('\n')[:5]))
        print("   ...")
        
        # 4. Send a notification
        print("\n4. Sending desktop notification...")
        notify_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "notify",
                "arguments": {
                    "title": "D-Bus MCP Demo",
                    "message": "Hello from the D-Bus MCP server!",
                    "urgency": "normal"
                }
            }
        }
        response = await send_request(writer, reader, notify_request)
        print(f"   {response['result']['content'][0]['text']}")
        
        # 5. Get system status
        print("\n5. Getting system status...")
        status_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "status",
                "arguments": {}
            }
        }
        response = await send_request(writer, reader, status_request)
        status_text = response['result']['content'][0]['text']
        print("   " + "\n   ".join(status_text.split('\n')))
        
        # 6. List D-Bus services
        print("\n6. Listing session bus services...")
        list_services_request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "list_services",
                "arguments": {"bus": "session"}
            }
        }
        response = await send_request(writer, reader, list_services_request)
        services_text = response['result']['content'][0]['text']
        lines = services_text.split('\n')
        print("   " + "\n   ".join(lines[:8]))
        print(f"   ... and {len(lines) - 8} more services")
        
        # 7. Introspect a service
        print("\n7. Introspecting notification service...")
        introspect_request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "introspect",
                "arguments": {
                    "service": "org.freedesktop.Notifications",
                    "path": "/org/freedesktop/Notifications",
                    "bus": "session"
                }
            }
        }
        response = await send_request(writer, reader, introspect_request)
        introspect_text = response['result']['content'][0]['text']
        print("   " + "\n   ".join(introspect_text.split('\n')[:15]))
        print("   ...")
        
        # 8. Call a safe method
        print("\n8. Getting notification server info...")
        call_method_request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "call_method",
                "arguments": {
                    "service": "org.freedesktop.Notifications",
                    "path": "/org/freedesktop/Notifications",
                    "interface": "org.freedesktop.Notifications",
                    "method": "GetServerInformation",
                    "bus": "session"
                }
            }
        }
        response = await send_request(writer, reader, call_method_request)
        print(f"   {response['result']['content'][0]['text']}")
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Terminate the server
        proc.terminate()
        await proc.wait()


def main():
    """Run the demo."""
    print("Starting D-Bus MCP Tools Demo...")
    print("This will:")
    print("- Connect to the MCP server")
    print("- List available tools")
    print("- Send a desktop notification")
    print("- Show system status")
    print("- Explore D-Bus services")
    print()
    
    try:
        asyncio.run(demo_tools())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Failed to run demo: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())