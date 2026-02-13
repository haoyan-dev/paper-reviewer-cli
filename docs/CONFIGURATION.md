# Configuration Guide

Complete guide for configuring `paper-reviewer-cli`.

## Overview

`paper-reviewer-cli` uses environment variables for configuration. You can set these variables directly in your environment or use a `.env` file for convenience.

## Configuration Methods

The tool searches for configuration in the following order:

1. Explicit `.env` file path (if provided programmatically)
2. `.env` file in current working directory
3. `.env` file in project root (parent of `src/` directory)
4. Environment variables

## Environment Variables

### Required Variables

#### `GEMINI_API_KEY`

**Description**: Google AI (Gemini) API key for PDF analysis.

**How to Obtain**:
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

**Format**: 
- String of alphanumeric characters
- Example: `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Validation**:
- Must be non-empty
- No specific format validation (relies on API validation)

**Security Note**: Keep your API key secret. Never commit it to version control.

#### `NOTION_TOKEN`

**Description**: Notion integration token for API access.

**How to Obtain**:
1. Visit [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Fill in the integration details:
   - **Name**: Choose a name (e.g., "Paper Reviewer")
   - **Type**: Select "Internal"
   - **Associated workspace**: Select your workspace
4. Click "Submit"
5. Copy the "Internal Integration Token" from the integration page

**Format**:
- String starting with `secret_`
- Example: `secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Validation**:
- Must be non-empty
- Must start with `secret_` (checked by Notion API)

**Security Note**: Treat this token like a password. It provides access to your Notion workspace.

#### `NOTION_DATABASE_ID`

**Description**: ID of the Notion database where papers will be created.

**How to Extract**:
1. Open your Notion database in a web browser
2. Look at the URL:
   ```
   https://www.notion.so/workspace/DatabaseName-<DATABASE_ID>?v=...
   ```
3. Copy the `DATABASE_ID` (32-character hex string)

**Format**:
- 32-character hexadecimal string
- Can be with or without dashes
- Examples:
  - With dashes: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
  - Without dashes: `a1b2c3d4e5f67890abcdef1234567890`

**Validation**:
- Must be exactly 32 hex characters (after removing dashes)
- Must be valid hexadecimal

**Note**: The tool automatically handles both formats (with or without dashes).

## .env File

### Location

The `.env` file can be placed in:

1. **Current Working Directory**: Where you run the command
   ```
   /current/directory/.env
   ```

2. **Project Root**: Parent directory of `src/`
   ```
   /project/root/.env
   ```

### Format

The `.env` file uses a simple `KEY=VALUE` format:

```env
# Google AI (Gemini) API Configuration
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_google_ai_api_key_here

# Notion Integration Token
# Create an internal integration at: https://www.notion.so/my-integrations
# Then copy the "Internal Integration Token"
NOTION_TOKEN=secret_your_notion_integration_token_here

# Notion Database ID
# Get this from your Notion database URL:
# https://www.notion.so/workspace/DatabaseName-<DATABASE_ID>
# The DATABASE_ID is the 32-character hex string (with or without dashes)
NOTION_DATABASE_ID=a1b2c3d4e5f67890abcdef1234567890
```

### Example .env File

```env
# ============================================
# Paper Reviewer CLI Configuration
# ============================================
# Copy this file to .env and fill in your values
# See docs/CONFIGURATION.md for detailed instructions

# Google AI (Gemini) API Key
# Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Notion Integration Token
# Create integration at: https://www.notion.so/my-integrations
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Notion Database ID
# Extract from database URL (32-character hex string)
NOTION_DATABASE_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Security Best Practices

1. **Never Commit .env Files**: Add `.env` to your `.gitignore`
   ```gitignore
   .env
   .env.local
   .env.*.local
   ```

2. **Use .env.example**: Keep a template file (`.env.example`) with placeholder values
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Restrict File Permissions**: On Unix systems, restrict access:
   ```bash
   chmod 600 .env
   ```

4. **Environment Variables**: For production, consider using environment variables instead of files:
   ```bash
   export GEMINI_API_KEY="your-key"
   export NOTION_TOKEN="your-token"
   export NOTION_DATABASE_ID="your-db-id"
   ```

5. **Rotate Keys Regularly**: Periodically rotate your API keys and tokens

## Notion Database Setup

### Required Properties

Your Notion database must have the following properties with exact names and types:

| Property Name | Type | Required | Description |
|--------------|------|----------|-------------|
| `Name` | Title | Yes | Paper title (automatically set as page title) |
| `Authors` | Multi-select | No | List of author names |
| `Year` | Number | No | Publication year |
| `BibTeX Key` | Rich text | No | BibTeX entry ID/key |
| `URL/DOI` | URL | No | Paper URL or DOI link |

### Step-by-Step Setup

1. **Create a New Database**:
   - In Notion, create a new page
   - Type `/database` and select "Table - Inline" or "Table - Full page"
   - Name your database (e.g., "Research Papers")

2. **Add Required Properties**:
   - The `Name` property is created by default (Title type)
   - Add other properties:
     - Click "+" or "Add a property"
     - Select property type and name exactly as listed above

3. **Property Configuration**:
   - **Authors**: Set type to "Multi-select"
   - **Year**: Set type to "Number"
   - **BibTeX Key**: Set type to "Text" (Rich text)
   - **URL/DOI**: Set type to "URL"

4. **Grant Integration Access**:
   - Open your database
   - Click "..." menu in the top right
   - Select "Connections" → "Add connections"
   - Find and select your integration
   - Click "Confirm"

### Database ID Extraction

To get your database ID:

1. **From URL**:
   ```
   https://www.notion.so/workspace/DatabaseName-a1b2c3d4e5f67890abcdef1234567890?v=...
                                                              ↑ DATABASE_ID ↑
   ```

2. **Copy the ID**:
   - The ID is the 32-character hex string after the last dash
   - Can include dashes or be without them
   - Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890` or `a1b2c3d4e5f67890abcdef1234567890`

3. **Add to .env**:
   ```env
   NOTION_DATABASE_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
   ```

### Integration Permissions

Your Notion integration needs:

- **Read Content**: To access database structure
- **Insert Content**: To create new pages
- **Update Content**: To modify pages (if needed)

**Note**: The integration must be added to the specific database, not just the workspace.

## Advanced Configuration

### Logging Configuration

#### Log Levels

Available log levels (from least to most verbose):
- `CRITICAL`: Only critical errors
- `ERROR`: Errors only
- `WARNING`: Warnings and errors
- `INFO`: Informational messages (default)
- `DEBUG`: Detailed diagnostic information

#### Default Logging

By default, logging is configured automatically:
- **Console**: INFO level and above
- **File**: DEBUG level and above
- **Log File**: `logs/paper-reviewer.log` (in project root)

#### Custom Logging Setup

You can customize logging programmatically:

```python
from paper_reviewer.logger import setup_logging
from pathlib import Path

# Custom log level
setup_logging(log_level="DEBUG")

# Custom log file location
setup_logging(log_file=Path("./custom.log"))

# Both
setup_logging(log_level="DEBUG", log_file=Path("./custom.log"))
```

#### Log File Location

Default log file location:
```
<project_root>/logs/paper-reviewer.log
```

The `logs/` directory is created automatically if it doesn't exist.

### Environment Variable Priority

When the same variable is set in multiple places, priority is:

1. Explicit `.env` file path (if provided)
2. `.env` in current directory
3. `.env` in project root
4. System environment variables

**Note**: Later sources override earlier ones if the same variable is defined.

### Configuration Validation

The tool validates configuration on startup:

1. **Required Variables**: All three variables must be present
2. **Format Validation**: 
   - Database ID format (32 hex chars)
   - Non-empty strings for all variables
3. **Error Messages**: Clear error messages if validation fails

**Example Error Messages**:
```
Missing required environment variables: GEMINI_API_KEY, NOTION_TOKEN
Please set these in your .env file or environment.
See .env.example for a template.
```

```
Invalid Notion database ID format: invalid-id
Expected 32-character hex string (with or without dashes).
```

## Troubleshooting Configuration

### Common Issues

**Issue**: "Configuration file not found"
- **Solution**: Create a `.env` file in the current directory or project root
- **Check**: File name is exactly `.env` (not `.env.txt` or `env`)

**Issue**: "Missing required environment variables"
- **Solution**: Ensure all three variables are set in `.env` or environment
- **Check**: Variable names are exact (case-insensitive but recommended uppercase)

**Issue**: "Invalid Notion database ID format"
- **Solution**: Verify the ID is 32 hex characters
- **Check**: Remove any extra characters or spaces
- **Try**: Both formats (with and without dashes)

**Issue**: "Notion API error: unauthorized"
- **Solution**: Verify your integration token is correct
- **Check**: Integration has access to the database
- **Verify**: Token starts with `secret_`

**Issue**: "Gemini API error: invalid API key"
- **Solution**: Verify your API key is correct
- **Check**: Key hasn't expired or been revoked
- **Verify**: Key is from Google AI Studio (not other Google services)

### Testing Configuration

You can test your configuration:

```python
from paper_reviewer.config import load_config

try:
    config = load_config()
    print("✓ Configuration loaded successfully")
    print(f"  Database ID: {config.notion_database_id}")
except Exception as e:
    print(f"✗ Configuration error: {e}")
```

### Verification Checklist

Before running the tool, verify:

- [ ] `.env` file exists and is readable
- [ ] All three required variables are set
- [ ] `GEMINI_API_KEY` is valid (starts with `AIza`)
- [ ] `NOTION_TOKEN` is valid (starts with `secret_`)
- [ ] `NOTION_DATABASE_ID` is 32 hex characters
- [ ] Notion integration has database access
- [ ] Database has required properties with correct names/types

## See Also

- [README.md](../README.md) - Quick start guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [API.md](API.md) - Programmatic configuration usage
