"""Unit tests for utilities"""

import pytest
import asyncio
import time
from src.utils.caching import Cache, ResponseCache
from src.utils.monitoring import MetricsCollector, CostTracker


class TestCache:
    """Test caching utilities"""

    def test_cache_set_get(self):
        """Test basic cache operations"""
        cache = Cache(default_ttl=60)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = Cache(default_ttl=1)

        cache.set("key1", "value1", ttl=0.1)
        assert cache.get("key1") == "value1"

        time.sleep(0.2)
        assert cache.get("key1") is None

    def test_cache_delete(self):
        """Test cache deletion"""
        cache = Cache()

        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_cache_clear(self):
        """Test clearing cache"""
        cache = Cache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_stats(self):
        """Test cache statistics"""
        cache = Cache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")
        cache.get("key1")

        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["total_hits"] == 2


class TestMetricsCollector:
    """Test metrics collection"""

    def test_record_metric(self):
        """Test recording metrics"""
        collector = MetricsCollector()

        collector.record_metric("latency", 100.5)
        collector.record_metric("latency", 150.0)

        stats = collector.get_metric_stats("latency")
        assert stats["count"] == 2
        assert stats["avg"] == 125.25

    def test_metric_stats(self):
        """Test metric statistics"""
        collector = MetricsCollector()

        collector.record_metric("response_time", 100)
        collector.record_metric("response_time", 200)
        collector.record_metric("response_time", 150)

        stats = collector.get_metric_stats("response_time")

        assert stats["min"] == 100
        assert stats["max"] == 200
        assert stats["avg"] == 150

    def test_time_window(self):
        """Test time window filtering"""
        collector = MetricsCollector()

        # Record old metric
        collector.record_metric("test", 1.0, timestamp=time.time() - 3600)

        # Record recent metric
        collector.record_metric("test", 2.0)

        # Get stats for last 1800 seconds
        stats = collector.get_metric_stats("test", time_window=1800)

        assert stats["count"] == 1  # Only recent metric


class TestCostTracker:
    """Test cost tracking"""

    def test_record_usage(self):
        """Test recording API usage"""
        tracker = CostTracker()

        tracker.record_usage(
            model="gpt-3.5-turbo",
            input_tokens=100,
            output_tokens=50
        )

        assert tracker.total_tokens == 150
        assert tracker.total_cost > 0

    def test_usage_summary(self):
        """Test usage summary"""
        tracker = CostTracker()

        tracker.record_usage("gpt-3.5-turbo", 100, 50)
        tracker.record_usage("gpt-4", 200, 100)

        summary = tracker.get_summary()

        assert summary["total_requests"] == 2
        assert summary["total_tokens"] == 450
        assert len(summary["by_model"]) == 2


class TestResponseCache:
    """Test response caching"""

    def test_cache_response(self):
        """Test caching LLM responses"""
        cache = ResponseCache(max_size=100)

        cache.cache_response(
            prompt="Hello",
            response="Hi there!",
            model="gpt-3.5-turbo"
        )

        cached = cache.get_cached_response("Hello", "gpt-3.5-turbo")
        assert cached == "Hi there!"

    def test_different_models(self):
        """Test caching for different models"""
        cache = ResponseCache()

        cache.cache_response("Hello", "Response 1", "gpt-3.5-turbo")
        cache.cache_response("Hello", "Response 2", "gpt-4")

        assert cache.get_cached_response("Hello", "gpt-3.5-turbo") == "Response 1"
        assert cache.get_cached_response("Hello", "gpt-4") == "Response 2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
