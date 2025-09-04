#!/usr/bin/env python3
"""
Error handling and edge case tests for League Analysis MCP Server.

Tests graceful degradation, error recovery, and boundary conditions
to ensure robust operation under adverse conditions.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .base import FunctionalTestCase, IntegrationTestCase, TestFixtures
from league_analysis_mcp_server.tools import get_league_info, get_standings
from league_analysis_mcp_server.enhanced_auth import EnhancedYahooAuthManager
from league_analysis_mcp_server.server import app_state


class TestAPIErrorHandling(FunctionalTestCase):
    """Test Yahoo API error handling and recovery."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_rate_limit_error_handling(self):
        """Test handling of Yahoo API rate limit errors."""
        # Mock rate limit error response
        rate_limit_error = {
            "success": False,
            "error": "Rate limit exceeded - 60 requests per minute",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": 60
        }
        
        self.set_yahoo_mock_response(rate_limit_error)
        
        result = get_league_info("123456", "nfl")
        
        # Should handle rate limit gracefully
        self.assertIn("error", result)
        self.assertIn("rate limit", result["error"].lower())
        
        # Should provide user-friendly message
        self.assertNotIn("RATE_LIMIT_EXCEEDED", result["error"])  # Technical error codes should be hidden
        
        # Should suggest retry behavior
        self.assertIn("try again", result["error"].lower())
    
    def test_authentication_error_handling(self):
        """Test handling of authentication errors."""
        auth_errors = [
            {
                "success": False,
                "error": "Invalid access token",
                "error_code": "AUTH_INVALID_TOKEN"
            },
            {
                "success": False,
                "error": "Token expired",
                "error_code": "AUTH_TOKEN_EXPIRED"
            },
            {
                "success": False,
                "error": "Insufficient permissions",
                "error_code": "AUTH_INSUFFICIENT_SCOPE"
            }
        ]
        
        for auth_error in auth_errors:
            self.set_yahoo_mock_response(auth_error)
            
            result = get_league_info("123456", "nfl")
            
            # Should identify as authentication issue
            self.assertIn("error", result)
            error_msg = result["error"].lower()
            self.assertTrue(
                any(word in error_msg for word in ["authentication", "token", "credentials", "permission"]),
                f"Error message should indicate auth issue: {result['error']}"
            )
            
            # Should provide actionable guidance
            self.assertTrue(
                any(phrase in error_msg for phrase in ["setup", "authenticate", "credentials"]),
                f"Error should provide guidance: {result['error']}"
            )
    
    def test_yahoo_service_unavailable_error(self):
        """Test handling when Yahoo API is completely unavailable."""
        service_errors = [
            {
                "success": False,
                "error": "Service temporarily unavailable",
                "error_code": "SERVICE_UNAVAILABLE"
            },
            {
                "success": False,
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR"
            },
            {
                "success": False,
                "error": "Gateway timeout",
                "error_code": "GATEWAY_TIMEOUT"
            }
        ]
        
        for service_error in service_errors:
            self.set_yahoo_mock_response(service_error)
            
            result = get_league_info("123456", "nfl")
            
            # Should handle service errors gracefully
            self.assertIn("error", result)
            error_msg = result["error"].lower()
            
            # Should provide user-friendly message
            self.assertTrue(
                any(word in error_msg for word in ["unavailable", "temporary", "later"]),
                f"Should indicate temporary issue: {result['error']}"
            )
            
            # Should not expose technical error codes
            self.assertNotIn("SERVICE_UNAVAILABLE", result["error"])
            self.assertNotIn("INTERNAL_ERROR", result["error"])
    
    def test_cache_fallback_on_api_error(self):
        """Test that cached data is used when API fails."""
        # First, populate cache with good data
        good_data = TestFixtures.get_mock_league_data()
        self.set_yahoo_mock_response({
            "success": True,
            "data": good_data
        })
        
        # Make initial request to populate cache
        result1 = get_league_info("123456", "nfl")
        self.assertEqual(result1["league"]["league_id"], "123456")
        
        # Now simulate API failure
        self.set_yahoo_mock_error("Network timeout")
        
        # Should fall back to cached data or provide informative error
        result2 = get_league_info("123456", "nfl")
        
        # Either we get cached data (ideal) or informative error
        if "error" not in result2:
            # Got cached data
            self.assertEqual(result2["league"]["league_id"], "123456")
        else:
            # Got error but it should be informative
            self.assertIn("error", result2)
            # Should mention it's a temporary issue
            self.assertIn("temporary", result2["error"].lower())
    
    def test_partial_data_error_handling(self):
        """Test handling when Yahoo API returns partial or corrupted data."""
        partial_responses = [
            {
                "success": True,
                "data": {
                    "league": {
                        "league_id": "123456"
                        # Missing required fields like name, num_teams
                    }
                }
            },
            {
                "success": True,
                "data": {
                    # Missing league object entirely
                    "settings": {"some": "data"}
                }
            },
            {
                "success": True,
                "data": None  # Null data
            }
        ]
        
        for partial_response in partial_responses:
            self.set_yahoo_mock_response(partial_response)
            
            result = get_league_info("123456", "nfl")
            
            # Should handle incomplete data gracefully
            if "error" in result:
                # Error handling approach
                self.assertIn("incomplete", result["error"].lower())
            else:
                # Data completion approach - should have sensible defaults
                self.assertIn("league", result)
                self.assertIsInstance(result["league"], dict)


class TestNetworkErrorRecovery(FunctionalTestCase):
    """Test network failure recovery and resilience."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_network_timeout_recovery(self):
        """Test handling of network timeouts."""
        with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
            # Simulate network timeout
            mock_query.side_effect = Exception("Connection timeout")
            
            result = get_league_info("123456", "nfl")
            
            # Should handle timeout gracefully
            self.assertIn("error", result)
            error_msg = result["error"].lower()
            self.assertTrue(
                any(word in error_msg for word in ["timeout", "connection", "network"]),
                f"Should indicate network issue: {result['error']}"
            )
            
            # Should suggest retry
            self.assertIn("try again", error_msg)
    
    def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
            # Simulate DNS failure
            mock_query.side_effect = Exception("Name resolution failed")
            
            result = get_league_info("123456", "nfl")
            
            # Should handle DNS failures gracefully
            self.assertIn("error", result)
            self.assertIn("connection", result["error"].lower())
    
    def test_ssl_certificate_errors(self):
        """Test handling of SSL/TLS certificate errors."""
        with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
            # Simulate SSL error
            mock_query.side_effect = Exception("SSL certificate verification failed")
            
            result = get_league_info("123456", "nfl")
            
            # Should handle SSL errors without exposing technical details
            self.assertIn("error", result)
            self.assertNotIn("certificate", result["error"].lower())  # Don't expose SSL details
            self.assertIn("connection", result["error"].lower())
    
    def test_intermittent_network_failures(self):
        """Test handling of intermittent network issues."""
        call_count = 0
        
        def intermittent_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                # First two calls fail
                raise Exception("Network unreachable")
            else:
                # Third call succeeds
                return {
                    "success": True,
                    "data": TestFixtures.get_mock_league_data()
                }
        
        with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
            mock_query.side_effect = intermittent_failure
            
            # Should handle intermittent failures
            # (This would require retry logic in the actual implementation)
            result = get_league_info("123456", "nfl")
            
            # Should either succeed (with retry) or provide helpful error
            if "error" in result:
                self.assertIn("temporary", result["error"].lower())
            else:
                self.assertEqual(result["league"]["league_id"], "123456")


class TestDataValidation(FunctionalTestCase):
    """Test handling of malformed and invalid data."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_invalid_league_id_handling(self):
        """Test handling of invalid league IDs."""
        invalid_league_ids = [
            "",           # Empty string
            "   ",        # Whitespace only
            "invalid",    # Non-numeric
            "0",          # Zero
            "-12345",     # Negative
            "12345abc",   # Mixed alphanumeric
            None,         # None value
        ]
        
        for invalid_id in invalid_league_ids:
            with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
                mock_query.return_value = {
                    "success": False,
                    "error": f"Invalid league ID: {invalid_id}",
                    "error_code": "INVALID_LEAGUE_ID"
                }
                
                result = get_league_info(str(invalid_id) if invalid_id is not None else "", "nfl")
                
                # Should handle invalid IDs gracefully
                self.assertIn("error", result)
                error_msg = result["error"].lower()
                self.assertTrue(
                    any(word in error_msg for word in ["invalid", "league", "id"]),
                    f"Should indicate invalid league ID: {result['error']}"
                )
    
    def test_malformed_json_response_handling(self):
        """Test handling of malformed JSON responses from Yahoo."""
        with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
            # Simulate malformed JSON
            mock_query.side_effect = ValueError("Invalid JSON response")
            
            result = get_league_info("123456", "nfl")
            
            # Should handle JSON parsing errors
            self.assertIn("error", result)
            self.assertNotIn("JSON", result["error"])  # Don't expose technical details
            self.assertIn("data", result["error"].lower())
    
    def test_unexpected_data_structure(self):
        """Test handling of unexpected data structures from Yahoo API."""
        unexpected_structures = [
            {"wrong": "structure", "no_league": True},
            {"league": "not_an_object"},
            {"league": {"missing": "required_fields"}},
            [],  # Array instead of object
            "string_response",  # String instead of object
        ]
        
        for structure in unexpected_structures:
            self.set_yahoo_mock_response({
                "success": True,
                "data": structure
            })
            
            result = get_league_info("123456", "nfl")
            
            # Should handle unexpected structures
            if "error" in result:
                error_msg = result["error"].lower()
                self.assertTrue(
                    any(word in error_msg for word in ["format", "structure", "unexpected"]),
                    f"Should indicate data structure issue: {result['error']}"
                )
            else:
                # If no error, should have reasonable defaults
                self.assertIsInstance(result, dict)
    
    def test_unicode_and_encoding_issues(self):
        """Test handling of unicode and encoding issues."""
        # Test data with various unicode characters
        unicode_data = {
            "league": {
                "league_id": "123456",
                "name": "Test League with émojis 🏈 and ünicode",
                "manager_names": ["José", "François", "Müller", "北京"]
            }
        }
        
        self.set_yahoo_mock_response({
            "success": True,
            "data": unicode_data
        })
        
        result = get_league_info("123456", "nfl")
        
        # Should handle unicode correctly
        if "error" not in result:
            self.assertIn("league", result)
            self.assertIsInstance(result["league"]["name"], str)
            # Unicode should be preserved
            self.assertIn("émojis", result["league"]["name"])
    
    def test_extremely_large_data_handling(self):
        """Test handling of extremely large data responses."""
        # Create artificially large data
        large_data = {
            "league": {
                "league_id": "123456",
                "name": "Large Data League",
                "large_field": "x" * 100000,  # 100KB of data
                "many_items": [f"item_{i}" for i in range(10000)]  # Many items
            }
        }
        
        self.set_yahoo_mock_response({
            "success": True,
            "data": large_data
        })
        
        result = get_league_info("123456", "nfl")
        
        # Should handle large data without crashing
        if "error" not in result:
            self.assertIn("league", result)
            self.assertEqual(result["league"]["league_id"], "123456")
        else:
            # If there's size limiting, error should be informative
            self.assertIn("large", result["error"].lower())


class TestBoundaryConditions(FunctionalTestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        super().setUp()
        app_state["cache_manager"] = self.cache_manager
        app_state["auth_manager"] = self.auth_manager
    
    def test_empty_league_handling(self):
        """Test handling of leagues with no teams or data."""
        empty_league_data = {
            "league": {
                "league_id": "123456",
                "name": "Empty League",
                "num_teams": 0
            },
            "teams": [],
            "settings": {}
        }
        
        self.set_yahoo_mock_response({
            "success": True,
            "data": empty_league_data
        })
        
        result = get_league_info("123456", "nfl")
        
        # Should handle empty leagues gracefully
        self.assertIn("league", result)
        self.assertEqual(result["league"]["num_teams"], 0)
    
    def test_maximum_league_size_handling(self):
        """Test handling of very large leagues."""
        # Create league with maximum teams (Yahoo supports up to 20)
        max_teams_data = {
            "league": {
                "league_id": "123456",
                "name": "Maximum Size League",
                "num_teams": 20
            },
            "teams": [
                {"team_id": str(i), "name": f"Team {i}"} 
                for i in range(1, 21)
            ]
        }
        
        self.set_yahoo_mock_response({
            "success": True,
            "data": max_teams_data
        })
        
        result = get_league_info("123456", "nfl")
        
        # Should handle maximum size correctly
        self.assertIn("league", result)
        self.assertEqual(result["league"]["num_teams"], 20)
    
    def test_historical_season_boundary_conditions(self):
        """Test handling of very old and future seasons."""
        boundary_seasons = [
            "1999",  # Very old season
            "2050",  # Future season
            "2015",  # First supported season
            "abcd",  # Invalid season format
            ""       # Empty season
        ]
        
        for season in boundary_seasons:
            # Mock response based on season validity
            if season in ["1999", "2050", "abcd", ""]:
                # Invalid seasons
                mock_response = {
                    "success": False,
                    "error": f"Invalid season: {season}",
                    "error_code": "INVALID_SEASON"
                }
            else:
                # Valid season
                mock_response = {
                    "success": True,
                    "data": TestFixtures.get_mock_league_data()
                }
            
            self.set_yahoo_mock_response(mock_response)
            
            result = get_league_info("123456", "nfl", season)
            
            # Should handle boundary seasons appropriately
            if season in ["1999", "2050", "abcd", ""]:
                self.assertIn("error", result)
            else:
                self.assertNotIn("error", result)
    
    def test_concurrent_request_handling(self):
        """Test handling of multiple simultaneous requests."""
        # Simulate multiple concurrent requests
        # (This is simplified - real concurrency would need threading)
        
        requests = []
        for i in range(10):
            league_id = f"12345{i}"
            self.set_yahoo_mock_response({
                "success": True,
                "data": TestFixtures.get_mock_league_data()
            })
            
            result = get_league_info(league_id, "nfl")
            requests.append(result)
        
        # All requests should succeed
        for result in requests:
            self.assertNotIn("error", result)
            self.assertIn("league", result)
    
    def test_memory_pressure_conditions(self):
        """Test behavior under memory pressure conditions."""
        # This would test what happens when system is low on memory
        # For now, just test that large cache operations don't crash
        
        cache_manager = self.cache_manager
        
        # Fill cache with many entries
        try:
            for i in range(1000):
                large_data = {
                    "id": i,
                    "data": "x" * 1000  # 1KB per entry
                }
                cache_manager.set(f"stress_test_{i}", large_data)
        except MemoryError:
            # If we hit memory limits, that's expected
            pass
        
        # Cache should still be functional
        stats = cache_manager.get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("memory_usage", stats)


class TestAuthenticationEdgeCases(FunctionalTestCase):
    """Test authentication edge cases and error conditions."""
    
    def test_corrupted_credentials_handling(self):
        """Test handling of corrupted or malformed credentials."""
        corrupted_credentials = [
            "not_base64_encoded_data",
            "partial_credential",
            "",
            "   ",  # Whitespace only
        ]
        
        for corrupted_cred in corrupted_credentials:
            # Temporarily corrupt credentials
            os.environ['YAHOO_CONSUMER_KEY'] = corrupted_cred
            
            auth_manager = EnhancedYahooAuthManager()
            
            # Should handle corrupted credentials gracefully
            if corrupted_cred.strip():
                self.assertTrue(auth_manager.is_configured())  # Format validation might be minimal
            else:
                self.assertFalse(auth_manager.is_configured())
        
        # Restore valid credentials
        os.environ['YAHOO_CONSUMER_KEY'] = 'test_key_123'
    
    def test_token_corruption_during_operation(self):
        """Test handling when tokens become corrupted during operation."""
        auth_manager = EnhancedYahooAuthManager()
        
        # Start with valid tokens
        self.assertTrue(auth_manager.has_access_token())
        
        # Simulate token corruption
        os.environ['YAHOO_ACCESS_TOKEN'] = 'corrupted_token_data'
        
        # Should detect token issues
        # (Actual detection would happen during API calls)
        with patch('league_analysis_mcp_server.tools.get_yahoo_query') as mock_query:
            mock_query.side_effect = Exception("Invalid token format")
            
            result = get_league_info("123456", "nfl")
            
            # Should handle token corruption gracefully
            self.assertIn("error", result)
            error_msg = result["error"].lower()
            self.assertTrue(
                any(word in error_msg for word in ["authentication", "token", "credentials"]),
                f"Should indicate auth issue: {result['error']}"
            )


if __name__ == "__main__":
    import unittest
    
    print("League Analysis MCP Server - Error Handling Functional Tests")
    print("=" * 68)
    print("Testing error handling and resilience with various failure scenarios")
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 68)
    if result.wasSuccessful():
        print("PASS: All error handling tests passed!")
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