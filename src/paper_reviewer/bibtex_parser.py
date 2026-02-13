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
        # Create a fresh parser instance for each file to avoid state accumulation
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        parser.ignore_nonstandard_types = False
        parser.homogenise_fields = True
        parser.expect_multiple_parse = False  # Don't accumulate entries across parses

        # Try different encodings
        encodings = ["utf-8", "latin-1", "cp1252"]
        entries = None
        last_error = None

        for encoding in encodings:
            try:
                with open(bib_path, "r", encoding=encoding) as f:
                    file_content = f.read()
                
                # Use loads() instead of load() to avoid parser state accumulation
                bib_database = bibtexparser.loads(file_content, parser=parser)
                entries = bib_database.entries
                
                # Deduplicate entries by ID to handle parser state accumulation
                seen_ids = set()
                unique_entries = []
                for entry in entries:
                    entry_id = entry.get('id') or entry.get('ID') or entry.get('key')
                    if entry_id and entry_id not in seen_ids:
                        seen_ids.add(entry_id)
                        unique_entries.append(entry)
                    elif not entry_id:
                        # Entry without ID - include it but log warning
                        unique_entries.append(entry)
                
                entries = unique_entries
                
                # bibtexparser with homogenise_fields=True normalizes ID to id (lowercase)
                # Map entry keys from entries_dict to entries
                if hasattr(bib_database, 'entries_dict'):
                    entries_dict = bib_database.entries_dict
                    # entries_dict maps entry keys to lists of entries
                    for entry_key, entry_list in entries_dict.items():
                        for entry in entry_list:
                            # Ensure entry has ID field (use lowercase 'id' for homogenise_fields)
                            if 'id' not in entry and 'ID' not in entry:
                                entry['id'] = entry_key
                            elif 'ID' in entry and 'id' not in entry:
                                entry['id'] = entry['ID']
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
                # bibtexparser with homogenise_fields=True uses lowercase 'id'
                # Normalize to ensure 'id' exists (prefer lowercase for homogenise_fields)
                if 'id' not in entry:
                    if 'ID' in entry:
                        entry['id'] = entry['ID']
                    elif hasattr(entry, 'key'):
                        entry['id'] = entry.key
                
                bibtex_entry = extract_metadata(entry)
                bibtex_entries.append(bibtex_entry)
            except Exception as e:
                entry_id = entry.get('ID') or entry.get('id') or entry.get('key', 'unknown')
                logger.warning(
                    f"Skipping entry in {bib_path}: {e}. "
                    f"Entry ID: {entry_id}"
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
    # bibtexparser may lowercase field names, so check both cases
    title = entry.get("title", "") or entry.get("Title", "")
    if isinstance(title, str):
        title = title.strip()
    else:
        title = str(title).strip()
    
    # Entry key/ID - bibtexparser with homogenise_fields uses lowercase 'id'
    bib_key = entry.get("id") or entry.get("ID") or entry.get("key") or ""
    if isinstance(bib_key, str):
        bib_key = bib_key.strip()
    else:
        bib_key = str(bib_key).strip()

    if not title:
        raise BibTeXParseError(f"Missing required field 'title' in entry: {bib_key}")

    if not bib_key:
        raise BibTeXParseError("Missing required field 'ID' in BibTeX entry")

    # Extract optional fields (check both lowercase and title case)
    authors_raw = entry.get("author") or entry.get("Author") or entry.get("authors") or entry.get("Authors")
    year_str = entry.get("year", "") or entry.get("Year", "")
    url_str = entry.get("url", "") or entry.get("URL", "") or entry.get("Url", "")
    doi_str = entry.get("doi", "") or entry.get("DOI", "") or entry.get("Doi", "")
    
    # Handle authors - keep as list if already a list, convert to string otherwise
    if isinstance(authors_raw, list):
        authors = authors_raw
    elif isinstance(authors_raw, str):
        authors = authors_raw.strip() if authors_raw.strip() else []
    else:
        authors = []
    
    # Convert other fields to strings and strip
    if isinstance(year_str, str):
        year_str = year_str.strip()
    else:
        year_str = str(year_str) if year_str else ""
    
    if isinstance(url_str, str):
        url_str = url_str.strip()
    else:
        url_str = str(url_str) if url_str else ""
    
    if isinstance(doi_str, str):
        doi_str = doi_str.strip()
    else:
        doi_str = str(doi_str) if doi_str else ""

    # Parse year
    year = None
    if year_str:
        try:
            year = int(year_str)
            if year < 1900 or year > 2100:
                logger.warning(f"Year {year} is out of valid range (1900-2100), setting to None")
                year = None  # Set to None if out of range to pass validation
        except ValueError:
            logger.warning(f"Could not parse year '{year_str}', skipping")

    # Authors are already handled above - pass directly to model

    # Validate and parse URL - HttpUrl is strict, so we need to validate format
    url_value = None
    if url_str:
        # Basic URL validation - HttpUrl will do stricter validation
        if url_str.startswith(("http://", "https://")):
            url_value = url_str
        else:
            logger.warning(f"Invalid URL format '{url_str}', skipping")

    # Build BibTeXEntry
    try:
        bibtex_entry = BibTeXEntry(
            title=title,
            authors=authors,
            year=year,
            bib_key=bib_key,
            url=url_value,
            doi=doi_str if doi_str else None,
        )
        return bibtex_entry
    except Exception as e:
        raise BibTeXParseError(
            f"Error creating BibTeXEntry from entry {bib_key}: {e}"
        ) from e
