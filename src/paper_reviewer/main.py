"""Main CLI entry point for paper reviewer."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Union

from .config import load_config
from .errors import GeminiAPIError, NotionAPIError, PaperReviewerError
from .gemini_client import analyze_paper
from .logger import get_logger, setup_logging
from .models import Config as ConfigModel, PaperPair
from .notion_client import create_paper_page
from .notion_converter import transform_to_notion_blocks
from .notion_properties import build_notion_properties
from .scanner import scan_directory
from .ui import (
    create_progress_tracker,
    display_error,
    display_info,
    display_papers_table,
    display_success,
)
from .zotero_parser import parse_zotero_bib_file

logger = get_logger(__name__)


def process_single_paper(paper: PaperPair, config: ConfigModel) -> bool:
    """
    Process a single paper through the full pipeline.

    Pipeline:
    1. Analyze PDF with Gemini
    2. Convert review to Notion blocks
    3. Build Notion properties from metadata
    4. Create Notion page

    Args:
        paper: PaperPair object containing metadata and PDF path
        config: Configuration object with API keys and database ID

    Returns:
        True if processing succeeded, False otherwise
    """
    bib_key = paper.metadata.bib_key
    logger.info(f"Processing paper: {bib_key}")

    try:
        # Step 1: Analyze PDF with Gemini
        logger.debug(f"Analyzing PDF: {paper.pdf_path}")
        review_json = analyze_paper(paper.pdf_path, config.gemini_api_key)
        logger.debug(f"Received review data with {len(review_json)} fields")

        # Step 2: Convert review to Notion blocks
        logger.debug("Converting review to Notion blocks")
        blocks = transform_to_notion_blocks(review_json)
        logger.debug(f"Created {len(blocks)} Notion blocks")

        # Step 3: Build Notion properties from metadata
        logger.debug("Building Notion properties")
        properties = build_notion_properties(paper.metadata)

        # Step 4: Create Notion page
        logger.debug("Creating Notion page")
        page_id = create_paper_page(
            config.notion_token,
            config.notion_database_id,
            properties,
            blocks,
        )
        logger.info(f"Successfully created Notion page: {page_id}")

        return True

    except GeminiAPIError as e:
        logger.error(f"Gemini API error processing {bib_key}: {e.message}", exc_info=True)
        display_error(f"Failed to analyze {bib_key}: {e.message}")
        return False

    except NotionAPIError as e:
        logger.error(f"Notion API error processing {bib_key}: {e.message}", exc_info=True)
        display_error(f"Failed to create Notion page for {bib_key}: {e.message}")
        return False

    except PaperReviewerError as e:
        logger.error(f"Paper reviewer error processing {bib_key}: {e.message}", exc_info=True)
        display_error(f"Error processing {bib_key}: {e.message}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error processing {bib_key}: {str(e)}", exc_info=True)
        display_error(f"Unexpected error processing {bib_key}: {str(e)}")
        return False


def main(directory: Optional[Union[Path, str]] = None) -> int:
    """
    Main CLI entry point for paper reviewer.

    Args:
        directory: Optional directory path to scan. If None, uses current directory.
                   Can be a Path object or string.

    Returns:
        Exit code: 0 for success, 1 for errors
    """
    # Setup logging first
    setup_logging()

    try:
        # Parse command-line arguments if directory not provided
        zotero_bib_path = None
        if directory is None:
            parser = argparse.ArgumentParser(
                description="Automatically review research papers and sync to Notion"
            )
            parser.add_argument(
                "directory",
                nargs="?",
                default=".",
                help="Directory to scan for papers (default: current directory)",
            )
            parser.add_argument(
                "--zotero-bib",
                "-z",
                dest="zotero_bib",
                help="Path to Zotero-exported BibTeX file (alternative to directory scanning)",
            )
            args = parser.parse_args()
            directory = args.directory
            zotero_bib_path = args.zotero_bib

        # Load configuration
        try:
            config = load_config()
            logger.info("Configuration loaded successfully")
        except (ValueError, FileNotFoundError) as e:
            display_error(f"Configuration error: {str(e)}")
            logger.error(f"Configuration error: {str(e)}")
            return 1

        # Determine workflow: Zotero BibTeX file or directory scanning
        if zotero_bib_path:
            # Zotero BibTeX workflow
            bib_path = Path(zotero_bib_path).resolve()
            
            # Validate BibTeX file exists
            if not bib_path.exists():
                display_error(f"BibTeX file does not exist: {bib_path}")
                logger.error(f"BibTeX file does not exist: {bib_path}")
                return 1

            if not bib_path.is_file():
                display_error(f"Path is not a file: {bib_path}")
                logger.error(f"Path is not a file: {bib_path}")
                return 1

            logger.info(f"Starting paper reviewer for Zotero BibTeX file: {bib_path}")
            display_info(f"Parsing Zotero BibTeX file: {bib_path}")
            
            try:
                papers = parse_zotero_bib_file(bib_path)
            except Exception as e:
                display_error(f"Failed to parse Zotero BibTeX file: {str(e)}")
                logger.error(f"Failed to parse Zotero BibTeX file: {str(e)}", exc_info=True)
                return 1
        else:
            # Existing directory scanning workflow (unchanged)
            # Convert to Path object
            if isinstance(directory, Path):
                directory_path = directory.resolve()
            else:
                directory_path = Path(directory).resolve()

            # Validate directory exists
            if not directory_path.exists():
                display_error(f"Directory does not exist: {directory_path}")
                logger.error(f"Directory does not exist: {directory_path}")
                return 1

            if not directory_path.is_dir():
                display_error(f"Path is not a directory: {directory_path}")
                logger.error(f"Path is not a directory: {directory_path}")
                return 1

            logger.info(f"Starting paper reviewer for directory: {directory_path}")

            # Scan directory for papers
            display_info(f"Scanning directory: {directory_path}")
            logger.info(f"Scanning directory: {directory_path}")
            try:
                papers = scan_directory(directory_path)
            except Exception as e:
                display_error(f"Failed to scan directory: {str(e)}")
                logger.error(f"Failed to scan directory: {str(e)}", exc_info=True)
                return 1

        if not papers:
            display_info("No papers found. Exiting.")
            logger.info("No papers found in directory")
            return 0

        # Display papers table
        logger.info(f"Found {len(papers)} paper(s) to process")
        display_papers_table(papers)

        # Process papers with progress tracking
        success_count = 0
        failure_count = 0

        with create_progress_tracker(len(papers)) as progress:
            task_id = progress.add_task(
                "[cyan]Processing papers...",
                total=len(papers),
            )

            for paper in papers:
                bib_key = paper.metadata.bib_key
                progress.update(
                    task_id,
                    description=f"[cyan]Processing {bib_key}...",
                )

                # Process paper
                if process_single_paper(paper, config):
                    success_count += 1
                    progress.console.print(f"[bold green]✔[/bold green] Completed: {bib_key}")
                else:
                    failure_count += 1

                # Advance progress
                progress.update(task_id, advance=1)

        # Display summary
        logger.info(f"Processing complete: {success_count} succeeded, {failure_count} failed")
        if success_count > 0:
            display_success(f"Successfully processed {success_count} paper(s)")
        if failure_count > 0:
            display_error(f"Failed to process {failure_count} paper(s)")

        # Return appropriate exit code
        return 0 if failure_count == 0 else 1

    except KeyboardInterrupt:
        display_info("\nInterrupted by user. Exiting...")
        logger.info("Interrupted by user")
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in main: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
