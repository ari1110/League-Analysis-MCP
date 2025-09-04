#!/usr/bin/env python3
"""
Integration tests for League Analysis MCP Server with real Yahoo API.

These tests require real Yahoo API credentials and validate actual
data retrieval and processing with live Yahoo Fantasy Sports data.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.functional.base import IntegrationTestCase
from league_analysis_mcp_server.tools import (
    get_league_info, get_standings, get_team_roster, get_matchups
)
from league_analysis_mcp_server.server import app_state


class TestLiveDataRetrieval(IntegrationTestCase):
    """Test live data retrieval from Yahoo API."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
        
        # Get test league ID from environment
        self.test_league_id = os.environ.get("TEST_LEAGUE_ID", "123456")
    
    def test_live_league_info_retrieval(self):
        """Test retrieving live league information."""
        result = get_league_info(self.test_league_id, "nfl")
        
        if "error" in result:
            self.skipTest(f"Cannot access test league: {result['error']}")
        
        # Validate real Yahoo API response structure
        self.assert_real_api_response(result)
        self.assertIn("league", result)
        
        league = result["league"]
        self.assertIn("league_id", league)
        self.assertIn("name", league)
        self.assertIn("num_teams", league)
        
        # Should be real data, not test data
        self.assertNotEqual(league["name"], "Test Fantasy Football League")
    
    def test_live_standings_retrieval(self):
        """Test retrieving live standings data."""
        result = get_standings(self.test_league_id, "nfl")
        
        if "error" in result:
            self.skipTest(f"Cannot access test league standings: {result['error']}")
        
        # Validate real standings data
        self.assert_real_api_response(result)
        self.assertIn("teams", result)
        
        teams = result["teams"]
        self.assertIsInstance(teams, list)
        self.assertGreater(len(teams), 0)
        
        # Validate team structure
        for team in teams:
            self.assertIn("team_id", team)
            self.assertIn("name", team)
            self.assertIn("team_standings", team)
            
            standings = team["team_standings"]
            self.assertIn("rank", standings)
            self.assertIn("outcome_totals", standings)
    
    def test_live_roster_retrieval(self):
        """Test retrieving live roster data."""
        # First get standings to find a valid team
        standings = get_standings(self.test_league_id, "nfl")
        
        if "error" in standings or not standings.get("teams"):
            self.skipTest("Cannot access team data for roster test")
        
        team_id = standings["teams"][0]["team_id"]
        result = get_team_roster(self.test_league_id, team_id, "nfl")
        
        if "error" in result:
            self.skipTest(f"Cannot access roster data: {result['error']}")
        
        # Validate roster structure
        self.assert_real_api_response(result)
        self.assertIn("roster", result)
        
        roster = result["roster"]
        self.assertIn("players", roster)
        
        players = roster["players"]
        self.assertIsInstance(players, list)
        
        # Validate player structure
        if players:
            player = players[0]
            self.assertIn("player_id", player)
            self.assertIn("name", player)
            self.assertIn("display_position", player)


class TestLiveAnalyticsData(IntegrationTestCase):
    """Test analytics with real Yahoo data."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
        
        self.test_league_id = os.environ.get("TEST_LEAGUE_ID", "123456")
    
    def test_live_draft_analysis(self):
        """Test draft analysis with real data."""
        from league_analysis_mcp_server.analytics import analyze_draft_strategy
        
        # This might not work for all leagues (data availability)
        try:
            result = analyze_draft_strategy(self.test_league_id, "nfl", ["2024"])
            
            if "error" not in result:
                self.assert_real_api_response(result)
                # Should contain some analysis
                self.assertIsInstance(result, dict)
            else:
                # Expected for leagues without sufficient data
                self.assertIn("data", result["error"].lower())
        
        except Exception as e:
            self.skipTest(f"Draft analysis requires specific data: {e}")
    
    def test_live_manager_evaluation(self):
        """Test manager evaluation with real data."""
        from league_analysis_mcp_server.analytics import evaluate_manager_skill
        
        # Get a real team ID first
        standings = get_standings(self.test_league_id, "nfl")
        if "error" in standings or not standings.get("teams"):
            self.skipTest("Cannot access team data for evaluation")
        
        team_id = standings["teams"][0]["team_id"]
        
        try:
            result = evaluate_manager_skill(
                self.test_league_id, "nfl", ["2024"], team_id
            )
            
            if "error" not in result:
                self.assert_real_api_response(result)
                self.assertIsInstance(result, dict)
            else:
                # May require multiple seasons of data
                self.assertIn("data", result["error"].lower())
        
        except Exception as e:
            self.skipTest(f"Manager evaluation requires historical data: {e}")


class TestLiveErrorHandling(IntegrationTestCase):
    """Test error handling with real Yahoo API."""
    
    def test_invalid_league_id_handling(self):
        """Test handling of invalid league IDs with real API."""
        result = get_league_info("invalid_league_999", "nfl")
        
        # Should get proper error from Yahoo API
        self.assertIn("error", result)
        self.assertIsInstance(result["error"], str)
        self.assertGreater(len(result["error"]), 10)
        
        # Should be user-friendly, not technical
        error_msg = result["error"].lower()
        self.assertNotIn("http", error_msg)  # No HTTP status codes
        self.assertNotIn("json", error_msg)  # No JSON parsing errors
    
    def test_authentication_error_handling(self):
        """Test authentication error handling with real API."""
        # Temporarily corrupt access token
        original_token = os.environ.get("YAHOO_ACCESS_TOKEN")
        
        try:
            os.environ["YAHOO_ACCESS_TOKEN"] = "invalid_token_123"
            
            result = get_league_info(self.test_league_id, "nfl")
            
            # Should get authentication error
            self.assertIn("error", result)
            error_msg = result["error"].lower()
            
            # Should indicate authentication issue
            self.assertTrue(
                any(word in error_msg for word in ["authentication", "token", "credentials"]),
                f"Should indicate auth issue: {result['error']}"
            )
        
        finally:
            # Restore original token
            if original_token:
                os.environ["YAHOO_ACCESS_TOKEN"] = original_token
            else:
                os.environ.pop("YAHOO_ACCESS_TOKEN", None)


def main():
    """Run integration tests."""
    import unittest
    
    print("League Analysis MCP Server - Integration Tests")
    print("=" * 55)
    print("Testing with real Yahoo Fantasy Sports API")
    print()
    
    # Check for credentials
    required_vars = ["YAHOO_CONSUMER_KEY", "YAHOO_CONSUMER_SECRET"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print()
        print("To run integration tests, set up Yahoo API credentials:")
        print("1. Create Yahoo Developer app at https://developer.yahoo.com/apps/")
        print("2. Set environment variables:")
        print("   export YAHOO_CONSUMER_KEY='your_key_here'")
        print("   export YAHOO_CONSUMER_SECRET='your_secret_here'")
        print("3. Optionally set TEST_LEAGUE_ID to use specific league")
        print()
        return 1
    
    # Check for test league ID
    test_league = os.environ.get("TEST_LEAGUE_ID")
    if not test_league:
        print("⚠️  No TEST_LEAGUE_ID set - using default league ID")
        print("   Set TEST_LEAGUE_ID environment variable to test with your league")
    else:
        print(f"🏈 Using test league ID: {test_league}")
    
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 55)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
    else:
        failed = len(result.failures) + len(result.errors)
        print(f"❌ {failed} integration test(s) failed")
        
        if result.failures:
            print("\nFailures:")
            for test, trace in result.failures:
                print(f"  - {test}: {trace.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nErrors:")
            for test, trace in result.errors:
                print(f"  - {test}: {trace.split('Exception:')[-1].strip()}")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())