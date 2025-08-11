#!/usr/bin/env python3
"""
Mood Sentinel - Main Application Entry Point
A social media mood monitoring system that tracks sentiment
and alerts on concerning patterns.
"""
import sys
import logging
import argparse
import sqlite3
from datetime import datetime
import yaml
import os
from etl import DataExtractor
from features import FeatureExtractor
from rules import RuleEngine
from report import ReportGenerator
from notify import NotificationService

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing config: {e}")
        sys.exit(1)

def setup_logging(config: dict) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, config.get('logging', {}).get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.get('logging', {}).get('file', 'mood-sentinel.log')),
            logging.StreamHandler()
        ]
    )

def setup_database(config: dict) -> str:
    """Setup database and create alerts table if it doesn't exist."""
    db_path = config.get('database', {}).get('path', 'mood_sentinel.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create alerts table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            summary TEXT NOT NULL,
            actions TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            report_date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    return db_path

def save_alert_to_database(alert: dict, db_path: str, report_date: str = None) -> None:
    """Save alert to database alerts table."""
    if not report_date:
        report_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Convert actions list to string
    actions_str = '; '.join(alert.get('actions', []))
    
    cursor.execute("""
        INSERT INTO alerts (alert_type, severity, summary, actions, timestamp, report_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        alert.get('type', 'Unknown'),
        alert.get('severity', 'Unknown'),
        alert.get('summary', 'No summary available'),
        actions_str,
        alert.get('timestamp', datetime.now().isoformat()),
        report_date
    ))
    
    conn.commit()
    conn.close()

def save_report_to_file(report_content: str, report_date: str = None) -> None:
    """Save report content to daily report file."""
    if not report_date:
        report_date = datetime.now().strftime('%Y-%m-%d')
    
    # Ensure reports directory exists
    os.makedirs('reports', exist_ok=True)
    
    # Create report filename
    report_filename = f'reports/daily_{report_date}.txt'
    
    # Append to or create report file
    with open(report_filename, 'a', encoding='utf-8') as f:
        f.write(f"\n=== {datetime.now().strftime('%H:%M:%S')} ===\n")
        f.write(report_content)
        f.write("\n\n")
    
    logging.info(f"Report saved to {report_filename}")

def process_alerts(alerts: list, features: dict, config: dict, args: argparse.Namespace, db_path: str) -> None:
    """Process alerts by saving summary/actions to alerts list, database, and writing reports."""
    logger = logging.getLogger(__name__)
    
    if not alerts:
        return
    
    # Store summary and actions in alerts
    for alert in alerts:
        if 'summary' not in alert:
            alert['summary'] = f"Alert: {alert.get('type', 'Unknown')} detected"
        if 'actions' not in alert:
            alert['actions'] = ["Monitor situation", "Review sentiment patterns"]
        
        # Save alert to database
        target_date = args.date if hasattr(args, 'date') and args.date else None
        save_alert_to_database(alert, db_path, target_date)
    
    # Create report content
    report_lines = []
    report_lines.append(f"MOOD SENTINEL ALERT REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 60)
    
    for i, alert in enumerate(alerts, 1):
        report_lines.append(f"\nAlert #{i}:")
        report_lines.append(f"Type: {alert.get('type', 'Unknown')}")
        report_lines.append(f"Severity: {alert.get('severity', 'Unknown')}")
        report_lines.append(f"Summary: {alert.get('summary', 'No summary available')}")
        report_lines.append(f"Timestamp: {alert.get('timestamp', datetime.now().isoformat())}")
        
        if 'actions' in alert:
            report_lines.append("Recommended Actions:")
            for action in alert['actions']:
                report_lines.append(f"  - {action}")
    
    report_lines.append(f"\nTotal Alerts: {len(alerts)}")
    report_lines.append(f"Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    report_content = "\n".join(report_lines)
    
    # Save to daily report file
    target_date = args.date if hasattr(args, 'date') and args.date else None
    save_report_to_file(report_content, target_date)
    
    logger.warning(f"Processed {len(alerts)} alerts, saved to database and daily report")

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Mood Sentinel - Social Media Mood Monitor')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--date', help='Target date for report (YYYY-MM-DD format)')
    parser.add_argument('--weekly', action='store_true', help='Generate weekly report')
    parser.add_argument('--no-telegram', action='store_true', help='Disable Telegram notifications')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    setup_logging(config)
    
    # Setup database
    db_path = setup_database(config)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Mood Sentinel...")
    
    # Handle command line arguments
    if args.no_telegram:
        logger.info("Telegram notifications disabled")
        if 'notifications' not in config:
            config['notifications'] = {}
        config['notifications']['telegram_enabled'] = False
    
    if args.weekly:
        logger.info("Weekly report mode enabled")
    
    if args.date:
        logger.info(f"Target date set to: {args.date}")
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    try:
        # Initialize components
        extractor = DataExtractor(config)
        feature_extractor = FeatureExtractor(config)
        rule_engine = RuleEngine(config)
        report_generator = ReportGenerator(config)
        notification_service = NotificationService(config)
        
        # Main processing loop
        while True:
            logger.info("Starting data processing cycle...")
            
            # Extract data from sources
            raw_data = extractor.extract_all()
            logger.info(f"Extracted {len(raw_data)} records")
            
            if raw_data:
                # Extract features
                features = feature_extractor.process(raw_data)
                
                # Apply rules and detect issues
                alerts = rule_engine.evaluate(features)
                
                if alerts:
                    logger.warning(f"Generated {len(alerts)} alerts")
                    
                    # Process alerts (save summary/actions, database, and write reports)
                    process_alerts(alerts, features, config, args, db_path)
                    
                    # Generate reports
                    report = report_generator.create_alert_report(alerts, features)
                    
                    # Send notifications (unless disabled)
                    if not args.no_telegram:
                        notification_service.send_alerts(alerts, report)
                    else:
                        logger.info("Telegram notifications skipped (--no-telegram flag)")
                
                # Generate periodic reports
                if should_generate_report(config, args):
                    periodic_report = report_generator.create_periodic_report(features)
                    save_report_to_file(periodic_report, args.date if hasattr(args, 'date') else None)
                    
                    if not args.no_telegram:
                        notification_service.send_report(periodic_report)
            
            if args.once:
                break
                
            # Wait for next cycle
            import time
            interval = config.get('monitoring', {}).get('interval_minutes', 15) * 60
            logger.info(f"Waiting {interval} seconds until next cycle...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Mood Sentinel stopped")

def should_generate_report(config: dict, args: argparse.Namespace = None) -> bool:
    """Determine if periodic report should be generated."""
    # If weekly mode is enabled, generate report on specific conditions
    if args and args.weekly:
        now = datetime.now()
        return now.weekday() == 0 and now.hour == 9  # Monday at 9 AM
    
    # Simple logic: generate report every hour
    now = datetime.now()
    return now.minute == 0

if __name__ == "__main__":
    main()
