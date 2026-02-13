# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation (README, API reference, architecture, configuration, troubleshooting)
- Contributing guidelines
- Enhanced .env.example with detailed comments

## [0.1.0] - 2024-01-XX

### Added
- Initial release of paper-reviewer-cli
- CLI tool for automatic paper review generation
- Directory scanning for BibTeX and PDF files
- BibTeX parsing with support for multiple entry types
- PDF file discovery and pairing
- Google Gemini AI integration for paper analysis
- Structured review generation with 6 sections:
  - Summary
  - Novelty & Impact
  - Methodology
  - Validation
  - Discussion
  - Next Steps
- Notion integration for creating review pages
- Rich terminal UI with progress tracking
- Comprehensive error handling with custom exceptions
- Logging to both console and file
- Configuration via environment variables or .env file
- Support for single directory and recursive scanning modes
- Programmatic API for library usage
- Type hints throughout codebase
- Pydantic models for data validation

### Features
- Automatic discovery of BibTeX and PDF files
- Smart directory scanning (single or recursive mode)
- Robust BibTeX parsing with multiple encoding support
- Author parsing handles various formats ("Last, First" and "First Last")
- PDF upload to Gemini File API with status polling
- Intelligent Notion block conversion (headings, paragraphs, bullet lists)
- Metadata extraction and mapping to Notion properties
- Progress tracking with Rich library
- Detailed logging for debugging

### Technical Details
- Python 3.10+ required
- Uses `gemini-3-pro-preview` model for analysis
- Notion API integration with block and property support
- Comprehensive test suite with pytest
- Code formatting with Black (line length 100)
- Linting with Ruff
- Type safety with Pydantic models

### Known Limitations
- Sequential processing (no parallelization yet)
- File processing timeout: 5 minutes (configurable programmatically)
- Single PDF per directory (uses first found if multiple exist)
- Notion database schema must match required properties exactly
- API rate limits depend on Gemini and Notion API quotas

### Documentation
- README with quick start guide
- API reference documentation
- Architecture documentation
- Configuration guide
- Troubleshooting guide
- Contributing guidelines

[Unreleased]: https://github.com/yourusername/paper-reviewer-cli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/paper-reviewer-cli/releases/tag/v0.1.0
