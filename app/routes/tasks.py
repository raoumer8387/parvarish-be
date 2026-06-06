"""API routes for generating child tasks from chatbot responses."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.models.child import Child
from app.schemas.task import TaskFromChatRequest, TasksFromChatResponse, ChildTaskOut, ChildTaskListResponse, TaskCompleteResponse, TaskFromScoresRequest, UpdateTaskStatusRequest
from app.services.task_service import generate_tasks_from_chat, list_child_tasks, mark_task_completed, generate_tasks_from_scores, update_task_status
from app.services.unified_behavior import refresh_and_notify_dashboard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/from-chat", response_model=TasksFromChatResponse, status_code=status.HTTP_201_CREATED)
def create_tasks_from_chat(
    request: TaskFromChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate tasks for a child based on chatbot response and recent behavior performance."""
    # Auth: parent only & owns child
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can generate tasks.")

    child = db.query(Child).filter(Child.id == request.child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Child {request.child_id} not found")
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this child")

    result = generate_tasks_from_chat(
        db=db,
        child_id=request.child_id,
        chatbot_response=request.chatbot_response,
        chatbot_tags=request.chatbot_tags,
    )
    refresh_and_notify_dashboard(db, request.child_id, trigger_source="task")

    # Use Pydantic model validation; attribute meta already compatible
    return TasksFromChatResponse(
        count=result["count"],
        tasks=[ChildTaskOut.model_validate(t) for t in result["tasks"]],
        categories_considered=result["categories_considered"],
        categories_low_score=result["categories_low_score"],
        keywords_detected=result["keywords_detected"],
    )


@router.post("/from-scores", response_model=TasksFromChatResponse, status_code=status.HTTP_201_CREATED)
def create_tasks_from_scores(
    request: TaskFromScoresRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate tasks purely from child's recent low behavior categories (no chatbot required)."""
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can generate tasks.")

    child = db.query(Child).filter(Child.id == request.child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Child {request.child_id} not found")
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this child")

    result = generate_tasks_from_scores(
        db=db,
        child_id=request.child_id,
        days=request.days,
        max_tasks=request.max_tasks,
    )
    refresh_and_notify_dashboard(db, request.child_id, trigger_source="task")

    return TasksFromChatResponse(
        count=result["count"],
        tasks=[ChildTaskOut.model_validate(t) for t in result["tasks"]],
        categories_considered=result["categories_considered"],
        categories_low_score=result["categories_low_score"],
        keywords_detected=result["keywords_detected"],
    )


@router.get("/child/{child_id}", response_model=ChildTaskListResponse)
def get_child_tasks(
    child_id: int,
    task_status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent tasks for a child (for dashboard)."""
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can view tasks.")
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Child {child_id} not found")
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this child")

    tasks = list_child_tasks(db, child_id=child_id, status=task_status, limit=limit)
    return ChildTaskListResponse(
        child_id=child_id,
        child_name=child.name,
        total=len(tasks),
        tasks=[ChildTaskOut(**t) for t in tasks],
    )


@router.get("/all", response_model=ChildTaskListResponse)
def get_all_parent_tasks(
    child_id: int | None = None,
    task_status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tasks for all parent's children or filter by specific child_id."""
    from app.db.models.child_task import ChildTask
    
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can view tasks.")
    
    # Get all parent's children
    children = db.query(Child).filter(Child.parent_id == current_user.id).all()
    if not children:
        return ChildTaskListResponse(total=0, tasks=[])
    
    child_ids = [c.id for c in children]
    child_names = {c.id: c.name for c in children}
    
    # Build query
    query = db.query(ChildTask).filter(ChildTask.child_id.in_(child_ids))
    
    # Filter by specific child if provided
    if child_id:
        if child_id not in child_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this child")
        query = query.filter(ChildTask.child_id == child_id)
    
    # Filter by status if provided
    if task_status:
        query = query.filter(ChildTask.status == task_status)
    
    # Get tasks
    tasks = query.order_by(ChildTask.created_at.desc()).limit(limit).all()
    
    # Add child names to tasks
    tasks_with_names = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "child_id": task.child_id,
            "child_name": child_names.get(task.child_id, "Unknown"),
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "xp_reward": task.xp_reward,
            "difficulty": task.difficulty,
            "status": task.status,
            "source": task.source,
            "meta": task.meta,
            "created_at": task.created_at
        }
        tasks_with_names.append(task_dict)
    
    return ChildTaskListResponse(
        child_id=child_id,
        child_name=child_names.get(child_id) if child_id else None,
        total=len(tasks_with_names),
        tasks=[ChildTaskOut(**t) for t in tasks_with_names],
    )


@router.post("/{task_id}/complete", response_model=TaskCompleteResponse)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a task as completed."""
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can complete tasks.")

    task = mark_task_completed(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

    # Ownership check: ensure parent owns the child
    child = db.query(Child).filter(Child.id == task.child_id).first()
    if not child or child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this task")

    refresh_and_notify_dashboard(db, task.child_id, trigger_source="task")

    completed_at = (task.meta or {}).get("completed_at")
    return TaskCompleteResponse(task_id=task.id, status=task.status, completed_at=completed_at)


@router.patch("/{task_id}/status", response_model=TaskCompleteResponse)
def update_task_status_endpoint(
    task_id: int,
    request: UpdateTaskStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update task status (completed, incomplete, pending)."""
    if current_user.user_type != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents can update tasks.")

    # First get the task to check ownership
    from app.db.models.child_task import ChildTask
    task = db.query(ChildTask).filter(ChildTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")
    
    # Ownership check: ensure parent owns the child
    child = db.query(Child).filter(Child.id == task.child_id).first()
    if not child or child.parent_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this task")

    # Update the status
    updated_task = update_task_status(db, task_id, request.status)
    if not updated_task:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update task")

    refresh_and_notify_dashboard(db, task.child_id, trigger_source="task")

    completed_at = (updated_task.meta or {}).get("completed_at")
    return TaskCompleteResponse(task_id=updated_task.id, status=updated_task.status, completed_at=completed_at)
