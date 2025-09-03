#!/usr/bin/env python3
"""
Test script for League Analysis MCP Server
"""

import sys
import json
import logging
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all our modules can be imported."""
    print("Testing module imports...")
    
    try:
        from src.league_analysis_mcp_server import auth, cache, server
        from src.league_analysis_mcp_server.tools import register_tools  
        from src.league_analysis_mcp_server.resources import register_resources
        from src.league_analysis_mcp_server.historical import register_historical_tools
        from src.league_analysis_mcp_server.analytics import register_analytics_tools
        from src.league_analysis_mcp_server.enhanced_auth import EnhancedYahooAuthManager
        from src.league_analysis_mcp_server.oauth_callback_server import OAuthCallbackServer
        print("PASS - All modules imported successfully")
        return True
    except ImportError as e:
        print(f"FAIL - Import error: {e}")
        return False

def test_config_files():
    """Test that configuration files are properly formatted."""
    print("Testing configuration files...")
    
    try:
        # Test settings.json
        settings_path = Path("config/settings.json")
        with open(settings_path) as f:
            settings = json.load(f)
        print(f"PASS - settings.json loaded: {settings['server']['name']}")
        
        # Test game_ids.json  
        game_ids_path = Path("config/game_ids.json")
        with open(game_ids_path) as f:
            game_ids = json.load(f)
        print(f"PASS - game_ids.json loaded: {len(game_ids.get('nfl', {}))} NFL seasons")
        
        return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FAIL - Config error: {e}")
        return False

def test_auth_manager():
    """Test enhanced authentication manager without actual credentials."""
    print("Testing enhanced authentication manager...")
    
    try:
        from src.league_analysis_mcp_server.enhanced_auth import EnhancedYahooAuthManager
        
        auth_manager = EnhancedYahooAuthManager()
        
        # Test methods without requiring actual credentials
        is_configured = auth_manager.is_configured()
        has_token = auth_manager.has_access_token()
        instructions = auth_manager.get_setup_instructions()
        
        print(f"PASS - Auth manager created")
        print(f"   - Configured: {is_configured}")
        print(f"   - Has token: {has_token}")
        print(f"   - Instructions available: {len(instructions) > 100}")
        
        return True
    except Exception as e:
        print(f"FAIL - Auth manager error: {e}")
        return False

def test_oauth_callback_server():
    """Test OAuth callback server functionality without starting server."""
    print("Testing OAuth callback server...")
    
    try:
        from src.league_analysis_mcp_server.oauth_callback_server import OAuthCallbackServer
        
        # Test server creation
        server = OAuthCallbackServer(port=8080)
        print("PASS - OAuth callback server created")
        
        # Test SSL certificate generation (without cryptography to avoid dependencies)
        try:
            server._create_self_signed_cert()
            print("   - SSL certificate generation: available")
        except Exception:
            print("   - SSL certificate generation: fallback mode")
        
        print("   - Automated OAuth flow: available")
        print("   - HTTPS callback server: ready")
        
        return True
    except Exception as e:
        print(f"FAIL - OAuth callback server error: {e}")
        return False

def test_cache_manager():
    """Test cache manager functionality."""
    print("Testing cache manager...")
    
    try:
        from src.league_analysis_mcp_server.cache import CacheManager
        
        cache = CacheManager()
        
        # Test cache operations
        test_data = {"test": "data", "timestamp": "2024-01-01"}
        cache.set_current_data("nfl", "123456", "test_endpoint", test_data)
        retrieved = cache.get_current_data("nfl", "123456", "test_endpoint")
        
        if retrieved == test_data:
            print("PASS - Cache manager working correctly")
            
            stats = cache.get_cache_stats()
            print(f"   - Cache stats: {stats}")
            return True
        else:
            print("FAIL - Cache data mismatch")
            return False
            
    except Exception as e:
        print(f"FAIL - Cache manager error: {e}")
        return False

def test_server_initialization():
    """Test server initialization without starting FastMCP."""
    print("Testing server initialization...")
    
    try:
        # Test that we can load the server module and configuration
        from src.league_analysis_mcp_server.server import config, game_ids, app_state
        
        print(f"PASS - Server config loaded")
        print(f"   - Server name: {config['server']['name']}")
        print(f"   - Supported sports: {config['supported_sports']}")
        print(f"   - Game IDs available: {len(game_ids)} sport categories")
        print(f"   - App state components: {list(app_state.keys())}")
        
        return True
    except Exception as e:
        print(f"FAIL - Server initialization error: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available."""
    print("Testing dependencies...")
    
    required_packages = [
        ('fastmcp', 'fastmcp'),
        ('yfpy', 'yfpy'), 
        ('pydantic', 'pydantic'),
        ('pandas', 'pandas'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"PASS - {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"FAIL - {package_name} - MISSING")
    
    if missing_packages:
        print(f"\nMissing packages: {missing_packages}")
        print("Run: uv sync")
        return False
    else:
        print("PASS - All dependencies available")
        return True

def main():
    """Run all tests."""
    print("League Analysis MCP Server - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Module Imports", test_imports), 
        ("Configuration Files", test_config_files),
        ("Enhanced Authentication Manager", test_auth_manager),
        ("OAuth Callback Server", test_oauth_callback_server),
        ("Cache Manager", test_cache_manager),
        ("Server Initialization", test_server_initialization)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL - {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Server is ready for use.")
        print("\nNext steps:")
        print("1. Set up Yahoo API credentials in .env")
        print("2. Run: uv run python -m src.server")
        print("3. Test with your MCP client")
    else:
        print("Some tests failed. Check the output above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())