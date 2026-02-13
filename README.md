# paper-reviewer-cli

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com)

> CLI tool for automatically reviewing research papers using Google Gemini AI and syncing structured reviews to Notion databases.

## Description

`paper-reviewer-cli` is a command-line tool that automates the process of reviewing research papers. It scans directories for BibTeX files and PDF papers, uses Google's Gemini AI to generate structured reviews, and automatically creates formatted pages in your Notion database.

**Key Features:**
- 🔍 **Automatic Discovery**: Scans directories for BibTeX and PDF files
- 🤖 **AI-Powered Analysis**: Uses Google Gemini AI to generate comprehensive paper reviews
- 📝 **Structured Reviews**: Creates reviews with 6 standardized sections (summary, novelty, methodology, validation, discussion, next steps)
- 📚 **Notion Integration**: Automatically syncs reviews to Notion with formatted blocks and metadata
- 🎨 **Rich Terminal UI**: Beautiful progress tracking and error reporting using Rich
- 🔄 **Batch Processing**: Process multiple papers in a single run

## Features

- **Smart Directory Scanning**: Automatically detects BibTeX and PDF files, supports both single directory and recursive scanning modes
- **BibTeX Parsing**: Robust parsing with support for various BibTeX formats and encodings
- **Gemini AI Integration**: Uploads PDFs to Gemini File API and generates structured JSON reviews
- **Notion Block Conversion**: Intelligently converts review content to Notion blocks (headings, paragraphs, bullet lists)
- **Metadata Extraction**: Extracts and maps BibTeX metadata (title, authors, year, URL, DOI) to Notion properties
- **Error Handling**: Comprehensive error handling with custom exception types
- **Logging**: Detailed logging to both console and file for debugging
- **Type Safety**: Full type hints and Pydantic models for data validation

## Prerequisites

- **Python**: 3.10 or higher
- **Google AI API Key**: Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Notion Integration Token**: Create an internal integration at [Notion Integrations](https://www.notion.so/my-integrations)
- **Notion Database**: A Notion database with the required properties (see [Configuration](#configuration))

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/paper-reviewer-cli.git
cd paper-reviewer-cli

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

### Development Installation

For development with all dev dependencies:

```bash
pip install -e ".[dev]"
```

This installs additional tools like `pytest`, `black`, and `ruff` for testing and code formatting.

## Quick Start

1. **Set up your `.env` file**:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

2. **Configure your Notion database** with these properties:
   - `Name` (title)
   - `Authors` (multi_select)
   - `Year` (number)
   - `BibTeX Key` (rich_text)
   - `URL/DOI` (url)

3. **Organize your papers**:

```
papers/
├── paper1/
│   ├── paper.bib
│   └── paper.pdf
└── paper2/
    ├── paper.bib
    └── paper.pdf
```

4. **Run the tool**:

```bash
paper-reviewer papers/
```

## Configuration

### Environment Variables

Create a `.env` file in your project root or current working directory:

```env
# Google AI (Gemini) API Configuration
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_google_ai_api_key

# Notion Integration Token
# Create an internal integration at: https://www.notion.so/my-integrations
# Then copy the "Internal Integration Token"
NOTION_TOKEN=your_notion_internal_integration_token

# Notion Database ID
# Get this from your Notion database URL:
# https://www.notion.so/workspace/DatabaseName-<DATABASE_ID>
# The DATABASE_ID is the 32-character hex string (with or without dashes)
NOTION_DATABASE_ID=your_database_id
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for detailed setup instructions.

### Notion Database Setup

Your Notion database must have the following properties:

| Property Name | Type | Description |
|--------------|------|-------------|
| `Name` | Title | Paper title (required) |
| `Authors` | Multi-select | List of authors |
| `Year` | Number | Publication year |
| `BibTeX Key` | Rich text | BibTeX entry ID |
| `URL/DOI` | URL | Paper URL or DOI link |

**Important**: Make sure your Notion integration has access to the database. You can grant access by:
1. Opening your database in Notion
2. Clicking the "..." menu in the top right
3. Selecting "Connections" → "Add connections"
4. Choosing your integration

## Usage

### Basic Command

```bash
paper-reviewer [directory]
```

- `directory`: Path to directory containing papers (default: current directory)

### Zotero BibTeX File Mode

Alternatively, you can process a Zotero-exported BibTeX file directly:

```bash
paper-reviewer --zotero-bib path/to/zotero_export.bib
```

or using the short flag:

```bash
paper-reviewer -z path/to/zotero_export.bib
```

This mode extracts PDF paths directly from the `file` field in Zotero BibTeX entries, eliminating the need to organize papers in directories. Entries without a `file` field or with invalid PDF paths are automatically skipped.

### Directory Structure

The tool supports two scanning modes:

**Single Directory Mode**: When the specified directory directly contains both `.bib` and `.pdf` files:
```
paper/
├── paper.bib
└── paper.pdf
```

**Recursive Mode**: When scanning subdirectories:
```
papers/
├── paper1/
│   ├── paper.bib
│   └── paper.pdf
└── paper2/
    ├── paper.bib
    └── paper.pdf
```

### BibTeX File Format

Your BibTeX file must include:
- `@article{ID, ...}` or similar entry type
- `title` field (required)
- `ID` field (required) - the BibTeX key
- Optional fields: `author`, `year`, `url`, `doi`

Example:
```bibtex
@article{smith2024example,
  title={Example Paper Title},
  author={Smith, John and Doe, Jane},
  year={2024},
  url={https://example.com/paper},
  doi={10.1000/example}
}
```

### PDF Requirements

- PDF files should be readable and not corrupted
- The tool searches recursively for `.pdf`, `.PDF`, or `.Pdf` files
- If multiple PDFs are found in a directory, the first one is used

### Exit Codes

- `0`: Success (all papers processed successfully)
- `1`: Error (one or more papers failed to process)
- `130`: Interrupted by user (Ctrl+C)

## Examples

### Process Current Directory

```bash
paper-reviewer
```

### Process Specific Directory

```bash
paper-reviewer /path/to/papers
```

### Process Single Paper Directory

```bash
paper-reviewer ./papers/paper1
```

### Process Zotero BibTeX File

```bash
paper-reviewer --zotero-bib zotero_export.bib
```

This will process all entries in the BibTeX file that have valid PDF paths in their `file` field.

## Output

For each paper, the tool:

1. **Scans** the directory for BibTeX and PDF files
2. **Parses** BibTeX metadata
3. **Uploads** PDF to Gemini File API
4. **Generates** structured review using Gemini AI (model: `gemini-3-pro-preview`)
5. **Creates** a Notion page with:
   - **Properties**: Title, authors, year, BibTeX key, URL/DOI
   - **Content Blocks**: 
     - Overview (summary)
     - 1. Novelty & Impact
     - 2. Methodology
     - 3. Validation
     - 4. Discussion
     - 5. Next Steps

The review content is intelligently formatted as Notion blocks (headings, paragraphs, and bullet lists).

## Troubleshooting

### Common Issues

**No papers found**
- Ensure your directory contains both `.bib` and `.pdf` files
- Check file permissions

**Configuration errors**
- Verify your `.env` file exists and contains all required variables
- Check that API keys are valid and not expired

**Gemini API errors**
- Check your API key is valid
- Ensure you have sufficient API quota
- Large PDFs may take longer to process (default timeout: 5 minutes)

**Notion API errors**
- Verify your integration token is correct
- Ensure your integration has access to the database
- Check that database properties match the required schema

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more detailed troubleshooting.

## Development

### Setting Up Development Environment

```bash
# Clone and install
git clone https://github.com/yourusername/paper-reviewer-cli.git
cd paper-reviewer-cli
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

### Project Structure

```
paper-reviewer-cli/
├── src/
│   └── paper_reviewer/
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       ├── config.py             # Configuration management
│       ├── models.py              # Data models
│       ├── scanner.py            # Directory scanning
│       ├── bibtex_parser.py      # BibTeX parsing
│       ├── pdf_finder.py         # PDF discovery
│       ├── gemini_client.py      # Gemini API integration
│       ├── notion_client.py      # Notion API integration
│       ├── notion_converter.py   # Review to Notion blocks
│       ├── notion_properties.py  # Metadata to properties
│       ├── errors.py             # Custom exceptions
│       ├── ui.py                 # Rich terminal UI
│       └── logger.py             # Logging configuration
├── tests/                        # Test suite
├── docs/                         # Documentation
└── pyproject.toml                # Project configuration
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Programmatic API

You can also use `paper-reviewer-cli` as a Python library:

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
    print(f"Processed {paper.metadata.bib_key}: {success}")
```

See [docs/API.md](docs/API.md) for complete API reference.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Development setup
- Code style and formatting
- Testing requirements
- Pull request process

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Related Resources

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Notion API Documentation](https://developers.notion.com/)
- [BibTeX Format Reference](http://www.bibtex.org/Format/)

## Support

- **Documentation**: See the `docs/` directory for detailed guides
- **Issues**: Report bugs or request features on GitHub Issues
- **API Reference**: See [docs/API.md](docs/API.md) for programmatic usage

---

**Note**: This tool is currently in alpha status. API and behavior may change in future versions.
