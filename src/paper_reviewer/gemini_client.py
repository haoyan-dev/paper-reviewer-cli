"""Gemini API client for PDF upload and paper analysis."""

import json
import time
from pathlib import Path
from typing import Dict

from google import genai

from .errors import GeminiAPIError
from .gemini_prompts import SYSTEM_INSTRUCTION, USER_PROMPT


def upload_pdf(pdf_path: Path, api_key: str, client: object = None) -> object:
    """
    Upload a PDF file to Gemini File API.

    Args:
        pdf_path: Path to the PDF file
        api_key: Google AI API key
        client: Optional genai.Client instance (creates new one if not provided)

    Returns:
        File handle object with .name and .state attributes

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        GeminiAPIError: If upload fails
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        if client is None:
            client = genai.Client(api_key=api_key)
        file_handle = client.files.upload(file=str(pdf_path))
        return file_handle
    except Exception as e:
        raise GeminiAPIError(f"Failed to upload PDF: {str(e)}", file_path=str(pdf_path)) from e


def wait_for_file_processing(
    file_handle: object, client: object, timeout: int = 300, poll_interval: int = 2
) -> bool:
    """
    Wait for file to finish processing in Gemini API.

    Args:
        file_handle: File handle object from upload_pdf()
        client: genai.Client instance
        timeout: Maximum time to wait in seconds (default: 300)
        poll_interval: Time between polls in seconds (default: 2)

    Returns:
        True if file is ready (ACTIVE), False if timeout

    Raises:
        GeminiAPIError: If file processing fails
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Refresh file state
            file_handle = client.files.get(name=file_handle.name)
            state = file_handle.state

            if state == "ACTIVE":
                return True
            elif state == "FAILED":
                raise GeminiAPIError(
                    f"File processing failed for file: {file_handle.name}"
                )
            elif state == "PROCESSING":
                # Continue polling
                time.sleep(poll_interval)
            else:
                # Unknown state, continue polling
                time.sleep(poll_interval)
        except Exception as e:
            if isinstance(e, GeminiAPIError):
                raise
            # Retry on transient errors
            time.sleep(poll_interval)

    return False


def parse_gemini_response(response: object) -> Dict[str, str]:
    """
    Parse Gemini API response and extract JSON review data.

    Args:
        response: Response object from generate_content()

    Returns:
        Dictionary with 6 fields: summary, novelty, methodology, validation, discussion, next_steps

    Raises:
        GeminiAPIError: If JSON is invalid or missing required fields
    """
    try:
        # Extract text from response
        response_text = response.text
    except AttributeError:
        raise GeminiAPIError("Response object missing 'text' attribute")

    try:
        # Parse JSON
        review_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise GeminiAPIError(f"Failed to parse JSON response: {str(e)}") from e

    # Required fields matching ReviewData model
    required_fields = ["summary", "novelty", "methodology", "validation", "discussion", "next_steps"]

    # Validate and extract fields
    result = {}
    for field in required_fields:
        if field not in review_data:
            # Use empty string as fallback (ReviewData allows empty strings)
            result[field] = ""
        else:
            result[field] = str(review_data[field])

    return result


def analyze_paper(pdf_path: Path, api_key: str) -> Dict[str, str]:
    """
    Analyze a research paper PDF using Gemini API and return structured review.

    Args:
        pdf_path: Path to the PDF file
        api_key: Google AI API key

    Returns:
        Dictionary with 6 fields: summary, novelty, methodology, validation, discussion, next_steps

    Raises:
        GeminiAPIError: If analysis fails at any step
        FileNotFoundError: If PDF file doesn't exist
    """
    # Initialize client
    client = genai.Client(api_key=api_key)

    # Upload PDF (reuse client)
    file_handle = upload_pdf(pdf_path, api_key, client=client)

    # Wait for file processing
    if not wait_for_file_processing(file_handle, client):
        raise GeminiAPIError(
            f"File processing timeout for PDF: {pdf_path}. "
            "File may still be processing."
        )

    # Refresh file handle to ensure it's ACTIVE
    file_handle = client.files.get(name=file_handle.name)

    try:
        # Generate content with system instruction and JSON output
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=[file_handle, USER_PROMPT],
            system_instruction=SYSTEM_INSTRUCTION,
            config={"response_mime_type": "application/json"},
        )

        # Parse response
        review_data = parse_gemini_response(response)

        return review_data

    except GeminiAPIError:
        raise
    except Exception as e:
        raise GeminiAPIError(f"Failed to analyze paper: {str(e)}", file_path=str(pdf_path)) from e
