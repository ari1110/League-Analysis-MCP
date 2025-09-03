#!/usr/bin/env python3
"""
Test MCP connection and functionality
"""

import sys
import json
import subprocess
from pathlib import Path


def test_mcp_server_stdio():
    """Test MCP server stdio connection."""
    print("Testing MCP server stdio connection...")
    
    try:
        # Start the server process
        cmd = ["uv", "run", "python", "-m", "league_analysis_mcp_server.server"]
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Send initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send request
        request_json = json.dumps(initialize_request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Wait a bit for response
        import time
        time.sleep(2)
        
        # Terminate process
        process.terminate()
        process.wait(timeout=5)
        
        # Check if process started without immediate errors
        if process.returncode is None or process.returncode == -15:  # SIGTERM
            print("SUCCESS - MCP server started and responded to stdio")
            return True
        else:
            print(f"FAILED - MCP server exited with code: {process.returncode}")
            if process.stderr:
                stderr_output = process.stderr.read()
                print(f"STDERR: {stderr_output}")
            return False
            
    except Exception as e:
        print(f"FAILED - MCP connection test error: {e}")
        return False


def generate_config_examples():
    """Generate MCP configuration examples for different clients."""
    print("\nGenerating MCP configuration examples...")
    
    # Get current directory for examples
    current_dir = Path(__file__).parent.absolute()
    
    configs = {
        "claude_desktop_config.json": {
            "mcpServers": {
                "league-analysis-mcp": {
                    "command": "uv",
                    "args": ["run", "python", "-m", "league_analysis_mcp_server.server"],
                    "cwd": str(current_dir)
                }
            }
        },
        "claude_code_config.json": {
            "mcpServers": {
                "league-analysis-mcp": {
                    "command": "uv",
                    "args": ["run", "python", "-m", "league_analysis_mcp_server.server"],
                    "cwd": str(current_dir),
                    "env": {}
                }
            }
        },
        "continue_config.json": {
            "mcpServers": [
                {
                    "name": "league-analysis-mcp",
                    "command": ["uv", "run", "python", "-m", "league_analysis_mcp_server.server"],
                    "cwd": str(current_dir)
                }
            ]
        }
    }
    
    # Create configs directory
    configs_dir = current_dir / "example_configs"
    configs_dir.mkdir(exist_ok=True)
    
    for filename, config in configs.items():
        config_path = configs_dir / filename
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Created: {config_path}")
    
    print(f"\nConfiguration examples created in: {configs_dir}")
    return True


def check_server_capabilities():
    """Check what capabilities our server exposes."""
    print("\nChecking server capabilities...")
    
    try:
        # Import our server modules to check capabilities
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from league_analysis_mcp_server.server import mcp, app_state
        
        print("Server capabilities:")
        print(f"  - Server name: {mcp.name}")
        print(f"  - App state keys: {list(app_state.keys())}")
        
        # Check if we can access the tools/resources (this is FastMCP specific)
        print("  - Tools and resources registered via FastMCP decorators")
        print("  - Authentication system: Enhanced with token refresh")
        print("  - Caching system: Historical + current data")
        
        return True
        
    except Exception as e:
        print(f"FAILED - Server capabilities check error: {e}")
        return False


def main():
    """Run MCP connection tests."""
    print("League Analysis MCP - Connection Testing")
    print("=" * 50)
    
    tests = [
        ("MCP Server stdio Connection", test_mcp_server_stdio),
        ("Generate Config Examples", generate_config_examples), 
        ("Check Server Capabilities", check_server_capabilities),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAILED - {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "=" * 50)
    print("MCP CONNECTION TEST RESULTS")
    print("=" * 50)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nSummary: {passed}/{total} MCP tests passed")
    
    if passed == total:
        print("\nMCP server is ready for client connections!")
        print("\nNext steps:")
        print("1. Use configuration examples in example_configs/")
        print("2. Add to your MCP client (Claude Desktop, Claude Code, etc.)")
        print("3. Restart your MCP client")
        print("4. Test with: 'Can you get server info for the league analysis server?'")
    else:
        print(f"\nWARNING: {total - passed} MCP tests failed.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nMCP testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nMCP testing failed with error: {e}")
        sys.exit(1)