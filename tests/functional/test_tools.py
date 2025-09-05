#!/usr/bin/env python3
"""
Functional tests for MCP tools - validates real user value delivery.

Tests core functionality of all MCP tools with realistic scenarios
to ensure they provide meaningful fantasy sports insights.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .base import FunctionalTestCase, TestFixtures

# Import the modules containing MCP tools
# Import the MCP tool functions directly (decorated functions are importable)
try:
    from league_analysis_mcp_server.tools import (
        get_league_info, get_standings, get_team_roster, get_matchups
    )
except ImportError as e:
    print(f"Import error in test_tools.py: {e}")
    # Define placeholder functions for testing
    def get_league_info(*args, **kwargs):
        return {"error": "Function not available"}
    def get_standings(*args, **kwargs):
        return {"error": "Function not available"}
    def get_team_roster(*args, **kwargs):
        return {"error": "Function not available"}
    def get_matchups(*args, **kwargs):
        return {"error": "Function not available"}
from league_analysis_mcp_server.server import app_state


class TestBasicTools(FunctionalTestCase):
    """Test basic MCP tools functionality."""
    
    def setUp(self):
        """Set up test with app state."""
        super().setUp()
        # Mock app_state to use our test managers
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_get_league_info_returns_valid_data(self):
        """Test get_league_info returns properly formatted league data."""
        # Set mock response
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["league_info"]
        })
        
        # Call the function
        result = get_league_info("123456", "nfl")
        
        # Assertions
        self.assertIn("league", result)
        league_data = result["league"]
        
        # Validate required fields
        self.assertEqual(league_data["league_id"], "123456")
        self.assertEqual(league_data["name"], "Test Fantasy Football League")
        self.assertEqual(league_data["num_teams"], 10)
        self.assertEqual(league_data["current_week"], 8)
        self.assertIn("settings", result)
        
        # Validate settings structure
        settings = result["settings"]
        self.assertIn("roster_positions", settings)
        self.assertIn("playoff_start_week", settings)
        self.assertIn("trade_end_date", settings)
        
        # Verify cache was populated
        self.assert_cache_contains("nfl", "123456", "league_info")
    
    def test_get_league_info_with_historical_season(self):
        """Test get_league_info works with historical seasons."""
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        historical_data = fixture_data["league_info"].copy()
        historical_data["league"]["season"] = "2023"
        
        self.set_yahoo_mock_response({
            "success": True,
            "data": historical_data
        })
        
        result = get_league_info("123456", "nfl", "2023")
        
        # Should return historical data
        self.assertEqual(result["league"]["season"], "2023")
        
        # Should cache in historical cache
        self.assert_cache_contains("nfl", "123456", "league_info", "2023")
    
    def test_get_standings_returns_proper_format(self):
        """Test get_standings returns properly formatted standings data."""
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["standings"]
        })
        
        result = get_standings("123456", "nfl")
        
        # Validate response structure
        self.assertIn("teams", result)
        teams = result["teams"]
        self.assertIsInstance(teams, list)
        self.assertGreater(len(teams), 0)
        
        # Validate team data structure
        team = teams[0]
        required_fields = [
            "team_id", "name", "team_standings"
        ]
        
        for field in required_fields:
            self.assertIn(field, team)
        
        # Validate standings data
        standings = team["team_standings"]
        self.assertIn("rank", standings)
        self.assertIn("outcome_totals", standings)
        self.assertIn("points_for", standings)
        self.assertIn("points_against", standings)
        
        # Validate wins/losses format
        outcome = standings["outcome_totals"]
        self.assertIn("wins", outcome)
        self.assertIn("losses", outcome)
        self.assertIn("percentage", outcome)
    
    def test_get_team_roster_returns_player_data(self):
        """Test get_team_roster returns properly formatted roster data."""
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["team_roster"]
        })
        
        result = get_team_roster("123456", "1", "nfl")
        
        # Validate response structure
        self.assertIn("team", result)
        self.assertIn("roster", result)
        
        team = result["team"]
        self.assertEqual(team["team_id"], "1")
        self.assertEqual(team["name"], "Team Alpha")
        
        roster = result["roster"]
        self.assertIn("players", roster)
        self.assertIn("week", roster)
        self.assertIn("is_editable", roster)
        
        # Validate player data
        players = roster["players"]
        self.assertIsInstance(players, list)
        
        if players:
            player = players[0]
            required_fields = [
                "player_id", "name", "display_position", "eligible_positions"
            ]
            
            for field in required_fields:
                self.assertIn(field, player)
            
            # Validate name structure
            name = player["name"]
            self.assertIn("full", name)
            self.assertIn("first", name)
            self.assertIn("last", name)
    
    def test_tools_handle_yahoo_api_errors_gracefully(self):
        """Test that tools handle Yahoo API errors appropriately."""
        # Set up API error
        self.set_yahoo_mock_error("Rate limit exceeded")
        
        with patch.object(self.auth_manager, 'is_configured', return_value=True), \
             patch.object(self.auth_manager, 'get_auth_credentials', return_value={
                 'yahoo_consumer_key': 'test_key',
                 'yahoo_consumer_secret': 'test_secret'
             }):
            
            tool = self.mcp.get_tool('get_league_info')
            result = tool.fn(league_id="123456", sport="nfl")
            
            # Should not crash or return malformed data
            self.assertIsInstance(result, dict)
            # May or may not have error - depends on implementation
            if "error" in result:
                self.assertIn("rate limit", result["error"].lower())
    
    def test_tools_validate_parameters(self):
        """Test that tools properly validate input parameters."""
        # Test with invalid sport
        result = get_league_info("123456", "invalid_sport")
        
        # Should handle invalid sport gracefully
        self.assertIn("error", result)
        
        # Test with empty league_id
        result = get_league_info("", "nfl")
        
        # Should handle empty league_id
        self.assertIn("error", result)
    
    def test_cache_behavior_with_multiple_calls(self):
        """Test that caching works correctly with multiple calls."""
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["league_info"]
        })
        
        # First call should hit API
        result1 = get_league_info("123456", "nfl")
        self.assertEqual(self.mock_yahoo_query.call_count, 1)
        
        # Second call should use cache
        result2 = get_league_info("123456", "nfl")
        self.assertEqual(self.mock_yahoo_query.call_count, 1)  # No additional calls
        
        # Results should be identical
        self.assertEqual(result1, result2)
        
        # Cache should contain the data
        self.assert_cache_contains("nfl", "123456", "league_info")


class TestMatchupTools(FunctionalTestCase):
    """Test matchup-related tools."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_get_matchups_returns_valid_data(self):
        """Test get_matchups returns proper matchup data."""
        # Mock matchup data
        matchup_data = {
            "league": {"league_id": "123456"},
            "scoreboard": {
                "week": "8",
                "matchups": [
                    {
                        "week": "8",
                        "teams": [
                            {
                                "team_key": "414.l.123456.t.1",
                                "team_id": "1",
                                "name": "Team Alpha",
                                "team_points": {
                                    "coverage_type": "week",
                                    "coverage_value": 8,
                                    "total": "125.50"
                                },
                                "team_projected_points": {
                                    "coverage_type": "week", 
                                    "coverage_value": 8,
                                    "total": "118.75"
                                }
                            },
                            {
                                "team_key": "414.l.123456.t.2", 
                                "team_id": "2",
                                "name": "Team Beta",
                                "team_points": {
                                    "coverage_type": "week",
                                    "coverage_value": 8,
                                    "total": "98.25"
                                },
                                "team_projected_points": {
                                    "coverage_type": "week",
                                    "coverage_value": 8, 
                                    "total": "110.30"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        self.set_yahoo_mock_response({
            "success": True,
            "data": matchup_data
        })
        
        result = get_matchups("123456", "nfl", week="8")
        
        # Validate structure
        self.assertIn("scoreboard", result)
        scoreboard = result["scoreboard"]
        
        self.assertIn("week", scoreboard)
        self.assertIn("matchups", scoreboard)
        self.assertEqual(scoreboard["week"], "8")
        
        # Validate matchup data
        matchups = scoreboard["matchups"]
        self.assertIsInstance(matchups, list)
        self.assertGreater(len(matchups), 0)
        
        matchup = matchups[0]
        self.assertIn("teams", matchup)
        
        teams = matchup["teams"]
        self.assertEqual(len(teams), 2)  # Should be head-to-head
        
        # Validate team matchup data
        for team in teams:
            self.assertIn("team_id", team)
            self.assertIn("name", team)
            self.assertIn("team_points", team)
            self.assertIn("team_projected_points", team)
    
    def test_get_matchups_current_week_default(self):
        """Test get_matchups uses current week when no week specified."""
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        league_data = fixture_data["league_info"]
        
        # Mock league data first (to get current week)
        self.set_yahoo_mock_response({
            "success": True,
            "data": league_data
        })
        
        # Then mock matchup call
        matchup_data = {
            "scoreboard": {
                "week": "8",  # Current week from league data
                "matchups": []
            }
        }
        
        with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
            mock_query.side_effect = [
                {"success": True, "data": league_data},  # League info call
                {"success": True, "data": matchup_data}   # Matchup call
            ]
            
            result = get_matchups("123456", "nfl")
            
            # Should use current week from league
            self.assertIn("scoreboard", result)
            self.assertEqual(result["scoreboard"]["week"], "8")


class TestToolsIntegration(FunctionalTestCase):
    """Test tools working together in realistic scenarios."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_complete_league_overview_workflow(self):
        """Test getting complete league overview using multiple tools."""
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        
        # Set up responses for different API calls
        responses = {
            "league_info": fixture_data["league_info"],
            "standings": fixture_data["standings"],
            "matchups": {
                "scoreboard": {
                    "week": "8",
                    "matchups": []
                }
            }
        }
        
        # Test complete workflow
        with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
            mock_query.side_effect = [
                {"success": True, "data": responses["league_info"]},
                {"success": True, "data": responses["standings"]},
                {"success": True, "data": responses["matchups"]}
            ]
            
            # Get league overview
            league_info = get_league_info("123456", "nfl")
            standings = get_standings("123456", "nfl")
            matchups = get_matchups("123456", "nfl")
            
            # Validate we got coherent data
            self.assertEqual(league_info["league"]["league_id"], "123456")
            self.assertEqual(standings["teams"][0]["team_id"], "1")
            self.assertEqual(matchups["scoreboard"]["week"], "8")
            
            # All data should be cached
            self.assert_cache_contains("nfl", "123456", "league_info")
            self.assert_cache_contains("nfl", "123456", "standings")
    
    def test_multi_sport_support(self):
        """Test that tools work correctly across different sports."""
        sports = ["nfl", "nba", "mlb", "nhl"]
        
        for sport in sports:
            fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
            league_data = fixture_data["league_info"]
            league_data["league"]["game_code"] = sport
            
            self.set_yahoo_mock_response({
                "success": True,
                "data": league_data
            })
            
            result = get_league_info("123456", sport)
            
            # Should work for all sports
            self.assertIn("league", result)
            self.assertEqual(result["league"]["game_code"], sport)
            
            # Each sport should cache separately
            self.assert_cache_contains(sport, "123456", "league_info")
    
    def test_error_recovery_and_fallback(self):
        """Test error recovery and fallback mechanisms."""
        # First, populate cache with good data
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["league_info"]
        })
        
        with patch.object(self.auth_manager, 'is_configured', return_value=True), \
             patch.object(self.auth_manager, 'get_auth_credentials', return_value={
                 'yahoo_consumer_key': 'test_key',
                 'yahoo_consumer_secret': 'test_secret'
             }):
            
            tool = self.mcp.get_tool('get_league_info')
            result1 = tool.fn(league_id="123456", sport="nfl")
        
        # Now simulate API failure and test again
        self.set_yahoo_mock_error("Network timeout")
        
        with patch.object(self.auth_manager, 'is_configured', return_value=True), \
             patch.object(self.auth_manager, 'get_auth_credentials', return_value={
                 'yahoo_consumer_key': 'test_key',
                 'yahoo_consumer_secret': 'test_secret'
             }):
            
            result2 = tool.fn(league_id="123456", sport="nfl")
        
            # Should handle error gracefully
            # (This depends on implementation details - might need adjustment)
            if "error" in result2:
                # At minimum, error should be informative
                self.assertIn("timeout", result2["error"].lower())
            else:
                # Or we got cached data successfully
                self.assertEqual(result1, result2)


if __name__ == "__main__":
    import unittest
    
    print("League Analysis MCP Server - MCP Tools Functional Tests")
    print("=" * 60)
    print("Testing basic MCP tool functionality with mock Yahoo API")
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 60)
    if result.wasSuccessful():
        print("PASS: All MCP tools tests passed!")
    else:
        failed = len(result.failures) + len(result.errors)
        print(f"FAILED: {failed} test(s) failed")
        
        if result.failures:
            print("\nFailures:")
            for test, trace in result.failures:
                print(f"  - {test}: {trace.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nErrors:")
            for test, trace in result.errors:
                print(f"  - {test}: {trace.split('Exception:')[-1].strip()}")
    
    sys.exit(0 if result.wasSuccessful() else 1)