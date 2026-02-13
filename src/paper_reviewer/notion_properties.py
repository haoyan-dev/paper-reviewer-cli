"""Notion properties builder module for converting BibTeX metadata to Notion properties."""

from typing import Dict, List, Optional

from .models import BibTeXEntry


def build_notion_properties(metadata: BibTeXEntry) -> Dict:
    """
    Build Notion page properties from BibTeXEntry metadata.

    Maps BibTeXEntry fields to Notion property types:
    - title → Name (title property)
    - authors → Authors (multi_select property)
    - year → Year (number property)
    - bib_key → BibTeX Key (rich_text property)
    - url or doi → URL/DOI (url property, prefers url over doi)

    Args:
        metadata: BibTeXEntry object with paper metadata

    Returns:
        Dictionary compatible with Notion API properties format

    Example:
        >>> from .models import BibTeXEntry
        >>> entry = BibTeXEntry(
        ...     title="Test Paper",
        ...     authors=["Author 1", "Author 2"],
        ...     year=2024,
        ...     bib_key="test2024"
        ... )
        >>> props = build_notion_properties(entry)
        >>> "Name" in props
        True
    """
    properties = {}

    # Title property (required)
    properties["Name"] = {
        "title": [{"type": "text", "text": {"content": metadata.title}}]
    }

    # Authors property (multi_select)
    if metadata.authors:
        properties["Authors"] = {
            "multi_select": format_authors(metadata.authors)
        }

    # Year property (number)
    if metadata.year is not None:
        properties["Year"] = {"number": metadata.year}

    # BibTeX Key property (rich_text)
    properties["BibTeX Key"] = {
        "rich_text": [{"type": "text", "text": {"content": metadata.bib_key}}]
    }

    # URL/DOI property (url)
    url_or_doi = extract_url_or_doi(metadata)
    if url_or_doi:
        properties["URL/DOI"] = {"url": url_or_doi}

    return properties


def format_authors(authors: List[str]) -> List[Dict]:
    """
    Convert list of author strings to Notion multi_select format.

    Args:
        authors: List of author name strings

    Returns:
        List of dicts with "name" keys for Notion multi_select

    Example:
        >>> format_authors(["John Doe", "Jane Smith"])
        [{'name': 'John Doe'}, {'name': 'Jane Smith'}]
    """
    if not authors:
        return []

    return [{"name": author} for author in authors if author.strip()]


def extract_url_or_doi(metadata: BibTeXEntry) -> Optional[str]:
    """
    Extract URL or DOI from BibTeXEntry, preferring URL over DOI.

    Args:
        metadata: BibTeXEntry object

    Returns:
        URL string if available, otherwise DOI string, or None if neither exists

    Example:
        >>> from .models import BibTeXEntry
        >>> entry = BibTeXEntry(title="Test", bib_key="test", url="https://example.com")
        >>> extract_url_or_doi(entry)
        'https://example.com'
    """
    # Prefer URL over DOI
    if metadata.url:
        # HttpUrl is a Pydantic type that can be converted to string
        return str(metadata.url)

    if metadata.doi:
        # DOI might need to be formatted as URL
        # If it's already a URL, return as-is, otherwise prepend https://doi.org/
        doi_str = str(metadata.doi)
        if doi_str.startswith(("http://", "https://")):
            return doi_str
        return f"https://doi.org/{doi_str}"

    return None
