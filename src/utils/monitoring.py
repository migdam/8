"""Monitoring and metrics tracking for agents"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import time
import json
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Collect and track agent performance metrics"""

    def __init__(self, persist_path: Optional[str] = None):
        """
        Initialize metrics collector

        Args:
            persist_path: Optional path to persist metrics
        """
        self.metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.persist_path = persist_path
        self.start_time = time.time()

    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[float] = None
    ):
        """
        Record a metric value

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for grouping
            timestamp: Optional timestamp (defaults to now)
        """
        metric_data = {
            "value": value,
            "timestamp": timestamp or time.time(),
            "tags": tags or {}
        }

        self.metrics[metric_name].append(metric_data)
        logger.debug(f"Recorded metric {metric_name}: {value}")

    def get_metric_stats(
        self,
        metric_name: str,
        time_window: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a metric

        Args:
            metric_name: Metric name
            time_window: Optional time window in seconds

        Returns:
            Metric statistics
        """
        if metric_name not in self.metrics:
            return {}

        values = self.metrics[metric_name]

        # Filter by time window
        if time_window:
            cutoff = time.time() - time_window
            values = [v for v in values if v["timestamp"] >= cutoff]

        if not values:
            return {}

        metric_values = [v["value"] for v in values]

        return {
            "count": len(metric_values),
            "min": min(metric_values),
            "max": max(metric_values),
            "avg": sum(metric_values) / len(metric_values),
            "sum": sum(metric_values),
            "latest": metric_values[-1]
        }

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all metrics"""
        return {
            name: self.get_metric_stats(name)
            for name in self.metrics.keys()
        }

    def save_to_disk(self):
        """Save metrics to disk"""
        if not self.persist_path:
            return

        try:
            Path(self.persist_path).parent.mkdir(parents=True, exist_ok=True)

            data = {
                "start_time": self.start_time,
                "metrics": {
                    name: values
                    for name, values in self.metrics.items()
                }
            }

            with open(self.persist_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved metrics to {self.persist_path}")

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")


class CostTracker:
    """Track API costs and token usage"""

    # Approximate costs (as of 2024)
    MODEL_COSTS = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},  # per 1K tokens
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    }

    def __init__(self):
        """Initialize cost tracker"""
        self.usage_history: List[Dict[str, Any]] = []
        self.total_tokens = 0
        self.total_cost = 0.0

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Record API usage

        Args:
            model: Model name
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            context: Optional context information
        """
        # Get cost rates
        if model in self.MODEL_COSTS:
            rates = self.MODEL_COSTS[model]
        else:
            # Default to GPT-3.5 turbo rates
            rates = self.MODEL_COSTS["gpt-3.5-turbo"]

        # Calculate cost
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        total_cost = input_cost + output_cost

        # Record
        usage = {
            "timestamp": time.time(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": total_cost,
            "context": context or {}
        }

        self.usage_history.append(usage)
        self.total_tokens += input_tokens + output_tokens
        self.total_cost += total_cost

        logger.debug(f"Recorded usage: {model}, {input_tokens + output_tokens} tokens, ${total_cost:.4f}")

    def get_summary(self, time_window: Optional[int] = None) -> Dict[str, Any]:
        """
        Get usage summary

        Args:
            time_window: Optional time window in seconds

        Returns:
            Usage summary
        """
        usage = self.usage_history

        if time_window:
            cutoff = time.time() - time_window
            usage = [u for u in usage if u["timestamp"] >= cutoff]

        if not usage:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0
            }

        total_tokens = sum(u["total_tokens"] for u in usage)
        total_cost = sum(u["cost"] for u in usage)

        # Group by model
        by_model = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        for u in usage:
            model = u["model"]
            by_model[model]["requests"] += 1
            by_model[model]["tokens"] += u["total_tokens"]
            by_model[model]["cost"] += u["cost"]

        return {
            "total_requests": len(usage),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "by_model": dict(by_model)
        }


class PerformanceProfiler:
    """Profile agent performance"""

    def __init__(self):
        """Initialize profiler"""
        self.timings: Dict[str, List[float]] = defaultdict(list)
        self.active_timers: Dict[str, float] = {}

    def start_timer(self, name: str):
        """Start a timer"""
        self.active_timers[name] = time.time()

    def end_timer(self, name: str) -> Optional[float]:
        """
        End a timer and record duration

        Args:
            name: Timer name

        Returns:
            Duration in seconds
        """
        if name not in self.active_timers:
            logger.warning(f"Timer '{name}' was not started")
            return None

        duration = time.time() - self.active_timers[name]
        self.timings[name].append(duration)
        del self.active_timers[name]

        return duration

    def get_stats(self, name: str) -> Dict[str, Any]:
        """Get timing statistics"""
        if name not in self.timings or not self.timings[name]:
            return {}

        timings = self.timings[name]

        return {
            "count": len(timings),
            "total": sum(timings),
            "avg": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
            "latest": timings[-1]
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get all timing statistics"""
        return {
            name: self.get_stats(name)
            for name in self.timings.keys()
        }


class AgentTelemetry:
    """Comprehensive telemetry for agent systems"""

    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize telemetry

        Args:
            persist_dir: Optional directory for persisting data
        """
        self.metrics = MetricsCollector(
            persist_path=f"{persist_dir}/metrics.json" if persist_dir else None
        )
        self.cost_tracker = CostTracker()
        self.profiler = PerformanceProfiler()
        self.events: List[Dict[str, Any]] = []

    def log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        severity: str = "info"
    ):
        """
        Log an event

        Args:
            event_type: Type of event
            data: Event data
            severity: Event severity
        """
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "severity": severity,
            "data": data
        }

        self.events.append(event)

        # Keep only recent events
        if len(self.events) > 10000:
            self.events = self.events[-10000:]

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for monitoring dashboard

        Returns:
            Dashboard data
        """
        return {
            "metrics": self.metrics.get_all_metrics(),
            "cost": self.cost_tracker.get_summary(time_window=3600),  # Last hour
            "performance": self.profiler.get_all_stats(),
            "recent_events": self.events[-100:],  # Last 100 events
            "timestamp": datetime.now().isoformat()
        }

    def save_telemetry(self):
        """Save all telemetry data"""
        self.metrics.save_to_disk()
