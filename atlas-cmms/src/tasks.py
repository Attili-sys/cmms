"""Background work — periodic jobs runner and background scheduler."""

import logging
import threading
from sqlalchemy.orm import Session

from ajnkit.db import session as get_platform_session
from src import envs
from src.jobs.cleanup import cleanup_expired_tokens
from src.jobs.downtime_notifier import notify_ongoing_downtimes
from src.jobs.pm_generator import generate_due_work_orders
from src.jobs.preventive_maintenance_notifier import notify_upcoming_preventive_maintenance

logger = logging.getLogger(__name__)

_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()


def run_periodic_jobs_once(db: Session) -> dict:
    """Run all periodic maintenance and background tasks once using the given db session."""
    logger.info("Starting periodic background jobs run")
    pm_wos = generate_due_work_orders(db)
    pm_notifs = notify_upcoming_preventive_maintenance(db)
    downtime_alerts = notify_ongoing_downtimes(db)
    cleanup_res = cleanup_expired_tokens(db)

    results = {
        "work_orders_generated": len(pm_wos),
        "pm_notifications": pm_notifs,
        "downtime_notifications": downtime_alerts,
        "cleanup": cleanup_res,
    }
    logger.info("Periodic jobs completed: %s", results)
    return results


def start_background_scheduler(poll_interval: int = 60) -> threading.Thread | None:
    """Start the periodic background job scheduler loop if DATABASE_URL is set."""
    global _scheduler_thread
    if not envs.DATABASE_URL:
        logger.info("DATABASE_URL is not set; background scheduler will not start.")
        return None

    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        logger.warning("Background scheduler is already running.")
        return _scheduler_thread

    _stop_event.clear()

    def _loop() -> None:
        logger.info("Background scheduler thread started (interval=%ds)", poll_interval)
        while not _stop_event.is_set():
            try:
                gen = get_platform_session()
                db = next(gen)
                try:
                    run_periodic_jobs_once(db)
                finally:
                    gen.close()
            except Exception as e:
                logger.error("Error running periodic background jobs: %s", e, exc_info=True)
            _stop_event.wait(timeout=poll_interval)
        logger.info("Background scheduler thread stopped.")

    _scheduler_thread = threading.Thread(target=_loop, name="BackgroundScheduler", daemon=True)
    _scheduler_thread.start()
    return _scheduler_thread


def stop_background_scheduler() -> None:
    """Signal background scheduler to stop and wait for completion."""
    global _scheduler_thread
    _stop_event.set()
    if _scheduler_thread and _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=5)
        _scheduler_thread = None
