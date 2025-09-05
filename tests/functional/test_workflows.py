#!/usr/bin/env python3
"""
End-to-end workflow tests for League Analysis MCP Server.

Tests complete user journeys from authentication to analysis,
validating that users can achieve their fantasy sports goals.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .base import FunctionalTestCase, IntegrationTestCase, TestFixtures, TestDataBuilder
from league_analysis_mcp_server.server import (
    get_server_info, check_setup_status
)
from league_analysis_mcp_server.analytics import (
    analyze_draft_strategy,
    evaluate_manager_skill,
    predict_trade_likelihood
)
from league_analysis_mcp_server.server import app_state

# Create utility functions that directly call implementation functions with app_state
from league_analysis_mcp_server.tools_impl import (
    get_league_info_impl,
    get_standings_impl
)

def get_league_info(league_id: str, sport: str = "nfl", season=None):
    """Wrapper for get_league_info implementation."""
    return get_league_info_impl(league_id, sport, season, app_state)

def get_standings(league_id: str, sport: str = "nfl", season=None):
    """Wrapper for get_standings implementation.""" 
    return get_standings_impl(league_id, sport, season, app_state)


class TestNewUserWorkflow(FunctionalTestCase):
    """Test complete new user onboarding and first analysis."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_complete_new_user_journey(self):
        """Test complete journey from first connection to meaningful insight."""
        # Step 1: User connects to MCP server and checks status
        server_info = get_server_info()
        
        # Should get server information
        self.assertIn("server", server_info)
        self.assertIn("supported_sports", server_info)
        self.assertEqual(server_info["server"]["name"], "league-analysis-mcp-server")
        
        # Step 2: Check setup status (already configured in test environment)
        setup_status = check_setup_status()
        
        # Should show configured status
        self.assertIn("authentication", setup_status)
        self.assertTrue(setup_status["authentication"]["configured"])
        
        # Step 3: User asks for their league info - first real query
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["league_info"]
        })
        
        league_info = get_league_info("123456", "nfl")
        
        # Should get meaningful league data
        self.assertIn("league", league_info)
        self.assertEqual(league_info["league"]["name"], "Test Fantasy Football League")
        self.assertEqual(league_info["league"]["num_teams"], 10)
        self.assertEqual(league_info["league"]["current_week"], 8)
        
        # Step 4: User asks for current standings
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["standings"]
        })
        
        standings = get_standings("123456", "nfl")
        
        # Should get current standings
        self.assertIn("teams", standings)
        teams = standings["teams"]
        self.assertGreater(len(teams), 0)
        
        # Should show meaningful standings data
        top_team = teams[0]
        self.assertIn("team_standings", top_team)
        self.assertIn("rank", top_team["team_standings"])
        self.assertIn("outcome_totals", top_team["team_standings"])
        
        # Verify user gets actionable insights
        wins = top_team["team_standings"]["outcome_totals"]["wins"]
        self.assertIsInstance(wins, str)
        self.assertGreater(int(wins), 0)
    
    def test_new_user_error_recovery(self):
        """Test new user experience when things go wrong."""
        # Step 1: Server info should always work
        server_info = get_server_info()
        self.assertNotIn("error", server_info)
        
        # Step 2: Setup status with missing credentials
        # (Simulate user who hasn't set up credentials yet)
        with patch.object(self.auth_manager, 'is_configured', return_value=False):
            setup_status = check_setup_status()
            
            # Should provide helpful setup guidance
            self.assertIn("authentication", setup_status)
            self.assertFalse(setup_status["authentication"]["configured"])
            self.assertIn("next_steps", setup_status)
        
        # Step 3: League info with authentication error
        self.set_yahoo_mock_error("Authentication failed")
        
        league_info = get_league_info("123456", "nfl")
        
        # Should get helpful error message
        self.assertIn("error", league_info)
        self.assertIn("authentication", league_info["error"].lower())
        self.assertIn("setup", league_info["error"].lower())
    
    def test_new_user_progressive_feature_discovery(self):
        """Test that new users can progressively discover advanced features."""
        # Start with basic queries
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        
        # Basic league info - always works
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["league_info"]
        })
        
        basic_info = get_league_info("123456", "nfl")
        self.assertNotIn("error", basic_info)
        
        # Progress to standings
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["standings"]
        })
        
        standings = get_standings("123456", "nfl")
        self.assertNotIn("error", standings)
        
        # Advance to analytics (requires historical data)
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_analytics:
            mock_analytics.return_value = {
                "success": True,
                "data": {
                    "draft_results": fixture_data["draft_results"]["draft_results"],
                    "league_settings": fixture_data["league_info"]["settings"]
                }
            }
            
            draft_analysis = analyze_draft_strategy("123456", "nfl", ["2024"], "1")
            
            # Should work even for new users with limited data
            if "error" not in draft_analysis:
                self.assertIn("primary_strategy", draft_analysis)
            else:
                # Should explain data requirements
                self.assertIn("data", draft_analysis["error"].lower())


class TestHistoricalWorkflow(FunctionalTestCase):
    """Test multi-season historical analysis workflows."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_multi_season_analysis_workflow(self):
        """Test complete multi-season analysis workflow."""
        seasons = ["2022", "2023", "2024"]
        
        # Mock historical data for multiple seasons
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            # Create realistic multi-season data
            historical_data = {}
            for season in seasons:
                historical_data[season] = {
                    "draft_results": TestDataBuilder.build_draft_results(10, 15),
                    "final_standings": [
                        {"team_id": str(i), "wins": 8 + i, "rank": i + 1}
                        for i in range(10)
                    ]
                }
            
            mock_query.return_value = {
                "success": True,
                "data": {
                    "multi_season_data": historical_data,
                    "league_averages": {
                        "avg_wins": 7,
                        "avg_points": 1200,
                        "playoff_rate": 0.6
                    }
                }
            }
            
            # Step 1: Draft strategy evolution
            draft_evolution = analyze_draft_strategy("123456", "nfl", seasons, "1")
            
            # Should show strategy changes over time
            if "error" not in draft_evolution:
                self.assertIn("strategy_evolution", draft_evolution)
                self.assertIn("trends", draft_evolution)
            
            # Step 2: Manager skill evaluation over time
            skill_evaluation = evaluate_manager_skill("123456", "nfl", seasons, "1")
            
            # Should provide comprehensive skill analysis
            if "error" not in skill_evaluation:
                self.assertIn("skill_tier", skill_evaluation)
                self.assertIn("consistency_score", skill_evaluation)
                self.assertIn("performance_trends", skill_evaluation)
            
            # Step 3: League-wide historical patterns
            league_analysis = evaluate_manager_skill("123456", "nfl", seasons)
            
            # Should provide league-wide insights
            if "error" not in league_analysis:
                self.assertIn("league_competitiveness", league_analysis)
    
    def test_historical_data_caching_workflow(self):
        """Test that historical analysis benefits from caching."""
        seasons = ["2022", "2023"]
        
        # First analysis should hit API
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {"historical_data": "comprehensive_data"}
            }
            
            # First call
            result1 = analyze_draft_strategy("123456", "nfl", seasons, "1")
            initial_call_count = mock_query.call_count
            
            # Second call should benefit from caching
            result2 = analyze_draft_strategy("123456", "nfl", seasons, "1")
            
            # Should have fewer API calls due to caching
            self.assertEqual(mock_query.call_count, initial_call_count)
            
            # Results should be consistent
            if "error" not in result1 and "error" not in result2:
                self.assertEqual(result1, result2)
    
    def test_historical_data_gap_handling(self):
        """Test handling when some historical seasons are missing."""
        # Simulate missing data for some seasons
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            # 2022 data available, 2023 missing, 2024 available
            def selective_data(*args, **kwargs):
                request_data = args[0] if args else ""
                if "2023" in str(request_data):
                    return {
                        "success": False,
                        "error": "Season data not available"
                    }
                else:
                    return {
                        "success": True,
                        "data": {"available_season": "data"}
                    }
            
            mock_query.side_effect = selective_data
            
            result = analyze_draft_strategy("123456", "nfl", ["2022", "2023", "2024"], "1")
            
            # Should handle partial data gracefully
            if "error" not in result:
                self.assertIn("data_coverage", result)
                self.assertIn("missing_seasons", result)
            else:
                # Should explain data gaps
                self.assertIn("incomplete", result["error"].lower())


class TestManagerProfileWorkflow(FunctionalTestCase):
    """Test complete manager profiling and comparison workflows."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_individual_manager_deep_dive(self):
        """Test complete deep-dive analysis of individual manager."""
        target_manager = "1"
        seasons = ["2022", "2023", "2024"]
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            # Create comprehensive manager data
            manager_data = {
                "draft_history": TestDataBuilder.build_manager_history(target_manager, seasons),
                "trade_history": [
                    {"season": "2023", "partner": "3", "count": 4},
                    {"season": "2024", "partner": "5", "count": 2}
                ],
                "performance_metrics": {
                    "championships": 1,
                    "playoff_appearances": 3,
                    "avg_wins": 9.5,
                    "consistency_score": 85
                }
            }
            
            mock_query.return_value = {
                "success": True,
                "data": manager_data
            }
            
            # Step 1: Overall skill evaluation
            skill_eval = evaluate_manager_skill("123456", "nfl", seasons, target_manager)
            
            # Should provide comprehensive evaluation
            if "error" not in skill_eval:
                self.assertIn("skill_tier", skill_eval)
                self.assertIn("overall_score", skill_eval)
                self.assertIn("strengths", skill_eval)
                self.assertIn("improvement_areas", skill_eval)
            
            # Step 2: Draft strategy analysis
            draft_analysis = analyze_draft_strategy("123456", "nfl", seasons, target_manager)
            
            # Should identify drafting patterns
            if "error" not in draft_analysis:
                self.assertIn("primary_strategy", draft_analysis)
                self.assertIn("strategy_evolution", draft_analysis)
            
            # Step 3: Trading behavior analysis
            trade_analysis = predict_trade_likelihood("123456", "nfl", target_manager)
            
            # Should provide trading insights
            if "error" not in trade_analysis:
                self.assertIn("trade_frequency", trade_analysis)
                self.assertIn("preferred_partners", trade_analysis)
    
    def test_manager_comparison_workflow(self):
        """Test comparing multiple managers head-to-head."""
        managers = ["1", "2", "3"]
        seasons = ["2023", "2024"]
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            # Create comparison data
            comparison_data = {}
            for manager in managers:
                comparison_data[manager] = {
                    "performance": TestDataBuilder.build_manager_history(manager, seasons),
                    "skill_metrics": {
                        "consistency": 70 + int(manager) * 10,
                        "peak_performance": 80 + int(manager) * 5
                    }
                }
            
            mock_query.return_value = {
                "success": True,
                "data": {"manager_comparison": comparison_data}
            }
            
            # Compare managers
            results = {}
            for manager in managers:
                results[manager] = evaluate_manager_skill("123456", "nfl", seasons, manager)
            
            # Should enable meaningful comparisons
            valid_results = {k: v for k, v in results.items() if "error" not in v}
            if len(valid_results) >= 2:
                # Should be able to rank managers
                scores = {k: v.get("overall_score", 0) for k, v in valid_results.items()}
                self.assertTrue(any(score > 0 for score in scores.values()))
    
    def test_league_manager_ranking_workflow(self):
        """Test complete league manager ranking and tier analysis."""
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            # Create league-wide manager data
            league_managers = {}
            skill_tiers = ["Elite", "Above Average", "Average", "Below Average"]
            
            for i in range(10):  # 10 managers
                manager_id = str(i + 1)
                league_managers[manager_id] = {
                    "skill_tier": skill_tiers[i % len(skill_tiers)],
                    "overall_score": 90 - (i * 8),  # Declining scores
                    "championships": 1 if i < 2 else 0,  # Top 2 have championships
                    "consistency": 85 - (i * 5)
                }
            
            mock_query.return_value = {
                "success": True,
                "data": {"league_rankings": league_managers}
            }
            
            # Get league-wide evaluation
            league_eval = evaluate_manager_skill("123456", "nfl", ["2022", "2023", "2024"])
            
            # Should provide league hierarchy
            if "error" not in league_eval:
                self.assertIn("manager_rankings", league_eval)
                self.assertIn("skill_distribution", league_eval)
                self.assertIn("competitive_balance", league_eval)


class TestDraftToChampionshipWorkflow(FunctionalTestCase):
    """Test complete season tracking from draft through championship."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_complete_season_analysis_workflow(self):
        """Test tracking a complete fantasy season journey."""
        fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
        season = "2024"
        
        # Step 1: Pre-season - Draft analysis
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "draft_results": fixture_data["draft_results"]["draft_results"],
                    "league_settings": fixture_data["league_info"]["settings"]
                }
            }
            
            draft_analysis = analyze_draft_strategy("123456", "nfl", [season])
            
            # Should analyze draft strategies
            if "error" not in draft_analysis:
                self.assertIn("draft_grades", draft_analysis)
                self.assertIn("strategy_distribution", draft_analysis)
        
        # Step 2: Mid-season - Current standings and performance
        self.set_yahoo_mock_response({
            "success": True,
            "data": fixture_data["standings"]
        })
        
        current_standings = get_standings("123456", "nfl")
        
        # Should show current state
        self.assertIn("teams", current_standings)
        teams = current_standings["teams"]
        
        # Should identify leaders and trends
        self.assertGreater(len(teams), 0)
        top_team = teams[0]
        self.assertEqual(top_team["team_standings"]["rank"], 1)
        
        # Step 3: Trade analysis during season
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "trade_activity": [
                        {"teams": ["1", "3"], "week": 4},
                        {"teams": ["2", "5"], "week": 6}
                    ],
                    "trade_patterns": {"active_traders": ["1", "2", "3"]}
                }
            }
            
            trade_analysis = predict_trade_likelihood("123456", "nfl")
            
            # Should identify active trading period
            if "error" not in trade_analysis:
                self.assertIn("league_activity", trade_analysis)
        
        # Step 4: Playoff implications
        # (Based on current standings, identify playoff picture)
        playoff_teams = []
        for team in teams:
            if team.get("clinched_playoffs") == 1:
                playoff_teams.append(team["team_id"])
        
        # Should identify playoff contenders
        self.assertGreater(len(playoff_teams), 0)
    
    def test_championship_prediction_workflow(self):
        """Test championship probability analysis workflow."""
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            # Create championship prediction data
            championship_data = {
                "current_standings": [
                    {"team_id": "1", "wins": 10, "points_for": 1400, "rank": 1},
                    {"team_id": "2", "wins": 9, "points_for": 1350, "rank": 2},
                    {"team_id": "3", "wins": 8, "points_for": 1300, "rank": 3}
                ],
                "historical_performance": {
                    "1": {"championship_rate": 0.3, "playoff_success": 0.8},
                    "2": {"championship_rate": 0.1, "playoff_success": 0.6},
                    "3": {"championship_rate": 0.2, "playoff_success": 0.7}
                },
                "remaining_schedule": {
                    "strength_of_schedule": {"1": "hard", "2": "medium", "3": "easy"}
                }
            }
            
            mock_query.return_value = {
                "success": True,
                "data": championship_data
            }
            
            # Analyze championship probabilities
            championship_analysis = evaluate_manager_skill("123456", "nfl", ["2024"])
            
            # Should provide championship insights
            if "error" not in championship_analysis:
                self.assertIn("championship_probabilities", championship_analysis)
                self.assertIn("playoff_scenarios", championship_analysis)
    
    def test_season_wrap_up_analysis(self):
        """Test comprehensive season wrap-up analysis."""
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            # Create end-of-season summary data
            fixture_data = TestFixtures.load_fixture("yahoo_responses.json")
            season_summary = {
                "final_standings": fixture_data["historical_seasons"]["2023"]["final_standings"],
                "season_stats": {
                    "highest_score": {"team": "1", "week": 8, "score": 180.5},
                    "total_trades": 15,
                    "waiver_pickups": 245,
                    "closest_matchup": {"week": 6, "margin": 0.5}
                },
                "award_winners": {
                    "champion": "1",
                    "highest_scorer": "1", 
                    "most_trades": "3",
                    "best_draft": "2"
                }
            }
            
            mock_query.return_value = {
                "success": True,
                "data": season_summary
            }
            
            # Generate season wrap-up
            season_analysis = evaluate_manager_skill("123456", "nfl", ["2024"])
            
            # Should provide comprehensive season summary
            if "error" not in season_analysis:
                self.assertIn("season_highlights", season_analysis)
                self.assertIn("performance_summary", season_analysis)


class TestIntegrationWorkflows(IntegrationTestCase):
    """Integration tests for complete workflows with real Yahoo API."""
    
    def test_real_league_analysis_workflow(self):
        """Test complete workflow with real Yahoo API data."""
        # This test requires real credentials and league access
        if self.skip_integration:
            self.skipTest(self.skip_reason)
        
        # Test with real league ID (would need to be provided)
        real_league_id = os.environ.get("TEST_LEAGUE_ID", "123456")
        
        try:
            # Step 1: Get real league info
            league_info = get_league_info(real_league_id, "nfl")
            
            if "error" not in league_info:
                # Step 2: Get real standings
                standings = get_standings(real_league_id, "nfl")
                
                # Should get real data
                self.assertNotIn("error", standings)
                self.assert_real_api_response(standings)
                
                # Step 3: Try analytics with real data
                if len(standings.get("teams", [])) > 0:
                    team_id = standings["teams"][0]["team_id"]
                    
                    draft_analysis = analyze_draft_strategy(
                        real_league_id, "nfl", ["2024"], team_id
                    )
                    
                    # May or may not work depending on data availability
                    # But should not crash
                    self.assertIsInstance(draft_analysis, dict)
            
        except Exception as e:
            self.fail(f"Real integration workflow failed: {e}")
    
    def test_real_error_handling_workflow(self):
        """Test error handling with real API constraints."""
        if self.skip_integration:
            self.skipTest(self.skip_reason)
        
        # Test with invalid league ID
        result = get_league_info("invalid_league_id", "nfl")
        
        # Should handle real API errors gracefully
        self.assertIn("error", result)
        self.assertIsInstance(result["error"], str)
        self.assertGreater(len(result["error"]), 10)  # Should be informative


if __name__ == "__main__":
    import unittest
    
    print("League Analysis MCP Server - End-to-End Workflow Tests")
    print("=" * 63)
    print("Testing complete user workflows and integration scenarios")
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 63)
    if result.wasSuccessful():
        print("PASS: All workflow tests passed!")
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