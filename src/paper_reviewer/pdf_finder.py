"""PDF file finder module."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def find_pdf_in_directory(directory: Path) -> Optional[Path]:
    """
    Find the single PDF file in a directory.

    Searches recursively in the directory and subdirectories.
    Returns the first `.pdf` file found, or None if none exists.

    Args:
        directory: Directory path to search for PDF files

    Returns:
        Path to the first PDF file found, or None if no PDF found

    Raises:
        PDFNotFoundError: If multiple PDFs found and strict mode is enabled
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return None

    if not directory.is_dir():
        logger.warning(f"Path is not a directory: {directory}")
        return None

    # Find all PDF files recursively (case-insensitive)
    pdf_files = []
    for pattern in ["*.pdf", "*.PDF", "*.Pdf"]:
        pdf_files.extend(directory.rglob(pattern))

    # Filter to only actual files (not directories)
    pdf_files = [f for f in pdf_files if f.is_file()]

    if not pdf_files:
        logger.debug(f"No PDF files found in directory: {directory}")
        return None

    if len(pdf_files) > 1:
        logger.warning(
            f"Multiple PDF files found in directory {directory}: {len(pdf_files)} files. "
            f"Using first one: {pdf_files[0]}"
        )

    # Return the first PDF found
    pdf_path = pdf_files[0]
    logger.debug(f"Found PDF file: {pdf_path}")
    return pdf_path
