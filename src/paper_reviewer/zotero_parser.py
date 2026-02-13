"""Zotero BibTeX file parser module for extracting PDF paths from file fields."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

from .bibtex_parser import extract_metadata
from .errors import BibTeXParseError, PDFNotFoundError
from .models import BibTeXEntry, PaperPair

logger = logging.getLogger(__name__)


def extract_pdf_path_from_file_field(file_field: str) -> Optional[Path]:
    """
    Extract PDF path from Zotero file field format.

    Zotero file field format: {PDF:<escaped_path>:application/pdf}
    Example: {PDF:C\:\\Users\\haoyan.li\\Zotero\\storage\\F8XWENS7\\file.pdf:application/pdf}

    Args:
        file_field: The file field value from BibTeX entry

    Returns:
        Path object if successfully extracted and file exists, None otherwise
    """
    if not file_field or not isinstance(file_field, str):
        return None

    # Remove outer braces if present
    file_field = file_field.strip()
    if file_field.startswith("{") and file_field.endswith("}"):
        file_field = file_field[1:-1]

    # Match pattern: PDF:<path>:application/pdf
    # Handle both Windows (C\:\\...) and Unix (/home/...) paths
    pattern = r"^PDF:(.+?):application/pdf$"
    match = re.match(pattern, file_field)

    if not match:
        logger.debug(f"File field does not match Zotero PDF format: {file_field[:50]}...")
        return None

    path_str = match.group(1)

    # Handle path unescaping
    # Zotero exports Windows paths with escaped backslashes: C\:\\Users\\...
    # When bibtexparser processes it, backslashes may be escaped or normalized
    # Path() is robust and handles both forward and backslashes on Windows
    
    # Normalize Windows paths
    # Handle escaped colon: C\: -> C: (for patterns like C\:Users)
    path_str = re.sub(r"\\([A-Za-z]):", r"\1:", path_str)
    
    # Normalize multiple consecutive backslashes to single backslash
    # This handles cases like C:\\Users (double backslash) or C\:\\Users (escaped)
    # Replace any sequence of backslashes with a single backslash
    path_str = re.sub(r"\\+", r"\\", path_str)
    
    # Path() will handle further normalization and works with both / and \ on Windows

    try:
        pdf_path = Path(path_str)
        
        # Validate path exists
        if not pdf_path.exists():
            logger.warning(f"PDF path from file field does not exist: {pdf_path}")
            return None
        
        if not pdf_path.is_file():
            logger.warning(f"PDF path from file field is not a file: {pdf_path}")
            return None
        
        return pdf_path
    except Exception as e:
        logger.debug(f"Error converting file field to Path: {e}")
        return None


def parse_zotero_bib_file(bib_path: Path) -> List[PaperPair]:
    """
    Parse a Zotero-exported BibTeX file and extract PDF paths from file fields.

    This function reads a BibTeX file, extracts metadata using the existing parser,
    and pairs each entry with its PDF path from the 'file' field.

    Args:
        bib_path: Path to the Zotero-exported `.bib` file

    Returns:
        List of PaperPair objects, one for each BibTeX entry with a valid PDF path

    Raises:
        BibTeXParseError: If the BibTeX file cannot be parsed
        FileNotFoundError: If the BibTeX file does not exist
    """
    if not bib_path.exists():
        raise FileNotFoundError(f"BibTeX file not found: {bib_path}")

    if not bib_path.is_file():
        raise BibTeXParseError(f"Path is not a file: {bib_path}", str(bib_path))

    try:
        # Configure parser to handle unicode and preserve all fields
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        parser.ignore_nonstandard_types = False
        parser.homogenise_fields = True
        parser.expect_multiple_parse = False

        # Try different encodings
        encodings = ["utf-8", "latin-1", "cp1252"]
        entries = None
        last_error = None

        for encoding in encodings:
            try:
                with open(bib_path, "r", encoding=encoding) as f:
                    file_content = f.read()

                bib_database = bibtexparser.loads(file_content, parser=parser)
                entries = bib_database.entries

                # Deduplicate entries by ID
                seen_ids = set()
                unique_entries = []
                for entry in entries:
                    entry_id = entry.get("id") or entry.get("ID") or entry.get("key")
                    if entry_id and entry_id not in seen_ids:
                        seen_ids.add(entry_id)
                        unique_entries.append(entry)
                    elif not entry_id:
                        unique_entries.append(entry)

                entries = unique_entries
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

        # Process entries and create PaperPair objects
        paper_pairs = []
        skipped_count = 0

        for entry in entries:
            try:
                # Ensure entry has ID field
                if "id" not in entry:
                    if "ID" in entry:
                        entry["id"] = entry["ID"]
                    elif hasattr(entry, "key"):
                        entry["id"] = entry.key

                # Extract metadata using existing function
                bibtex_entry = extract_metadata(entry)

                # Extract file field (check both lowercase and title case)
                file_field = entry.get("file") or entry.get("File") or entry.get("FILE")

                if not file_field:
                    bib_key = bibtex_entry.bib_key
                    logger.warning(
                        f"Entry '{bib_key}' does not have a 'file' field. Skipping."
                    )
                    skipped_count += 1
                    continue

                # Extract PDF path from file field
                pdf_path = extract_pdf_path_from_file_field(file_field)

                if pdf_path is None:
                    bib_key = bibtex_entry.bib_key
                    logger.warning(
                        f"Could not extract valid PDF path from file field for entry '{bib_key}'. "
                        f"File field: {file_field[:100]}..."
                    )
                    skipped_count += 1
                    continue

                # Create PaperPair
                paper_pair = PaperPair(metadata=bibtex_entry, pdf_path=pdf_path)
                paper_pairs.append(paper_pair)
                logger.debug(
                    f"Created PaperPair for '{bibtex_entry.bib_key}' with PDF: {pdf_path}"
                )

            except BibTeXParseError:
                # Re-raise BibTeX parsing errors
                raise
            except Exception as e:
                entry_id = entry.get("ID") or entry.get("id") or entry.get("key", "unknown")
                logger.warning(
                    f"Skipping entry '{entry_id}' due to error: {e}", exc_info=True
                )
                skipped_count += 1
                continue

        if not paper_pairs:
            if skipped_count > 0:
                raise BibTeXParseError(
                    f"No valid entries with PDF paths found in BibTeX file: {bib_path}. "
                    f"Skipped {skipped_count} entries.",
                    str(bib_path),
                )
            else:
                raise BibTeXParseError(
                    f"No entries found in BibTeX file: {bib_path}", str(bib_path)
                )

        logger.info(
            f"Successfully parsed {len(paper_pairs)} paper(s) from {bib_path}. "
            f"Skipped {skipped_count} entry/entries."
        )

        return paper_pairs

    except BibTeXParseError:
        raise
    except FileNotFoundError:
        raise
    except Exception as e:
        raise BibTeXParseError(
            f"Error parsing Zotero BibTeX file {bib_path}: {e}", str(bib_path)
        ) from e
