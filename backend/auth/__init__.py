"""
Authentication package initialization.
"""

from .middleware import verify_credentials, optional_verify_credentials, get_auth_config

__all__ = ["verify_credentials", "optional_verify_credentials", "get_auth_config"]
