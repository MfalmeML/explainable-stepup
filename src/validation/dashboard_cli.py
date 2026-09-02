from src.validation.metrics import ValidationMetrics
import sys

def print_completion_table(rates: dict, title: str):
    """Pretty print completion rates."""
    print(f"\n{title}")
    print("-" * 60)
    print(f"{'Category':<20} {'Completed':<10} {'Abandoned':<10} {'Failed':<10} {'Rate':<8}")
    print("-" * 60)
    for category, data in sorted(rates.items(), key=lambda x: x[1]['completion_rate']):
        print(
            f"{category:<20} "
            f"{data['completed']:<10} "
            f"{data['abandoned']:<10} "
            f"{data['failed']:<10} "
            f"{data['completion_rate']:.2%}"
        )
    print("-" * 60)

def print_drift_alerts(alerts: dict):
    """Pretty print drift alerts."""
    if not alerts:
        print("\nNo drift detected.")
        return
    
    print("\nDrift Alerts")
    print("-" * 60)
    print(f"{'Category':<20} {'Old Rate':<12} {'New Rate':<12} {'Change':<10}")
    print("-" * 60)
    for category, data in alerts.items():
        direction = "↑" if data['direction'] == 'up' else "↓"
        print(
            f"{category:<20} "
            f"{data['old_rate']:.2%} ({data['old_count']})    "
            f"{data['new_rate']:.2%} ({data['new_count']})    "
            f"{direction} {abs(data['change']):.2%}"
        )
    print("-" * 60)

def print_trend(trend: dict, category: str):
    """Print trend for a specific category."""
    if category not in trend or not trend[category]:
        print(f"\nNo trend data for category: {category}")
        return
    
    print(f"\nTrend for {category}")
    print("-" * 60)
    print(f"{'Time':<20} {'Rate':<8} {'Completed':<10} {'Total':<8}")
    print("-" * 60)
    for point in trend[category]:
        print(
            f"{point['timestamp'][:13]:<20} "
            f"{point['completion_rate']:.2%}    "
            f"{point['completed']:<10} "
            f"{point['total']:<8}"
        )
    print("-" * 60)

def main():
    store_path = "outcome_store.json"
    metrics = ValidationMetrics(store_path)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python dashboard_cli.py rates              - Show completion rates by category")
        print("  python dashboard_cli.py score              - Show completion rates by ring_score bucket")
        print("  python dashboard_cli.py drift              - Check for drift")
        print("  python dashboard_cli.py trend <category>   - Show trend for category")
        print("  python dashboard_cli.py dashboard          - Show full dashboard")
        return
    
    command = sys.argv[1]
    
    if command == "rates":
        rates = metrics.get_completion_rate_by_category()
        print_completion_table(rates, "Completion Rates by Reason Category")
    
    elif command == "score":
        rates = metrics.get_completion_rate_by_score_bucket()
        print_completion_table(rates, "Completion Rates by Ring Score Bucket")
    
    elif command == "drift":
        alerts = metrics.detect_drift()
        print_drift_alerts(alerts)
    
    elif command == "trend" and len(sys.argv) > 2:
        trend = metrics.get_trend_by_category()
        print_trend(trend, sys.argv[2])
    
    elif command == "dashboard":
        rates_by_category = metrics.get_completion_rate_by_category()
        rates_by_score = metrics.get_completion_rate_by_score_bucket()
        alerts = metrics.detect_drift()
        
        print_completion_table(rates_by_category, "Completion Rates by Reason Category")
        print_completion_table(rates_by_score, "Completion Rates by Ring Score Bucket")
        print_drift_alerts(alerts)
        
        # Show top trend
        trend = metrics.get_trend_by_category()
        if trend:
            top_category = max(trend.items(), key=lambda x: len(x[1]))[0]
            print_trend(trend, top_category)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()