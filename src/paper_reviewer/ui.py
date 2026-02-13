"""Rich UI components for paper reviewer CLI."""

from typing import List

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from .models import PaperPair

# Singleton console instance for consistent output
_console = Console()


def display_papers_table(papers: List[PaperPair]) -> None:
    """
    Display a Rich table showing discovered papers.

    Args:
        papers: List of PaperPair objects to display
    """
    if not papers:
        _console.print("[yellow]No papers found to display.[/yellow]")
        return

    table = Table(title="Papers to Process", show_header=True, header_style="bold magenta")
    table.add_column("BibTeX Key", style="cyan", no_wrap=True)
    table.add_column("Title", style="white", max_width=50)
    table.add_column("PDF Path", style="green", max_width=40)
    table.add_column("Authors", style="yellow", max_width=30)

    for paper in papers:
        # Truncate title if too long
        title = paper.metadata.title
        if len(title) > 50:
            title = title[:47] + "..."

        # Format PDF path (show relative path if possible)
        pdf_path = str(paper.pdf_path)
        if len(pdf_path) > 40:
            pdf_path = "..." + pdf_path[-37:]

        # Format authors (show first 2, then "...")
        authors = paper.metadata.authors
        if len(authors) > 2:
            authors_str = ", ".join(authors[:2]) + f", ... ({len(authors) - 2} more)"
        elif authors:
            authors_str = ", ".join(authors)
        else:
            authors_str = "N/A"

        table.add_row(
            paper.metadata.bib_key,
            title,
            pdf_path,
            authors_str,
        )

    _console.print(table)


def create_progress_tracker(total: int) -> Progress:
    """
    Create a Rich Progress instance for tracking paper processing.

    Args:
        total: Total number of papers to process

    Returns:
        Progress instance configured with appropriate columns
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=_console,
    )


def display_success(message: str) -> None:
    """
    Display a success message with green styling.

    Args:
        message: Success message to display
    """
    _console.print(f"[bold green]✔[/bold green] {message}")


def display_error(message: str) -> None:
    """
    Display an error message with red styling.

    Args:
        message: Error message to display
    """
    _console.print(f"[bold red]✘[/bold red] {message}")


def display_info(message: str) -> None:
    """
    Display an info message with blue styling.

    Args:
        message: Info message to display
    """
    _console.print(f"[bold blue]ℹ[/bold blue] {message}")
