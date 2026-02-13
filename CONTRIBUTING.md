# Contributing to paper-reviewer-cli

Thank you for your interest in contributing to `paper-reviewer-cli`! This document provides guidelines and instructions for contributing.

## Welcome

We welcome contributions of all kinds:
- Bug fixes
- New features
- Documentation improvements
- Test coverage
- Code quality improvements
- Performance optimizations

## Development Setup

### Forking and Cloning

1. **Fork the Repository**:
   - Click the "Fork" button on GitHub
   - This creates your own copy of the repository

2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/yourusername/paper-reviewer-cli.git
   cd paper-reviewer-cli
   ```

3. **Add Upstream Remote**:
   ```bash
   git remote add upstream https://github.com/originalowner/paper-reviewer-cli.git
   ```

### Virtual Environment Setup

We recommend using a virtual environment to isolate dependencies:

**Using venv**:
```bash
# Create virtual environment
python -m venv .venv

# Activate (Unix/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

**Using conda**:
```bash
conda create -n paper-reviewer python=3.10
conda activate paper-reviewer
```

### Installing Dev Dependencies

Install the package in development mode with all dev dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- The package itself (editable mode)
- Development tools: `pytest`, `pytest-cov`, `pytest-mock`
- Code formatting: `black`
- Linting: `ruff`

### Running Tests

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=paper_reviewer --cov-report=html

# Run specific test file
pytest tests/test_bibtex_parser.py

# Run with verbose output
pytest -v
```

**Test Coverage**: Aim to maintain or improve test coverage. Check coverage reports:
```bash
pytest --cov=paper_reviewer --cov-report=term-missing
```

## Code Style

### Formatting

We use **Black** for code formatting with a line length of 100:

```bash
# Format all code
black src/ tests/

# Check formatting without changing files
black --check src/ tests/
```

**Black Configuration** (in `pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ["py310"]
```

### Linting

We use **Ruff** for linting:

```bash
# Lint code
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

**Ruff Configuration** (in `pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py310"
```

### Type Hints

- **Always use type hints** for function parameters and return types
- Use `typing` module for complex types (`List`, `Dict`, `Optional`, `Union`)
- Use `pathlib.Path` for file paths (not `str`)
- Use Pydantic models for data structures

**Example**:
```python
from pathlib import Path
from typing import List, Optional

def process_files(paths: List[Path], config: Optional[Config] = None) -> bool:
    """Process files with optional configuration."""
    ...
```

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    Longer description if needed, explaining what the function does,
    any important details, or usage examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
        FileNotFoundError: When file doesn't exist

    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    ...
```

### Import Organization

Organize imports in this order:
1. Standard library imports
2. Third-party imports
3. Local application imports

**Example**:
```python
# Standard library
import logging
from pathlib import Path
from typing import List, Optional

# Third-party
from pydantic import BaseModel
import requests

# Local
from .errors import PaperReviewerError
from .models import BibTeXEntry
```

## Testing

### Writing Tests

- Place tests in `tests/` directory
- Test files should start with `test_`
- Test functions should start with `test_`
- Use descriptive test names

**Example**:
```python
def test_parse_bibtex_with_valid_entry():
    """Test parsing a valid BibTeX entry."""
    # Arrange
    bib_path = Path("tests/fixtures/valid.bib")
    
    # Act
    entries = parse_bibtex_file(bib_path)
    
    # Assert
    assert len(entries) == 1
    assert entries[0].title == "Test Paper"
```

### Test Structure

Use the **Arrange-Act-Assert** pattern:
1. **Arrange**: Set up test data and conditions
2. **Act**: Execute the code being tested
3. **Assert**: Verify the results

### Fixtures

Use pytest fixtures for common test data:

```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_bibtex_file(tmp_path):
    """Create a sample BibTeX file for testing."""
    bib_file = tmp_path / "test.bib"
    bib_file.write_text("@article{test2024, title={Test}}")
    return bib_file
```

### Mocking External APIs

Use `pytest-mock` or `unittest.mock` for external API calls:

```python
from unittest.mock import patch, MagicMock

def test_gemini_analysis(mocker):
    """Test Gemini API analysis."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"summary": "Test"}'
    mock_client.models.generate_content.return_value = mock_response
    
    with patch('paper_reviewer.gemini_client.genai.Client', return_value=mock_client):
        result = analyze_paper(Path("test.pdf"), "api-key")
        assert "summary" in result
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=paper_reviewer

# Run specific test
pytest tests/test_bibtex_parser.py::test_parse_valid_entry

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "bibtex"
```

## Pull Request Process

### Branch Naming

Use descriptive branch names:
- `fix/description` - Bug fixes
- `feat/description` - New features
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions/changes

**Examples**:
- `fix/bibtex-parsing-error`
- `feat/add-custom-review-format`
- `docs/update-api-reference`

### Before Submitting

1. **Update Your Fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create Feature Branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```

3. **Make Changes**:
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Run Checks**:
   ```bash
   # Format code
   black src/ tests/
   
   # Lint code
   ruff check src/ tests/
   
   # Run tests
   pytest
   
   # Check type hints (if using mypy)
   mypy src/
   ```

5. **Commit Changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples**:
```
feat(scanner): add recursive directory scanning

Add support for scanning subdirectories when root directory
doesn't contain both .bib and .pdf files.

Closes #123
```

```
fix(bibtex): handle missing author field gracefully

Previously raised exception when author field was missing.
Now defaults to empty list.

Fixes #456
```

### PR Description Template

When creating a pull request, include:

1. **Description**: What changes were made and why
2. **Type**: Bug fix, feature, documentation, etc.
3. **Testing**: How the changes were tested
4. **Checklist**:
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] All tests pass
   - [ ] No breaking changes (or documented)

**Example**:
```markdown
## Description
Adds support for custom review formats by allowing users to specify
custom prompt templates.

## Type
- [ ] Bug fix
- [x] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- Added unit tests for custom prompt loading
- Tested with sample BibTeX files
- Verified Notion integration still works

## Checklist
- [x] Code follows style guidelines (black, ruff)
- [x] Tests added/updated
- [x] Documentation updated
- [x] All tests pass
- [x] No breaking changes
```

### Review Process

1. **Automated Checks**: CI will run tests and linting
2. **Code Review**: Maintainers will review your code
3. **Feedback**: Address any feedback or requested changes
4. **Merge**: Once approved, your PR will be merged

## Project Structure

```
paper-reviewer-cli/
├── src/
│   └── paper_reviewer/
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       ├── config.py             # Configuration
│       ├── models.py             # Data models
│       ├── scanner.py            # Directory scanning
│       ├── bibtex_parser.py      # BibTeX parsing
│       ├── pdf_finder.py         # PDF discovery
│       ├── gemini_client.py      # Gemini API
│       ├── notion_client.py      # Notion API
│       ├── notion_converter.py   # Review conversion
│       ├── notion_properties.py # Property building
│       ├── errors.py             # Exceptions
│       ├── ui.py                 # Terminal UI
│       └── logger.py             # Logging
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_bibtex_parser.py
│   ├── test_integration.py
│   └── test_pdf_finder.py
├── docs/                        # Documentation
├── pyproject.toml               # Project config
└── README.md                    # Main docs
```

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Questions?

- **Documentation**: Check `docs/` directory
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

Thank you for contributing! 🎉
