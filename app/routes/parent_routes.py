"""Parent-specific routes (aliases for settings where helpful)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.child import Child
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parent", tags=["parent"])


@router.get("/children")
async def list_parent_children(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias for fetching children of the logged-in parent.

    Mirrors the behavior of `GET /settings/children` but under `/parent` for
    clearer semantics and backward compatibility with the frontend.
    """
    if hasattr(current_user, 'user_type') and current_user.user_type != 'parent':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )

    children = db.query(Child).filter(Child.parent_id == current_user.id).all()

    result = []
    for child in children:
        # Only expose necessary fields; username can be obtained from users if needed
        result.append({
            "id": child.id,
            "name": child.name,
            "age": child.age,
            "gender": child.gender,
            "school": child.school,
            "class_name": child.class_name,
            "temperament": child.temperament,
            "created_at": child.created_at.isoformat() if getattr(child, 'created_at', None) else None
        })

    return {"total": len(result), "children": result}
