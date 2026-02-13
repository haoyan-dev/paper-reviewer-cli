"""Notion block converter module for transforming Gemini review JSON to Notion blocks."""

from typing import Dict, List

# Maximum characters per rich_text element in Notion API
NOTION_RICH_TEXT_LIMIT = 2000


def transform_to_notion_blocks(review_json: Dict[str, str]) -> List[Dict]:
    """
    Convert Gemini's JSON review output into Notion block structure.

    Args:
        review_json: Dictionary with 6 fields: summary, novelty, methodology,
                     validation, discussion, next_steps

    Returns:
        List of Notion block objects ready for API creation

    Example:
        >>> review = {"summary": "Paper overview", "novelty": "New approach"}
        >>> blocks = transform_to_notion_blocks(review)
        >>> len(blocks) > 0
        True
    """
    blocks = []

    # Mapping from JSON keys to Notion headings
    mapping = {
        "summary": "Overview",
        "novelty": "1. Novelty & Impact",
        "methodology": "2. Methodology",
        "validation": "3. Validation",
        "discussion": "4. Discussion",
        "next_steps": "5. Next Steps",
    }

    for key, heading in mapping.items():
        content = review_json.get(key, "")
        if not content or not content.strip():
            continue

        # Add heading block
        blocks.append(create_heading_block(heading))

        # Add content blocks (smart splitting)
        content_blocks = _create_content_blocks(content)
        blocks.extend(content_blocks)

    return blocks


def create_heading_block(text: str) -> Dict:
    """
    Create a Notion heading_2 block for page creation.

    Args:
        text: Heading text

    Returns:
        Notion block dict with heading_2 type

    Example:
        >>> block = create_heading_block("Overview")
        >>> block["type"] == "heading_2"
        True
    """
    return {
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        },
    }


def create_paragraph_block(text: str) -> Dict:
    """
    Create a Notion paragraph block.

    Args:
        text: Paragraph text (will be truncated to NOTION_RICH_TEXT_LIMIT)

    Returns:
        Notion block dict with paragraph type

    Example:
        >>> block = create_paragraph_block("Some text")
        >>> block["type"] == "paragraph"
        True
    """
    # Truncate to Notion's limit
    truncated_text = text[:NOTION_RICH_TEXT_LIMIT]
    return {
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": truncated_text}}]
        },
    }


def create_bullet_block(text: str) -> Dict:
    """
    Create a Notion bulleted_list_item block.

    Args:
        text: Bullet item text (will be truncated to NOTION_RICH_TEXT_LIMIT)

    Returns:
        Notion block dict with bulleted_list_item type

    Example:
        >>> block = create_bullet_block("Item text")
        >>> block["type"] == "bulleted_list_item"
        True
    """
    # Truncate to Notion's limit
    truncated_text = text[:NOTION_RICH_TEXT_LIMIT]
    return {
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": truncated_text}}]
        },
    }


def split_content_smartly(content: str) -> List[str]:
    """
    Intelligently split content into list items.

    Detects markdown-style bullet points and newline-separated items.
    If no clear list structure is found, returns single-item list for paragraph.

    Args:
        content: Content string that may contain list items

    Returns:
        List of strings, each representing a content item

    Example:
        >>> split_content_smartly("- Item 1\\n- Item 2")
        ['Item 1', 'Item 2']
        >>> split_content_smartly("Single paragraph")
        ['Single paragraph']
    """
    if not content:
        return []

    # Split by newlines
    lines = content.split("\n")

    # Strip and filter empty lines
    cleaned_lines = [line.strip() for line in lines if line.strip()]

    if not cleaned_lines:
        return []

    # Check if content looks like a list (starts with - or *)
    is_list = any(
        line.startswith("- ") or line.startswith("* ") for line in cleaned_lines
    )

    if is_list:
        # Extract list items by removing bullet markers
        items = []
        for line in cleaned_lines:
            # Remove bullet markers
            item = line.lstrip("- ").lstrip("* ").strip()
            if item:
                items.append(item)
        return items if items else cleaned_lines

    # Check if multiple lines exist (treat as list even without bullets)
    if len(cleaned_lines) > 1:
        return cleaned_lines

    # Single line or no clear structure - return as single item
    return [content.strip()]


def _create_content_blocks(content: str) -> List[Dict]:
    """
    Create appropriate Notion blocks from content string.

    Intelligently chooses between paragraph and bullet blocks based on content structure.

    Args:
        content: Content string

    Returns:
        List of Notion block dicts
    """
    items = split_content_smartly(content)

    if not items:
        return []

    # If multiple items, use bullet blocks
    if len(items) > 1:
        return [create_bullet_block(item) for item in items]

    # Single item - use paragraph block
    return [create_paragraph_block(items[0])]
