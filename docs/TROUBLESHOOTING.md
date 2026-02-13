# Troubleshooting Guide

Common issues and solutions for `paper-reviewer-cli`.

## Installation Issues

### Python Version Compatibility

**Issue**: "Python version X.Y.Z is not supported"

**Solution**: 
- `paper-reviewer-cli` requires Python 3.10 or higher
- Check your Python version: `python --version` or `python3 --version`
- Upgrade Python if needed:
  - Download from [python.org](https://www.python.org/downloads/)
  - Or use a version manager like `pyenv`

**Verification**:
```bash
python --version
# Should show: Python 3.10.x or higher
```

### Missing Dependencies

**Issue**: "ModuleNotFoundError: No module named 'X'"

**Solution**:
1. Ensure you've installed the package:
   ```bash
   pip install -e .
   ```

2. If using a virtual environment, ensure it's activated:
   ```bash
   # On Unix/Mac
   source .venv/bin/activate
   
   # On Windows
   .venv\Scripts\activate
   ```

3. Reinstall dependencies:
   ```bash
   pip install --upgrade -e .
   ```

**Common Missing Modules**:
- `google.genai` → Install `google-genai`
- `notion_client` → Install `notion-client`
- `bibtexparser` → Install `bibtexparser`
- `pydantic` → Install `pydantic` and `pydantic-settings`
- `rich` → Install `rich`

### Virtual Environment Issues

**Issue**: Package installed but command not found

**Solution**:
1. Ensure virtual environment is activated
2. Verify installation:
   ```bash
   pip list | grep paper-reviewer
   ```

3. Check PATH:
   ```bash
   which paper-reviewer  # Unix/Mac
   where paper-reviewer   # Windows
   ```

4. Reinstall:
   ```bash
   pip uninstall paper-reviewer-cli
   pip install -e .
   ```

## Configuration Issues

### Missing API Keys

**Issue**: "Missing required environment variables: GEMINI_API_KEY"

**Solution**:
1. Create a `.env` file in your project root or current directory
2. Copy from `.env.example`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API keys
4. Verify the file is readable and in the correct location

**Check**:
```bash
# Verify .env file exists
ls -la .env  # Unix/Mac
dir .env     # Windows

# Check file contents (don't expose keys!)
cat .env | grep -v "KEY\|TOKEN"  # Shows structure without values
```

### Invalid Notion Database ID

**Issue**: "Invalid Notion database ID format: X"

**Solution**:
1. Extract ID from Notion database URL:
   ```
   https://www.notion.so/workspace/DatabaseName-<DATABASE_ID>?v=...
   ```
2. ID should be 32 hexadecimal characters
3. Can be with or without dashes:
   - `a1b2c3d4-e5f6-7890-abcd-ef1234567890` ✓
   - `a1b2c3d4e5f67890abcdef1234567890` ✓
4. Remove any extra characters or spaces

**Verification**:
```python
# Test database ID format
db_id = "your-database-id"
clean_id = db_id.replace("-", "")
assert len(clean_id) == 32, "Must be 32 characters"
assert all(c in "0123456789abcdefABCDEF" for c in clean_id), "Must be hex"
```

### Permission Errors

**Issue**: "Notion API error: unauthorized" or "Notion API error: restricted resource"

**Solution**:
1. **Verify Integration Token**:
   - Check token starts with `secret_`
   - Ensure token is copied correctly (no extra spaces)

2. **Grant Database Access**:
   - Open your Notion database
   - Click "..." menu → "Connections" → "Add connections"
   - Select your integration
   - Click "Confirm"

3. **Check Integration Status**:
   - Visit [Notion Integrations](https://www.notion.so/my-integrations)
   - Verify integration is active
   - Check if token needs to be regenerated

4. **Verify Database Permissions**:
   - Ensure database is not in a private workspace
   - Check integration has "Read" and "Insert" capabilities

## Runtime Issues

### No Papers Found

**Issue**: "No papers found. Exiting."

**Solution**:
1. **Check Directory Structure**:
   - Ensure directory contains both `.bib` and `.pdf` files
   - Verify file extensions are correct (case-insensitive)

2. **Verify File Locations**:
   ```bash
   # Check for BibTeX files
   find . -name "*.bib" -o -name "*.BIB"
   
   # Check for PDF files
   find . -name "*.pdf" -o -name "*.PDF"
   ```

3. **Check Scanning Mode**:
   - **Single Directory Mode**: Root directory must contain both files
   - **Recursive Mode**: Subdirectories must contain both files

4. **File Permissions**:
   - Ensure files are readable
   - Check file permissions: `ls -l paper.bib paper.pdf`

**Example Structure**:
```
papers/
├── paper1/
│   ├── paper.bib  ✓
│   └── paper.pdf  ✓
└── paper2/
    ├── paper.bib  ✓
    └── paper.pdf  ✓
```

### BibTeX Parsing Errors

**Issue**: "BibTeXParseError: Missing required field 'title'"

**Solution**:
1. **Check BibTeX Format**:
   - Ensure entry has `@article{ID, ...}` format
   - Verify `title` field exists
   - Verify `ID` field exists (the BibTeX key)

2. **Required Fields**:
   ```bibtex
   @article{example2024,
     title={Paper Title},  # Required
     author={Author Name},  # Optional
     year={2024},           # Optional
   }
   ```

3. **Encoding Issues**:
   - Try saving BibTeX file as UTF-8
   - Check for special characters that might cause issues

4. **Multiple Entries**:
   - Tool supports multiple entries in one `.bib` file
   - Each entry creates a separate Notion page

**Common BibTeX Errors**:
- Missing `title` → Add title field
- Missing `ID` → Add ID in `@article{ID, ...}`
- Invalid author format → Tool handles various formats automatically
- Encoding issues → Save as UTF-8

### PDF Not Found

**Issue**: "PDFNotFoundError: No PDF file found in directory"

**Solution**:
1. **Verify PDF Exists**:
   ```bash
   ls -la *.pdf  # Check current directory
   find . -name "*.pdf"  # Search recursively
   ```

2. **Check File Extension**:
   - Tool searches for `.pdf`, `.PDF`, `.Pdf`
   - Ensure file has correct extension

3. **File Location**:
   - PDF should be in same directory as `.bib` file
   - Or in a subdirectory (recursive search)

4. **File Corruption**:
   - Verify PDF opens correctly
   - Try re-downloading if corrupted

**Note**: If multiple PDFs are found, the first one is used (with a warning).

### Gemini API Errors

#### Rate Limits

**Issue**: "Gemini API error: rate limit exceeded"

**Solution**:
1. **Wait and Retry**:
   - Gemini API has rate limits
   - Wait a few minutes and try again
   - Consider processing papers in smaller batches

2. **Check API Quota**:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Check your API usage and limits
   - Upgrade plan if needed

3. **Implement Delays**:
   ```python
   import time
   for paper in papers:
       process_single_paper(paper, config)
       time.sleep(5)  # Wait 5 seconds between papers
   ```

#### File Processing Timeout

**Issue**: "File processing timeout for PDF"

**Solution**:
1. **Large PDFs**:
   - Large PDFs take longer to process
   - Default timeout is 5 minutes (300 seconds)
   - Very large PDFs may exceed this

2. **Increase Timeout** (programmatic):
   ```python
   from paper_reviewer.gemini_client import (
       upload_pdf, wait_for_file_processing, analyze_paper
   )
   # Custom timeout (10 minutes)
   wait_for_file_processing(file_handle, client, timeout=600)
   ```

3. **Check PDF Size**:
   - Very large PDFs (>50MB) may have issues
   - Consider compressing PDFs if possible

#### Invalid API Key

**Issue**: "Gemini API error: invalid API key"

**Solution**:
1. **Verify API Key**:
   - Check key is copied correctly
   - Ensure no extra spaces or characters
   - Key should start with `AIza`

2. **Regenerate Key**:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Update `.env` file

3. **Check API Status**:
   - Verify API is enabled in Google Cloud Console
   - Check for any service outages

### Notion API Errors

#### Invalid Properties

**Issue**: "Notion API error: property 'X' does not exist"

**Solution**:
1. **Check Property Names**:
   - Property names must match exactly (case-sensitive)
   - Required: `Name`, `Authors`, `Year`, `BibTeX Key`, `URL/DOI`

2. **Verify Property Types**:
   - `Name`: Title type
   - `Authors`: Multi-select type
   - `Year`: Number type
   - `BibTeX Key`: Rich text type
   - `URL/DOI`: URL type

3. **Database Schema**:
   - See [CONFIGURATION.md](CONFIGURATION.md) for setup instructions
   - Recreate properties if types are wrong

#### Permission Errors

**Issue**: "Notion API error: restricted resource"

**Solution**:
1. **Grant Database Access**:
   - Open database → "..." → "Connections"
   - Add your integration
   - Ensure "Can read" and "Can edit" are enabled

2. **Check Workspace**:
   - Integration must be in same workspace as database
   - Personal workspaces may have restrictions

3. **Verify Token**:
   - Ensure token is correct and active
   - Regenerate if needed

## Error Messages

### Common Error Messages and Solutions

#### "Configuration file not found"

**Meaning**: `.env` file not found in expected locations

**Solution**:
- Create `.env` file in current directory or project root
- Copy from `.env.example` template

#### "Missing required environment variables: X, Y"

**Meaning**: Required configuration variables not set

**Solution**:
- Add missing variables to `.env` file
- Or set as environment variables

#### "Directory does not exist: X"

**Meaning**: Specified directory path is invalid

**Solution**:
- Verify directory path is correct
- Use absolute path if relative path fails
- Check file permissions

#### "Failed to parse BibTeX file"

**Meaning**: BibTeX file has syntax errors or missing fields

**Solution**:
- Check BibTeX syntax
- Ensure required fields (`title`, `ID`) are present
- Verify file encoding (UTF-8 recommended)

#### "File processing timeout"

**Meaning**: PDF took too long to process in Gemini API

**Solution**:
- Wait and retry
- Check PDF size (very large files may timeout)
- Increase timeout if processing programmatically

## Debugging

### Enable Debug Logging

To get more detailed information:

**Programmatic**:
```python
from paper_reviewer.logger import setup_logging

setup_logging(log_level="DEBUG")
```

**Check Log File**:
- Default location: `logs/paper-reviewer.log`
- Contains DEBUG-level information
- Useful for diagnosing issues

### Common Debugging Steps

1. **Check Logs**:
   ```bash
   tail -f logs/paper-reviewer.log
   ```

2. **Verify Configuration**:
   ```python
   from paper_reviewer.config import load_config
   config = load_config()
   print(config)  # Verify all values are set
   ```

3. **Test Individual Components**:
   ```python
   # Test BibTeX parsing
   from paper_reviewer.bibtex_parser import parse_bibtex_file
   entries = parse_bibtex_file(Path("paper.bib"))
   
   # Test PDF finding
   from paper_reviewer.pdf_finder import find_pdf_in_directory
   pdf = find_pdf_in_directory(Path("."))
   
   # Test scanning
   from paper_reviewer.scanner import scan_directory
   papers = scan_directory(Path("."))
   ```

4. **Check API Connectivity**:
   ```python
   # Test Gemini API
   from paper_reviewer.gemini_client import analyze_paper
   # This will show detailed errors if API fails
   
   # Test Notion API
   from paper_reviewer.notion_client import create_paper_page
   # Check error messages for API issues
   ```

### Verbose Output

Run with Python's verbose mode:
```bash
python -v -m paper_reviewer.main papers/
```

## Getting Help

### Before Asking for Help

1. **Check Documentation**:
   - [README.md](../README.md) - Quick start
   - [CONFIGURATION.md](CONFIGURATION.md) - Configuration details
   - [API.md](API.md) - Programmatic usage

2. **Check Logs**:
   - Review `logs/paper-reviewer.log` for errors
   - Enable DEBUG logging for more details

3. **Verify Setup**:
   - Configuration is correct
   - API keys are valid
   - Notion database is set up correctly

### Reporting Issues

When reporting issues, include:

1. **Error Message**: Full error message and stack trace
2. **Configuration**: `.env` file structure (without actual keys!)
3. **Logs**: Relevant log entries from `logs/paper-reviewer.log`
4. **Environment**:
   - Python version
   - Operating system
   - Package version
5. **Steps to Reproduce**: Clear steps to reproduce the issue
6. **Expected Behavior**: What should happen
7. **Actual Behavior**: What actually happens

### Useful Commands

```bash
# Check Python version
python --version

# Check package installation
pip show paper-reviewer-cli

# List installed dependencies
pip list

# Test configuration
python -c "from paper_reviewer.config import load_config; print(load_config())"

# Check logs
tail -n 50 logs/paper-reviewer.log

# Verify files exist
ls -la papers/*/*.{bib,pdf}
```

## See Also

- [README.md](../README.md) - Quick start guide
- [CONFIGURATION.md](CONFIGURATION.md) - Detailed configuration
- [API.md](API.md) - Programmatic API reference
