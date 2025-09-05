#!/usr/bin/env python3
"""
Base test classes and utilities for functional testing.

Provides foundation for both mock-based functional tests and 
real Yahoo API integration tests.
"""

import os
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch, MagicMock

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from league_analysis_mcp_server.cache import CacheManager
from league_analysis_mcp_server.enhanced_auth import EnhancedYahooAuthManager


class TestFixtures:
    """Utility class for loading test fixtures."""
    
    @classmethod
    def load_fixture(cls, filename: str) -> Dict[str, Any]:
        """Load a JSON fixture file."""
        fixture_path = Path(__file__).parent / "fixtures" / filename
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @classmethod
    def get_mock_league_data(cls) -> Dict[str, Any]:
        """Get mock league data for testing."""
        return {
            "league_id": "123456",
            "name": "Test Fantasy League",
            "num_teams": 10,
            "settings": {
                "scoring_type": "standard",
                "playoff_teams": 6,
                "roster_positions": ["QB", "RB", "WR", "TE", "K", "DEF"]
            },
            "current_week": 8,
            "season": "2024"
        }
    
    @classmethod
    def get_mock_standings_data(cls) -> List[Dict[str, Any]]:
        """Get mock standings data for testing."""
        return [
            {
                "team_id": "1",
                "team_name": "Team Alpha",
                "manager_name": "Manager A",
                "wins": 6,
                "losses": 2,
                "points_for": 1150.5,
                "points_against": 980.2
            },
            {
                "team_id": "2", 
                "team_name": "Team Beta",
                "manager_name": "Manager B",
                "wins": 5,
                "losses": 3,
                "points_for": 1080.3,
                "points_against": 1020.7
            }
        ]
    
    @classmethod
    def get_mock_draft_data(cls) -> Dict[str, Any]:
        """Get mock draft data for testing."""
        return {
            "draft_results": [
                {
                    "pick": 1,
                    "round": 1,
                    "team_id": "1",
                    "player_name": "Player A",
                    "position": "RB"
                },
                {
                    "pick": 2,
                    "round": 1, 
                    "team_id": "2",
                    "player_name": "Player B",
                    "position": "WR"
                }
            ],
            "draft_type": "standard",
            "season": "2024"
        }


class FunctionalTestCase(unittest.TestCase):
    """
    Base class for functional tests using mocked Yahoo API responses.
    
    Provides:
    - Mock Yahoo API setup
    - Cache manager for testing
    - Authentication manager setup
    - Fixture loading utilities
    """
    
    def setUp(self):
        """Set up test environment with mocks."""
        # Set up fake environment variables
        self.test_env = {
            'YAHOO_CONSUMER_KEY': 'test_key_123',
            'YAHOO_CONSUMER_SECRET': 'test_secret_456',
            'YAHOO_ACCESS_TOKEN': 'test_token_789',
            'YAHOO_REFRESH_TOKEN': 'test_refresh_abc'
        }
        
        # Apply environment variables
        for key, value in self.test_env.items():
            os.environ[key] = value
        
        # Create test cache manager
        self.cache_manager = CacheManager()
        
        # Create test auth manager  
        self.auth_manager = EnhancedYahooAuthManager()
        
        # Mock the Yahoo API client
        self.yahoo_client_patcher = patch(
            'league_analysis_mcp_server.tools.get_yahoo_query'
        )
        self.mock_yahoo_query = self.yahoo_client_patcher.start()
        
        # Set up default mock responses
        self._setup_default_mocks()
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        self.yahoo_client_patcher.stop()
        
        # Clean up environment variables
        for key in self.test_env.keys():
            os.environ.pop(key, None)
        
        # Clear cache
        self.cache_manager.clear()
    
    def _setup_default_mocks(self):
        """Set up default mock responses for Yahoo API."""
        # Default successful response
        self.mock_yahoo_query.return_value = {
            "success": True,
            "data": TestFixtures.get_mock_league_data()
        }
    
    def set_yahoo_mock_response(self, response: Dict[str, Any]):
        """Set a specific mock response for Yahoo API calls."""
        self.mock_yahoo_query.return_value = response
    
    def set_yahoo_mock_error(self, error_message: str):
        """Set Yahoo API to return an error."""
        self.mock_yahoo_query.return_value = {
            "success": False,
            "error": error_message
        }
    
    def assert_cache_contains(self, sport: str, league_id: str, 
                            endpoint: str, season: Optional[str] = None):
        """Assert that cache contains data for given parameters."""
        if season:
            cached_data = self.cache_manager.get_historical_data(
                sport, season, league_id, endpoint
            )
        else:
            cached_data = self.cache_manager.get_current_data(
                sport, league_id, endpoint
            )
        
        self.assertIsNotNone(cached_data, 
                           f"Cache should contain data for {sport}/{league_id}/{endpoint}")
    
    def assert_valid_league_data(self, data: Dict[str, Any]):
        """Assert that league data has required fields."""
        required_fields = ['league_id', 'name', 'num_teams', 'settings']
        for field in required_fields:
            self.assertIn(field, data, f"League data missing required field: {field}")
    
    def assert_valid_standings_data(self, data: List[Dict[str, Any]]):
        """Assert that standings data is properly formatted."""
        self.assertIsInstance(data, list, "Standings should be a list")
        
        if data:  # If not empty
            required_fields = ['team_id', 'team_name', 'wins', 'losses']
            for team in data:
                for field in required_fields:
                    self.assertIn(field, team, f"Team data missing field: {field}")


class IntegrationTestCase(unittest.TestCase):
    """
    Base class for integration tests using real Yahoo API.
    
    Requires real Yahoo credentials to be set in environment or .env file.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources."""
        cls.skip_integration = False
        
        # Check if real credentials are available
        required_env_vars = [
            'YAHOO_CONSUMER_KEY', 
            'YAHOO_CONSUMER_SECRET'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            cls.skip_integration = True
            cls.skip_reason = f"Missing environment variables: {', '.join(missing_vars)}"
    
    def setUp(self):
        """Set up test environment for integration tests."""
        if self.skip_integration:
            self.skipTest(self.skip_reason)
        
        # Use real cache manager
        self.cache_manager = CacheManager()
        
        # Use real auth manager
        self.auth_manager = EnhancedYahooAuthManager()
        
        # Verify authentication is working
        if not self.auth_manager.is_configured():
            self.skipTest("Yahoo API credentials not properly configured")
    
    def tearDown(self):
        """Clean up after integration tests."""
        # Clear cache to avoid interference between tests
        self.cache_manager.clear()
    
    def assert_real_api_response(self, response: Dict[str, Any]):
        """Assert that response came from real Yahoo API."""
        # Real Yahoo API responses have specific characteristics
        self.assertIsInstance(response, dict)
        self.assertNotIn('mock', str(response).lower())
        
        # Should not contain our test data
        test_markers = ['test_key_123', 'Test Fantasy League']
        response_str = json.dumps(response)
        for marker in test_markers:
            self.assertNotIn(marker, response_str)


class TestDataBuilder:
    """Utility class for building test data structures."""
    
    @staticmethod
    def build_league_settings(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build league settings with optional overrides."""
        base_settings = {
            "scoring_type": "standard",
            "playoff_teams": 6,
            "trade_deadline": "2024-11-01",
            "waiver_type": "daily",
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]
        }
        
        if overrides:
            base_settings.update(overrides)
        
        return base_settings
    
    @staticmethod
    def build_manager_history(team_id: str, seasons: List[str]) -> Dict[str, Any]:
        """Build manager historical data."""
        history = {}
        
        for i, season in enumerate(seasons):
            history[season] = {
                "team_id": team_id,
                "wins": 8 + i,  # Progressive improvement
                "losses": 6 - i,
                "points_for": 1100 + (i * 50),
                "playoff_finish": max(1, 4 - i),
                "championship": i == len(seasons) - 1  # Won most recent season
            }
        
        return history
    
    @staticmethod
    def build_draft_results(num_teams: int = 10, rounds: int = 15) -> List[Dict[str, Any]]:
        """Build realistic draft results."""
        results = []
        pick = 1
        
        for round_num in range(1, rounds + 1):
            for team in range(1, num_teams + 1):
                results.append({
                    "pick": pick,
                    "round": round_num,
                    "team_id": str(team),
                    "player_name": f"Player {pick}",
                    "position": ["QB", "RB", "WR", "TE", "K", "DEF"][pick % 6]
                })
                pick += 1
        
        return results


class MockYahooAPI:
    """Mock Yahoo Fantasy API for consistent testing."""
    
    def __init__(self):
        self.responses = {}
        self.call_count = 0
    
    def set_response(self, endpoint: str, response: Dict[str, Any]):
        """Set mock response for specific endpoint."""
        self.responses[endpoint] = response
    
    def get_response(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get mock response for endpoint."""
        self.call_count += 1
        
        # Return specific response if available
        if endpoint in self.responses:
            return self.responses[endpoint]
        
        # Return default response
        return {
            "success": True,
            "data": {"mock_response": True, "endpoint": endpoint, "params": params}
        }
    
    def reset(self):
        """Reset mock state."""
        self.responses = {}
        self.call_count = 0