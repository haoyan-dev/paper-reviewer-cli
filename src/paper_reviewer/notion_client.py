"""Notion API client for creating paper pages."""

from typing import Dict, List

from notion_client import APIResponseError, Client

from .errors import NotionAPIError


def create_paper_page(
    token: str, db_id: str, properties: Dict, blocks: List[Dict]
) -> str:
    """
    Create a complete paper page in Notion database.

    Args:
        token: Notion integration token
        db_id: Notion database ID (with or without dashes)
        properties: Page properties dict (from build_notion_properties)
        blocks: List of block dicts (from transform_to_notion_blocks)

    Returns:
        Created page ID (string)

    Raises:
        NotionAPIError: If page creation fails

    Example:
        >>> props = {"Name": {"title": [{"type": "text", "text": {"content": "Test"}}]}}
        >>> blocks = [{"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Content"}}]}}]
        >>> # page_id = create_paper_page(token, db_id, props, blocks)
    """
    try:
        # Initialize Notion client
        client = Client(auth=token)

        # Create page with blocks
        page_id = create_page_with_blocks(client, db_id, properties, blocks)

        return page_id

    except APIResponseError as e:
        # APIResponseError has code and message attributes
        error_msg = getattr(e, "message", str(e))
        error_code = getattr(e, "code", "unknown")
        raise NotionAPIError(
            f"Notion API error ({error_code}): {error_msg}", file_path=None
        ) from e
    except Exception as e:
        raise NotionAPIError(
            f"Failed to create Notion page: {str(e)}", file_path=None
        ) from e


def create_page_with_blocks(
    client: Client, db_id: str, properties: Dict, blocks: List[Dict]
) -> str:
    """
    Internal helper to create a Notion page using the SDK.

    Args:
        client: Initialized Notion Client instance
        db_id: Notion database ID
        properties: Page properties dict
        blocks: List of block dicts

    Returns:
        Created page ID (string)

    Raises:
        NotionAPIError: If page creation fails
    """
    try:
        # Create page with properties and blocks
        response = client.pages.create(
            parent={"database_id": db_id},
            properties=properties,
            children=blocks,
        )

        # Extract page ID from response
        page_id = response.get("id")
        if not page_id:
            raise NotionAPIError(
                "Page created but no ID returned in response", file_path=None
            )

        return page_id

    except APIResponseError as e:
        # APIResponseError has code and message attributes
        error_msg = getattr(e, "message", str(e))
        error_code = getattr(e, "code", "unknown")
        raise NotionAPIError(
            f"Notion API error creating page ({error_code}): {error_msg}", file_path=None
        ) from e
    except Exception as e:
        if isinstance(e, NotionAPIError):
            raise
        raise NotionAPIError(
            f"Unexpected error creating Notion page: {str(e)}", file_path=None
        ) from e
