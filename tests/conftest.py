"""Shared pytest fixtures for paper-reviewer-cli tests."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from paper_reviewer.models import BibTeXEntry, Config, PaperPair


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_bibtex_entry() -> BibTeXEntry:
    """Create a sample BibTeXEntry for testing."""
    return BibTeXEntry(
        title="Test Paper Title",
        authors=["John Doe", "Jane Smith"],
        year=2024,
        bib_key="test2024",
        url="https://example.com/paper",
        doi="10.1000/test.doi",
    )


@pytest.fixture
def minimal_bibtex_entry() -> BibTeXEntry:
    """Create a minimal BibTeXEntry with only required fields."""
    return BibTeXEntry(
        title="Minimal Paper",
        bib_key="minimal2024",
    )


@pytest.fixture
def sample_config() -> Config:
    """Create a sample Config object for testing."""
    return Config(
        gemini_api_key="test-gemini-key",
        notion_token="test-notion-token",
        notion_database_id="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    )


@pytest.fixture
def sample_paper_pair(sample_bibtex_entry, temp_dir) -> PaperPair:
    """Create a sample PaperPair for testing."""
    pdf_path = temp_dir / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")  # Minimal valid PDF header
    return PaperPair(metadata=sample_bibtex_entry, pdf_path=pdf_path)
