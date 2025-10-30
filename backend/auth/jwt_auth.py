"""
Authentication utilities for JWT token handling and password management.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import User, UserSession


# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Truncate password to 72 bytes for bcrypt compatibility
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    truncated_password = password_bytes.decode("utf-8", errors="ignore")

    return pwd_context.verify(truncated_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate password hash.

    Note: Bcrypt has a 72-byte limit. Passwords are truncated to this limit
    using UTF-8 encoding to ensure compatibility.
    """
    # Truncate password to 72 bytes for bcrypt compatibility
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    truncated_password = password_bytes.decode("utf-8", errors="ignore")

    return pwd_context.hash(truncated_password)


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """Authenticate user with username and password."""
    result = await db.execute(
        select(User).where(User.username == username, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return None

    return user


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add JWT standard claims
    jti = str(uuid.uuid4())  # JWT ID for token tracking
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "jti": jti})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str, db: AsyncSession) -> Optional[User]:
    """Verify JWT token and return user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        jti = payload.get("jti")

        if not username or not jti:
            return None  # Check if token exists in database and is not expired
        result = await db.execute(
            select(UserSession).where(
                UserSession.token_jti == jti,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Get user
        result = await db.execute(
            select(User).where(User.id == session.user_id, User.is_active.is_(True))
        )
        user = result.scalar_one_or_none()

        return user

    except JWTError:
        return None


async def create_user_session(db: AsyncSession, user: User, token: str) -> UserSession:
    """Create user session record for token tracking."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token format"
            )

        session = UserSession(
            user_id=user.id,
            token_jti=jti,
            expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid token: {e}"
        )


async def revoke_user_session(db: AsyncSession, token: str) -> bool:
    """Revoke user session (logout)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")

        if not jti:
            return False

        result = await db.execute(
            select(UserSession).where(UserSession.token_jti == jti)
        )
        session = result.scalar_one_or_none()

        if session:
            await db.delete(session)
            await db.commit()
            return True

        return False

    except JWTError:
        return False


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """Clean up expired sessions from database."""
    result = await db.execute(
        select(UserSession).where(UserSession.expires_at < datetime.now(timezone.utc))
    )
    expired_sessions = result.scalars().all()

    count = len(expired_sessions)
    for session in expired_sessions:
        await db.delete(session)

    await db.commit()
    return count
