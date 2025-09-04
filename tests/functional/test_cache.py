#!/usr/bin/env python3
"""
Cache behavior validation tests for League Analysis MCP Server.

Tests caching strategies, TTL behavior, size limits, and cache management
to ensure optimal performance and correct data freshness.
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .base import FunctionalTestCase, TestFixtures
from league_analysis_mcp_server.cache import CacheManager


class TestCacheTTLBehavior(FunctionalTestCase):
    """Test time-to-live behavior for different data types."""
    
    def test_historical_data_permanent_cache(self):
        """Test that historical data is cached permanently (TTL = -1)."""
        cache_manager = CacheManager()
        
        # Store historical data
        test_data = TestFixtures.get_mock_league_data()
        cache_manager.set_historical_data("nfl", "2023", "123456", "draft_results", test_data)
        
        # Should retrieve immediately
        retrieved = cache_manager.get_historical_data("nfl", "2023", "123456", "draft_results")
        self.assertEqual(retrieved, test_data)
        
        # Simulate time passing (historical data should persist)
        with patch('time.time', return_value=time.time() + 10000):  # 10,000 seconds later
            retrieved_later = cache_manager.get_historical_data("nfl", "2023", "123456", "draft_results")
            self.assertEqual(retrieved_later, test_data)
        
        # Check cache entry details
        cache_key = cache_manager._build_historical_key("nfl", "2023", "123456", "draft_results")
        cache_entry = cache_manager.cache.get(cache_key)
        
        self.assertIsNotNone(cache_entry)
        self.assertEqual(cache_entry['ttl'], -1)  # Permanent
    
    def test_current_data_ttl_expiry(self):
        """Test that current season data expires after TTL (300 seconds)."""
        cache_manager = CacheManager()
        
        # Store current data
        test_data = TestFixtures.get_mock_standings_data()
        cache_manager.set_current_data("nfl", "123456", "standings", test_data)
        
        # Should retrieve immediately
        retrieved = cache_manager.get_current_data("nfl", "123456", "standings")
        self.assertEqual(retrieved, test_data)
        
        # Simulate time passing within TTL
        with patch('time.time', return_value=time.time() + 200):  # 200 seconds later
            retrieved_within_ttl = cache_manager.get_current_data("nfl", "123456", "standings")
            self.assertEqual(retrieved_within_ttl, test_data)
        
        # Simulate time passing beyond TTL
        with patch('time.time', return_value=time.time() + 400):  # 400 seconds later
            retrieved_expired = cache_manager.get_current_data("nfl", "123456", "standings")
            self.assertIsNone(retrieved_expired)  # Should be expired
    
    def test_cache_ttl_configuration(self):
        """Test that TTL can be configured for different data types."""
        cache_manager = CacheManager()
        
        # Test custom TTL
        custom_ttl = 600  # 10 minutes
        test_data = {"custom": "data"}
        
        # Store with custom TTL
        cache_key = "test_custom_ttl"
        cache_manager.set(cache_key, test_data, ttl=custom_ttl)
        
        # Check cache entry
        cache_entry = cache_manager.cache.get(cache_key)
        self.assertEqual(cache_entry['ttl'], custom_ttl)
        
        # Should be available within TTL
        retrieved = cache_manager.get(cache_key)
        self.assertEqual(retrieved, test_data)
        
        # Should expire after custom TTL
        with patch('time.time', return_value=time.time() + custom_ttl + 1):
            expired = cache_manager.get(cache_key)
            self.assertIsNone(expired)
    
    def test_cache_refresh_on_ttl_expiry(self):
        """Test cache behavior when data expires and needs refresh."""
        cache_manager = CacheManager()
        
        # Store data that will expire
        original_data = {"version": "1"}
        cache_manager.set_current_data("nfl", "123456", "league_info", original_data)
        
        # Verify it's cached
        self.assertEqual(
            cache_manager.get_current_data("nfl", "123456", "league_info"),
            original_data
        )
        
        # Simulate expiry
        with patch('time.time', return_value=time.time() + 400):
            expired = cache_manager.get_current_data("nfl", "123456", "league_info")
            self.assertIsNone(expired)
            
            # Store refreshed data
            refreshed_data = {"version": "2"}
            cache_manager.set_current_data("nfl", "123456", "league_info", refreshed_data)
            
            # Should get new data
            self.assertEqual(
                cache_manager.get_current_data("nfl", "123456", "league_info"),
                refreshed_data
            )


class TestCacheEviction(FunctionalTestCase):
    """Test cache size limits and LRU eviction policy."""
    
    def test_cache_size_limit_enforcement(self):
        """Test that cache respects size limits."""
        # Create cache with small size limit for testing
        small_cache = CacheManager(size_limit=1024)  # 1KB limit
        
        # Fill cache with data approaching the limit
        for i in range(10):
            large_data = {"data": "x" * 100, "id": i}  # ~100 bytes each
            small_cache.set(f"key_{i}", large_data)
        
        # Check that cache size is being tracked
        stats = small_cache.get_cache_stats()
        self.assertIn("memory_usage", stats)
        self.assertIn("size_limit", stats)
        
        # Add data that exceeds limit
        oversized_data = {"data": "x" * 2000}  # 2KB
        small_cache.set("oversized", oversized_data)
        
        # Should trigger eviction
        stats_after = small_cache.get_cache_stats()
        self.assertLessEqual(stats_after["memory_usage"], stats_after["size_limit"])
    
    def test_lru_eviction_policy(self):
        """Test that Least Recently Used items are evicted first."""
        cache_manager = CacheManager(size_limit=2048)  # 2KB limit
        
        # Add items in order
        items = []
        for i in range(5):
            data = {"item": i, "data": "x" * 200}  # ~200 bytes each
            key = f"item_{i}"
            cache_manager.set(key, data)
            items.append((key, data))
        
        # Access some items to change LRU order
        # Access items 1 and 3 to make them recently used
        cache_manager.get("item_1")
        cache_manager.get("item_3")
        
        # Add large item to trigger eviction
        large_data = {"large": "x" * 1000}
        cache_manager.set("large_item", large_data)
        
        # Items 1 and 3 should still be available (recently used)
        self.assertIsNotNone(cache_manager.get("item_1"))
        self.assertIsNotNone(cache_manager.get("item_3"))
        
        # Items 0, 2, 4 may have been evicted (least recently used)
        # At least one should be evicted
        evicted_count = 0
        for i in [0, 2, 4]:
            if cache_manager.get(f"item_{i}") is None:
                evicted_count += 1
        
        self.assertGreater(evicted_count, 0, "Some LRU items should be evicted")
    
    def test_cache_eviction_preserves_historical_data(self):
        """Test that historical data is preserved during eviction."""
        cache_manager = CacheManager(size_limit=1024)
        
        # Add historical data (should be preserved)
        historical_data = TestFixtures.get_mock_draft_data()
        cache_manager.set_historical_data("nfl", "2023", "123456", "draft", historical_data)
        
        # Fill cache with current data to trigger eviction
        for i in range(20):
            current_data = {"current": i, "data": "x" * 100}
            cache_manager.set_current_data("nfl", f"league_{i}", "standings", current_data)
        
        # Historical data should still be available
        retrieved_historical = cache_manager.get_historical_data("nfl", "2023", "123456", "draft")
        self.assertEqual(retrieved_historical, historical_data)
    
    def test_cache_memory_calculation(self):
        """Test that memory usage is calculated correctly."""
        cache_manager = CacheManager()
        
        initial_stats = cache_manager.get_cache_stats()
        initial_usage = initial_stats["memory_usage"]
        
        # Add known size data
        test_data = {"data": "x" * 1000}  # ~1KB
        cache_manager.set("test_key", test_data)
        
        updated_stats = cache_manager.get_cache_stats()
        updated_usage = updated_stats["memory_usage"]
        
        # Memory usage should have increased
        self.assertGreater(updated_usage, initial_usage)
        
        # Should be roughly 1KB increase (allowing for overhead)
        usage_increase = updated_usage - initial_usage
        self.assertGreater(usage_increase, 800)  # At least 800 bytes
        self.assertLess(usage_increase, 2000)    # Less than 2KB (with overhead)


class TestMultiSportCache(FunctionalTestCase):
    """Test cache separation and management across different sports."""
    
    def test_sport_specific_cache_separation(self):
        """Test that different sports cache data separately."""
        cache_manager = CacheManager()
        
        sports_data = {
            "nfl": TestFixtures.get_mock_league_data(),
            "nba": TestFixtures.get_mock_league_data(),
            "mlb": TestFixtures.get_mock_league_data(),
            "nhl": TestFixtures.get_mock_league_data()
        }
        
        # Modify data to be sport-specific
        for sport, data in sports_data.items():
            data["sport"] = sport
            cache_manager.set_current_data(sport, "123456", "league_info", data)
        
        # Each sport should retrieve its own data
        for sport, expected_data in sports_data.items():
            retrieved = cache_manager.get_current_data(sport, "123456", "league_info")
            self.assertEqual(retrieved, expected_data)
            self.assertEqual(retrieved["sport"], sport)
    
    def test_same_league_id_different_sports(self):
        """Test handling same league ID across different sports."""
        cache_manager = CacheManager()
        
        league_id = "123456"
        
        # Same league ID but different sports
        nfl_data = {"sport": "nfl", "teams": 10}
        nba_data = {"sport": "nba", "teams": 12}
        
        cache_manager.set_current_data("nfl", league_id, "info", nfl_data)
        cache_manager.set_current_data("nba", league_id, "info", nba_data)
        
        # Should maintain separation
        retrieved_nfl = cache_manager.get_current_data("nfl", league_id, "info")
        retrieved_nba = cache_manager.get_current_data("nba", league_id, "info")
        
        self.assertEqual(retrieved_nfl, nfl_data)
        self.assertEqual(retrieved_nba, nba_data)
        self.assertNotEqual(retrieved_nfl, retrieved_nba)
    
    def test_sport_specific_cache_statistics(self):
        """Test cache statistics break down by sport."""
        cache_manager = CacheManager()
        
        # Add data for different sports
        sports = ["nfl", "nba", "mlb", "nhl"]
        for sport in sports:
            for i in range(3):  # 3 items per sport
                data = {"sport": sport, "item": i}
                cache_manager.set_current_data(sport, f"league_{i}", "data", data)
        
        # Get overall statistics
        stats = cache_manager.get_cache_stats()
        
        self.assertIn("total_entries", stats)
        self.assertEqual(stats["total_entries"], len(sports) * 3)
        
        # Should track entries by category
        self.assertIn("current_entries", stats)
        self.assertIn("historical_entries", stats)
    
    def test_cross_sport_cache_operations(self):
        """Test cache operations that span multiple sports."""
        cache_manager = CacheManager()
        
        # Add data for multiple sports
        sports_data = []
        for sport in ["nfl", "nba"]:
            for league in ["123", "456"]:
                data = {"sport": sport, "league_id": league}
                cache_manager.set_current_data(sport, league, "info", data)
                sports_data.append((sport, league, data))
        
        # Clear cache by type (current vs historical)
        cache_manager.clear_current_cache()
        
        # All current data should be cleared
        for sport, league, data in sports_data:
            retrieved = cache_manager.get_current_data(sport, league, "info")
            self.assertIsNone(retrieved)
        
        # Add historical data
        cache_manager.set_historical_data("nfl", "2023", "123", "draft", {"draft": "data"})
        
        # Historical data should remain after current cache clear
        historical = cache_manager.get_historical_data("nfl", "2023", "123", "draft")
        self.assertIsNotNone(historical)


class TestCacheManagement(FunctionalTestCase):
    """Test cache management operations and utilities."""
    
    def test_cache_clear_operations(self):
        """Test various cache clearing operations."""
        cache_manager = CacheManager()
        
        # Add different types of data
        current_data = TestFixtures.get_mock_standings_data()
        historical_data = TestFixtures.get_mock_draft_data()
        
        cache_manager.set_current_data("nfl", "123456", "standings", current_data)
        cache_manager.set_historical_data("nfl", "2023", "123456", "draft", historical_data)
        
        # Verify data is cached
        self.assertIsNotNone(cache_manager.get_current_data("nfl", "123456", "standings"))
        self.assertIsNotNone(cache_manager.get_historical_data("nfl", "2023", "123456", "draft"))
        
        # Clear only current data
        cache_manager.clear_current_cache()
        
        # Current data should be gone, historical should remain
        self.assertIsNone(cache_manager.get_current_data("nfl", "123456", "standings"))
        self.assertIsNotNone(cache_manager.get_historical_data("nfl", "2023", "123456", "draft"))
        
        # Clear all data
        cache_manager.clear()
        
        # Everything should be gone
        self.assertIsNone(cache_manager.get_current_data("nfl", "123456", "standings"))
        self.assertIsNone(cache_manager.get_historical_data("nfl", "2023", "123456", "draft"))
    
    def test_cache_statistics_accuracy(self):
        """Test that cache statistics are accurate and useful."""
        cache_manager = CacheManager()
        
        initial_stats = cache_manager.get_cache_stats()
        
        # Add various types of data
        cache_manager.set_current_data("nfl", "123", "standings", {"current": True})
        cache_manager.set_historical_data("nfl", "2023", "123", "draft", {"historical": True})
        cache_manager.set_current_data("nba", "456", "roster", {"basketball": True})
        
        updated_stats = cache_manager.get_cache_stats()
        
        # Should show increased counts
        self.assertEqual(updated_stats["total_entries"], initial_stats["total_entries"] + 3)
        self.assertGreater(updated_stats["memory_usage"], initial_stats["memory_usage"])
        
        # Should categorize correctly
        self.assertGreaterEqual(updated_stats["current_entries"], 2)
        self.assertGreaterEqual(updated_stats["historical_entries"], 1)
    
    def test_cache_hit_rate_tracking(self):
        """Test that cache hit rates are tracked correctly."""
        cache_manager = CacheManager()
        
        # Add data to cache
        test_data = TestFixtures.get_mock_league_data()
        cache_manager.set_current_data("nfl", "123456", "league_info", test_data)
        
        # Multiple cache hits
        for _ in range(5):
            retrieved = cache_manager.get_current_data("nfl", "123456", "league_info")
            self.assertEqual(retrieved, test_data)
        
        # Cache misses
        for i in range(3):
            missed = cache_manager.get_current_data("nfl", f"missing_{i}", "info")
            self.assertIsNone(missed)
        
        # Get statistics
        stats = cache_manager.get_cache_stats()
        
        # Should track hits and misses
        if "hit_rate" in stats:
            # Hit rate should be reasonable (5 hits out of 8 total requests = 62.5%)
            self.assertGreater(stats["hit_rate"], 0.5)
            self.assertLess(stats["hit_rate"], 1.0)
    
    def test_cache_key_generation_consistency(self):
        """Test that cache keys are generated consistently."""
        cache_manager = CacheManager()
        
        # Test current data keys
        key1 = cache_manager._build_current_key("nfl", "123456", "standings")
        key2 = cache_manager._build_current_key("nfl", "123456", "standings")
        self.assertEqual(key1, key2)
        
        # Different parameters should generate different keys
        key3 = cache_manager._build_current_key("nba", "123456", "standings")
        key4 = cache_manager._build_current_key("nfl", "654321", "standings")
        key5 = cache_manager._build_current_key("nfl", "123456", "roster")
        
        keys = [key1, key3, key4, key5]
        self.assertEqual(len(keys), len(set(keys)))  # All should be unique
        
        # Test historical data keys
        hist_key1 = cache_manager._build_historical_key("nfl", "2023", "123456", "draft")
        hist_key2 = cache_manager._build_historical_key("nfl", "2023", "123456", "draft")
        self.assertEqual(hist_key1, hist_key2)
        
        # Should be different from current keys
        self.assertNotEqual(hist_key1, key1)
    
    def test_concurrent_cache_access(self):
        """Test cache behavior with concurrent access patterns."""
        cache_manager = CacheManager()
        
        # Simulate concurrent reads and writes
        test_data = {"concurrent": "test"}
        
        # Multiple threads might access cache simultaneously
        # This is a simplified test - real concurrency would need threading
        
        # Write data
        cache_manager.set_current_data("nfl", "123456", "test", test_data)
        
        # Multiple reads
        results = []
        for _ in range(10):
            result = cache_manager.get_current_data("nfl", "123456", "test")
            results.append(result)
        
        # All reads should return the same data
        for result in results:
            self.assertEqual(result, test_data)
        
        # Overwrite data
        new_data = {"concurrent": "updated"}
        cache_manager.set_current_data("nfl", "123456", "test", new_data)
        
        # Subsequent reads should get new data
        updated_result = cache_manager.get_current_data("nfl", "123456", "test")
        self.assertEqual(updated_result, new_data)


if __name__ == "__main__":
    import unittest
    
    print("League Analysis MCP Server - Cache Functional Tests")
    print("=" * 58)
    print("Testing caching behavior and TTL management")
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 58)
    if result.wasSuccessful():
        print("PASS: All cache tests passed!")
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