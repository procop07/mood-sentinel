#!/usr/bin/env python3
"""
Database-backed notification system for Mood Sentinel

This module provides functions to send alerts from the database
and mark them as delivered to prevent duplicate notifications.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Import notification service from existing notify.py
try:
    from notify import NotificationService
except ImportError:
    # Fallback if notify.py is not available
    print("Warning: notify.py not available, notifications will be disabled")
    NotificationService = None


class DatabaseNotificationService:
    """Service for database-backed notifications with delivery tracking."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the database notification service."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Database configuration
        self.db_url = os.getenv(
            "DATABASE_URL", 
            "sqlite:///mood_sentinel.db"
        )
        
        # Initialize database connection
        self.engine = None
        self.Session = None
        
        if SQLALCHEMY_AVAILABLE:
            try:
                self.engine = create_engine(self.db_url)
                self.Session = sessionmaker(bind=self.engine)
                self.logger.info("Database connection initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize database: {e}")
                self.engine = None
                self.Session = None
        else:
            self.logger.warning(
                "SQLAlchemy not available, database operations will be disabled"
            )
        
        # Initialize notification service
        self.notification_service = None
        if NotificationService:
            try:
                self.notification_service = NotificationService(self.config)
            except Exception as e:
                self.logger.error(f"Failed to initialize notification service: {e}")
    
    def get_undelivered_alerts(self, since_hours: int = 24) -> List[Dict[str, Any]]:
        """Fetch undelivered alerts from the database."""
        if not self.Session:
            self.logger.warning("Database not available, returning empty alerts")
            return []
        
        try:
            session = self.Session()
            
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=since_hours)
            
            # Query for undelivered alerts
            query = text("""
                SELECT 
                    a.id,
                    a.alert_type,
                    a.message,
                    a.urgency,
                    a.created_at,
                    a.metadata,
                    an.anomaly_type,
                    an.severity,
                    an.description
                FROM alerts a
                JOIN anomalies an ON a.anomaly_id = an.id
                WHERE a.delivery_status = 'pending'
                    AND a.created_at >= :cutoff_time
                ORDER BY a.urgency DESC, a.created_at ASC
            """)
            
            result = session.execute(query, {"cutoff_time": cutoff_time})
            
            alerts = []
            for row in result:
                alert_data = {
                    "id": row.id,
                    "type": row.alert_type,
                    "message": row.message,
                    "urgency": row.urgency,
                    "timestamp": row.created_at.isoformat() if row.created_at else None,
                    "severity": row.severity,
                    "anomaly_type": row.anomaly_type,
                    "description": row.description,
                    "metadata": row.metadata
                }
                
                # Add summary combining message and description
                alert_data["summary"] = row.message
                if row.description and row.description != row.message:
                    alert_data["summary"] += f" - {row.description}"
                
                alerts.append(alert_data)
            
            session.close()
            self.logger.info(f"Retrieved {len(alerts)} undelivered alerts")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error fetching undelivered alerts: {e}")
            return []
    
    def mark_alerts_as_delivered(self, alert_ids: List[int], 
                                 delivery_channel: str = "telegram") -> bool:
        """Mark alerts as delivered in the database."""
        if not self.Session or not alert_ids:
            return False
        
        try:
            session = self.Session()
            
            # Update delivery status
            query = text("""
                UPDATE alerts 
                SET delivery_status = 'delivered',
                    sent_at = :sent_at,
                    delivery_channel = :delivery_channel
                WHERE id IN :alert_ids
            """)
            
            session.execute(query, {
                "sent_at": datetime.now(),
                "delivery_channel": delivery_channel,
                "alert_ids": tuple(alert_ids)
            })
            
            session.commit()
            session.close()
            
            self.logger.info(f"Marked {len(alert_ids)} alerts as delivered")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking alerts as delivered: {e}")
            return False
    
    def send_alerts_from_db(self, since_hours: int = 24) -> Dict[str, Any]:
        """Send undelivered alerts from database and mark them as delivered."""
        try:
            # Get undelivered alerts
            alerts = self.get_undelivered_alerts(since_hours)
            
            if not alerts:
                self.logger.info("No undelivered alerts found")
                return {
                    "success": True,
                    "alerts_sent": 0,
                    "message": "No alerts to send"
                }
            
            # Send alerts using notification service
            if not self.notification_service:
                self.logger.warning("Notification service not available")
                return {
                    "success": False,
                    "alerts_sent": 0,
                    "message": "Notification service not available"
                }
            
            # Attempt to send alerts
            send_success = self.notification_service.send_alerts(alerts)
            
            if send_success:
                # Mark alerts as delivered
                alert_ids = [alert["id"] for alert in alerts]
                mark_success = self.mark_alerts_as_delivered(alert_ids)
                
                if mark_success:
                    return {
                        "success": True,
                        "alerts_sent": len(alerts),
                        "message": f"Successfully sent and marked {len(alerts)} alerts"
                    }
                else:
                    return {
                        "success": False,
                        "alerts_sent": len(alerts),
                        "message": "Alerts sent but failed to mark as delivered"
                    }
            else:
                return {
                    "success": False,
                    "alerts_sent": 0,
                    "message": "Failed to send alerts"
                }
                
        except Exception as e:
            self.logger.error(f"Error in send_alerts_from_db: {e}")
            return {
                "success": False,
                "alerts_sent": 0,
                "message": f"Error: {str(e)}"
            }
    
    def get_alert_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get statistics about alerts from the database."""
        if not self.Session:
            return {}
        
        try:
            session = self.Session()
            
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # Query for alert statistics
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(CASE WHEN delivery_status = 'delivered' THEN 1 END) as delivered_alerts,
                    COUNT(CASE WHEN delivery_status = 'pending' THEN 1 END) as pending_alerts,
                    COUNT(CASE WHEN urgency = 'high' THEN 1 END) as high_urgency,
                    COUNT(CASE WHEN urgency = 'medium' THEN 1 END) as medium_urgency,
                    COUNT(CASE WHEN urgency = 'low' THEN 1 END) as low_urgency
                FROM alerts
                WHERE created_at >= :cutoff_time
            """)
            
            result = session.execute(stats_query, {"cutoff_time": cutoff_time})
            row = result.fetchone()
            
            statistics = {
                "period_days": days,
                "total_alerts": row.total_alerts or 0,
                "delivered_alerts": row.delivered_alerts or 0,
                "pending_alerts": row.pending_alerts or 0,
                "urgency_breakdown": {
                    "high": row.high_urgency or 0,
                    "medium": row.medium_urgency or 0,
                    "low": row.low_urgency or 0
                },
                "delivery_rate": (
                    (row.delivered_alerts / row.total_alerts * 100) 
                    if row.total_alerts > 0 else 0
                )
            }
            
            session.close()
            return statistics
            
        except Exception as e:
            self.logger.error(f"Error getting alert statistics: {e}")
            return {}


def send_alerts_from_db(since_hours: int = 24) -> Dict[str, Any]:
    """Convenience function to send alerts from database.
    
    Args:
        since_hours: Number of hours back to look for undelivered alerts
    
    Returns:
        Dict containing success status, number of alerts sent, and message
    """
    service = DatabaseNotificationService()
    return service.send_alerts_from_db(since_hours)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Send database alerts via notification system'
    )
    parser.add_argument(
        '--since-hours', 
        type=int, 
        default=24,
        help='Hours back to look for undelivered alerts (default: 24)'
    )
    parser.add_argument(
        '--stats', 
        action='store_true',
        help='Show alert statistics instead of sending alerts'
    )
    parser.add_argument(
        '--stats-days',
        type=int,
        default=7,
        help='Days back for statistics (default: 7)'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    service = DatabaseNotificationService()
    
    if args.stats:
        # Show statistics
        stats = service.get_alert_statistics(args.stats_days)
        print("\nAlert Statistics:")
        print(f"Period: {stats.get('period_days', 0)} days")
        print(f"Total alerts: {stats.get('total_alerts', 0)}")
        print(f"Delivered alerts: {stats.get('delivered_alerts', 0)}")
        print(f"Pending alerts: {stats.get('pending_alerts', 0)}")
        print(f"Delivery rate: {stats.get('delivery_rate', 0):.1f}%")
        
        urgency_breakdown = stats.get('urgency_breakdown', {})
        print(f"High urgency: {urgency_breakdown.get('high', 0)}")
        print(f"Medium urgency: {urgency_breakdown.get('medium', 0)}")
        print(f"Low urgency: {urgency_breakdown.get('low', 0)}")
    else:
        # Send alerts
        result = service.send_alerts_from_db(args.since_hours)
        
        print(f"\nResult: {result['message']}")
        print(f"Alerts sent: {result['alerts_sent']}")
        print(f"Success: {result['success']}")


if __name__ == "__main__":
    main()
