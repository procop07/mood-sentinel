#!/usr/bin/env python3
"""
BioPulse Guardian Scheduler
Handles scheduled tasks for data synchronization and processing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from etl_pipeline import ETLPipeline

class BioPulseScheduler:
    """
    Scheduler for BioPulse Guardian data processing tasks
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.scheduler = AsyncIOScheduler()
        self.etl_pipeline = ETLPipeline(config)
        self.running = False
        
    async def sync_health_data(self, sources: Optional[list] = None):
        """
        Synchronize health data from all configured sources
        
        Args:
            sources: Optional list of specific sources to sync
        """
        if sources is None:
            sources = self.config.get('data_sources', ['zepp', 'fitbit'])
            
        self.logger.info(f"Starting scheduled health data sync for sources: {sources}")
        
        try:
            results = await self.etl_pipeline.run_pipeline(sources)
            
            success_count = sum(1 for status in results.values() if status)
            total_count = len(results)
            
            self.logger.info(
                f"Health data sync completed: {success_count}/{total_count} sources successful"
            )
            
            if success_count < total_count:
                failed_sources = [source for source, status in results.items() if not status]
                self.logger.warning(f"Failed to sync data from sources: {failed_sources}")
                
        except Exception as e:
            self.logger.error(f"Error during scheduled health data sync: {str(e)}")
            
    async def generate_daily_report(self):
        """
        Generate daily health and mood report
        """
        self.logger.info("Generating daily health report")
        
        try:
            # This would integrate with the reporting module
            # For now, just log the action
            today = datetime.now().strftime('%Y-%m-%d')
            self.logger.info(f"Daily report generated for {today}")
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {str(e)}")
            
    async def check_mood_alerts(self):
        """
        Check for mood-related alerts and notifications
        """
        self.logger.info("Checking mood alerts")
        
        try:
            # This would check for concerning patterns in mood data
            # and trigger notifications if needed
            # For now, just log the check
            self.logger.info("Mood alert check completed")
            
        except Exception as e:
            self.logger.error(f"Error checking mood alerts: {str(e)}")
            
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data beyond retention period
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        self.logger.info(f"Cleaning up data older than {days_to_keep} days")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            # This would execute database cleanup
            # For now, just log the action
            self.logger.info(f"Data cleanup completed for data before {cutoff_date.strftime('%Y-%m-%d')}")
            
        except Exception as e:
            self.logger.error(f"Error during data cleanup: {str(e)}")
            
    def setup_schedule(self):
        """
        Set up the job schedule based on configuration
        """
        # Data synchronization - every hour during waking hours
        self.scheduler.add_job(
            self.sync_health_data,
            trigger=CronTrigger(hour='6-23', minute=0),
            id='hourly_sync',
            name='Hourly Health Data Sync',
            max_instances=1,
            replace_existing=True
        )
        
        # Full data sync - every 6 hours
        self.scheduler.add_job(
            self.sync_health_data,
            trigger=IntervalTrigger(hours=6),
            id='full_sync',
            name='Full Health Data Sync',
            max_instances=1,
            replace_existing=True
        )
        
        # Daily report generation - at 8:00 AM
        self.scheduler.add_job(
            self.generate_daily_report,
            trigger=CronTrigger(hour=8, minute=0),
            id='daily_report',
            name='Daily Report Generation',
            max_instances=1,
            replace_existing=True
        )
        
        # Mood alerts check - every 2 hours during waking hours
        self.scheduler.add_job(
            self.check_mood_alerts,
            trigger=CronTrigger(hour='6-23/2', minute=15),
            id='mood_alerts',
            name='Mood Alerts Check',
            max_instances=1,
            replace_existing=True
        )
        
        # Data cleanup - weekly on Sunday at 2:00 AM
        self.scheduler.add_job(
            self.cleanup_old_data,
            trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='weekly_cleanup',
            name='Weekly Data Cleanup',
            max_instances=1,
            replace_existing=True
        )
        
        self.logger.info("Job schedule configured")
        
    async def start(self):
        """
        Start the scheduler
        """
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
            
        self.logger.info("Starting BioPulse Guardian scheduler")
        
        self.setup_schedule()
        self.scheduler.start()
        self.running = True
        
        self.logger.info("Scheduler started successfully")
        
    async def stop(self):
        """
        Stop the scheduler
        """
        if not self.running:
            self.logger.warning("Scheduler is not running")
            return
            
        self.logger.info("Stopping BioPulse Guardian scheduler")
        
        self.scheduler.shutdown(wait=True)
        self.running = False
        
        self.logger.info("Scheduler stopped")
        
    def get_job_status(self) -> Dict[str, Any]:
        """
        Get status of all scheduled jobs
        
        Returns:
            Dictionary with job status information
        """
        if not self.running:
            return {'status': 'stopped', 'jobs': []}
            
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
            
        return {
            'status': 'running',
            'jobs': jobs,
            'total_jobs': len(jobs)
        }
        
    async def run_job_now(self, job_id: str) -> bool:
        """
        Run a specific job immediately
        
        Args:
            job_id: ID of the job to run
            
        Returns:
            Success status
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                self.logger.error(f"Job {job_id} not found")
                return False
                
            self.logger.info(f"Running job {job_id} manually")
            job.modify(next_run_time=datetime.now())
            return True
            
        except Exception as e:
            self.logger.error(f"Error running job {job_id}: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    import asyncio
    
    config = {
        'database_url': 'sqlite:///mood_sentinel.db',
        'data_sources': ['zepp', 'fitbit', 'manual_entry'],
        'zepp_api_key': 'your_zepp_api_key',
        'fitbit_client_id': 'your_fitbit_client_id',
    }
    
    async def main():
        scheduler = BioPulseScheduler(config)
        
        try:
            # Start the scheduler
            await scheduler.start()
            
            # Keep running
            while True:
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            print("Shutting down scheduler...")
            await scheduler.stop()
    
    asyncio.run(main())
