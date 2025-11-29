"""Settings and profile management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from typing import List, Optional

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.parent import Parent
from app.db.models.child import Child
from app.core.security import get_current_user, get_password_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])


# ==================== PARENT PROFILE ====================

@router.get("/parent/profile")
async def get_parent_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get parent profile information.
    
    Returns:
        Parent profile with user details
    """
    # Verify user is a parent
    if hasattr(current_user, 'user_type') and current_user.user_type != 'parent':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    parent = db.query(Parent).filter(Parent.id == current_user.id).first()
    
    if not parent:
        # Return user info even if parent profile not created yet
        return {
            "user_id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "picture": current_user.picture,
            "has_profile": False,
            "profile": None
        }
    
    return {
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "picture": current_user.picture,
        "has_profile": True,
        "profile": {
            "phone": parent.phone,
            "country": parent.country,
            "city": parent.city,
            "father_age": parent.father_age,
            "mother_age": parent.mother_age,
            "married_since": parent.married_since,
            "is_single_parent": parent.is_single_parent
        }
    }


@router.put("/parent/profile")
async def update_parent_profile(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update parent profile information.
    
    Args:
        data: Profile data to update
        
    Returns:
        Updated profile
    """
    # Verify user is a parent
    if hasattr(current_user, 'user_type') and current_user.user_type != 'parent':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    # Update user name if provided
    if "name" in data and data["name"]:
        current_user.name = data["name"]
        db.commit()
    
    parent = db.query(Parent).filter(Parent.id == current_user.id).first()
    
    if parent:
        # Update existing profile
        for field in ["phone", "country", "city", "father_age", "mother_age", "married_since", "is_single_parent"]:
            if field in data:
                setattr(parent, field, data[field])
        db.commit()
        db.refresh(parent)
        message = "Parent profile updated successfully"
    else:
        # Create new profile
        parent = Parent(
            id=current_user.id,
            phone=data.get("phone"),
            country=data.get("country"),
            city=data.get("city"),
            father_age=data.get("father_age"),
            mother_age=data.get("mother_age"),
            married_since=data.get("married_since"),
            is_single_parent=data.get("is_single_parent")
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)
        message = "Parent profile created successfully"
    
    logger.info(f"Parent profile updated for user {current_user.id}")
    
    return {
        "message": message,
        "profile": {
            "phone": parent.phone,
            "country": parent.country,
            "city": parent.city,
            "father_age": parent.father_age,
            "mother_age": parent.mother_age,
            "married_since": parent.married_since,
            "is_single_parent": parent.is_single_parent
        }
    }


# ==================== CHILDREN MANAGEMENT ====================

@router.get("/children")
async def get_all_children(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all children for the logged-in parent.
    
    Returns:
        List of all children with their profiles
    """
    # Verify user is a parent
    if hasattr(current_user, 'user_type') and current_user.user_type != 'parent':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    # Get all children for this parent
    children = db.query(Child).filter(Child.parent_id == current_user.id).all()
    
    result = []
    for child in children:
        # Get associated user info
        user = db.query(User).filter(User.id == child.id).first()
        result.append({
            "id": child.id,
            "username": user.username if user else None,
            "name": child.name,
            "age": child.age,
            "gender": child.gender,
            "school": child.school,
            "class_name": child.class_name,
            "temperament": child.temperament,
            "created_at": child.created_at.isoformat() if child.created_at else None
        })
    
    return {
        "total": len(result),
        "children": result
    }


@router.get("/children/{child_id}")
async def get_child(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific child's profile.
    
    Args:
        child_id: The child's user ID
        
    Returns:
        Child profile details
    """
    # Verify user is a parent
    if hasattr(current_user, 'user_type') and current_user.user_type != 'parent':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.parent_id == current_user.id
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or does not belong to this parent"
        )
    
    user = db.query(User).filter(User.id == child.id).first()
    
    return {
        "id": child.id,
        "username": user.username if user else None,
        "name": child.name,
        "age": child.age,
        "gender": child.gender,
        "school": child.school,
        "class_name": child.class_name,
        "temperament": child.temperament,
        "created_at": child.created_at.isoformat() if child.created_at else None
    }


@router.post("/children")
async def add_child(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new child.
    
    Args:
        data: Child data including username, password, name, etc.
        
    Returns:
        Created child profile
    """
    # Verify user is a parent
    if hasattr(current_user, 'user_type') and current_user.user_type != 'parent':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    
    if not username or not password or not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username, password, and name are required"
        )
    
    # Check for duplicate username
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' already exists"
        )
    
    # Create user record for child
    hashed_pw = get_password_hash(password)
    user = User(
        username=username,
        hashed_password=hashed_pw,
        email=None,
        name=name,
        created_at=datetime.utcnow(),
    )
    if hasattr(user, 'user_type'):
        user.user_type = 'child'
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create child profile
    child = Child(
        id=user.id,
        parent_id=current_user.id,
        name=name,
        age=data.get("age"),
        gender=data.get("gender"),
        school=data.get("school"),
        class_name=data.get("class_name"),
        temperament=data.get("temperament"),
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    
    logger.info(f"Child {child.id} added by parent {current_user.id}")
    
    return {
        "message": "Child added successfully",
        "child": {
            "id": child.id,
            "username": user.username,
            "name": child.name,
            "age": child.age,
            "gender": child.gender,
            "school": child.school,
            "class_name": child.class_name,
            "temperament": child.temperament
        }
    }


@router.put("/children/{child_id}")
async def update_child(
    child_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a child's profile.
    
    Args:
        child_id: The child's user ID
        data: Updated child data
        
    Returns:
        Updated child profile
    """
    # Verify user is a parent
    if hasattr(current_user, 'user_type') and current_user.user_type != 'parent':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.parent_id == current_user.id
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or does not belong to this parent"
        )
    
    # Update child profile fields
    for field in ["name", "age", "gender", "school", "class_name", "temperament"]:
        if field in data:
            setattr(child, field, data[field])
    
    # Update user record if name or username changed
    user = db.query(User).filter(User.id == child_id).first()
    if user:
        if "name" in data:
            user.name = data["name"]
        if "username" in data and data["username"] != user.username:
            # Check for duplicate username
            existing = db.query(User).filter(User.username == data["username"]).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{data['username']}' already exists"
                )
            user.username = data["username"]
        
        # Update password if provided
        if "password" in data and data["password"]:
            user.hashed_password = get_password_hash(data["password"])
    
    db.commit()
    db.refresh(child)
    db.refresh(user)
    
    logger.info(f"Child {child_id} updated by parent {current_user.id}")
    
    return {
        "message": "Child updated successfully",
        "child": {
            "id": child.id,
            "username": user.username,
            "name": child.name,
            "age": child.age,
            "gender": child.gender,
            "school": child.school,
            "class_name": child.class_name,
            "temperament": child.temperament
        }
    }


@router.delete("/children/{child_id}")
async def delete_child(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a child's profile and user account.
    
    Args:
        child_id: The child's user ID
        
    Returns:
        Success message
    """
    # Verify user is a parent
    if hasattr(current_user, 'user_type') and current_user.user_type != 'parent':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    # Find the child to ensure it belongs to the parent
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.parent_id == current_user.id
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or does not belong to this parent"
        )
    
    # The user corresponding to the child
    user = db.query(User).filter(User.id == child_id).first()

    try:
        # Delete child profile first (due to foreign key)
        db.delete(child)
        
        # Delete user account
        if user:
            db.delete(user)
        
        db.commit()
        
        logger.info(f"Child {child_id} deleted by parent {current_user.id}")
        
        return {
            "message": "Child deleted successfully",
            "child_id": child_id
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete child {child_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete child. Please try again."
        )
