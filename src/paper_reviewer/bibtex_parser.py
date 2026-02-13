"""BibTeX file parser module."""

import logging
from pathlib import Path
from typing import Dict, List

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

from .errors import BibTeXParseError
from .models import BibTeXEntry

logger = logging.getLogger(__name__)


def parse_bibtex_file(bib_path: Path) -> List[BibTeXEntry]:
    """
    Parse a BibTeX file and extract structured metadata.

    Args:
        bib_path: Path to the `.bib` file

    Returns:
        List of BibTeXEntry objects parsed from the file

    Raises:
        BibTeXParseError: If the file cannot be parsed or is malformed
        FileNotFoundError: If the file does not exist
    """
    if not bib_path.exists():
        raise FileNotFoundError(f"BibTeX file not found: {bib_path}")

    if not bib_path.is_file():
        raise BibTeXParseError(f"Path is not a file: {bib_path}", str(bib_path))

    try:
        # Configure parser to handle unicode and common issues
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        parser.ignore_nonstandard_types = False
        parser.homogenise_fields = True

        # Try different encodings
        encodings = ["utf-8", "latin-1", "cp1252"]
        entries = None
        last_error = None

        for encoding in encodings:
            try:
                with open(bib_path, "r", encoding=encoding) as f:
                    bib_database = bibtexparser.load(f, parser=parser)
                    entries = bib_database.entries
                    break
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                continue

        if entries is None:
            raise BibTeXParseError(
                f"Failed to parse BibTeX file with any encoding: {bib_path}. "
                f"Last error: {last_error}",
                str(bib_path),
            ) from last_error

        # Convert entries to BibTeXEntry objects
        bibtex_entries = []
        for entry in entries:
            try:
                bibtex_entry = extract_metadata(entry)
                bibtex_entries.append(bibtex_entry)
            except Exception as e:
                logger.warning(
                    f"Skipping entry in {bib_path}: {e}. "
                    f"Entry ID: {entry.get('ID', 'unknown')}"
                )
                continue

        if not bibtex_entries:
            raise BibTeXParseError(
                f"No valid entries found in BibTeX file: {bib_path}", str(bib_path)
            )

        return bibtex_entries

    except BibTeXParseError:
        raise
    except Exception as e:
        raise BibTeXParseError(
            f"Error parsing BibTeX file {bib_path}: {e}", str(bib_path)
        ) from e


def extract_metadata(entry: Dict) -> BibTeXEntry:
    """
    Convert a raw bibtexparser entry dictionary to a BibTeXEntry model.

    Args:
        entry: Raw entry dictionary from bibtexparser

    Returns:
        BibTeXEntry object with parsed metadata

    Raises:
        BibTeXParseError: If required fields are missing
    """
    # Extract required fields
    title = entry.get("title", "").strip()
    bib_key = entry.get("ID", "").strip()

    if not title:
        raise BibTeXParseError(f"Missing required field 'title' in entry: {bib_key}")

    if not bib_key:
        raise BibTeXParseError("Missing required field 'ID' in BibTeX entry")

    # Extract optional fields
    authors_str = entry.get("author", "") or entry.get("authors", "")
    year_str = entry.get("year", "").strip()
    url_str = entry.get("url", "").strip()
    doi_str = entry.get("doi", "").strip()

    # Parse year
    year = None
    if year_str:
        try:
            year = int(year_str)
            if year < 1900 or year > 2100:
                logger.warning(f"Year {year} seems unusual, but keeping it")
        except ValueError:
            logger.warning(f"Could not parse year '{year_str}', skipping")

    # Parse authors (handled by BibTeXEntry model validator)
    authors = authors_str if authors_str else []

    # Build BibTeXEntry
    try:
        bibtex_entry = BibTeXEntry(
            title=title,
            authors=authors,
            year=year,
            bib_key=bib_key,
            url=url_str if url_str else None,
            doi=doi_str if doi_str else None,
        )
        return bibtex_entry
    except Exception as e:
        raise BibTeXParseError(
            f"Error creating BibTeXEntry from entry {bib_key}: {e}"
        ) from e
