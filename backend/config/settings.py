"""
Configuration settings management.
Loads configuration from config.yml and provides application settings.
"""

import os
import yaml
from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings

from models.schemas import (
    Settings,
    AuthenticationSettings,
    ServerSettings,
    PathSettings,
)


class AppSettings(BaseSettings):
    """Application settings with environment variable support."""

    # Server settings
    server_host: str = "0.0.0.0"
    server_port: int = 47393
    server_reload: bool = False

    # Authentication settings
    auth_enabled: bool = False
    auth_username: str = "admin"
    auth_password: str = "admin"

    # Path settings
    projects_path: str = "./projects"
    b_roll_path: str = "./b-roll"
    temp_path: str = "./temp"

    # Configuration file path
    config_file: str = "config.yml"

    class Config:
        env_prefix = "PREMONTAGE_"
        case_sensitive = False


def load_config_from_yaml(config_path: Optional[Path] = None) -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, searches for config.yml in common locations.

    Returns:
        Dictionary containing configuration data
    """
    if config_path is None:
        # Search for config.yml in common locations
        search_paths = [
            Path("config.yml"),  # Current directory
            Path("../config.yml"),  # Parent directory
            Path("../../config.yml"),  # Project root
            Path(__file__).parent.parent.parent / "config.yml",  # Relative to this file
        ]

        for path in search_paths:
            if path.exists():
                config_path = path
                break

    if config_path is None or not config_path.exists():
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        return config
    except Exception as e:
        print(f"Warning: Could not load config from {config_path}: {e}")
        return {}


def create_settings_from_config(config: dict) -> Settings:
    """
    Create Settings object from configuration dictionary.

    Args:
        config: Configuration dictionary loaded from YAML

    Returns:
        Settings object with configuration applied
    """
    # Extract dashboard/auth configuration
    dashboard_config = config.get("dashboard", {})
    auth_config = dashboard_config.get("auth", {})

    # Extract server configuration
    server_config = config.get("server", {})

    # Extract path configuration
    paths_config = config.get("paths", {})

    # Create authentication settings
    auth_settings = AuthenticationSettings(
        enabled=auth_config.get("enabled", False),
        username=auth_config.get(
            "username", "admin"
        ),  # default username, change if needed in config.yml
        password=auth_config.get(
            "password", "admin"
        ),  # default password, change if needed in config.yml
    )

    # Create server settings
    server_settings = ServerSettings(
        host=server_config.get(
            "host", "0.0.0.0"
        ),  # default host, change if needed in config.yml
        port=server_config.get(
            "port", 47393
        ),  # default port, change if needed in config.yml
        reload=server_config.get(
            "reload", False
        ),  # default reload setting, keep for production
    )

    # Create path settings
    path_settings = PathSettings(
        projects=paths_config.get("projects", "./projects"),
        b_roll=paths_config.get("b_roll", "./b-roll"),
        temp=paths_config.get("temp", "./temp"),
    )

    return Settings(
        authentication=auth_settings, server=server_settings, paths=path_settings
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    Cached for performance.

    Returns:
        Settings object with current configuration
    """
    # Load from environment variables first
    app_settings = AppSettings()

    # Load configuration from YAML
    config = load_config_from_yaml()

    if config:
        # Create settings from YAML config
        settings = create_settings_from_config(config)
    else:
        # Fallback to environment variables and defaults
        settings = Settings(
            authentication=AuthenticationSettings(
                enabled=app_settings.auth_enabled,
                username=app_settings.auth_username,
                password=app_settings.auth_password,
            ),
            server=ServerSettings(
                host=app_settings.server_host,
                port=app_settings.server_port,
                reload=app_settings.server_reload,
            ),
            paths=PathSettings(
                projects=app_settings.projects_path,
                b_roll=app_settings.b_roll_path,
                temp=app_settings.temp_path,
            ),
        )

    return settings


def update_temp_path_for_project(project_name: str) -> None:
    """
    Update the temp path for a specific project.
    This clears the cache and updates the path.

    Args:
        project_name: Name of the project
    """
    # Clear the cache to force reload
    get_settings.cache_clear()

    # Update environment variable
    os.environ["PREMONTAGE_TEMP_PATH"] = f"./projects/{project_name}/temp"


def get_project_temp_path(project_name: str) -> Path:
    """
    Get the temp path for a specific project.

    Args:
        project_name: Name of the project

    Returns:
        Path to the project's temp directory
    """
    settings = get_settings()
    projects_path = Path(settings.paths.projects)
    return projects_path / project_name / "temp"


def ensure_directories_exist(settings: Settings) -> None:
    """
    Ensure all required directories exist.

    Args:
        settings: Application settings
    """
    directories = [
        Path(settings.paths.projects),
        Path(settings.paths.b_roll),
        Path(settings.paths.temp),
        Path(settings.paths.b_roll) / "ressources",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def validate_configuration(settings: Settings) -> list:
    """
    Validate the configuration and return any issues found.

    Args:
        settings: Application settings to validate

    Returns:
        List of validation issues (empty if all valid)
    """
    issues = []

    # Validate paths
    required_paths = [
        (settings.paths.projects, "projects"),
        (settings.paths.b_roll, "b_roll"),
    ]

    for path_str, name in required_paths:
        path = Path(path_str)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create {name} directory at {path}: {e}")

    # Validate server settings
    if not (1 <= settings.server.port <= 65535):
        issues.append(f"Invalid server port: {settings.server.port}")

    # Validate authentication settings
    if settings.authentication.enabled:
        if not settings.authentication.username:
            issues.append("Authentication enabled but username is empty")
        if not settings.authentication.password:
            issues.append("Authentication enabled but password is empty")

    return issues


# Configuration reload functionality
_config_file_mtime = None


def config_needs_reload() -> bool:
    """
    Check if configuration file has been modified and needs reload.

    Returns:
        True if configuration needs to be reloaded
    """
    global _config_file_mtime

    config_paths = [
        Path("config.yml"),
        Path("../config.yml"),
        Path("../../config.yml"),
    ]

    for config_path in config_paths:
        if config_path.exists():
            current_mtime = config_path.stat().st_mtime
            if _config_file_mtime is None:
                _config_file_mtime = current_mtime
                return False
            elif current_mtime > _config_file_mtime:
                _config_file_mtime = current_mtime
                return True

    return False


def reload_settings() -> Settings:
    """
    Force reload of settings from configuration file.

    Returns:
        Reloaded Settings object
    """
    get_settings.cache_clear()
    return get_settings()
