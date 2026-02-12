"""
Background Agent Discovery - Runs automatically on Railway
Discovers and deploys agents every hour without manual intervention
"""

import os
import sys
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cron_discovery import AutomatedCrawler
from backend.database.base import SessionLocal

logger = logging.getLogger(__name__)

# Scheduler instance
scheduler = BackgroundScheduler()


def run_discovery_job():
    """Background job that runs hourly"""
    try:
        logger.info("[DISCOVERY] Starting automated agent discovery...")
        
        crawler = AutomatedCrawler()
        count = crawler.run()
        
        logger.info(f"[DISCOVERY] Completed: {count} new agents deployed")
        return count
    
    except Exception as e:
        logger.error(f"[DISCOVERY] Error during automated discovery: {e}")
        return 0


def seed_initial_agents():
    """One-time seed on first startup"""
    try:
        # Check if agents already exist
        from backend.models.agent import Agent
        db = SessionLocal()
        
        existing_count = db.query(Agent).count()
        db.close()
        
        if existing_count > 0:
            logger.info(f"[SEED] Agents already exist ({existing_count}), skipping seed")
            return existing_count
        
        logger.info("[SEED] No agents found, running initial discovery...")
        
        # Run initial discovery
        count = run_discovery_job()
        
        logger.info(f"[SEED] Initial seed complete: {count} agents deployed")
        return count
    
    except Exception as e:
        logger.error(f"[SEED] Error during initial seed: {e}")
        return 0


def start_scheduler():
    """Start background scheduler"""
    if not scheduler.running:
        # Add hourly discovery job
        scheduler.add_job(
            func=run_discovery_job,
            trigger="interval",
            hours=1,
            id="agent_discovery",
            name="Automated Agent Discovery",
            max_instances=1,  # Prevent overlapping runs
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("[SCHEDULER] Background agent discovery started (runs every hour)")
    
    return scheduler


def stop_scheduler():
    """Stop background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[SCHEDULER] Background agent discovery stopped")
