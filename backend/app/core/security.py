"""
PERIMETER Security & Authentication Module
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# Password hashing context with pbkdf2_sha256 and bcrypt
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password, with fallback for legacy plain text seeds.
    """
    if not hashed_password:
        return False
    # If the password in DB is plain text (e.g. from early seeds)
    if hashed_password == plain_password:
        return True
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return plain_password == hashed_password

def get_password_hash(password: str) -> str:
    """
    Hash a password securely.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate signed JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to extract and verify the current authenticated user from Bearer token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please register or log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not auth or not auth.credentials:
        raise credentials_exception
    
    token = auth.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user

def require_role(allowed_roles: List[str]):
    """
    Dependency factory to enforce role-based access control (RBAC).
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Admin has superuser privileges across roles
        if current_user.role == "admin" or current_user.role in allowed_roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Allowed roles for this action: {', '.join(allowed_roles)}"
        )
    return role_checker

def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extract current user if authenticated, else return None without raising 401.
    """
    if not auth or not auth.credentials:
        return None
    try:
        payload = decode_access_token(auth.credentials)
        if not payload or not payload.get("sub"):
            return None
        return db.query(User).filter(User.id == payload.get("sub")).first()
    except Exception:
        return None
