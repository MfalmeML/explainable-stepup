from src.validation.metrics import ValidationMetrics
import argparse
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

    parser = argparse.ArgumentParser(
        description="Validation dashboard for step-up completion rates and drift."
    )
    subparsers = parser.add_subparsers(dest="command")

    p_rates = subparsers.add_parser("rates", help="Show completion rates by category")
    p_rates.add_argument("--min-cases", type=int, default=5, help="Minimum cases per category to display (default: 5)")

    p_score = subparsers.add_parser("score", help="Show completion rates by ring_score bucket")
    p_score.add_argument("--min-cases", type=int, default=5, help="Minimum cases per bucket to display (default: 5)")

    p_drift = subparsers.add_parser("drift", help="Check for drift")
    p_drift.add_argument("--min-cases", type=int, default=5, help="Minimum cases per period to display (default: 5)")

    p_trend = subparsers.add_parser("trend", help="Show trend for category")
    p_trend.add_argument("category", help="Reason category to show the trend for, e.g. new_device")
    p_trend.add_argument("--min-cases", type=int, default=3, help="Minimum cases per interval to display (default: 3)")

    p_dash = subparsers.add_parser("dashboard", help="Show full dashboard")
    p_dash.add_argument("--min-cases", type=int, default=5, help="Minimum cases per category/bucket/period to display (default: 5)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    metrics = ValidationMetrics(store_path)

    if args.command == "rates":
        rates = metrics.get_completion_rate_by_category(min_cases=args.min_cases)
        print_completion_table(rates, "Completion Rates by Reason Category")

    elif args.command == "score":
        rates = metrics.get_completion_rate_by_score_bucket(min_cases=args.min_cases)
        print_completion_table(rates, "Completion Rates by Ring Score Bucket")

    elif args.command == "drift":
        alerts = metrics.detect_drift(min_cases=args.min_cases)
        print_drift_alerts(alerts)

    elif args.command == "trend":
        trend = metrics.get_trend_by_category(min_cases=args.min_cases)
        print_trend(trend, args.category)

    elif args.command == "dashboard":
        rates_by_category = metrics.get_completion_rate_by_category(min_cases=args.min_cases)
        rates_by_score = metrics.get_completion_rate_by_score_bucket(min_cases=args.min_cases)
        alerts = metrics.detect_drift(min_cases=args.min_cases)

        print_completion_table(rates_by_category, "Completion Rates by Reason Category")
        print_completion_table(rates_by_score, "Completion Rates by Ring Score Bucket")
        print_drift_alerts(alerts)

        # Show top trend
        trend = metrics.get_trend_by_category(min_cases=args.min_cases)
        if trend:
            top_category = max(trend.items(), key=lambda x: len(x[1]))[0]
            print_trend(trend, top_category)

    else:
        print(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()