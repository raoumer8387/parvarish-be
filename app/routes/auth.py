"""Authentication routes for email/password authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.schemas.user import UserCreate, UserLogin, UserRead, Token
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.parent import Parent
from app.db.models.child import Child
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# 1️⃣ GOOGLE LOGIN (Parent)
from fastapi import Body
from sqlalchemy import or_
from app.core.security import get_password_hash

@router.post("/google-login")
def google_login_parent(
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Accepts: { google_uid, email, name }
    Returns: { user_id, user_type, is_new_user, has_parent_profile, has_children }
    """
    google_uid = data.get("google_uid")
    email = data.get("email")
    name = data.get("name")
    if not google_uid or not email or not name:
        raise HTTPException(status_code=400, detail="Missing google_uid, email, or name")

    user = db.query(User).filter(or_(User.google_id == google_uid, User.email == email)).first()
    is_new_user = False
    if user:
        # If user exists, update info if needed
        if user.google_id != google_uid:
            user.google_id = google_uid
        if user.name != name:
            user.name = name
        db.commit()
        db.refresh(user)
    else:
        user = User(
            google_id=google_uid,
            email=email,
            name=name,
            hashed_password=None,
            created_at=datetime.utcnow(),
            # user_type will be handled below
        )
        # Add user_type column if not present in model
        if hasattr(user, 'user_type'):
            user.user_type = 'parent'
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new_user = True
    
    # Set user_type to parent if not already
    if hasattr(user, 'user_type') and user.user_type != 'parent':
        user.user_type = 'parent'
        db.commit()
    
    # Check if parent profile exists
    has_parent_profile = db.query(Parent).filter(Parent.id == user.id).first() is not None
    
    # Check if children exist (only if parent profile exists)
    has_children = False
    if has_parent_profile:
        has_children = db.query(Child).filter(Child.parent_id == user.id).first() is not None
    
    logger.info(f"Google login for user {user.id}: is_new={is_new_user}, has_profile={has_parent_profile}, has_children={has_children}")
    
    return {
        "user_id": user.id,
        "user_type": "parent",
        "is_new_user": is_new_user,
        "has_parent_profile": has_parent_profile,
        "has_children": has_children
    }


# 2️⃣ PARENT ONBOARDING
@router.post("/register-parent")
def register_parent(
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Accepts: { user_id, phone, country, city, father_age, mother_age, married_since, is_single_parent }
    Returns: { message, parent_id }
    """
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    parent = db.query(Parent).filter(Parent.id == user_id).first()
    if parent:
        # Update existing
        for field in ["phone", "country", "city", "father_age", "mother_age", "married_since", "is_single_parent"]:
            if field in data:
                setattr(parent, field, data[field])
        db.commit()
        db.refresh(parent)
        msg = "Parent profile updated successfully"
    else:
        parent = Parent(
            id=user_id,
            phone=data.get("phone"),
            country=data.get("country"),
            city=data.get("city"),
            father_age=data.get("father_age"),
            mother_age=data.get("mother_age"),
            married_since=data.get("married_since"),
            is_single_parent=data.get("is_single_parent"),
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)
        msg = "Parent profile created successfully"
    return {"message": msg, "parent_id": parent.id}


# 3️⃣ ADD CHILDREN
@router.post("/add-children")
def add_children(
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Accepts: { parent_id, children: [ { username, password, name, age, gender, school, class_name, temperament } ] }
    Returns: { message, added_children }
    """
    parent_id = data.get("parent_id")
    children = data.get("children", [])
    if not parent_id or not children:
        raise HTTPException(status_code=400, detail="Missing parent_id or children list")
    added = 0
    errors = []
    for child in children:
        username = child.get("username")
        password = child.get("password")
        name = child.get("name")
        if not username or not password or not name:
            errors.append(f"Missing username, password, or name for child: {child}")
            continue
        # Check for duplicate username
        existing = db.query(User).filter(User.email == None, User.username == username).first()
        if existing:
            errors.append(f"Username '{username}' already exists.")
            continue
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
        child_profile = Child(
            id=user.id,
            parent_id=parent_id,
            name=name,
            age=child.get("age"),
            gender=child.get("gender"),
            school=child.get("school"),
            class_name=child.get("class_name"),
            temperament=child.get("temperament"),
        )
        db.add(child_profile)
        db.commit()
        db.refresh(child_profile)
        added += 1
    if errors:
        raise HTTPException(status_code=400, detail={"message": "Some children could not be added", "errors": errors, "added_children": added})
    return {"message": "Children added successfully", "added_children": added}


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email and password.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If email already registered
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.email}")
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user with email/username and password.
    
    Supports both:
    - Parent login with email + password
    - Child login with username + password
    
    Args:
        user_data: User login credentials (email OR username + password)
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Validate that either email or username is provided
    if not user_data.email and not user_data.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or username must be provided"
        )
    
    # Find user by email or username
    if user_data.email:
        user = db.query(User).filter(User.email == user_data.email).first()
        identifier = user_data.email
    else:
        user = db.query(User).filter(User.username == user_data.username).first()
        identifier = user_data.username
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has a password (not Google-only account)
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google sign-in. Please login with Google."
        )
    
    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User logged in: {identifier} (user_id: {user.id})")
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email if user.email else None,
            "username": user.username if hasattr(user, 'username') else None,
            "name": user.name
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user


@router.get("/validate")
async def validate_token(current_user: User = Depends(get_current_user)):
    """Validate JWT token.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Validation status
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }
