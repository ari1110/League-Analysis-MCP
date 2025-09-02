#!/usr/bin/env python3
"""
Test Yahoo API authentication without real credentials
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_auth_flow():
    """Test authentication flow with fake credentials."""
    print("Testing Yahoo API authentication flow...")
    
    # Set fake environment variables
    os.environ['YAHOO_CONSUMER_KEY'] = 'fake_key_12345'
    os.environ['YAHOO_CONSUMER_SECRET'] = 'fake_secret_67890'
    
    try:
        from src.league_analysis_mcp_server.auth import YahooAuthManager
        
        auth_manager = YahooAuthManager()
        
        print(f"PASS - Auth manager with fake credentials:")
        print(f"   - Configured: {auth_manager.is_configured()}")
        print(f"   - Has token: {auth_manager.has_access_token()}")
        
        # Test credential extraction
        credentials = auth_manager.get_auth_credentials()
        expected_keys = ['yahoo_consumer_key', 'yahoo_consumer_secret']
        
        for key in expected_keys:
            if key in credentials:
                print(f"   - {key}: *** (found)")
            else:
                print(f"   - {key}: MISSING")
        
        return True
        
    except Exception as e:
        print(f"FAIL - Auth flow error: {e}")
        return False

def test_server_tools_without_yahoo():
    """Test server tools that don't require Yahoo API."""
    print("\nTesting server tools without Yahoo API...")
    
    try:
        from src.server import mcp, app_state
        
        # Test server info tool (should work without Yahoo API)
        print("Testing get_server_info()...")
        
        # Import the function directly
        from src.server import get_server_info
        
        result = get_server_info()
        
        if isinstance(result, dict):
            print("PASS - get_server_info() works:")
            print(f"   - Server name: {result.get('server', {}).get('name')}")
            print(f"   - Supported sports: {result.get('supported_sports')}")
            print(f"   - Auth configured: {result.get('authentication', {}).get('configured')}")
            return True
        else:
            print(f"FAIL - get_server_info() returned unexpected type: {type(result)}")
            return False
            
    except Exception as e:
        print(f"FAIL - Server tools error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_game_ids():
    """Test game ID mappings."""
    print("\nTesting game ID mappings...")
    
    try:
        from src.server import list_available_seasons
        
        # Test each sport
        sports = ["nfl", "nba", "mlb", "nhl"]
        
        for sport in sports:
            result = list_available_seasons(sport)
            
            if "error" not in result:
                seasons = result.get("available_seasons", {})
                print(f"PASS - {sport.upper()}: {len(seasons)} seasons available")
            else:
                print(f"FAIL - {sport.upper()}: {result['error']}")
                return False
        
        return True
        
    except Exception as e:
        print(f"FAIL - Game IDs error: {e}")
        return False

def test_cache_operations():
    """Test advanced cache operations."""
    print("\nTesting cache operations...")
    
    try:
        from src.cache import get_cache_manager
        
        cache_manager = get_cache_manager()
        
        # Test different cache scenarios
        test_cases = [
            ("current", "nfl", "123456", "standings", {"team": "data"}),
            ("historical", "nba", "654321", "2023", "draft_results", {"draft": "picks"}),
        ]
        
        for cache_type, sport, league_id, *args in test_cases:
            if cache_type == "current":
                endpoint, data = args
                cache_manager.set_current_data(sport, league_id, endpoint, data)
                retrieved = cache_manager.get_current_data(sport, league_id, endpoint)
            else:
                season, endpoint, data = args
                cache_manager.set_historical_data(sport, season, league_id, endpoint, data)
                retrieved = cache_manager.get_historical_data(sport, season, league_id, endpoint)
            
            if retrieved == data:
                print(f"PASS - {cache_type} cache: {sport}/{endpoint}")
            else:
                print(f"FAIL - {cache_type} cache mismatch: {sport}/{endpoint}")
                return False
        
        # Test cache stats
        stats = cache_manager.get_cache_stats()
        print(f"PASS - Cache stats: {stats['total_entries']} entries")
        
        return True
        
    except Exception as e:
        print(f"FAIL - Cache operations error: {e}")
        return False

def main():
    """Run authentication and offline testing."""
    print("League Analysis MCP - Authentication & Offline Testing")
    print("=" * 60)
    
    tests = [
        ("Authentication Flow", test_auth_flow),
        ("Server Tools (Offline)", test_server_tools_without_yahoo),
        ("Game ID Mappings", test_game_ids),
        ("Cache Operations", test_cache_operations),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL - {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "=" * 60)
    print("AUTHENTICATION & OFFLINE TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nSummary: {passed}/{total} offline tests passed")
    
    if passed == total:
        print("\nAll offline tests passed!")
        print("\nNext Steps for Full Testing:")
        print("1. Get Yahoo Developer credentials:")
        print("   - Go to https://developer.yahoo.com/apps/")
        print("   - Create new app with redirect_uri: 'oob'")
        print("   - Copy Consumer Key & Secret")
        print()
        print("2. Create .env file:")
        print("   cp .env.example .env")
        print("   # Edit .env with your credentials")
        print()
        print("3. Test with real Yahoo API:")
        print("   uv run python -c \"from src.server import *; print(get_setup_instructions())\"")
        print()
        print("4. Start the MCP server:")
        print("   uv run python -m src.server")
        
    else:
        print(f"\nWARNING: {total - passed} offline tests failed.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())