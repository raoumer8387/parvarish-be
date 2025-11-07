"""Google OAuth authentication routes.

Only PARENTS can register/login through Google OAuth.
Children will be added by their parents later through the parent dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.oauth import oauth
from app.core.security import create_access_token
from app.core.config import settings
from app.db.session import get_db
from app.db.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/google", tags=["google-auth"])


@router.get("/login")
async def google_login(request: Request):
    """Initiate Google OAuth login flow for PARENTS.
    
    This endpoint is specifically for parent registration/login.
    Children cannot register through Google - they will be added by parents.
    
    Redirects user to Google's OAuth consent screen.
    
    Returns:
        Redirect response to Google OAuth page
    """
    # Prefer dynamic redirect URI based on current host (works with ngrok)
    # Falls back to settings.GOOGLE_REDIRECT_URI if url_for fails
    try:
        redirect_uri = str(request.url_for("google_callback"))
    except Exception:
        redirect_uri = settings.GOOGLE_REDIRECT_URI

    logger.info(
        f"Initiating Google OAuth login (PARENT) with redirect_uri: {redirect_uri}"
    )
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback for PARENT registration/login.
    
    This callback automatically creates a PARENT account when a user
    authenticates with Google for the first time.
    
    Children CANNOT register through Google - they must be added by parents
    through the parent dashboard after parent login.
    
    Processes the OAuth callback from Google, creates or updates parent user,
    and redirects to frontend with JWT token.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        Redirect to frontend with token or error
    """
    try:
        # Exchange authorization code for access token
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            logger.error("Failed to get user info from Google")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google"
            )
        
        # Extract user information
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        logger.info(f"Google OAuth callback for email: {email}")
        
        # Check if user exists by Google ID
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Check if email already exists (user registered with password)
            existing_user = db.query(User).filter(User.email == email).first()
            
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = google_id
                existing_user.name = name
                existing_user.picture = picture
                existing_user.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_user)
                user = existing_user
                is_new_user = False
                logger.info(f"Linked Google account to existing user: {email}")
            else:
                # Create new PARENT user (Google OAuth is only for parents)
                user = User(
                    google_id=google_id,
                    email=email,
                    name=name,
                    picture=picture,
                    created_at=datetime.utcnow()
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                is_new_user = True
                logger.info(f"Created new PARENT user from Google OAuth: {email}")
        else:
            # Update existing user info
            user.name = name
            user.picture = picture
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            is_new_user = False
            logger.info(f"Updated existing Google user: {email}")
        
        # Create JWT access token with role information
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": "parent"  # All Google OAuth users are parents
            }
        )
        
        # Redirect to frontend with token in URL as specified
        frontend_url = settings.FRONTEND_URL
        
        # Format: http://localhost:3000?access_token={JWT_TOKEN}
        redirect_url = f"{frontend_url}?access_token={access_token}"
        
        logger.info(f"Redirecting to frontend with access_token: {redirect_url}")
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}", exc_info=True)
        # Redirect to frontend with error
        frontend_url = settings.FRONTEND_URL
        error_message = str(e).replace(' ', '+')
        return RedirectResponse(
            url=f"{frontend_url}/auth/error?message={error_message}"
        )


@router.get("/status")
async def google_auth_status():
    """Check Google OAuth configuration status.
    
    Returns:
        Configuration status information
    """
    return {
        "google_oauth_enabled": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "client_id_configured": bool(settings.GOOGLE_CLIENT_ID),
        "note": "Google OAuth is only available for PARENT registration/login. Children are added by parents."
    }


@router.get("/redirect-uri")
async def google_auth_redirect_uri(request: Request):
    """Return the effective redirect URI the server will use for OAuth.

    Helpful when using tunneling tools (e.g., ngrok). Copy this URL and add it
    to Google Cloud Console > OAuth 2.0 Client > Authorized redirect URIs.
    """
    try:
        effective_uri = str(request.url_for("google_callback"))
    except Exception:
        effective_uri = settings.GOOGLE_REDIRECT_URI
    return {
        "effective_redirect_uri": effective_uri,
        "configured_redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
