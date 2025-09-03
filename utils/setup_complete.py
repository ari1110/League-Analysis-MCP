#!/usr/bin/env python3
"""
Complete Setup Script for League Analysis MCP Server

This script provides a comprehensive setup experience that:
1. Checks all dependencies
2. Sets up Yahoo OAuth automatically
3. Tests the complete system
4. Provides usage instructions
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"Running {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS - {description}")
            return True
        else:
            print(f"FAILED - {description}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"FAILED - {description} - Exception: {e}")
        return False


def main():
    """Run complete setup process."""
    print("League Analysis MCP Server - Complete Setup")
    print("=" * 60)
    print()
    
    # Step 1: Check UV installation
    print("Step 1: Checking UV installation")
    if not run_command("uv --version", "UV version check"):
        print("Please install UV first:")
        print("- Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        print("- macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return 1
    
    # Step 2: Install dependencies
    print("\nStep 2: Installing dependencies")
    if not run_command("uv sync", "Dependency installation"):
        print("Failed to install dependencies. Check your pyproject.toml file.")
        return 1
    
    # Step 3: Run basic tests
    print("\nStep 3: Running basic system tests")
    if not run_command("uv run python test_server.py", "Basic server tests"):
        print("Basic tests failed. Check the output above.")
        return 1
    
    # Step 4: Run authentication tests
    print("\nStep 4: Running authentication tests")
    if not run_command("uv run python test_auth.py", "Authentication tests"):
        print("Authentication tests failed. Check the output above.")
        return 1
    
    # Step 5: Run startup tests
    print("\nStep 5: Running startup tests")
    if not run_command("uv run python test_startup.py", "Server startup tests"):
        print("Startup tests failed. Check the output above.")
        return 1
    
    print("\n" + "=" * 60)
    print("ALL SYSTEM TESTS PASSED!")
    print("=" * 60)
    
    # Step 6: Yahoo OAuth setup
    print("\nStep 6: Yahoo OAuth Setup")
    print("Now let's set up your Yahoo Fantasy Sports API access...")
    print()
    
    response = input("Do you want to set up Yahoo OAuth now? (y/n): ").lower().strip()
    
    if response == 'y':
        print("\nStarting Yahoo OAuth setup...")
        if run_command("uv run python utils/setup_yahoo_auth.py", "Yahoo OAuth setup"):
            print("\nComplete setup finished successfully!")
        else:
            print("\nYahoo OAuth setup had issues. You can run it manually later:")
            print("   uv run python utils/setup_yahoo_auth.py")
    else:
        print("\nTo set up Yahoo OAuth later, run:")
        print("   uv run python utils/setup_yahoo_auth.py")
    
    # Final instructions
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. If you haven't set up Yahoo OAuth yet:")
    print("   uv run python utils/setup_yahoo_auth.py")
    print()
    print("2. Start the MCP server:")
    print("   uv run python -m src.server")
    print()
    print("3. Connect with your MCP client (e.g., Claude Desktop)")
    print("   Add this server to your MCP configuration")
    print()
    print("Test Commands:")
    print("- uv run python test_server.py    # Basic tests")
    print("- uv run python test_auth.py      # Auth tests") 
    print("- uv run python test_startup.py   # Startup tests")
    print()
    print("Available Tools:")
    print("- get_server_info()               # Server status")
    print("- get_setup_instructions()        # Setup help")
    print("- list_available_seasons(sport)   # Game IDs")
    print("- refresh_yahoo_token()           # Token refresh")
    print("- get_league_info(league_id, sport) # League data")
    print("- analyze_manager_history(...)    # Historical analysis")
    print()
    print("Resources:")
    print("- league_overview/{sport}/{league_id}")
    print("- current_week/{sport}/{league_id}")
    print("- league_history/{sport}/{league_id}")
    print("- manager_profiles/{sport}/{league_id}")
    print()
    print("Happy analyzing!")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nSetup failed with error: {e}")
        sys.exit(1)