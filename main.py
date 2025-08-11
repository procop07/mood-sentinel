#!/usr/bin/env python3
"""
Mood Sentinel - Main Application Entry Point

A social media mood monitoring system that tracks sentiment
and alerts on concerning patterns.
"""

import sys
import logging
import argparse
from datetime import datetime

import yaml

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


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Mood Sentinel - Social Media Mood Monitor')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Mood Sentinel...")
    
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
                    
                    # Generate reports
                    report = report_generator.create_alert_report(alerts, features)
                    
                    # Send notifications
                    notification_service.send_alerts(alerts, report)
                
                # Generate periodic reports
                if should_generate_report(config):
                    periodic_report = report_generator.create_periodic_report(features)
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


def should_generate_report(config: dict) -> bool:
    """Determine if periodic report should be generated."""
    # Simple logic: generate report every hour
    now = datetime.now()
    return now.minute == 0


if __name__ == "__main__":
    main()
