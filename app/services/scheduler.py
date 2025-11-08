"""Background task scheduler for reminders and notifications.

Optional: Use APScheduler or run as a separate cron job.
For now, provides helper functions to check who needs reminders.
"""
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session

from app.db.models.child import Child
from app.db.models.parent import Parent
from app.db.models.user import User
from app.db.models.behavior_models import ChildBehaviorResponse


def get_parents_needing_reminders(
    db: Session,
    hours_threshold: int = 24
) -> List[Dict]:
    """Find parents whose children haven't been checked in for X hours.
    
    Returns list of dicts with parent info and children needing check-ins.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours_threshold)
    
    parents = db.query(Parent).all()
    results = []
    
    for parent in parents:
        children_needing_checkin = []
        
        for child in db.query(Child).filter(Child.parent_id == parent.id).all():
            last_response = (
                db.query(ChildBehaviorResponse)
                .filter(ChildBehaviorResponse.child_id == child.id)
                .order_by(ChildBehaviorResponse.timestamp.desc())
                .first()
            )
            
            needs_reminder = False
            if not last_response:
                needs_reminder = True  # Never answered
            elif last_response.timestamp < cutoff:
                needs_reminder = True  # Too long ago
            
            if needs_reminder:
                children_needing_checkin.append({
                    "child_id": child.id,
                    "child_name": child.name,
                    "last_check_in": last_response.timestamp.isoformat() if last_response else None
                })
        
        if children_needing_checkin:
            user = db.query(User).filter(User.id == parent.id).first()
            results.append({
                "parent_id": parent.id,
                "parent_email": user.email if user else None,
                "parent_name": user.name if user else None,
                "children": children_needing_checkin
            })
    
    return results


def send_reminder_notification(parent_email: str, parent_name: str, children: List[Dict]):
    """Send reminder email/notification to parent.
    
    TODO: Integrate with email service (SendGrid, AWS SES, etc.)
    For now, just logs the reminder.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    child_names = ", ".join([c["child_name"] for c in children])
    logger.info(
        f"REMINDER: {parent_name} ({parent_email}) needs to check in for: {child_names}"
    )
    
    # Future: Send actual email/push notification
    # Example:
    # send_email(
    #     to=parent_email,
    #     subject="Daily Check-in Reminder - Parvarish AI",
    #     body=f"Assalamu Alaikum {parent_name},\n\n"
    #          f"Please complete today's behavior check-in for: {child_names}\n\n"
    #          f"Visit: https://yourapp.com/check-in"
    # )


def run_daily_reminders(db: Session):
    """Main task to check and send reminders.
    
    Can be called by:
    1. APScheduler (runs in-process)
    2. Cron job (separate script)
    3. Cloud scheduler (AWS EventBridge, Google Cloud Scheduler)
    """
    parents = get_parents_needing_reminders(db, hours_threshold=24)
    
    for parent_info in parents:
        send_reminder_notification(
            parent_email=parent_info["parent_email"],
            parent_name=parent_info["parent_name"],
            children=parent_info["children"]
        )
    
    return {
        "reminders_sent": len(parents),
        "timestamp": datetime.utcnow().isoformat()
    }


# Optional: APScheduler integration (uncomment to enable)
# from apscheduler.schedulers.background import BackgroundScheduler
# from app.db.session import SessionLocal
# 
# scheduler = BackgroundScheduler()
# 
# def scheduled_reminder_job():
#     db = SessionLocal()
#     try:
#         run_daily_reminders(db)
#     finally:
#         db.close()
# 
# def start_scheduler():
#     """Start background scheduler. Call from main.py on app startup."""
#     # Run daily at 9 AM
#     scheduler.add_job(scheduled_reminder_job, 'cron', hour=9, minute=0)
#     scheduler.start()
