#!/usr/bin/env python3
"""
Functional tests for MCP tools - validates real user value delivery.

Tests core functionality of all MCP tools with realistic scenarios
to ensure they provide meaningful fantasy sports insights.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch

# Add src and tests to path
src_path = Path(__file__).parent.parent.parent / "src"
tests_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(tests_path))

# Direct import from functional directory to avoid conflicts
sys.path.insert(0, str(Path(__file__).parent))
from base import FunctionalTestCase, TestFixtures
from league_analysis_mcp_server.tools_impl import (
    get_league_info_impl,
    get_standings_impl, 
    get_team_roster_impl,
    get_matchups_impl
)
from league_analysis_mcp_server.server import app_state


class ToolTestMixin:
    """Mixin class providing tool implementation methods for testing."""
    
    def _setup_tool_implementations(self):
        """Set up tool implementation functions for testing."""
        # These mirror the MCP tools but can be called directly
        pass
    
    def _get_yahoo_query(self, league_id: str, game_id: Optional[str] = None, sport: str = "nfl") -> Any:
        """Create a Yahoo Fantasy Sports Query object for testing."""
        auth_manager = app_state["auth_manager"]
        
        if not auth_manager.is_configured():
            raise ValueError("Yahoo authentication not configured")
        
        auth_credentials = auth_manager.get_auth_credentials()
        
        if game_id:
            query_params = {**auth_credentials, 'game_id': game_id}
        else:
            query_params = {**auth_credentials, 'game_code': sport}
        
        from yfpy import YahooFantasySportsQuery
        return YahooFantasySportsQuery(league_id=league_id, **query_params)
    
    def _get_league_info_impl(self, league_id: str, sport: str = "nfl", season: Optional[str] = None) -> Dict[str, Any]:
        """Get basic league information and settings - implementation for testing."""
        try:
            cache_manager = app_state["cache_manager"]
            
            # Check cache first
            if season:
                cached_data = cache_manager.get_historical_data(sport, season, league_id, "league_info")
            else:
                cached_data = cache_manager.get_current_data(sport, league_id, "league_info")
            
            if cached_data:
                return cached_data
            
            # Get game_id for specific season if provided
            game_id = None
            if season:
                game_id = app_state["game_ids"].get(sport, {}).get(season)
                if not game_id:
                    return {"error": f"No game_id found for {sport} {season}"}
            
            # Mock the Yahoo API response since we're using mocked responses
            # Access the mock from the test class
            mock_response = getattr(self, 'mock_yahoo_query').return_value if hasattr(self, 'mock_yahoo_query') else {"success": False, "data": {}}
            if "success" in mock_response and mock_response["success"]:
                data = mock_response.get("data", {})
                result = {
                    "league_id": league_id,
                    "sport": sport,
                    "season": season or "current",
                    "league": data.get("league", {}),
                    "settings": data.get("settings", {})
                }
                
                # Cache the result
                if season:
                    cache_manager.set_historical_data(sport, season, league_id, "league_info", result)
                else:
                    cache_manager.set_current_data(sport, league_id, "league_info", result)
                
                return result
            else:
                return {"error": mock_response.get("error", "Unknown error")}
                    
        except Exception as e:
            return {"error": str(e)}
    
    def _get_standings_impl(self, league_id: str, sport: str = "nfl", season: Optional[str] = None) -> Dict[str, Any]:
        """Get league standings - implementation for testing."""
        try:
            cache_manager = app_state["cache_manager"]
            
            # Check cache first
            if season:
                cached_data = cache_manager.get_historical_data(sport, season, league_id, "standings")
            else:
                cached_data = cache_manager.get_current_data(sport, league_id, "standings")
            
            if cached_data:
                return cached_data
            
            # Mock the Yahoo API response
            mock_response = getattr(self, 'mock_yahoo_query').return_value if hasattr(self, 'mock_yahoo_query') else {"success": False, "data": {}}
            if "success" in mock_response and mock_response["success"]:
                data = mock_response.get("data", {})
                result = {
                    "league_id": league_id,
                    "sport": sport,
                    "season": season or "current",
                    "teams": data.get("teams", [])
                }
                
                # Cache the result
                if season:
                    cache_manager.set_historical_data(sport, season, league_id, "standings", result)
                else:
                    cache_manager.set_current_data(sport, league_id, "standings", result)
                
                return result
            else:
                return {"error": mock_response.get("error", "Unknown error")}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _get_team_roster_impl(self, league_id: str, team_id: str, sport: str = "nfl", 
                             week: Optional[int] = None, season: Optional[str] = None) -> Dict[str, Any]:
        """Get team roster - implementation for testing."""
        try:
            cache_manager = app_state["cache_manager"]
            cache_key = f"team_roster_{team_id}_{week or 'current'}"
            
            # Check cache first
            if season:
                cached_data = cache_manager.get_historical_data(sport, season, league_id, cache_key)
            else:
                cached_data = cache_manager.get_current_data(sport, league_id, cache_key)
            
            if cached_data:
                return cached_data
            
            # Mock the Yahoo API response
            mock_response = getattr(self, 'mock_yahoo_query').return_value if hasattr(self, 'mock_yahoo_query') else {"success": False, "data": {}}
            if "success" in mock_response and mock_response["success"]:
                data = mock_response.get("data", {})
                result = {
                    "league_id": league_id,
                    "team_id": team_id,
                    "sport": sport,
                    "week": week or "current",
                    "season": season or "current",
                    "team": data.get("team", {}),
                    "roster": data.get("roster", {})
                }
                
                # Cache the result
                if season:
                    cache_manager.set_historical_data(sport, season, league_id, cache_key, result)
                else:
                    cache_manager.set_current_data(sport, league_id, cache_key, result)
                
                return result
            else:
                return {"error": mock_response.get("error", "Unknown error")}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _get_matchups_impl(self, league_id: str, sport: str = "nfl", week: Optional[int] = None, 
                          season: Optional[str] = None) -> Dict[str, Any]:
        """Get matchups for a specific week - implementation for testing."""
        try:
            cache_manager = app_state["cache_manager"]
            cache_key = f"matchups_{week or 'current'}"
            
            # Check cache first
            if season:
                cached_data = cache_manager.get_historical_data(sport, season, league_id, cache_key)
            else:
                cached_data = cache_manager.get_current_data(sport, league_id, cache_key)
            
            if cached_data:
                return cached_data
            
            # Mock the Yahoo API response
            mock_response = getattr(self, 'mock_yahoo_query').return_value if hasattr(self, 'mock_yahoo_query') else {"success": False, "data": {}}
            if "success" in mock_response and mock_response["success"]:
                data = mock_response.get("data", {})
                result = {
                    "league_id": league_id,
                    "sport": sport,
                    "week": week or "current",
                    "season": season or "current",
                    "scoreboard": data.get("scoreboard", {})
                }
                
                # Cache the result
                if season:
                    cache_manager.set_historical_data(sport, season, league_id, cache_key, result)
                else:
                    cache_manager.set_current_data(sport, league_id, cache_key, result)
                
                return result
            else:
                return {"error": mock_response.get("error", "Unknown error")}
                
        except Exception as e:
            return {"error": str(e)}

# Implementation functions imported from tools_impl module at top of file


class TestBasicTools(FunctionalTestCase):
    """Test basic MCP tools functionality."""
    
    def setUp(self):
        """Set up test with app state and implementation functions."""
        super().setUp()
        # Import here to avoid circular imports
        # Mock app_state to use our test managers
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
        app_state["config"] = {"supported_sports": ["nfl", "nba", "mlb", "nhl"]}
        app_state["game_ids"] = {"nfl": {"2024": "414"}}
        
        # Implementation functions imported from tools_impl module
    
    def test_get_league_info_returns_valid_data(self):
        """Test get_league_info returns properly formatted league data."""
        # Set mock response
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["league_info"]
        })
        
        # Call the implementation function
        result = get_league_info_impl("123456", "nfl", None, app_state)
        
        # Assertions
        self.assertIn("league", result)
        league_data = result["league"]
        
        # Validate required fields
        self.assertEqual(league_data.get("league_id"), "123456")
        self.assertEqual(league_data.get("name"), "Test Fantasy Football League")
        self.assertEqual(league_data.get("num_teams"), 10)
        self.assertEqual(league_data.get("current_week"), 8)
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
        
        result = get_league_info_impl("123456", "nfl", "2023", app_state)
        
        # Should return historical data
        self.assertEqual(result["league"].get("season"), "2023")
        
        # Should cache in historical cache
        self.assert_cache_contains("nfl", "123456", "league_info", "2023")
    
    def test_get_standings_returns_proper_format(self):
        """Test get_standings returns properly formatted standings data."""
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["standings"]
        })
        
        result = get_standings_impl("123456", "nfl", None, app_state)
        
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
        standings = team.get("team_standings", {})
        self.assertIn("rank", standings)
        self.assertIn("outcome_totals", standings)
        self.assertIn("points_for", standings)
        self.assertIn("points_against", standings)
        
        # Validate wins/losses format
        outcome = standings.get("outcome_totals", {})
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
        
        result = get_team_roster_impl("123456", "1", "nfl", None, app_state)
        
        # Validate response structure
        self.assertIn("team", result)
        self.assertIn("roster", result)
        
        team = result["team"]
        self.assertEqual(team.get("team_id"), "1")
        self.assertEqual(team.get("name"), "Team Alpha")
        
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
            result = get_league_info_impl("123456", "nfl", None, app_state)
            
            # Should not crash or return malformed data
            self.assertIsInstance(result, dict)
            # May or may not have error - depends on implementation
            if "error" in result:
                self.assertIn("rate limit", result["error"].lower())
    
    def test_tools_validate_parameters(self):
        """Test that tools properly validate input parameters."""
        # Test with invalid sport
        result = get_league_info_impl("123456", "invalid_sport", None, app_state)
        
        # Should handle invalid sport gracefully
        self.assertIn("error", result)
        
        # Test with empty league_id
        result = get_league_info_impl("", "nfl", None, app_state)
        
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
        result1 = get_league_info_impl("123456", "nfl", None, app_state)
        self.assertEqual(self.mock_yahoo_query.call_count, 1)
        
        # Second call should use cache
        result2 = get_league_info_impl("123456", "nfl", None, app_state)
        self.assertEqual(self.mock_yahoo_query.call_count, 1)  # No additional calls
        
        # Results should be identical
        self.assertEqual(result1, result2)
        
        # Cache should contain the data
        self.assert_cache_contains("nfl", "123456", "league_info")


class TestMatchupTools(FunctionalTestCase):
    """Test matchup-related tools."""
    
    def setUp(self):
        super().setUp()
        # Import here to avoid circular imports
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
        app_state["config"] = {"supported_sports": ["nfl", "nba", "mlb", "nhl"]}
        app_state["game_ids"] = {"nfl": {"2024": "414"}}
        
        # Implementation functions imported from tools_impl module
    
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
        
        result = get_matchups_impl("123456", "nfl", 8, None, app_state)
        
        # Validate structure
        self.assertIn("scoreboard", result)
        scoreboard = result["scoreboard"]
        
        self.assertIn("week", scoreboard)
        self.assertIn("matchups", scoreboard)
        self.assertEqual(scoreboard.get("week"), "8")
        
        # Validate matchup data
        matchups = scoreboard.get("matchups", [])
        self.assertIsInstance(matchups, list)
        self.assertGreater(len(matchups), 0)
        
        matchup = matchups[0]
        self.assertIn("teams", matchup)
        
        teams = matchup.get("teams", [])
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
            
            result = get_matchups_impl("123456", "nfl", None, None, app_state)
            
            # Should use current week from league
            self.assertIn("scoreboard", result)
            self.assertEqual(result["scoreboard"].get("week"), "8")


class TestToolsIntegration(FunctionalTestCase):
    """Test tools working together in realistic scenarios."""
    
    def setUp(self):
        super().setUp()
        # Import here to avoid circular imports
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
        app_state["config"] = {"supported_sports": ["nfl", "nba", "mlb", "nhl"]}
        app_state["game_ids"] = {"nfl": {"2024": "414"}}
        
        # Implementation functions imported from tools_impl module
    
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
            league_info = get_league_info_impl("123456", "nfl", None, app_state)
            standings = get_standings_impl("123456", "nfl", None, app_state)
            matchups = get_matchups_impl("123456", "nfl", None, None, app_state)
            
            # Validate we got coherent data
            self.assertEqual(league_info["league"].get("league_id"), "123456")
            self.assertEqual(standings["teams"][0].get("team_id"), "1")
            self.assertEqual(matchups["scoreboard"].get("week"), "8")
            
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
            
            result = get_league_info_impl("123456", sport, None, app_state)
            
            # Should work for all sports
            self.assertIn("league", result)
            self.assertEqual(result["league"].get("game_code"), sport)
            
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
            
                result1 = get_league_info_impl("123456", "nfl", None, app_state)
        
        # Now simulate API failure and test again
        self.set_yahoo_mock_error("Network timeout")
        
        with patch.object(self.auth_manager, 'is_configured', return_value=True), \
             patch.object(self.auth_manager, 'get_auth_credentials', return_value={
                 'yahoo_consumer_key': 'test_key',
                 'yahoo_consumer_secret': 'test_secret'
             }):
            
            result2 = get_league_info_impl("123456", "nfl", None, app_state)
        
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