"""Directory scanner module for finding and pairing BibTeX and PDF files."""

import logging
from pathlib import Path
from typing import List, Optional

from .bibtex_parser import parse_bibtex_file
from .errors import BibTeXParseError
from .models import BibTeXEntry, PaperPair
from .pdf_finder import find_pdf_in_directory

logger = logging.getLogger(__name__)


def scan_directory(directory: Path) -> List[PaperPair]:
    """
    Scan a directory for BibTeX and PDF files, pairing them together.

    Each directory should contain one `.bib` file and one `.pdf` file.
    The function can operate in two modes:
    - Single directory mode: Process the given directory if it contains both files
    - Recursive mode: Process all subdirectories that contain both files

    Args:
        directory: Root directory to scan

    Returns:
        List of PaperPair objects, one for each BibTeX entry paired with its PDF

    Raises:
        FileNotFoundError: If the directory does not exist
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")

    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    paper_pairs = []

    # Check if the root directory itself contains a .bib and .pdf
    bib_file = _find_bibtex_file(directory)
    pdf_file = find_pdf_in_directory(directory)

    if bib_file and pdf_file:
        # Single directory mode: process the root directory
        logger.info(f"Processing directory: {directory}")
        pairs = scan_single_directory(directory)
        paper_pairs.extend(pairs)
    else:
        # Recursive mode: process subdirectories
        logger.info(f"Scanning subdirectories in: {directory}")
        for subdir in sorted(directory.iterdir()):
            if not subdir.is_dir():
                continue

            try:
                pairs = scan_single_directory(subdir)
                paper_pairs.extend(pairs)
            except Exception as e:
                logger.warning(f"Skipping directory {subdir} due to error: {e}")
                continue

    logger.info(f"Found {len(paper_pairs)} paper pairs in {directory}")
    return paper_pairs


def scan_single_directory(directory: Path) -> List[PaperPair]:
    """
    Process a single directory that contains one `.bib` and one `.pdf` file.

    Args:
        directory: Directory path containing the BibTeX and PDF files

    Returns:
        List of PaperPair objects, one for each BibTeX entry paired with the PDF

    Raises:
        BibTeXParseError: If BibTeX file cannot be parsed
    """
    # Find the BibTeX file
    bib_file = _find_bibtex_file(directory)
    if not bib_file:
        logger.debug(f"No BibTeX file found in directory: {directory}")
        return []

    # Find the PDF file
    pdf_file = find_pdf_in_directory(directory)
    if not pdf_file:
        logger.warning(f"No PDF file found in directory: {directory}")
        return []

    # Parse BibTeX entries
    try:
        bibtex_entries = parse_bibtex_file(bib_file)
    except BibTeXParseError as e:
        logger.error(f"Failed to parse BibTeX file {bib_file}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing BibTeX file {bib_file}: {e}")
        raise BibTeXParseError(f"Error parsing BibTeX file: {e}", str(bib_file)) from e

    if not bibtex_entries:
        logger.warning(f"No entries found in BibTeX file: {bib_file}")
        return []

    # Create PaperPair objects for each BibTeX entry
    paper_pairs = []
    for entry in bibtex_entries:
        try:
            pair = _create_paper_pair(entry, pdf_file)
            paper_pairs.append(pair)
        except Exception as e:
            logger.warning(
                f"Skipping entry {entry.bib_key} due to error creating pair: {e}"
            )
            continue

    logger.info(
        f"Created {len(paper_pairs)} paper pairs from {len(bibtex_entries)} "
        f"BibTeX entries in {directory}"
    )
    return paper_pairs


def _find_bibtex_file(directory: Path) -> Optional[Path]:
    """
    Find the single BibTeX file in a directory.

    Searches recursively in the directory and subdirectories.
    Returns the first `.bib` file found, or None if none exists.

    Args:
        directory: Directory path to search for BibTeX files

    Returns:
        Path to the first BibTeX file found, or None if no BibTeX file found
    """
    if not directory.exists() or not directory.is_dir():
        return None

    # Find all BibTeX files recursively (case-insensitive)
    bib_files = []
    for pattern in ["*.bib", "*.BIB", "*.Bib"]:
        bib_files.extend(directory.rglob(pattern))

    # Filter to only actual files (not directories)
    bib_files = [f for f in bib_files if f.is_file()]

    if not bib_files:
        return None

    if len(bib_files) > 1:
        logger.warning(
            f"Multiple BibTeX files found in directory {directory}: {len(bib_files)} files. "
            f"Using first one: {bib_files[0]}"
        )

    return bib_files[0]


def _create_paper_pair(entry: BibTeXEntry, pdf_path: Path) -> PaperPair:
    """
    Create a PaperPair from a BibTeXEntry and PDF path.

    Args:
        entry: BibTeXEntry object with metadata
        pdf_path: Path to the PDF file

    Returns:
        PaperPair object

    Raises:
        ValueError: If PDF file does not exist (handled by PaperPair model)
    """
    return PaperPair(metadata=entry, pdf_path=pdf_path)
