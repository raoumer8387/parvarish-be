"""Parent routes for lacking analysis and task generation.

These routes are for parent users to:
1. View their children's lacking analysis
2. Get notifications/tickers about areas needing attention
3. Get Islamic guidance from chatbot
4. Generate and assign tasks based on lacking areas
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
import json
import logging

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.parent import Parent
from app.db.models.child import Child
from app.db.models.child_task import ChildTask
from app.schemas.lacking_schemas import (
    LackingAnalysisResponse,
    TickerNotification,
    NotificationListResponse,
    LackingGuidanceRequest,
    LackingGuidanceResponse,
    GenerateTasksRequest,
    GenerateTasksResponse,
    GeneratedTask,
    MarkNotificationReadRequest,
    AllChildrenLackingResponse,
    ChildLackingSummary
)
from app.services.lacking_analyzer import (
    get_child_lacking_analysis,
    should_generate_ticker,
    resolve_lacking_area_info,
)
from app.services.llm_task_generator import (
    generate_lacking_guidance,
    generate_islamic_tasks
)
from app.services.parent_realtime import (
    mark_parent_notification_read,
    schedule_lacking_alert_realtime,
)
from app.services.unified_behavior import refresh_and_notify_dashboard

router = APIRouter(prefix="/parent/lacking", tags=["parent-lacking-analysis"])
logger = logging.getLogger(__name__)

# In-memory notification store (in production, use database table)
_notifications_store: List[dict] = []


def _assert_parent_user(user: User) -> Parent:
    """Ensure the authenticated user is a parent."""
    if user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    return user


def _assert_parent_owns_child(db: Session, parent: Parent, child_id: int) -> Child:
    """Ensure the parent owns the child."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    if child.parent_id != parent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this child's data"
        )
    
    return child


@router.get("/analyze/all", response_model=AllChildrenLackingResponse)
def analyze_all_children_lacking(
    days: int = 7,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Analyze lacking areas for all parent's children.
    
    This provides a summary view of all children's lacking areas.
    
    Args:
        days: Number of days to analyze (default: 7)
    """
    
    parent = _assert_parent_user(user)
    
    # Get all parent's children
    children = db.query(Child).filter(Child.parent_id == parent.id).all()
    if not children:
        return AllChildrenLackingResponse(
            total_children=0,
            children_with_lackings=0,
            children=[],
            analyzed_at=datetime.utcnow().isoformat()
        )
    
    children_summaries = []
    children_with_lackings = 0
    
    for child in children:
        try:
            analysis = get_child_lacking_analysis(db, child.id, days)
            
            if analysis["lacking_areas"]:
                children_with_lackings += 1
            
            summary = ChildLackingSummary(
                child_id=child.id,
                child_name=child.name,
                child_age=child.age,
                total_lackings=len(analysis["lacking_areas"]),
                lacking_areas=analysis["lacking_areas"],
                requires_attention=analysis["requires_attention"],
                last_analyzed=analysis["analyzed_at"]
            )
            children_summaries.append(summary)
            
            # Generate notifications for new lacking areas
            for lacking in analysis["lacking_areas"]:
                if should_generate_ticker(db, child.id, lacking["area"]):
                    _create_notification(child, lacking, analysis)
        
        except Exception as e:
            logger.warning(f"Could not analyze child {child.id}: {e}")
            # Add empty summary for children with no data
            children_summaries.append(ChildLackingSummary(
                child_id=child.id,
                child_name=child.name,
                child_age=child.age,
                total_lackings=0,
                lacking_areas=[],
                requires_attention=False,
                last_analyzed=datetime.utcnow().isoformat()
            ))
    
    return AllChildrenLackingResponse(
        total_children=len(children),
        children_with_lackings=children_with_lackings,
        children=children_summaries,
        analyzed_at=datetime.utcnow().isoformat()
    )


@router.get("/analyze/{child_id}", response_model=LackingAnalysisResponse)
def analyze_child_lacking(
    child_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Analyze child's lacking areas based on recent game performance.
    
    This endpoint analyzes:
    - Memory game → Presence of Mind
    - Mood picker → Mood Identification
    - Islamic quiz → Learning Capability
    - Scenario game → Behavior Identification
    
    Args:
        child_id: Child's ID
        days: Number of days to analyze (default: 7)
    """
    parent = _assert_parent_user(user)
    child = _assert_parent_owns_child(db, parent, child_id)
    
    try:
        analysis = get_child_lacking_analysis(db, child_id, days)
        
        # Generate notifications for new lacking areas
        for lacking in analysis["lacking_areas"]:
            if should_generate_ticker(db, child_id, lacking["area"]):
                _create_notification(child, lacking, analysis)
        
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing child lacking: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error analyzing child performance"
        )


@router.get("/notifications", response_model=NotificationListResponse)
def get_notifications(
    child_id: int = None,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get all lacking notifications for parent's children.
    
    Args:
        child_id: Filter by specific child (optional)
        unread_only: Only show unread notifications
    """
    parent = _assert_parent_user(user)
    
    # Filter notifications for this parent's children
    parent_child_ids = [child.id for child in db.query(Child).filter(Child.parent_id == parent.id).all()]
    
    filtered_notifications = [
        n for n in _notifications_store
        if n["child_id"] in parent_child_ids
    ]
    
    if child_id:
        filtered_notifications = [
            n for n in filtered_notifications
            if n["child_id"] == child_id
        ]
    
    if unread_only:
        filtered_notifications = [
            n for n in filtered_notifications
            if not n.get("read", False)
        ]
    
    # Sort by priority and created_at
    filtered_notifications.sort(
        key=lambda x: (
            0 if x["priority"] == "high" else 1,
            x["created_at"]
        ),
        reverse=True
    )
    
    unread_count = len([n for n in filtered_notifications if not n.get("read", False)])
    
    return {
        "notifications": filtered_notifications,
        "total_count": len(filtered_notifications),
        "unread_count": unread_count
    }


@router.post("/notifications/mark-read")
def mark_notification_read(
    request: MarkNotificationReadRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    parent = _assert_parent_user(user)
    
    # Find and update notification
    for notification in _notifications_store:
        if notification["id"] == request.notification_id:
            # Verify parent owns this child
            parent_child_ids = [child.id for child in db.query(Child).filter(Child.parent_id == parent.id).all()]
            if notification["child_id"] not in parent_child_ids:
                raise HTTPException(status_code=403, detail="Access denied")
            
            notification["read"] = True
            mark_parent_notification_read(parent.id, request.notification_id)
            return {"success": True, "message": "Notification marked as read"}
    
    raise HTTPException(status_code=404, detail="Notification not found")


@router.post("/guidance", response_model=LackingGuidanceResponse)
def get_lacking_guidance(
    request: LackingGuidanceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get Islamic guidance from chatbot on how to tackle child's lacking area.
    
    This uses LLM with RAG (Islamic references) to provide personalized guidance.
    """
    parent = _assert_parent_user(user)
    child = _assert_parent_owns_child(db, parent, request.child_id)
    
    try:
        try:
            lacking_info = resolve_lacking_area_info(
                db, request.child_id, request.lacking_area, days=7
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        guidance = generate_lacking_guidance(
            lacking_area=lacking_info["area"],
            score=lacking_info["score"],
            child_name=child.name,
            child_age=child.age
        )
        
        return {
            "child_id": child.id,
            "child_name": child.name,
            "lacking_area": lacking_info["area"],
            "lacking_label": lacking_info["label"],
            "score": lacking_info["score"],
            "guidance": guidance,
            "islamic_references_used": True,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating guidance: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error generating guidance"
        )


@router.post("/generate-tasks", response_model=GenerateTasksResponse)
def generate_tasks_for_lacking(
    request: GenerateTasksRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Generate Islamic-oriented tasks based on child's lacking area.
    
    This uses LLM with Islamic references to create personalized tasks.
    The tasks are automatically saved and assigned to the child.
    """
    parent = _assert_parent_user(user)
    child = _assert_parent_owns_child(db, parent, request.child_id)
    
    try:
        try:
            lacking_info = resolve_lacking_area_info(
                db, request.child_id, request.lacking_area, days=7
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        tasks = generate_islamic_tasks(
            db=db,
            child_id=request.child_id,
            lacking_area=lacking_info["area"],
            score=lacking_info["score"],
            child_age=child.age
        )
        
        if not tasks:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate tasks"
            )
        
        # Save tasks to database
        saved_tasks = []
        for task_data in tasks[:request.num_tasks]:
            task = ChildTask(
                child_id=request.child_id,
                title=task_data["title"],
                description=task_data["description"],
                category=task_data["category"],
                difficulty=task_data["difficulty"],
                xp_reward=task_data["xp_reward"],
                status="pending",
                source="lacking_analysis",
                meta={
                    "lacking_area": lacking_info["area"],
                    "islamic_reference": task_data.get("islamic_reference", ""),
                    "generated_by": "llm",
                    "parent_id": parent.id
                }
            )
            db.add(task)
            saved_tasks.append(task_data)
        
        db.commit()
        refresh_and_notify_dashboard(db, request.child_id, trigger_source="lacking_analysis")
        
        return {
            "child_id": request.child_id,
            "child_name": child.name,
            "lacking_area": lacking_info["area"],
            "tasks": [GeneratedTask(**t) for t in saved_tasks],
            "tasks_saved": True,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating tasks: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error generating tasks"
        )


def _create_notification(child: Child, lacking: dict, analysis: dict) -> None:
    """Create a notification ticker for a lacking area."""
    notification = {
        "id": str(uuid.uuid4()),
        "child_id": child.id,
        "child_name": child.name,
        "lacking_area": lacking["area"],
        "lacking_label": lacking["label"],
        "score": lacking["score"],
        "priority": lacking["priority"],
        "message": _get_notification_message(lacking),
        "action_required": True,
        "created_at": datetime.utcnow().isoformat(),
        "read": False
    }
    
    _notifications_store.append(notification)
    logger.info(f"Created notification for child {child.id}, lacking: {lacking['area']}")
    schedule_lacking_alert_realtime(child, notification)


def _get_notification_message(lacking: dict) -> str:
    """Generate notification message based on lacking area."""
    messages = {
        "presence_of_mind": f"⚠️ {lacking['label']}: {lacking['score']:.0f}/100 - Focus aur attention pe kaam karein",
        "mood_identification": f"⚠️ {lacking['label']}: {lacking['score']:.0f}/100 - Emotional awareness improve karna hai",
        "learning_capability": f"⚠️ {lacking['label']}: {lacking['score']:.0f}/100 - Islamic learning ko mazeed asan banayein",
        "behavior_identification": f"⚠️ {lacking['label']}: {lacking['score']:.0f}/100 - Moral decision-making pe dhyan dein"
    }
    
    return messages.get(
        lacking["area"],
        f"⚠️ {lacking['label']} needs attention - Score: {lacking['score']:.0f}/100"
    )
