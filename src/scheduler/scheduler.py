import logging
import signal
import sys
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from config.settings import (
    SCHEDULE_INTERVAL_HOURS, SCHEDULER_TIMEZONE, 
    DB_CLEANUP_INTERVAL_HOURS, DATA_RETENTION_DAYS,
    LOG_FILE, LOG_LEVEL, ENABLE_SCHEDULER,
    NOTIFICATION_EMAIL
)
from src.database import db

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger("ping_bot.scheduler")


class PingBotScheduler:
    """Background job scheduler for Ping Bot"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE)
        self.is_running = False
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle graceful shutdown on interrupt"""
        logger.info(f"[Scheduler] Received signal {sig}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("[Scheduler] Already running")
            return
        
        if not ENABLE_SCHEDULER:
            logger.warning("[Scheduler] Disabled via config. Run manually only.")
            return
        
        logger.info(f"[Scheduler] Starting with {SCHEDULE_INTERVAL_HOURS}h interval...")
        
        # Add main job - run Pritam monitoring
        self.scheduler.add_job(
            _run_pritam_monitoring,
            trigger='interval',
            hours=SCHEDULE_INTERVAL_HOURS,
            id="pritam_monitoring",
            name="Pritam News Monitoring",
            replace_existing=True,
            next_run_time=datetime.now()  # Run immediately on start
        )
        
        # Add cleanup job - run database cleanup
        self.scheduler.add_job(
            _run_database_cleanup,
            trigger='interval',
            hours=DB_CLEANUP_INTERVAL_HOURS,
            id="database_cleanup",
            name="Database Cleanup",
            replace_existing=True,
            next_run_time=datetime.now()
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("[Scheduler] Started successfully")
    
    def stop(self):
        """Stop the background scheduler"""
        if not self.is_running:
            logger.warning("[Scheduler] Not running")
            return
        
        logger.info("[Scheduler] Stopping...")
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("[Scheduler] Stopped successfully")
    
    def pause(self):
        """Pause all scheduled jobs"""
        if self.is_running:
            self.scheduler.pause()
            logger.info("[Scheduler] Paused")
    
    def resume(self):
        """Resume all scheduled jobs"""
        if self.is_running:
            self.scheduler.resume()
            logger.info("[Scheduler] Resumed")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def print_schedule(self):
        """Print current scheduled jobs"""
        jobs = self.get_jobs()
        if not jobs:
            logger.info("[Scheduler] No jobs scheduled")
            return
        
        logger.info("[Scheduler] Current jobs:")
        for job in jobs:
            logger.info(f"  - {job.name} (id: {job.id}, next run: {job.next_run_time})")


def _run_pritam_monitoring():
    """Job: Run main monitoring task"""
    logger.info("="*70)
    logger.info("[Job] Starting Pritam News Monitoring...")
    
    try:
        # Import here to avoid circular imports
        from main import application_init
        
        result = application_init()
        logger.info(f"[Job] Monitoring completed: {result}")
        
        # Log database stats
        stats = db.get_run_stats(hours=201)
        logger.info(f"[Job] Stats (24h): {stats}")
        
    except Exception as e:
        logger.error(f"[Job] Monitoring failed: {str(e)}", exc_info=True)
        db.log_run(status="error", error_message=str(e))
    
    logger.info("="*70)


def _run_database_cleanup():
    """Job: Run database cleanup"""
    logger.info("[Job] Starting database cleanup...")
    
    try:
        deleted = db.cleanup_old_data(days=DATA_RETENTION_DAYS)
        logger.info(f"[Job] Cleanup completed, deleted {deleted} records")
        
    except Exception as e:
        logger.error(f"[Job] Cleanup failed: {str(e)}", exc_info=True)


# Global scheduler instance
scheduler = PingBotScheduler()
