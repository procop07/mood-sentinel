#!/usr/bin/env python3
"""Weekly Report Generator

Generates weekly reports by aggregating metrics from features and alerts
for the last 7 days and creating a text report file.

Usage:
    python weekly.py

Output:
    reports/weekly_<YYYY-WW>.txt
"""

import os
import json
import glob
from datetime import datetime, timedelta
from collections import defaultdict
import argparse


def get_week_number(date):
    """Get ISO week number for a given date."""
    return date.isocalendar()[1]


def get_year_week(date):
    """Get year-week string in format YYYY-WW."""
    year, week, _ = date.isocalendar()
    return f"{year}-{week:02d}"


def load_json_files(directory, days_back=7):
    """Load JSON files from directory for the last N days."""
    data = []
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    if not os.path.exists(directory):
        print(f"Warning: Directory {directory} not found")
        return data
    
    pattern = os.path.join(directory, "*.json")
    files = glob.glob(pattern)
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
            # Extract date from filename or data
            filename = os.path.basename(file_path)
            file_date = None
            
            # Try to parse date from filename (assuming format like YYYY-MM-DD)
            try:
                date_part = filename.split('.')[0][-10:]
                file_date = datetime.strptime(date_part, '%Y-%m-%d').date()
            except (ValueError, IndexError):
                # Try to get date from file content
                if 'timestamp' in file_data:
                    try:
                        file_date = datetime.fromisoformat(file_data['timestamp']).date()
                    except ValueError:
                        pass
                elif 'date' in file_data:
                    try:
                        file_date = datetime.strptime(file_data['date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
            
            # Include file if within date range
            if file_date and start_date <= file_date <= end_date:
                file_data['_file_date'] = file_date
                file_data['_file_path'] = file_path
                data.append(file_data)
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {file_path}: {e}")
    
    return data


def analyze_features_data(features_data):
    """Analyze features data and extract metrics."""
    metrics = {
        'total_features': len(features_data),
        'feature_types': defaultdict(int),
        'sentiment_distribution': defaultdict(int),
        'daily_counts': defaultdict(int),
        'top_features': []
    }
    
    for feature in features_data:
        # Count feature types
        if 'type' in feature:
            metrics['feature_types'][feature['type']] += 1
        
        # Count sentiment if available
        if 'sentiment' in feature:
            metrics['sentiment_distribution'][feature['sentiment']] += 1
        
        # Count by day
        if '_file_date' in feature:
            metrics['daily_counts'][str(feature['_file_date'])] += 1
        
        # Collect features for ranking
        if 'score' in feature or 'confidence' in feature:
            score = feature.get('score', feature.get('confidence', 0))
            metrics['top_features'].append({
                'name': feature.get('name', feature.get('text', 'Unknown')),
                'score': score,
                'type': feature.get('type', 'unknown')
            })
    
    # Sort top features by score
    metrics['top_features'] = sorted(
        metrics['top_features'], 
        key=lambda x: x['score'], 
        reverse=True
    )[:10]
    
    return metrics


def analyze_alerts_data(alerts_data):
    """Analyze alerts data and extract metrics."""
    metrics = {
        'total_alerts': len(alerts_data),
        'alert_types': defaultdict(int),
        'severity_distribution': defaultdict(int),
        'daily_counts': defaultdict(int),
        'critical_alerts': []
    }
    
    for alert in alerts_data:
        # Count alert types
        if 'type' in alert:
            metrics['alert_types'][alert['type']] += 1
        
        # Count severity levels
        if 'severity' in alert:
            metrics['severity_distribution'][alert['severity']] += 1
        elif 'priority' in alert:
            metrics['severity_distribution'][alert['priority']] += 1
        
        # Count by day
        if '_file_date' in alert:
            metrics['daily_counts'][str(alert['_file_date'])] += 1
        
        # Collect critical alerts
        severity = alert.get('severity', alert.get('priority', 'medium')).lower()
        if severity in ['critical', 'high', 'urgent']:
            metrics['critical_alerts'].append({
                'message': alert.get('message', alert.get('text', 'No message')),
                'severity': severity,
                'timestamp': alert.get('timestamp', str(alert.get('_file_date', 'Unknown')))
            })
    
    return metrics


def generate_report(features_metrics, alerts_metrics, week_string):
    """Generate the weekly report text."""
    report_lines = []
    report_lines.append(f"WEEKLY MOOD SENTINEL REPORT - WEEK {week_string}")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("EXECUTIVE SUMMARY")
    report_lines.append("-" * 20)
    total_features = features_metrics['total_features']
    total_alerts = alerts_metrics['total_alerts']
    critical_alerts = len(alerts_metrics['critical_alerts'])
    
    report_lines.append(f"Total Features Processed: {total_features}")
    report_lines.append(f"Total Alerts Generated: {total_alerts}")
    report_lines.append(f"Critical Alerts: {critical_alerts}")
    report_lines.append("")
    
    # Features Analysis
    report_lines.append("FEATURES ANALYSIS")
    report_lines.append("-" * 20)
    
    if features_metrics['feature_types']:
        report_lines.append("Feature Types Distribution:")
        for ftype, count in sorted(features_metrics['feature_types'].items()):
            percentage = (count / total_features) * 100 if total_features > 0 else 0
            report_lines.append(f"  {ftype}: {count} ({percentage:.1f}%)")
        report_lines.append("")
    
    if features_metrics['sentiment_distribution']:
        report_lines.append("Sentiment Distribution:")
        for sentiment, count in sorted(features_metrics['sentiment_distribution'].items()):
            percentage = (count / total_features) * 100 if total_features > 0 else 0
            report_lines.append(f"  {sentiment}: {count} ({percentage:.1f}%)")
        report_lines.append("")
    
    if features_metrics['top_features']:
        report_lines.append("Top Features (by score):")
        for i, feature in enumerate(features_metrics['top_features'][:5], 1):
            name = feature['name'][:50] + "..." if len(feature['name']) > 50 else feature['name']
            report_lines.append(f"  {i}. {name} (score: {feature['score']:.3f}, type: {feature['type']})")
        report_lines.append("")
    
    # Alerts Analysis
    report_lines.append("ALERTS ANALYSIS")
    report_lines.append("-" * 20)
    
    if alerts_metrics['alert_types']:
        report_lines.append("Alert Types Distribution:")
        for atype, count in sorted(alerts_metrics['alert_types'].items()):
            percentage = (count / total_alerts) * 100 if total_alerts > 0 else 0
            report_lines.append(f"  {atype}: {count} ({percentage:.1f}%)")
        report_lines.append("")
    
    if alerts_metrics['severity_distribution']:
        report_lines.append("Severity Distribution:")
        for severity, count in sorted(alerts_metrics['severity_distribution'].items()):
            percentage = (count / total_alerts) * 100 if total_alerts > 0 else 0
            report_lines.append(f"  {severity}: {count} ({percentage:.1f}%)")
        report_lines.append("")
    
    if alerts_metrics['critical_alerts']:
        report_lines.append("Critical Alerts Summary:")
        for i, alert in enumerate(alerts_metrics['critical_alerts'][:5], 1):
            message = alert['message'][:80] + "..." if len(alert['message']) > 80 else alert['message']
            report_lines.append(f"  {i}. [{alert['severity'].upper()}] {message}")
            report_lines.append(f"     Timestamp: {alert['timestamp']}")
        if len(alerts_metrics['critical_alerts']) > 5:
            remaining = len(alerts_metrics['critical_alerts']) - 5
            report_lines.append(f"     ... and {remaining} more critical alerts")
        report_lines.append("")
    
    # Daily Activity
    report_lines.append("DAILY ACTIVITY BREAKDOWN")
    report_lines.append("-" * 30)
    
    all_dates = set(features_metrics['daily_counts'].keys()) | set(alerts_metrics['daily_counts'].keys())
    sorted_dates = sorted(all_dates)
    
    for date in sorted_dates:
        features_count = features_metrics['daily_counts'].get(date, 0)
        alerts_count = alerts_metrics['daily_counts'].get(date, 0)
        report_lines.append(f"  {date}: {features_count} features, {alerts_count} alerts")
    
    if not sorted_dates:
        report_lines.append("  No daily activity data available")
    
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("End of Report")
    
    return "\n".join(report_lines)


def main():
    """Main function to generate weekly report."""
    parser = argparse.ArgumentParser(description='Generate weekly mood sentinel report')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back (default: 7)')
    parser.add_argument('--features-dir', default='features', help='Directory containing features data')
    parser.add_argument('--alerts-dir', default='alerts', help='Directory containing alerts data')
    parser.add_argument('--reports-dir', default='reports', help='Directory to save reports')
    
    args = parser.parse_args()
    
    # Create reports directory if it doesn't exist
    os.makedirs(args.reports_dir, exist_ok=True)
    
    # Get current week string
    current_date = datetime.now().date()
    week_string = get_year_week(current_date)
    
    print(f"Generating weekly report for week {week_string}...")
    
    # Load data from last N days
    print(f"Loading features data from {args.features_dir}...")
    features_data = load_json_files(args.features_dir, args.days)
    
    print(f"Loading alerts data from {args.alerts_dir}...")
    alerts_data = load_json_files(args.alerts_dir, args.days)
    
    print(f"Found {len(features_data)} feature files and {len(alerts_data)} alert files")
    
    # Analyze data
    features_metrics = analyze_features_data(features_data)
    alerts_metrics = analyze_alerts_data(alerts_data)
    
    # Generate report
    report_content = generate_report(features_metrics, alerts_metrics, week_string)
    
    # Save report
    report_filename = f"weekly_{week_string}.txt"
    report_path = os.path.join(args.reports_dir, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"Weekly report saved to: {report_path}")
    print(f"Report contains {len(features_data)} features and {len(alerts_data)} alerts")


if __name__ == "__main__":
    main()
