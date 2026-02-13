"""Configuration management for paper reviewer CLI."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from .models import Config as ConfigModel


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    gemini_api_key: str = Field(..., description="Google AI API key")
    notion_token: str = Field(..., description="Notion integration token")
    notion_database_id: str = Field(..., description="Notion database ID")

    def to_model(self) -> ConfigModel:
        """Convert to Config model for validation."""
        return ConfigModel(
            gemini_api_key=self.gemini_api_key,
            notion_token=self.notion_token,
            notion_database_id=self.notion_database_id,
        )


def load_config(env_file: Optional[Path] = None) -> ConfigModel:
    """
    Load configuration from environment variables or .env file.

    Args:
        env_file: Optional path to .env file. If None, searches for .env in:
            - Current working directory
            - Project root (parent of src/)

    Returns:
        Validated Config model instance

    Raises:
        FileNotFoundError: If .env file is specified but doesn't exist
        ValueError: If required environment variables are missing or invalid
    """
    # Determine .env file path
    if env_file is None:
        # Try current directory first
        current_dir_env = Path(".env")
        if current_dir_env.exists():
            env_file = current_dir_env
        else:
            # Try project root (parent of src/)
            project_root = Path(__file__).parent.parent.parent
            project_env = project_root / ".env"
            if project_env.exists():
                env_file = project_env
            else:
                # Use default (will try .env in current directory)
                env_file = Path(".env")

    # Check if file exists (if explicitly provided)
    if env_file and not env_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {env_file}\n"
            "Please create a .env file with the required variables:\n"
            "- GEMINI_API_KEY\n"
            "- NOTION_TOKEN\n"
            "- NOTION_DATABASE_ID\n"
            "\nSee .env.example for a template."
        )

    # Load settings
    # BaseSettings will automatically load from .env file if env_file is set in model_config
    # But we can override it if needed
    if env_file and env_file.exists():
        # Create config with explicit env file
        config = Config(_env_file=str(env_file))
    else:
        # Try loading from environment variables directly
        # BaseSettings will try .env in current directory by default
        config = Config()

    # Validate using ConfigModel
    try:
        return config.to_model()
    except Exception as e:
        # Provide helpful error message
        missing_vars = []
        if not os.getenv("GEMINI_API_KEY"):
            missing_vars.append("GEMINI_API_KEY")
        if not os.getenv("NOTION_TOKEN"):
            missing_vars.append("NOTION_TOKEN")
        if not os.getenv("NOTION_DATABASE_ID"):
            missing_vars.append("NOTION_DATABASE_ID")

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please set these in your .env file or environment.\n"
                "See .env.example for a template."
            ) from e
        raise
