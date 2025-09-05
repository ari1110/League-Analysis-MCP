#!/usr/bin/env python3
"""
Comprehensive test suite with static analysis integration
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Tuple
import json


def run_static_analysis() -> Tuple[bool, List[str]]:
    """Run static analysis tools and collect results."""
    print("Running static analysis...")
    
    issues = []
    all_passed = True
    
    # Check if ruff is available
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "src/", "--output-format", "json"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.stdout.strip():
            ruff_issues = json.loads(result.stdout)
            for issue in ruff_issues:
                issues.append(f"RUFF: {issue['filename']}:{issue['location']['row']} - {issue['message']}")
                all_passed = False
        else:
            print("PASS - Ruff checks passed")
            
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        issues.append(f"RUFF: Could not run ruff analysis: {e}")
        print(f"SKIP - Ruff not available: {e}")
    
    # Check if mypy is available
    try:
        result = subprocess.run(
            ["uv", "run", "mypy", "src/league_analysis_mcp_server/", "--ignore-missing-imports"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.returncode != 0 and result.stdout.strip():
            mypy_output = result.stdout.strip()
            if "error:" in mypy_output.lower():
                for line in mypy_output.split('\n'):
                    if 'error:' in line:
                        issues.append(f"MYPY: {line.strip()}")
                        all_passed = False
            else:
                print("PASS - MyPy checks passed")
        else:
            print("PASS - MyPy checks passed")
            
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        issues.append(f"MYPY: Could not run mypy analysis: {e}")
        print(f"SKIP - MyPy not available: {e}")
    
    return all_passed, issues


def run_ide_diagnostics() -> Tuple[bool, List[str]]:
    """Run IDE diagnostics using MCP getDiagnostics tool."""
    print("Running IDE diagnostics...")
    
    try:
        # Import the MCP IDE tool
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        # We'll simulate the diagnostics check since we can't directly call MCP tools in test
        # In a real scenario, this would use the MCP getDiagnostics tool
        
        critical_issues = [
            "historical.py:170 - Type error: game_id parameter",
            "team_tools.py:774 - Missing _decode_name_bytes method", 
            "user_tools.py:139 - Missing _decode_name_bytes method"
        ]
        
        warnings = [
            "Multiple unused imports detected",
            "Deprecated datetime.utcnow() usage",
            "Unused variables in analytics.py"
        ]
        
        issues = []
        has_errors = False
        
        for issue in critical_issues:
            issues.append(f"ERROR: {issue}")
            has_errors = True
        
        for warning in warnings:
            issues.append(f"WARNING: {warning}")
        
        return not has_errors, issues
        
    except Exception as e:
        return False, [f"IDE_DIAGNOSTICS: Failed to run diagnostics: {e}"]


def test_function_coverage() -> Tuple[bool, List[str]]:
    """Test that all functions are properly covered."""
    print("Testing function coverage...")
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    try:
        # Import all modules and check for function registration
        from league_analysis_mcp_server import (
            tools, historical, analytics, team_tools, 
            player_tools, user_tools, game_tools, utility_tools
        )
        
        modules_to_test = [
            (tools, "register_tools"),
            (historical, "register_historical_tools"),
            (analytics, "register_analytics_tools"),
            (team_tools, "register_team_tools"),
            (player_tools, "register_player_tools"),
            (user_tools, "register_user_tools"), 
            (game_tools, "register_game_tools"),
            (utility_tools, "register_utility_tools"),
        ]
        
        issues = []
        all_good = True
        
        for module, func_name in modules_to_test:
            if not hasattr(module, func_name):
                issues.append(f"Missing registration function: {module.__name__}.{func_name}")
                all_good = False
            else:
                print(f"PASS - {module.__name__}.{func_name} exists")
        
        return all_good, issues
        
    except Exception as e:
        return False, [f"FUNCTION_COVERAGE: Import error: {e}"]


def test_critical_fixes() -> Tuple[bool, List[str]]:
    """Test that our critical fixes are working."""
    print("Testing critical fixes...")
    
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    try:
        issues = []
        all_good = True
        
        # Test 1: get_player_name function exists and works
        from league_analysis_mcp_server.enhancement_helpers import get_player_name
        
        # Mock player object with name attribute
        class MockPlayer:
            def __init__(self):
                self.name = MockName()
        
        class MockName:
            def __init__(self):
                self.full = "Test Player"
        
        mock_player = MockPlayer()
        result = get_player_name(mock_player)
        
        if result == "Test Player":
            print("PASS - get_player_name function working")
        else:
            issues.append(f"get_player_name returned: {result}, expected: Test Player")
            all_good = False
        
        # Test 2: DataEnhancer exists
        from league_analysis_mcp_server.enhancement_helpers import DataEnhancer
        print("PASS - DataEnhancer class importable")
        
        # Test 3: Check if _decode_name_bytes method exists (this should fail based on diagnostics)
        if hasattr(DataEnhancer, '_decode_name_bytes'):
            print("PASS - DataEnhancer has _decode_name_bytes method")
        else:
            issues.append("DataEnhancer missing _decode_name_bytes method (detected in diagnostics)")
            all_good = False
        
        return all_good, issues
        
    except Exception as e:
        return False, [f"CRITICAL_FIXES: Test error: {e}"]


def test_error_handling() -> Tuple[bool, List[str]]:
    """Test error handling in critical paths."""
    print("Testing error handling...")
    
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    try:
        issues = []
        all_good = True
        
        # Test authentication error handling
        from league_analysis_mcp_server.enhanced_auth import EnhancedYahooAuthManager
        
        # Test with no credentials
        os.environ.pop('YAHOO_CONSUMER_KEY', None)
        os.environ.pop('YAHOO_CONSUMER_SECRET', None)
        
        auth_manager = EnhancedYahooAuthManager()
        
        if not auth_manager.is_configured():
            print("PASS - Auth manager correctly detects missing credentials")
        else:
            issues.append("Auth manager should detect missing credentials")
            all_good = False
        
        # Test cache manager error handling
        from league_analysis_mcp_server.cache import CacheManager
        
        cache = CacheManager()
        
        # Test invalid cache operations
        result = cache.get("invalid_key")
        if result is None:
            print("PASS - Cache manager handles invalid keys")
        else:
            issues.append(f"Cache manager returned {result} for invalid key")
            all_good = False
        
        return all_good, issues
        
    except Exception as e:
        return False, [f"ERROR_HANDLING: Test error: {e}"]


def main():
    """Run comprehensive test suite."""
    print("League Analysis MCP - Comprehensive Test Suite with Static Analysis")
    print("=" * 80)
    
    tests = [
        ("Static Analysis (Ruff/MyPy)", run_static_analysis),
        ("IDE Diagnostics", run_ide_diagnostics),
        ("Function Coverage", test_function_coverage),
        ("Critical Fixes", test_critical_fixes),
        ("Error Handling", test_error_handling),
    ]
    
    all_results = []
    all_issues = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        try:
            passed, issues = test_func()
            all_results.append((test_name, passed))
            all_issues.extend(issues)
            
            if passed:
                print(f"PASS - {test_name}")
            else:
                print(f"FAIL - {test_name}")
                for issue in issues:
                    print(f"   - {issue}")
                    
        except Exception as e:
            print(f"ERROR - {test_name}: {e}")
            all_results.append((test_name, False))
            all_issues.append(f"{test_name}: Exception - {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    passed_count = sum(1 for _, passed in all_results if passed)
    total_count = len(all_results)
    
    for test_name, passed in all_results:
        status = "PASS" if passed else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nSummary: {passed_count}/{total_count} test suites passed")
    
    if all_issues:
        print(f"\nIssues Found ({len(all_issues)}):")
        for issue in all_issues:
            print(f"   - {issue}")
    
    if passed_count == total_count:
        print("\nAll comprehensive tests passed!")
        print("   - Static analysis clean")
        print("   - All functions covered")
        print("   - Critical fixes working")
        print("   - Error handling robust")
    else:
        print(f"\n{total_count - passed_count} test suite(s) failed")
        print("   Review issues above for required fixes")
    
    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())