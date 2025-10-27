"""
Authentication middleware for HTTP Basic Auth.
Based on configuration from config.yml.
"""

import secrets
from typing import Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from config.settings import Settings, get_settings


security = HTTPBasic()


def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Optional[HTTPBasicCredentials]:
    """
    Verify HTTP Basic Auth credentials against configuration.

    Returns:
        HTTPBasicCredentials if authentication is disabled or credentials are valid

    Raises:
        HTTPException: If authentication is enabled and credentials are invalid
    """
    # If authentication is disabled, allow access
    if not settings.authentication.enabled:
        return None

    # Check credentials against configuration
    correct_username = settings.authentication.username
    correct_password = settings.authentication.password

    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": 'Basic realm="Premontage Server"'},
        )

    return credentials


def optional_verify_credentials(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Optional[HTTPBasicCredentials]:
    """
    Optional authentication verification.
    Returns None if no credentials provided and auth is disabled.
    """
    if not settings.authentication.enabled:
        return None

    if credentials is None:
        if settings.authentication.enabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": 'Basic realm="Premontage Server"'},
            )
        return None

    return verify_credentials(credentials, settings)


class AuthenticationConfig:
    """Authentication configuration helper."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self.settings.authentication.enabled

    @property
    def username(self) -> str:
        """Get configured username."""
        return self.settings.authentication.username

    @property
    def password(self) -> str:
        """Get configured password."""
        return self.settings.authentication.password

    def verify_user(self, username: str, password: str) -> bool:
        """Verify username and password."""
        if not self.enabled:
            return True

        is_correct_username = secrets.compare_digest(username, self.username)
        is_correct_password = secrets.compare_digest(password, self.password)

        return is_correct_username and is_correct_password


def get_auth_config(settings: Settings = Depends(get_settings)) -> AuthenticationConfig:
    """Get authentication configuration."""
    return AuthenticationConfig(settings)
