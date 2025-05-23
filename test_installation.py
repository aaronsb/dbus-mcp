#!/usr/bin/env python3
"""
Installation Test Script

Verifies that the D-Bus MCP server is properly installed and functional.
Run this after installation to ensure everything is working correctly.
"""

import sys
import subprocess
import json
import os
from pathlib import Path


def check_python_version():
    """Check if Python version meets requirements."""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version < (3, 9):
        print(f"  ❌ Python {version.major}.{version.minor} is too old. Need Python 3.9+")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_imports():
    """Check if all required modules can be imported."""
    print("\n✓ Checking Python imports...")
    
    modules = [
        ("mcp", "MCP SDK"),
        ("pydbus", "PyDBus"),
        ("gi", "GObject Introspection"),
        ("systemd", "systemd bindings (optional)"),
    ]
    
    all_good = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {description} ({module_name})")
        except ImportError as e:
            if module_name == "systemd":
                print(f"  ⚠️  {description} ({module_name}) - optional")
            else:
                print(f"  ❌ {description} ({module_name}) - {e}")
                all_good = False
    
    return all_good


def check_dbus_connection():
    """Check if we can connect to D-Bus."""
    print("\n✓ Checking D-Bus connection...")
    
    try:
        from pydbus import SessionBus
        bus = SessionBus()
        print("  ✓ Connected to session bus")
        
        # Try to get the D-Bus service itself
        dbus = bus.get('org.freedesktop.DBus', '/org/freedesktop/DBus')
        print("  ✓ Can communicate with D-Bus")
        return True
    except Exception as e:
        print(f"  ❌ Failed to connect to D-Bus: {e}")
        return False


def check_server_startup():
    """Check if the MCP server can start."""
    print("\n✓ Checking MCP server startup...")
    
    # Find the python executable in the venv if we're in one
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        python_exe = sys.executable
    else:
        python_exe = sys.executable
    
    try:
        # Try to run the server with --help
        result = subprocess.run(
            [python_exe, "-m", "dbus_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("  ✓ Server --help command works")
        else:
            print(f"  ❌ Server failed to start: {result.stderr}")
            return False
        
        # Try system detection
        result = subprocess.run(
            [python_exe, "-m", "dbus_mcp", "--detect"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("  ✓ System detection works")
            # Show detected profile
            for line in result.stdout.split('\n'):
                if 'Detected Profile:' in line:
                    print(f"  ℹ️  {line.strip()}")
        else:
            print(f"  ❌ System detection failed: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to run server: {e}")
        return False


def test_basic_functionality():
    """Test basic MCP protocol interaction."""
    print("\n✓ Testing basic MCP functionality...")
    
    import asyncio
    import json
    
    async def test_protocol():
        # Start the server
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'dbus_mcp',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        try:
            # Send initialize
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }
            
            proc.stdin.write((json.dumps(init_msg) + '\n').encode())
            await proc.stdin.drain()
            
            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5)
                response = json.loads(response_line.decode())
                
                if response.get('result', {}).get('serverInfo', {}).get('name') == 'dbus-mcp':
                    print("  ✓ MCP protocol communication works")
                    return True
                else:
                    print("  ❌ Unexpected response from server")
                    return False
                    
            except asyncio.TimeoutError:
                print("  ❌ Server did not respond to initialize")
                return False
                
        finally:
            proc.terminate()
            await proc.wait()
    
    try:
        return asyncio.run(test_protocol())
    except Exception as e:
        print(f"  ❌ Failed to test protocol: {e}")
        return False


def main():
    """Run all installation tests."""
    print("D-Bus MCP Server - Installation Test")
    print("=" * 50)
    
    tests = [
        check_python_version,
        check_imports,
        check_dbus_connection,
        check_server_startup,
        test_basic_functionality,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ All tests passed! The D-Bus MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Add the server to your Claude Desktop configuration")
        print("2. Run 'python -m dbus_mcp' to start the server manually")
        print("3. Check 'python -m dbus_mcp --help' for all options")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure you activated the virtual environment")
        print("2. Install system packages (python-gobject, python-systemd)")
        print("3. Check that D-Bus is running on your system")
        return 1


if __name__ == "__main__":
    sys.exit(main())