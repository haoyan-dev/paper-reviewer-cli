"""Mock utilities for testing API integrations."""

import json
from typing import Dict
from unittest.mock import MagicMock


def create_mock_gemini_response() -> Dict[str, str]:
    """
    Create a mock Gemini API response dictionary.

    Returns:
        Dictionary with all required review fields
    """
    return {
        "summary": "Test summary",
        "novelty": "Test novelty",
        "methodology": "Test methodology",
        "validation": "Test validation",
        "discussion": "Test discussion",
        "next_steps": "Test next steps",
    }


def create_mock_gemini_client(mocker, response_data: Dict[str, str] = None):
    """
    Create a mocked Gemini client.

    Args:
        mocker: pytest-mock mocker fixture
        response_data: Optional custom response data

    Returns:
        Mocked genai.Client instance
    """
    if response_data is None:
        response_data = create_mock_gemini_response()

    # Create mock file handle
    mock_file_handle = MagicMock()
    mock_file_handle.name = "files/test_file_123"
    mock_file_handle.state = "ACTIVE"

    # Create mock response
    mock_response = MagicMock()
    mock_response.text = json.dumps(response_data)  # Proper JSON string

    # Create mock client
    mock_client = MagicMock()
    mock_client.files.upload.return_value = mock_file_handle
    mock_client.files.get.return_value = mock_file_handle
    mock_client.models.generate_content.return_value = mock_response

    return mock_client


def create_mock_notion_client(mocker, page_id: str = "test-page-id-12345"):
    """
    Create a mocked Notion client.

    Args:
        mocker: pytest-mock mocker fixture
        page_id: Optional custom page ID to return

    Returns:
        Mocked notion_client.Client instance
    """
    mock_client = MagicMock()
    mock_response = {"id": page_id}
    mock_client.pages.create.return_value = mock_response

    return mock_client


def create_mock_notion_api_error(mocker, error_code: str = "object_not_found", message: str = "Not found"):
    """
    Create a mock Notion API error.

    Args:
        mocker: pytest-mock mocker fixture
        error_code: Error code string
        message: Error message string

    Returns:
        Mock APIResponseError exception
    """
    from notion_client import APIResponseError

    mock_error = MagicMock(spec=APIResponseError)
    mock_error.code = error_code
    mock_error.message = message
    return mock_error
