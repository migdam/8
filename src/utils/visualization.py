"""Visualization utilities for agent monitoring"""

from typing import Dict, Any, List
from datetime import datetime
import json


class DashboardGenerator:
    """Generate monitoring dashboard data"""

    def __init__(self, telemetry):
        """
        Initialize dashboard generator

        Args:
            telemetry: AgentTelemetry instance
        """
        self.telemetry = telemetry

    def generate_summary(self) -> Dict[str, Any]:
        """Generate dashboard summary"""
        metrics = self.telemetry.metrics.get_all_metrics()
        cost = self.telemetry.cost_tracker.get_summary()
        performance = self.telemetry.profiler.get_all_stats()

        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_metrics": len(metrics),
                "data": metrics
            },
            "cost": cost,
            "performance": {
                "total_operations": len(performance),
                "data": performance
            },
            "recent_events": len(self.telemetry.events)
        }

    def generate_metrics_chart_data(
        self,
        metric_name: str
    ) -> Dict[str, List]:
        """
        Generate chart data for a metric

        Args:
            metric_name: Metric name

        Returns:
            Chart data with timestamps and values
        """
        if metric_name not in self.telemetry.metrics.metrics:
            return {"timestamps": [], "values": []}

        data = self.telemetry.metrics.metrics[metric_name]

        return {
            "timestamps": [
                datetime.fromtimestamp(d["timestamp"]).isoformat()
                for d in data
            ],
            "values": [d["value"] for d in data]
        }

    def generate_cost_breakdown(self) -> Dict[str, Any]:
        """Generate cost breakdown by model"""
        summary = self.telemetry.cost_tracker.get_summary()

        if "by_model" not in summary:
            return {}

        return {
            "labels": list(summary["by_model"].keys()),
            "costs": [
                summary["by_model"][model]["cost"]
                for model in summary["by_model"]
            ],
            "tokens": [
                summary["by_model"][model]["tokens"]
                for model in summary["by_model"]
            ]
        }

    def export_dashboard_json(self, filepath: str):
        """
        Export dashboard data to JSON

        Args:
            filepath: Output file path
        """
        data = {
            "summary": self.generate_summary(),
            "cost_breakdown": self.generate_cost_breakdown(),
            "timestamp": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


def generate_ascii_chart(
    data: List[float],
    width: int = 50,
    height: int = 10
) -> str:
    """
    Generate ASCII bar chart

    Args:
        data: Data points
        width: Chart width
        height: Chart height

    Returns:
        ASCII chart string
    """
    if not data:
        return "No data"

    max_val = max(data)
    min_val = min(data)
    range_val = max_val - min_val if max_val != min_val else 1

    chart_lines = []

    # Generate chart rows
    for i in range(height):
        line = ""
        threshold = max_val - (i * range_val / height)

        for val in data:
            if val >= threshold:
                line += "█"
            else:
                line += " "

        chart_lines.append(line)

    # Add axis
    chart_lines.append("─" * len(data))

    return "\n".join(chart_lines)


def print_performance_table(stats: Dict[str, Dict[str, Any]]):
    """
    Print performance statistics as table

    Args:
        stats: Performance statistics
    """
    print("\n" + "="*80)
    print(f"{'Operation':<30} {'Count':<10} {'Avg (s)':<12} {'Min (s)':<12} {'Max (s)':<12}")
    print("="*80)

    for operation, data in stats.items():
        if not data:
            continue

        print(
            f"{operation:<30} "
            f"{data['count']:<10} "
            f"{data['avg']:<12.4f} "
            f"{data['min']:<12.4f} "
            f"{data['max']:<12.4f}"
        )

    print("="*80 + "\n")


def print_cost_summary(summary: Dict[str, Any]):
    """
    Print cost summary

    Args:
        summary: Cost summary data
    """
    print("\n" + "="*60)
    print("Cost Summary")
    print("="*60)
    print(f"Total Requests: {summary.get('total_requests', 0)}")
    print(f"Total Tokens:   {summary.get('total_tokens', 0):,}")
    print(f"Total Cost:     ${summary.get('total_cost', 0):.4f}")

    if "by_model" in summary:
        print("\nBy Model:")
        print("-"*60)

        for model, data in summary["by_model"].items():
            print(f"\n{model}:")
            print(f"  Requests: {data['requests']}")
            print(f"  Tokens:   {data['tokens']:,}")
            print(f"  Cost:     ${data['cost']:.4f}")

    print("="*60 + "\n")
