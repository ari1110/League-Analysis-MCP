#!/usr/bin/env python3
"""
Analytics validation tests for League Analysis MCP Server.

Tests accuracy and effectiveness of fantasy sports analytics algorithms
including manager profiling, draft strategy classification, and predictions.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .base import FunctionalTestCase, TestFixtures, TestDataBuilder
from league_analysis_mcp_server.analytics import (
    analyze_draft_strategy, predict_trade_likelihood, evaluate_manager_skill
)
from league_analysis_mcp_server.server import app_state


class TestManagerScoring(FunctionalTestCase):
    """Test manager skill evaluation accuracy."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_manager_skill_evaluation_elite_tier(self):
        """Test skill evaluation for elite-performing managers."""
        # Create elite manager history
        elite_history = TestDataBuilder.build_manager_history(
            team_id="1",
            seasons=["2022", "2023", "2024"]
        )
        
        # Mock the historical data retrieval
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "manager_history": elite_history,
                    "league_averages": {
                        "avg_wins": 7,
                        "avg_points": 1200,
                        "playoff_rate": 0.6
                    }
                }
            }
            
            result = evaluate_manager_skill("123456", "nfl", ["2022", "2023", "2024"], "1")
            
            # Should classify as elite
            self.assertIn("skill_tier", result)
            self.assertEqual(result["skill_tier"], "Elite")
            
            # Should have high scores
            self.assertIn("overall_score", result)
            self.assertGreater(result["overall_score"], 85)
            
            # Should have detailed metrics
            self.assertIn("consistency_score", result)
            self.assertIn("peak_performance", result)
            self.assertIn("championship_rate", result)
    
    def test_manager_skill_evaluation_struggling_tier(self):
        """Test skill evaluation for struggling managers."""
        # Create struggling manager history
        struggling_history = {
            "2022": {"team_id": "5", "wins": 4, "losses": 10, "points_for": 900, "playoff_finish": 8, "championship": False},
            "2023": {"team_id": "5", "wins": 3, "losses": 11, "points_for": 950, "playoff_finish": 10, "championship": False},
            "2024": {"team_id": "5", "wins": 5, "losses": 9, "points_for": 1000, "playoff_finish": 7, "championship": False}
        }
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "manager_history": struggling_history,
                    "league_averages": {
                        "avg_wins": 7,
                        "avg_points": 1200,
                        "playoff_rate": 0.6
                    }
                }
            }
            
            result = evaluate_manager_skill("123456", "nfl", ["2022", "2023", "2024"], "5")
            
            # Should classify in lower tier
            self.assertIn("skill_tier", result)
            self.assertIn(result["skill_tier"], ["Below Average", "Needs Improvement"])
            
            # Should have lower scores
            self.assertIn("overall_score", result)
            self.assertLess(result["overall_score"], 60)
            
            # Should identify areas for improvement
            self.assertIn("improvement_areas", result)
            self.assertIsInstance(result["improvement_areas"], list)
    
    def test_manager_skill_consistency_scoring(self):
        """Test consistency scoring algorithm accuracy."""
        # Create inconsistent manager history
        inconsistent_history = {
            "2022": {"team_id": "3", "wins": 12, "losses": 2, "points_for": 1500, "playoff_finish": 1, "championship": True},
            "2023": {"team_id": "3", "wins": 4, "losses": 10, "points_for": 1000, "playoff_finish": 9, "championship": False},
            "2024": {"team_id": "3", "wins": 11, "losses": 3, "points_for": 1450, "playoff_finish": 2, "championship": False}
        }
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "manager_history": inconsistent_history,
                    "league_averages": {
                        "avg_wins": 7,
                        "avg_points": 1200,
                        "playoff_rate": 0.6
                    }
                }
            }
            
            result = evaluate_manager_skill("123456", "nfl", ["2022", "2023", "2024"], "3")
            
            # Should detect inconsistency
            self.assertIn("consistency_score", result)
            self.assertLess(result["consistency_score"], 70)  # Low consistency
            
            # But should recognize high peak performance
            self.assertIn("peak_performance", result)
            self.assertGreater(result["peak_performance"], 90)
    
    def test_skill_evaluation_with_insufficient_data(self):
        """Test skill evaluation with limited historical data."""
        # Single season data
        limited_history = {
            "2024": {"team_id": "2", "wins": 8, "losses": 6, "points_for": 1200, "playoff_finish": 4, "championship": False}
        }
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "manager_history": limited_history,
                    "league_averages": {
                        "avg_wins": 7,
                        "avg_points": 1200,
                        "playoff_rate": 0.6
                    }
                }
            }
            
            result = evaluate_manager_skill("123456", "nfl", ["2024"], "2")
            
            # Should indicate limited data
            self.assertIn("data_quality", result)
            self.assertIn("limited", result["data_quality"].lower())
            
            # Should still provide some evaluation
            self.assertIn("skill_tier", result)
            self.assertIn("overall_score", result)


class TestDraftAnalysis(FunctionalTestCase):
    """Test draft strategy classification and analysis."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_rb_heavy_strategy_classification(self):
        """Test identification of RB-Heavy draft strategy."""
        # Create RB-Heavy draft pattern
        rb_heavy_draft = TestDataBuilder.build_draft_results(10, 15)
        
        # Modify to show RB preference in early rounds
        for i, pick in enumerate(rb_heavy_draft[:6]):  # First 6 picks
            if pick["team_id"] == "1":  # Target team
                if pick["round"] <= 3:  # Early rounds
                    rb_heavy_draft[i]["position"] = "RB"
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "draft_results": rb_heavy_draft,
                    "league_settings": {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]}
                }
            }
            
            result = analyze_draft_strategy("123456", "nfl", ["2024"], "1")
            
            # Should identify RB-Heavy strategy
            self.assertIn("primary_strategy", result)
            self.assertEqual(result["primary_strategy"], "RB-Heavy")
            
            # Should show position preferences
            self.assertIn("position_preferences", result)
            rb_preference = result["position_preferences"].get("RB", 0)
            self.assertGreater(rb_preference, 0.3)  # High RB preference
    
    def test_zero_rb_strategy_classification(self):
        """Test identification of Zero-RB draft strategy."""
        # Create Zero-RB draft pattern
        zero_rb_draft = TestDataBuilder.build_draft_results(10, 15)
        
        # Modify to show WR/TE preference early, RB later
        for i, pick in enumerate(zero_rb_draft):
            if pick["team_id"] == "2":  # Target team
                if pick["round"] <= 4:  # Early rounds - no RB
                    zero_rb_draft[i]["position"] = "WR" if pick["round"] % 2 == 1 else "TE"
                elif pick["round"] >= 5:  # Later rounds - RB
                    zero_rb_draft[i]["position"] = "RB"
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "draft_results": zero_rb_draft,
                    "league_settings": {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]}
                }
            }
            
            result = analyze_draft_strategy("123456", "nfl", ["2024"], "2")
            
            # Should identify Zero-RB strategy
            self.assertIn("primary_strategy", result)
            self.assertEqual(result["primary_strategy"], "Zero-RB")
            
            # Should show late RB preference
            self.assertIn("draft_timing", result)
            rb_timing = result["draft_timing"].get("RB", {})
            self.assertGreater(rb_timing.get("avg_round", 0), 4)
    
    def test_balanced_strategy_classification(self):
        """Test identification of Balanced draft strategy."""
        # Create balanced draft pattern
        balanced_draft = TestDataBuilder.build_draft_results(10, 15)
        
        # Modify to show even distribution
        positions = ["RB", "WR", "QB", "TE"]
        for i, pick in enumerate(balanced_draft):
            if pick["team_id"] == "3":  # Target team
                balanced_draft[i]["position"] = positions[pick["round"] % len(positions)]
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "draft_results": balanced_draft,
                    "league_settings": {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]}
                }
            }
            
            result = analyze_draft_strategy("123456", "nfl", ["2024"], "3")
            
            # Should identify Balanced strategy
            self.assertIn("primary_strategy", result)
            self.assertEqual(result["primary_strategy"], "Balanced")
            
            # Should show even distribution
            self.assertIn("position_preferences", result)
            preferences = result["position_preferences"]
            
            # No single position should dominate
            for position, pref in preferences.items():
                self.assertLess(pref, 0.6)  # No position > 60%
    
    def test_multi_season_draft_evolution(self):
        """Test tracking of draft strategy evolution over multiple seasons."""
        seasons = ["2022", "2023", "2024"]
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            # Mock different strategies per season
            draft_data = {}
            strategies = ["RB-Heavy", "Zero-RB", "Balanced"]
            
            for i, season in enumerate(seasons):
                draft_data[season] = TestDataBuilder.build_draft_results(10, 15)
                
            mock_query.return_value = {
                "success": True,
                "data": {
                    "multi_season_drafts": draft_data,
                    "league_settings": {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]}
                }
            }
            
            result = analyze_draft_strategy("123456", "nfl", seasons, "1")
            
            # Should show evolution over time
            self.assertIn("strategy_evolution", result)
            evolution = result["strategy_evolution"]
            
            self.assertEqual(len(evolution), len(seasons))
            
            # Should identify trends
            self.assertIn("trends", result)
            self.assertIn("consistency", result)


class TestTradeAnalytics(FunctionalTestCase):
    """Test trade pattern identification and prediction."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_trade_likelihood_prediction_frequent_partners(self):
        """Test prediction for managers who trade frequently with each other."""
        # Mock historical trade data showing frequent partnership
        trade_history = {
            "2022": [
                {"team1_id": "1", "team2_id": "3", "date": "2022-10-15", "type": "player_trade"},
                {"team1_id": "1", "team2_id": "3", "date": "2022-11-01", "type": "player_trade"}
            ],
            "2023": [
                {"team1_id": "1", "team2_id": "3", "date": "2023-09-20", "type": "player_trade"},
                {"team1_id": "1", "team2_id": "3", "date": "2023-10-30", "type": "player_trade"}
            ]
        }
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "trade_history": trade_history,
                    "team_profiles": {
                        "1": {"manager_name": "Manager A", "trade_frequency": "high"},
                        "3": {"manager_name": "Manager C", "trade_frequency": "high"}
                    }
                }
            }
            
            result = predict_trade_likelihood("123456", "nfl", "1", "3", ["2022", "2023"])
            
            # Should predict high likelihood
            self.assertIn("likelihood_score", result)
            self.assertGreater(result["likelihood_score"], 70)
            
            # Should show historical partnership
            self.assertIn("historical_trades", result)
            self.assertGreater(result["historical_trades"], 3)
            
            # Should identify patterns
            self.assertIn("trade_patterns", result)
    
    def test_trade_likelihood_prediction_no_history(self):
        """Test prediction for managers with no trading history."""
        # Mock empty trade history
        trade_history = {"2022": [], "2023": []}
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "trade_history": trade_history,
                    "team_profiles": {
                        "2": {"manager_name": "Manager B", "trade_frequency": "low"},
                        "4": {"manager_name": "Manager D", "trade_frequency": "low"}
                    }
                }
            }
            
            result = predict_trade_likelihood("123456", "nfl", "2", "4", ["2022", "2023"])
            
            # Should predict low likelihood
            self.assertIn("likelihood_score", result)
            self.assertLess(result["likelihood_score"], 30)
            
            # Should note lack of history
            self.assertIn("historical_trades", result)
            self.assertEqual(result["historical_trades"], 0)
    
    def test_league_wide_trade_patterns(self):
        """Test identification of league-wide trading patterns."""
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": {
                    "league_trade_data": {
                        "total_trades": 25,
                        "trade_distribution": {
                            "1": 8,  # Heavy trader
                            "2": 2,  # Light trader
                            "3": 6,  # Moderate trader
                            "4": 0   # Non-trader
                        },
                        "seasonal_patterns": {
                            "pre_season": 5,
                            "early_season": 8,
                            "mid_season": 10,
                            "trade_deadline": 2
                        }
                    }
                }
            }
            
            result = predict_trade_likelihood("123456", "nfl")
            
            # Should identify league patterns
            self.assertIn("league_trade_volume", result)
            self.assertEqual(result["league_trade_volume"], "high")
            
            # Should identify active traders
            self.assertIn("most_active_traders", result)
            self.assertIn("1", str(result["most_active_traders"]))


class TestHistoricalAnalysis(FunctionalTestCase):
    """Test multi-season historical analysis accuracy."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_championship_probability_analysis(self):
        """Test championship probability based on historical performance."""
        # Create championship history data
        championship_data = {
            "historical_champions": {
                "2020": "1", "2021": "1", "2022": "3", "2023": "1"
            },
            "manager_profiles": {
                "1": {"championships": 3, "playoff_appearances": 4, "avg_wins": 10.5},
                "2": {"championships": 0, "playoff_appearances": 2, "avg_wins": 7.2},
                "3": {"championships": 1, "playoff_appearances": 3, "avg_wins": 8.8}
            }
        }
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": championship_data
            }
            
            result = evaluate_manager_skill("123456", "nfl", ["2020", "2021", "2022", "2023"])
            
            # Should identify championship patterns
            self.assertIn("championship_analysis", result)
            
            # Manager 1 should have high championship probability
            manager_1_data = next((m for m in result.get("managers", []) if m["team_id"] == "1"), None)
            if manager_1_data:
                self.assertGreater(manager_1_data.get("championship_probability", 0), 25)
    
    def test_league_competitiveness_analysis(self):
        """Test league competitiveness and balance analysis."""
        competitive_data = {
            "standings_history": {
                "2022": [
                    {"team_id": "1", "wins": 10, "rank": 1},
                    {"team_id": "2", "wins": 9, "rank": 2},
                    {"team_id": "3", "wins": 8, "rank": 3}
                ],
                "2023": [
                    {"team_id": "3", "wins": 11, "rank": 1},
                    {"team_id": "1", "wins": 9, "rank": 2},
                    {"team_id": "2", "wins": 8, "rank": 3}
                ]
            }
        }
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": competitive_data
            }
            
            result = evaluate_manager_skill("123456", "nfl", ["2022", "2023"])
            
            # Should calculate league balance metrics
            self.assertIn("league_competitiveness", result)
            competitiveness = result["league_competitiveness"]
            
            self.assertIn("balance_score", competitiveness)
            self.assertIn("parity_index", competitiveness)
            
            # Should identify competitive league
            self.assertGreater(competitiveness["balance_score"], 60)
    
    def test_performance_trend_identification(self):
        """Test identification of performance trends over multiple seasons."""
        trend_data = {
            "manager_progression": {
                "1": {  # Improving manager
                    "2020": {"wins": 6, "points": 1100},
                    "2021": {"wins": 8, "points": 1250},
                    "2022": {"wins": 10, "points": 1400},
                    "2023": {"wins": 12, "points": 1550}
                },
                "2": {  # Declining manager
                    "2020": {"wins": 11, "points": 1500},
                    "2021": {"wins": 9, "points": 1300},
                    "2022": {"wins": 7, "points": 1150},
                    "2023": {"wins": 5, "points": 1000}
                }
            }
        }
        
        with patch('league_analysis_mcp_server.analytics.get_yahoo_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": trend_data
            }
            
            result = evaluate_manager_skill("123456", "nfl", ["2020", "2021", "2022", "2023"])
            
            # Should identify trends
            self.assertIn("performance_trends", result)
            trends = result["performance_trends"]
            
            # Manager 1 should show improvement trend
            manager_1_trend = trends.get("1", {})
            self.assertEqual(manager_1_trend.get("trend"), "improving")
            
            # Manager 2 should show decline trend  
            manager_2_trend = trends.get("2", {})
            self.assertEqual(manager_2_trend.get("trend"), "declining")


if __name__ == "__main__":
    import unittest
    
    print("League Analysis MCP Server - Analytics Functional Tests")
    print("=" * 62)
    print("Testing advanced analytics and machine learning functionality")
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 62)
    if result.wasSuccessful():
        print("PASS: All analytics tests passed!")
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