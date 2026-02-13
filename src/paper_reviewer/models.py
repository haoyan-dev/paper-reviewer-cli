"""Core data models for paper reviewer CLI."""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict


class BibTeXEntry(BaseModel):
    """BibTeX entry metadata."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default_factory=list, description="List of author names")
    year: Optional[int] = Field(
        None,
        ge=1900,
        le=2100,
        description="Publication year",
    )
    bib_key: str = Field(..., alias="ID", description="BibTeX entry ID/key")
    url: Optional[HttpUrl] = Field(None, description="Paper URL")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")

    @field_validator("authors", mode="before")
    @classmethod
    def parse_authors(cls, v):
        """Parse authors from string or list."""
        if isinstance(v, str):
            # Split by "and" or comma
            authors = [a.strip() for a in v.replace(" and ", ", ").split(",")]
            return [a for a in authors if a]
        return v if isinstance(v, list) else []


class PaperPair(BaseModel):
    """Pair of BibTeX metadata and PDF file path."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    metadata: BibTeXEntry = Field(..., description="BibTeX entry metadata")
    pdf_path: Path = Field(..., description="Path to PDF file")

    @field_validator("pdf_path")
    @classmethod
    def validate_pdf_exists(cls, v: Path) -> Path:
        """Validate that PDF file exists."""
        if not v.exists():
            raise ValueError(f"PDF file does not exist: {v}")
        if not v.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return v


class ReviewData(BaseModel):
    """Structured review data from Gemini analysis."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    summary: str = Field(..., description="Overview of the paper")
    novelty: str = Field(..., description="Novelty and impact compared to previous work")
    methodology: str = Field(..., description="Core technical methodology")
    validation: str = Field(..., description="Validation and experimental results")
    discussion: str = Field(..., description="Discussion and limitations")
    next_steps: str = Field(..., description="Next steps and related papers")

    @field_validator("*", mode="before")
    @classmethod
    def allow_empty_strings(cls, v):
        """Allow empty strings (Gemini might return empty sections)."""
        return v if v is not None else ""


class Config(BaseModel):
    """Application configuration from environment variables."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    gemini_api_key: str = Field(..., min_length=1, description="Google AI API key")
    notion_token: str = Field(..., min_length=1, description="Notion integration token")
    notion_database_id: str = Field(
        ...,
        min_length=1,
        description="Notion database ID",
    )

    @field_validator("notion_database_id")
    @classmethod
    def validate_database_id(cls, v: str) -> str:
        """Basic validation for Notion database ID format."""
        # Remove dashes if present (Notion IDs can be with or without dashes)
        clean_id = v.replace("-", "")
        if len(clean_id) != 32:
            raise ValueError(
                f"Invalid Notion database ID format: {v}. "
                "Expected 32-character hex string (with or without dashes)."
            )
        # Check if it's valid hex
        try:
            int(clean_id, 16)
        except ValueError:
            raise ValueError(f"Invalid Notion database ID format: {v}. Must be hexadecimal.")
        return v
