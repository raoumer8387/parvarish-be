"""API routes for generating child tasks from chatbot responses."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.models.child import Child
from app.schemas.task import TaskFromChatRequest, TasksFromChatResponse, ChildTaskOut, ChildTaskListResponse, TaskCompleteResponse, TaskFromScoresRequest
from app.services.task_service import generate_tasks_from_chat, list_child_tasks, mark_task_completed, generate_tasks_from_scores

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
    status: str | None = None,
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

    tasks = list_child_tasks(db, child_id=child_id, status=status, limit=limit)
    return ChildTaskListResponse(
        child_id=child_id,
        total=len(tasks),
        tasks=[ChildTaskOut.model_validate(t) for t in tasks],
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

    completed_at = (task.meta or {}).get("completed_at")
    return TaskCompleteResponse(task_id=task.id, status=task.status, completed_at=completed_at)
