# API Reference

Complete API reference for programmatic usage of `paper-reviewer-cli`.

## Overview

`paper-reviewer-cli` can be used both as a command-line tool and as a Python library. This document describes the programmatic API for developers who want to integrate paper reviewing functionality into their own applications.

## Installation

Install the package to use it as a library:

```bash
pip install paper-reviewer-cli
```

Or install from source:

```bash
git clone https://github.com/yourusername/paper-reviewer-cli.git
cd paper-reviewer-cli
pip install -e .
```

## Quick Start

```python
from pathlib import Path
from paper_reviewer import scan_directory, process_single_paper, load_config

# Load configuration
config = load_config()

# Scan directory for papers
papers = scan_directory(Path("./papers"))

# Process each paper
for paper in papers:
    success = process_single_paper(paper, config)
    print(f"Processed {paper.metadata.bib_key}: {success}")
```

## Core API Reference

### Main Entry Point

#### `paper_reviewer.main.main()`

Main CLI entry point that can also be called programmatically.

```python
def main(directory: Optional[Union[Path, str]] = None) -> int
```

**Parameters**:
- `directory` (Optional[Union[Path, str]]): Directory path to scan. If `None`, uses current directory.

**Returns**:
- `int`: Exit code (0 for success, 1 for errors, 130 for interruption)

**Example**:
```python
from paper_reviewer.main import main

exit_code = main("/path/to/papers")
```

#### `paper_reviewer.main.process_single_paper()`

Process a single paper through the complete pipeline.

```python
def process_single_paper(paper: PaperPair, config: ConfigModel) -> bool
```

**Parameters**:
- `paper` (PaperPair): PaperPair object containing metadata and PDF path
- `config` (ConfigModel): Configuration object with API keys and database ID

**Returns**:
- `bool`: `True` if processing succeeded, `False` otherwise

**Pipeline Steps**:
1. Analyze PDF with Gemini
2. Convert review to Notion blocks
3. Build Notion properties from metadata
4. Create Notion page

**Example**:
```python
from paper_reviewer.main import process_single_paper
from paper_reviewer.models import PaperPair, BibTeXEntry
from pathlib import Path

# Create a paper pair
metadata = BibTeXEntry(
    title="Example Paper",
    authors=["John Doe"],
    year=2024,
    bib_key="example2024"
)
paper = PaperPair(
    metadata=metadata,
    pdf_path=Path("./paper.pdf")
)

# Process it
config = load_config()
success = process_single_paper(paper, config)
```

### Configuration

#### `paper_reviewer.config.load_config()`

Load configuration from environment variables or `.env` file.

```python
def load_config(env_file: Optional[Path] = None) -> ConfigModel
```

**Parameters**:
- `env_file` (Optional[Path]): Optional path to `.env` file. If `None`, searches for `.env` in:
  - Current working directory
  - Project root (parent of `src/`)

**Returns**:
- `ConfigModel`: Validated configuration model instance

**Raises**:
- `FileNotFoundError`: If `.env` file is specified but doesn't exist
- `ValueError`: If required environment variables are missing or invalid

**Example**:
```python
from paper_reviewer.config import load_config
from pathlib import Path

# Load from default location
config = load_config()

# Load from specific file
config = load_config(Path("/path/to/.env"))
```

#### `paper_reviewer.config.Config`

Pydantic Settings class for environment variables.

**Attributes**:
- `gemini_api_key` (str): Google AI API key
- `notion_token` (str): Notion integration token
- `notion_database_id` (str): Notion database ID

**Methods**:
- `to_model() -> ConfigModel`: Convert to Config model for validation

### Directory Scanning

#### `paper_reviewer.scanner.scan_directory()`

Scan a directory for BibTeX and PDF files, pairing them together.

```python
def scan_directory(directory: Path) -> List[PaperPair]
```

**Parameters**:
- `directory` (Path): Root directory to scan

**Returns**:
- `List[PaperPair]`: List of PaperPair objects, one for each BibTeX entry paired with its PDF

**Raises**:
- `FileNotFoundError`: If the directory does not exist

**Scanning Modes**:
- **Single Directory Mode**: When root directory directly contains both `.bib` and `.pdf` files
- **Recursive Mode**: When scanning subdirectories that contain both files

**Example**:
```python
from pathlib import Path
from paper_reviewer.scanner import scan_directory

papers = scan_directory(Path("./papers"))
for paper in papers:
    print(f"Found: {paper.metadata.title}")
```

#### `paper_reviewer.scanner.scan_single_directory()`

Process a single directory that contains one `.bib` and one `.pdf` file.

```python
def scan_single_directory(directory: Path) -> List[PaperPair]
```

**Parameters**:
- `directory` (Path): Directory path containing the BibTeX and PDF files

**Returns**:
- `List[PaperPair]`: List of PaperPair objects

**Raises**:
- `BibTeXParseError`: If BibTeX file cannot be parsed

### BibTeX Parsing

#### `paper_reviewer.bibtex_parser.parse_bibtex_file()`

Parse a BibTeX file and extract structured metadata.

```python
def parse_bibtex_file(bib_path: Path) -> List[BibTeXEntry]
```

**Parameters**:
- `bib_path` (Path): Path to the `.bib` file

**Returns**:
- `List[BibTeXEntry]`: List of BibTeXEntry objects parsed from the file

**Raises**:
- `BibTeXParseError`: If the file cannot be parsed or is malformed
- `FileNotFoundError`: If the file does not exist

**Example**:
```python
from pathlib import Path
from paper_reviewer.bibtex_parser import parse_bibtex_file

entries = parse_bibtex_file(Path("./paper.bib"))
for entry in entries:
    print(f"{entry.bib_key}: {entry.title}")
```

#### `paper_reviewer.bibtex_parser.extract_metadata()`

Convert a raw bibtexparser entry dictionary to a BibTeXEntry model.

```python
def extract_metadata(entry: Dict) -> BibTeXEntry
```

**Parameters**:
- `entry` (Dict): Raw entry dictionary from bibtexparser

**Returns**:
- `BibTeXEntry`: BibTeXEntry object with parsed metadata

**Raises**:
- `BibTeXParseError`: If required fields are missing

### PDF Finding

#### `paper_reviewer.pdf_finder.find_pdf_in_directory()`

Find the single PDF file in a directory.

```python
def find_pdf_in_directory(directory: Path) -> Optional[Path]
```

**Parameters**:
- `directory` (Path): Directory path to search for PDF files

**Returns**:
- `Optional[Path]`: Path to the first PDF file found, or `None` if no PDF found

**Example**:
```python
from pathlib import Path
from paper_reviewer.pdf_finder import find_pdf_in_directory

pdf_path = find_pdf_in_directory(Path("./paper"))
if pdf_path:
    print(f"Found PDF: {pdf_path}")
```

### Zotero BibTeX Parsing

#### `paper_reviewer.zotero_parser.parse_zotero_bib_file()`

Parse a Zotero-exported BibTeX file and extract PDF paths from `file` fields.

```python
def parse_zotero_bib_file(bib_path: Path) -> List[PaperPair]
```

**Parameters**:
- `bib_path` (Path): Path to the Zotero-exported `.bib` file

**Returns**:
- `List[PaperPair]`: List of PaperPair objects, one for each BibTeX entry with a valid PDF path

**Raises**:
- `BibTeXParseError`: If the BibTeX file cannot be parsed
- `FileNotFoundError`: If the BibTeX file does not exist

**Example**:
```python
from pathlib import Path
from paper_reviewer.zotero_parser import parse_zotero_bib_file

# Parse Zotero BibTeX file
paper_pairs = parse_zotero_bib_file(Path("zotero_export.bib"))

# Process each paper
for paper_pair in paper_pairs:
    print(f"Found: {paper_pair.metadata.title}")
    print(f"PDF: {paper_pair.pdf_path}")
```

**Notes**:
- Entries without a `file` field are automatically skipped
- Entries with invalid or non-existent PDF paths are skipped
- Supports Windows paths with escaped backslashes (Zotero format: `C\:\\Users\\...`)
- Supports Unix paths

#### `paper_reviewer.zotero_parser.extract_pdf_path_from_file_field()`

Extract PDF path from Zotero `file` field format.

```python
def extract_pdf_path_from_file_field(file_field: str) -> Optional[Path]
```

**Parameters**:
- `file_field` (str): The file field value from BibTeX entry (format: `{PDF:<path>:application/pdf}`)

**Returns**:
- `Optional[Path]`: Path object if successfully extracted and file exists, `None` otherwise

**Example**:
```python
from paper_reviewer.zotero_parser import extract_pdf_path_from_file_field

file_field = "{PDF:C\\:\\Users\\paper.pdf:application/pdf}"
pdf_path = extract_pdf_path_from_file_field(file_field)
if pdf_path:
    print(f"PDF path: {pdf_path}")
```

### Gemini Integration

#### `paper_reviewer.gemini_client.analyze_paper()`

Analyze a research paper PDF using Gemini API and return structured review.

```python
def analyze_paper(pdf_path: Path, api_key: str) -> Dict[str, str]
```

**Parameters**:
- `pdf_path` (Path): Path to the PDF file
- `api_key` (str): Google AI API key

**Returns**:
- `Dict[str, str]`: Dictionary with 6 fields:
  - `summary`: Overview of the paper
  - `novelty`: Novelty and impact compared to previous work
  - `methodology`: Core technical methodology
  - `validation`: Validation and experimental results
  - `discussion`: Discussion and limitations
  - `next_steps`: Next steps and related papers

**Raises**:
- `GeminiAPIError`: If analysis fails at any step
- `FileNotFoundError`: If PDF file doesn't exist

**Example**:
```python
from pathlib import Path
from paper_reviewer.gemini_client import analyze_paper

review_data = analyze_paper(Path("./paper.pdf"), "your-api-key")
print(review_data["summary"])
```

#### `paper_reviewer.gemini_client.upload_pdf()`

Upload a PDF file to Gemini File API.

```python
def upload_pdf(pdf_path: Path, api_key: str, client: object = None) -> object
```

**Parameters**:
- `pdf_path` (Path): Path to the PDF file
- `api_key` (str): Google AI API key
- `client` (object, optional): Optional genai.Client instance (creates new one if not provided)

**Returns**:
- `object`: File handle object with `.name` and `.state` attributes

**Raises**:
- `FileNotFoundError`: If PDF file doesn't exist
- `GeminiAPIError`: If upload fails

#### `paper_reviewer.gemini_client.wait_for_file_processing()`

Wait for file to finish processing in Gemini API.

```python
def wait_for_file_processing(
    file_handle: object, 
    client: object, 
    timeout: int = 300, 
    poll_interval: int = 2
) -> bool
```

**Parameters**:
- `file_handle` (object): File handle object from `upload_pdf()`
- `client` (object): genai.Client instance
- `timeout` (int): Maximum time to wait in seconds (default: 300)
- `poll_interval` (int): Time between polls in seconds (default: 2)

**Returns**:
- `bool`: `True` if file is ready (ACTIVE), `False` if timeout

**Raises**:
- `GeminiAPIError`: If file processing fails

#### `paper_reviewer.gemini_client.parse_gemini_response()`

Parse Gemini API response and extract JSON review data.

```python
def parse_gemini_response(response: object) -> Dict[str, str]
```

**Parameters**:
- `response` (object): Response object from `generate_content()`

**Returns**:
- `Dict[str, str]`: Dictionary with 6 fields: summary, novelty, methodology, validation, discussion, next_steps

**Raises**:
- `GeminiAPIError`: If JSON is invalid or missing required fields

### Notion Integration

#### `paper_reviewer.notion_client.create_paper_page()`

Create a complete paper page in Notion database.

```python
def create_paper_page(
    token: str, 
    db_id: str, 
    properties: Dict, 
    blocks: List[Dict]
) -> str
```

**Parameters**:
- `token` (str): Notion integration token
- `db_id` (str): Notion database ID (with or without dashes)
- `properties` (Dict): Page properties dict (from `build_notion_properties`)
- `blocks` (List[Dict]): List of block dicts (from `transform_to_notion_blocks`)

**Returns**:
- `str`: Created page ID

**Raises**:
- `NotionAPIError`: If page creation fails

**Example**:
```python
from paper_reviewer.notion_client import create_paper_page
from paper_reviewer.notion_properties import build_notion_properties
from paper_reviewer.notion_converter import transform_to_notion_blocks

properties = build_notion_properties(metadata)
blocks = transform_to_notion_blocks(review_data)
page_id = create_paper_page(token, db_id, properties, blocks)
```

### Notion Conversion

#### `paper_reviewer.notion_converter.transform_to_notion_blocks()`

Convert Gemini's JSON review output into Notion block structure.

```python
def transform_to_notion_blocks(review_json: Dict[str, str]) -> List[Dict]
```

**Parameters**:
- `review_json` (Dict[str, str]): Dictionary with 6 fields: summary, novelty, methodology, validation, discussion, next_steps

**Returns**:
- `List[Dict]`: List of Notion block objects ready for API creation

**Example**:
```python
from paper_reviewer.notion_converter import transform_to_notion_blocks

review_data = {
    "summary": "Paper overview...",
    "novelty": "New approach...",
    # ... other fields
}
blocks = transform_to_notion_blocks(review_data)
```

#### `paper_reviewer.notion_converter.create_heading_block()`

Create a Notion heading_2 block for page creation.

```python
def create_heading_block(text: str) -> Dict
```

**Parameters**:
- `text` (str): Heading text

**Returns**:
- `Dict`: Notion block dict with heading_2 type

#### `paper_reviewer.notion_converter.create_paragraph_block()`

Create a Notion paragraph block.

```python
def create_paragraph_block(text: str) -> Dict
```

**Parameters**:
- `text` (str): Paragraph text (will be truncated to 2000 characters)

**Returns**:
- `Dict`: Notion block dict with paragraph type

#### `paper_reviewer.notion_converter.create_bullet_block()`

Create a Notion bulleted_list_item block.

```python
def create_bullet_block(text: str) -> Dict
```

**Parameters**:
- `text` (str): Bullet item text (will be truncated to 2000 characters)

**Returns**:
- `Dict`: Notion block dict with bulleted_list_item type

#### `paper_reviewer.notion_converter.split_content_smartly()`

Intelligently split content into list items.

```python
def split_content_smartly(content: str) -> List[str]
```

**Parameters**:
- `content` (str): Content string that may contain list items

**Returns**:
- `List[str]`: List of strings, each representing a content item

**Features**:
- Detects markdown-style bullet points (`- `, `* `)
- Handles newline-separated items
- Returns single-item list for paragraphs if no clear list structure

### Notion Properties

#### `paper_reviewer.notion_properties.build_notion_properties()`

Build Notion page properties from BibTeXEntry metadata.

```python
def build_notion_properties(metadata: BibTeXEntry) -> Dict
```

**Parameters**:
- `metadata` (BibTeXEntry): BibTeXEntry object with paper metadata

**Returns**:
- `Dict`: Dictionary compatible with Notion API properties format

**Property Mapping**:
- `title` → `Name` (title property)
- `authors` → `Authors` (multi_select property)
- `year` → `Year` (number property)
- `bib_key` → `BibTeX Key` (rich_text property)
- `url` or `doi` → `URL/DOI` (url property, prefers url over doi)

**Example**:
```python
from paper_reviewer.notion_properties import build_notion_properties

properties = build_notion_properties(bibtex_entry)
```

#### `paper_reviewer.notion_properties.format_authors()`

Convert list of author strings to Notion multi_select format.

```python
def format_authors(authors: List[str]) -> List[Dict]
```

**Parameters**:
- `authors` (List[str]): List of author name strings

**Returns**:
- `List[Dict]`: List of dicts with "name" keys for Notion multi_select

#### `paper_reviewer.notion_properties.extract_url_or_doi()`

Extract URL or DOI from BibTeXEntry, preferring URL over DOI.

```python
def extract_url_or_doi(metadata: BibTeXEntry) -> Optional[str]
```

**Parameters**:
- `metadata` (BibTeXEntry): BibTeXEntry object

**Returns**:
- `Optional[str]`: URL string if available, otherwise DOI string, or `None` if neither exists

### Data Models

#### `paper_reviewer.models.BibTeXEntry`

Paper metadata model.

**Attributes**:
- `title` (str): Paper title (required)
- `authors` (List[str]): List of author names
- `year` (Optional[int]): Publication year (1900-2100)
- `bib_key` (str): BibTeX entry ID/key (required)
- `url` (Optional[HttpUrl]): Paper URL
- `doi` (Optional[str]): Digital Object Identifier

**Example**:
```python
from paper_reviewer.models import BibTeXEntry

entry = BibTeXEntry(
    title="Example Paper",
    authors=["John Doe", "Jane Smith"],
    year=2024,
    bib_key="example2024",
    url="https://example.com/paper"
)
```

#### `paper_reviewer.models.PaperPair`

Pair of BibTeX metadata and PDF file path.

**Attributes**:
- `metadata` (BibTeXEntry): BibTeX entry metadata
- `pdf_path` (Path): Path to PDF file (must exist)

**Example**:
```python
from paper_reviewer.models import PaperPair, BibTeXEntry
from pathlib import Path

pair = PaperPair(
    metadata=entry,
    pdf_path=Path("./paper.pdf")
)
```

#### `paper_reviewer.models.ReviewData`

Structured review data from Gemini analysis.

**Attributes**:
- `summary` (str): Overview of the paper
- `novelty` (str): Novelty and impact compared to previous work
- `methodology` (str): Core technical methodology
- `validation` (str): Validation and experimental results
- `discussion` (str): Discussion and limitations
- `next_steps` (str): Next steps and related papers

#### `paper_reviewer.models.Config`

Application configuration from environment variables.

**Attributes**:
- `gemini_api_key` (str): Google AI API key (required, min_length=1)
- `notion_token` (str): Notion integration token (required, min_length=1)
- `notion_database_id` (str): Notion database ID (required, 32-character hex string)

### Error Handling

#### `paper_reviewer.errors.PaperReviewerError`

Base exception for all paper reviewer errors.

**Attributes**:
- `message` (str): Error message
- `file_path` (Optional[str]): Optional path to file that caused the error

#### `paper_reviewer.errors.BibTeXParseError`

Raised when BibTeX file parsing fails.

#### `paper_reviewer.errors.PDFNotFoundError`

Raised when PDF file cannot be found or matched.

#### `paper_reviewer.errors.GeminiAPIError`

Raised when Gemini API calls fail.

#### `paper_reviewer.errors.NotionAPIError`

Raised when Notion API calls fail.

**Example**:
```python
from paper_reviewer.errors import GeminiAPIError, NotionAPIError

try:
    review_data = analyze_paper(pdf_path, api_key)
except GeminiAPIError as e:
    print(f"Gemini error: {e.message}")
except NotionAPIError as e:
    print(f"Notion error: {e.message}")
```

### Logging

#### `paper_reviewer.logger.setup_logging()`

Configure Python logging module for the application.

```python
def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> None
```

**Parameters**:
- `log_level` (str): Logging level for console output (default: "INFO")
- `log_file` (Optional[Path]): Optional path to log file. If `None`, uses default location (`logs/paper-reviewer.log`)

**Example**:
```python
from paper_reviewer.logger import setup_logging
from pathlib import Path

# Use defaults
setup_logging()

# Custom log level and file
setup_logging(log_level="DEBUG", log_file=Path("./custom.log"))
```

#### `paper_reviewer.logger.get_logger()`

Get a logger instance for a module.

```python
def get_logger(name: str) -> logging.Logger
```

**Parameters**:
- `name` (str): Logger name, typically `__name__` of the calling module

**Returns**:
- `logging.Logger`: Logger instance configured with application settings

**Example**:
```python
from paper_reviewer.logger import get_logger

logger = get_logger(__name__)
logger.info("Processing started")
```

### UI Components

#### `paper_reviewer.ui.display_papers_table()`

Display a Rich table showing discovered papers.

```python
def display_papers_table(papers: List[PaperPair]) -> None
```

**Parameters**:
- `papers` (List[PaperPair]): List of PaperPair objects to display

#### `paper_reviewer.ui.create_progress_tracker()`

Create a Rich Progress instance for tracking paper processing.

```python
def create_progress_tracker(total: int) -> Progress
```

**Parameters**:
- `total` (int): Total number of papers to process

**Returns**:
- `Progress`: Progress instance configured with appropriate columns

#### `paper_reviewer.ui.display_success()`

Display a success message with green styling.

```python
def display_success(message: str) -> None
```

#### `paper_reviewer.ui.display_error()`

Display an error message with red styling.

```python
def display_error(message: str) -> None
```

#### `paper_reviewer.ui.display_info()`

Display an info message with blue styling.

```python
def display_info(message: str) -> None
```

## Usage Examples

### Basic Programmatic Usage

```python
from pathlib import Path
from paper_reviewer import scan_directory, process_single_paper, load_config

# Load configuration
config = load_config()

# Scan directory
papers = scan_directory(Path("./papers"))

# Process each paper
for paper in papers:
    success = process_single_paper(paper, config)
    if success:
        print(f"✓ Processed {paper.metadata.bib_key}")
    else:
        print(f"✗ Failed to process {paper.metadata.bib_key}")
```

### Custom Processing Pipeline

```python
from pathlib import Path
from paper_reviewer.gemini_client import analyze_paper
from paper_reviewer.notion_converter import transform_to_notion_blocks
from paper_reviewer.notion_properties import build_notion_properties
from paper_reviewer.notion_client import create_paper_page
from paper_reviewer.config import load_config

# Load configuration
config = load_config()

# Custom processing
pdf_path = Path("./paper.pdf")
review_data = analyze_paper(pdf_path, config.gemini_api_key)

# Convert to Notion format
blocks = transform_to_notion_blocks(review_data)
properties = build_notion_properties(metadata)

# Create page
page_id = create_paper_page(
    config.notion_token,
    config.notion_database_id,
    properties,
    blocks
)
print(f"Created page: {page_id}")
```

### Error Handling

```python
from paper_reviewer.errors import GeminiAPIError, NotionAPIError, BibTeXParseError
from paper_reviewer.gemini_client import analyze_paper

try:
    review_data = analyze_paper(pdf_path, api_key)
except GeminiAPIError as e:
    print(f"Gemini API error: {e.message}")
    if e.file_path:
        print(f"File: {e.file_path}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Batch Processing with Custom Logic

```python
from pathlib import Path
from paper_reviewer.scanner import scan_directory
from paper_reviewer.main import process_single_paper
from paper_reviewer.config import load_config

config = load_config()
papers = scan_directory(Path("./papers"))

# Filter papers by year
recent_papers = [p for p in papers if p.metadata.year and p.metadata.year >= 2020]

# Process only recent papers
for paper in recent_papers:
    print(f"Processing {paper.metadata.title} ({paper.metadata.year})")
    process_single_paper(paper, config)
```

### Custom Notion Block Creation

```python
from paper_reviewer.notion_converter import (
    create_heading_block,
    create_paragraph_block,
    create_bullet_block
)

# Create custom blocks
blocks = [
    create_heading_block("Custom Section"),
    create_paragraph_block("This is a custom paragraph."),
    create_bullet_block("Item 1"),
    create_bullet_block("Item 2"),
]
```

## Type Hints

All functions include comprehensive type hints for IDE support and static type checking. The codebase uses:

- `typing` module for standard types
- `pathlib.Path` for file paths
- Pydantic models for data validation
- Custom exception types for error handling

## Best Practices

1. **Configuration**: Always use `load_config()` to get validated configuration
2. **Error Handling**: Catch specific exception types (`GeminiAPIError`, `NotionAPIError`) for better error handling
3. **Path Handling**: Use `pathlib.Path` objects instead of strings for file paths
4. **Logging**: Set up logging early in your application using `setup_logging()`
5. **Type Safety**: Use Pydantic models (`BibTeXEntry`, `PaperPair`, etc.) for type safety
6. **Batch Processing**: Use `scan_directory()` for multiple papers, `process_single_paper()` for individual papers

## See Also

- [Architecture Documentation](ARCHITECTURE.md) - System design and component details
- [Configuration Guide](CONFIGURATION.md) - Detailed configuration instructions
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
