"""Integration tests for paper-reviewer-cli workflow."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from paper_reviewer.errors import GeminiAPIError, NotionAPIError
from paper_reviewer.gemini_client import analyze_paper, parse_gemini_response, upload_pdf, wait_for_file_processing
from paper_reviewer.main import main, process_single_paper
from paper_reviewer.notion_client import create_paper_page, create_page_with_blocks
from paper_reviewer.notion_converter import (
    create_bullet_block,
    create_heading_block,
    create_paragraph_block,
    split_content_smartly,
    transform_to_notion_blocks,
)
from paper_reviewer.notion_properties import build_notion_properties, extract_url_or_doi, format_authors
from paper_reviewer.scanner import scan_directory, scan_single_directory
from tests.mocks import (
    create_mock_gemini_client,
    create_mock_gemini_response,
    create_mock_notion_api_error,
    create_mock_notion_client,
)


class TestScannerIntegration:
    """Test scanner module integration."""

    def test_scan_single_directory(self):
        """Test scanning a single directory with .bib and .pdf."""
        fixture_dir = Path(__file__).parent / "fixtures" / "integration" / "valid_paper"

        pairs = scan_single_directory(fixture_dir)

        assert len(pairs) == 1
        assert pairs[0].metadata.bib_key == "test2024"
        assert pairs[0].pdf_path.exists()
        assert pairs[0].pdf_path.name == "paper.pdf"

    def test_scan_directory_single_mode(self):
        """Test scan_directory in single directory mode."""
        fixture_dir = Path(__file__).parent / "fixtures" / "integration" / "valid_paper"

        pairs = scan_directory(fixture_dir)

        assert len(pairs) == 1
        assert pairs[0].metadata.bib_key == "test2024"

    def test_scan_directory_recursive_mode(self):
        """Test scan_directory in recursive mode."""
        fixture_dir = Path(__file__).parent / "fixtures" / "integration" / "multiple_papers"

        pairs = scan_directory(fixture_dir)

        assert len(pairs) >= 2
        bib_keys = [p.metadata.bib_key for p in pairs]
        assert "paper1_2024" in bib_keys
        assert "paper2_2024" in bib_keys

    def test_scan_directory_empty(self, temp_dir):
        """Test scanning empty directory."""
        pairs = scan_directory(temp_dir)

        assert len(pairs) == 0


class TestNotionConverter:
    """Test Notion converter module."""

    def test_transform_to_notion_blocks(self):
        """Test converting review JSON to Notion blocks."""
        review_json = create_mock_gemini_response()

        blocks = transform_to_notion_blocks(review_json)

        assert len(blocks) > 0
        # Should have headings and content blocks
        block_types = [b.get("type") for b in blocks]
        assert "heading_2" in block_types

    def test_create_heading_block(self):
        """Test creating heading block."""
        block = create_heading_block("Test Heading")

        assert block["type"] == "heading_2"
        assert block["heading_2"]["rich_text"][0]["text"]["content"] == "Test Heading"

    def test_create_paragraph_block(self):
        """Test creating paragraph block."""
        text = "This is a test paragraph."
        block = create_paragraph_block(text)

        assert block["type"] == "paragraph"
        assert block["paragraph"]["rich_text"][0]["text"]["content"] == text

    def test_create_paragraph_block_truncation(self):
        """Test paragraph block truncation at 2000 chars."""
        long_text = "x" * 3000
        block = create_paragraph_block(long_text)

        assert len(block["paragraph"]["rich_text"][0]["text"]["content"]) == 2000

    def test_create_bullet_block(self):
        """Test creating bullet block."""
        text = "Bullet point"
        block = create_bullet_block(text)

        assert block["type"] == "bulleted_list_item"
        assert block["bulleted_list_item"]["rich_text"][0]["text"]["content"] == text

    def test_create_bullet_block_truncation(self):
        """Test bullet block truncation at 2000 chars."""
        long_text = "x" * 3000
        block = create_bullet_block(long_text)

        assert len(block["bulleted_list_item"]["rich_text"][0]["text"]["content"]) == 2000

    def test_split_content_smartly_markdown_list(self):
        """Test splitting markdown-style list."""
        content = "- Item 1\n- Item 2\n- Item 3"
        items = split_content_smartly(content)

        assert len(items) == 3
        assert "Item 1" in items[0]
        assert "Item 2" in items[1]

    def test_split_content_smartly_multiline(self):
        """Test splitting multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        items = split_content_smartly(content)

        assert len(items) == 3

    def test_split_content_smartly_single_line(self):
        """Test single line content."""
        content = "Single paragraph"
        items = split_content_smartly(content)

        assert len(items) == 1
        assert items[0] == "Single paragraph"

    def test_split_content_smartly_empty(self):
        """Test empty content."""
        items = split_content_smartly("")

        assert len(items) == 0

    def test_transform_empty_fields(self):
        """Test transformation with empty fields."""
        review_json = {
            "summary": "Test",
            "novelty": "",
            "methodology": "Test",
            "validation": "",
            "discussion": "",
            "next_steps": "",
        }

        blocks = transform_to_notion_blocks(review_json)

        # Should only include non-empty fields
        assert len(blocks) > 0


class TestNotionProperties:
    """Test Notion properties builder."""

    def test_build_notion_properties_complete(self, sample_bibtex_entry):
        """Test building properties with complete entry."""
        properties = build_notion_properties(sample_bibtex_entry)

        assert "Name" in properties
        assert properties["Name"]["title"][0]["text"]["content"] == sample_bibtex_entry.title
        assert "Authors" in properties
        assert "Year" in properties
        assert properties["Year"]["number"] == sample_bibtex_entry.year
        assert "BibTeX Key" in properties
        assert "URL/DOI" in properties

    def test_build_notion_properties_minimal(self, minimal_bibtex_entry):
        """Test building properties with minimal entry."""
        properties = build_notion_properties(minimal_bibtex_entry)

        assert "Name" in properties
        assert "BibTeX Key" in properties
        # Optional fields may or may not be present
        assert properties["Name"]["title"][0]["text"]["content"] == minimal_bibtex_entry.title

    def test_format_authors(self):
        """Test formatting authors list."""
        authors = ["John Doe", "Jane Smith"]
        formatted = format_authors(authors)

        assert len(formatted) == 2
        assert formatted[0]["name"] == "John Doe"
        assert formatted[1]["name"] == "Jane Smith"

    def test_format_authors_empty(self):
        """Test formatting empty authors list."""
        formatted = format_authors([])

        assert len(formatted) == 0

    def test_extract_url_or_doi_url(self, sample_bibtex_entry):
        """Test extracting URL."""
        url = extract_url_or_doi(sample_bibtex_entry)

        assert url is not None
        assert "example.com" in url

    def test_extract_url_or_doi_doi_only(self):
        """Test extracting DOI when no URL."""
        from paper_reviewer.models import BibTeXEntry

        entry = BibTeXEntry(title="Test", bib_key="test", doi="10.1000/test")
        url = extract_url_or_doi(entry)

        assert url is not None
        assert "doi.org" in url or "10.1000" in url

    def test_extract_url_or_doi_none(self, minimal_bibtex_entry):
        """Test extracting when neither URL nor DOI."""
        url = extract_url_or_doi(minimal_bibtex_entry)

        assert url is None


class TestGeminiAPIMocking:
    """Test Gemini API with mocks."""

    def test_parse_gemini_response_valid(self):
        """Test parsing valid Gemini response."""
        mock_response = MagicMock()
        response_data = create_mock_gemini_response()
        mock_response.text = json.dumps(response_data)

        result = parse_gemini_response(mock_response)

        assert result["summary"] == response_data["summary"]
        assert result["novelty"] == response_data["novelty"]
        assert len(result) == 6

    def test_parse_gemini_response_missing_fields(self):
        """Test parsing response with missing fields."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"summary": "Test"})

        result = parse_gemini_response(mock_response)

        assert result["summary"] == "Test"
        # Missing fields should be empty strings
        assert result["novelty"] == ""

    def test_parse_gemini_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        mock_response = MagicMock()
        mock_response.text = "Not valid JSON"

        with pytest.raises(GeminiAPIError):
            parse_gemini_response(mock_response)

    def test_parse_gemini_response_missing_text(self):
        """Test parsing response without text attribute."""
        mock_response = MagicMock()
        del mock_response.text

        with pytest.raises(GeminiAPIError):
            parse_gemini_response(mock_response)

    @patch("paper_reviewer.gemini_client.genai.Client")
    def test_upload_pdf_success(self, mock_client_class, sample_paper_pair):
        """Test successful PDF upload."""
        mock_client = MagicMock()
        mock_file_handle = MagicMock()
        mock_file_handle.name = "files/test"
        mock_file_handle.state = "ACTIVE"
        mock_client.files.upload.return_value = mock_file_handle
        mock_client_class.return_value = mock_client

        result = upload_pdf(sample_paper_pair.pdf_path, "test-key", client=mock_client)

        assert result == mock_file_handle
        mock_client.files.upload.assert_called_once()

    @patch("paper_reviewer.gemini_client.genai.Client")
    def test_upload_pdf_file_not_found(self, mock_client_class):
        """Test upload with non-existent file."""
        fake_path = Path("/nonexistent/file.pdf")

        with pytest.raises(FileNotFoundError):
            upload_pdf(fake_path, "test-key")

    @patch("paper_reviewer.gemini_client.genai.Client")
    def test_wait_for_file_processing_active(self, mock_client_class):
        """Test waiting for file processing when already active."""
        mock_client = MagicMock()
        mock_file_handle = MagicMock()
        mock_file_handle.name = "files/test"
        mock_file_handle.state = "ACTIVE"
        mock_client.files.get.return_value = mock_file_handle
        mock_client_class.return_value = mock_client

        result = wait_for_file_processing(mock_file_handle, mock_client, timeout=10)

        assert result is True

    @patch("paper_reviewer.gemini_client.genai.Client")
    def test_wait_for_file_processing_failed(self, mock_client_class):
        """Test waiting for file processing when it fails."""
        mock_client = MagicMock()
        mock_file_handle = MagicMock()
        mock_file_handle.name = "files/test"
        mock_file_handle.state = "FAILED"
        mock_client.files.get.return_value = mock_file_handle
        mock_client_class.return_value = mock_client

        with pytest.raises(GeminiAPIError):
            wait_for_file_processing(mock_file_handle, mock_client, timeout=10)

    @patch("paper_reviewer.gemini_client.genai.Client")
    @patch("paper_reviewer.gemini_client.upload_pdf")
    @patch("paper_reviewer.gemini_client.wait_for_file_processing")
    def test_analyze_paper_success(self, mock_wait, mock_upload, mock_client_class, sample_paper_pair):
        """Test successful paper analysis."""
        # Setup mocks
        mock_client = MagicMock()
        mock_file_handle = MagicMock()
        mock_file_handle.name = "files/test"
        mock_file_handle.state = "ACTIVE"
        mock_client_class.return_value = mock_client
        mock_upload.return_value = mock_file_handle
        mock_wait.return_value = True

        response_data = create_mock_gemini_response()
        mock_response = MagicMock()
        mock_response.text = json.dumps(response_data)
        mock_client.files.get.return_value = mock_file_handle
        mock_client.models.generate_content.return_value = mock_response

        result = analyze_paper(sample_paper_pair.pdf_path, "test-key")

        assert result["summary"] == response_data["summary"]
        assert len(result) == 6


class TestNotionAPIMocking:
    """Test Notion API with mocks."""

    def test_create_page_with_blocks_success(self, sample_config):
        """Test successful page creation."""
        mock_client = create_mock_notion_client(None, "test-page-123")
        properties = {"Name": {"title": [{"type": "text", "text": {"content": "Test"}}]}}
        blocks = [{"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Content"}}]}}]

        page_id = create_page_with_blocks(mock_client, sample_config.notion_database_id, properties, blocks)

        assert page_id == "test-page-123"
        mock_client.pages.create.assert_called_once()

    def test_create_page_with_blocks_no_id(self, sample_config):
        """Test page creation when no ID returned."""
        mock_client = MagicMock()
        mock_client.pages.create.return_value = {}  # No ID

        properties = {"Name": {"title": [{"type": "text", "text": {"content": "Test"}}]}}
        blocks = []

        with pytest.raises(NotionAPIError):
            create_page_with_blocks(mock_client, sample_config.notion_database_id, properties, blocks)

    def test_create_paper_page_success(self, sample_config):
        """Test successful paper page creation."""
        mock_client = create_mock_notion_client(None, "test-page-123")

        with patch("paper_reviewer.notion_client.Client", return_value=mock_client):
            properties = {"Name": {"title": [{"type": "text", "text": {"content": "Test"}}]}}
            blocks = []

            page_id = create_paper_page(sample_config.notion_token, sample_config.notion_database_id, properties, blocks)

            assert page_id == "test-page-123"


class TestProcessSinglePaper:
    """Test process_single_paper function."""

    @patch("paper_reviewer.main.analyze_paper")
    @patch("paper_reviewer.main.create_paper_page")
    def test_process_single_paper_success(self, mock_create_page, mock_analyze, sample_paper_pair, sample_config):
        """Test successful paper processing."""
        mock_analyze.return_value = create_mock_gemini_response()
        mock_create_page.return_value = "test-page-123"

        result = process_single_paper(sample_paper_pair, sample_config)

        assert result is True
        mock_analyze.assert_called_once()
        mock_create_page.assert_called_once()

    @patch("paper_reviewer.main.analyze_paper")
    def test_process_single_paper_gemini_error(self, mock_analyze, sample_paper_pair, sample_config):
        """Test paper processing with Gemini error."""
        mock_analyze.side_effect = GeminiAPIError("API error", file_path=str(sample_paper_pair.pdf_path))

        result = process_single_paper(sample_paper_pair, sample_config)

        assert result is False

    @patch("paper_reviewer.main.analyze_paper")
    @patch("paper_reviewer.main.create_paper_page")
    def test_process_single_paper_notion_error(self, mock_create_page, mock_analyze, sample_paper_pair, sample_config):
        """Test paper processing with Notion error."""
        mock_analyze.return_value = create_mock_gemini_response()
        mock_create_page.side_effect = NotionAPIError("Notion error", file_path=None)

        result = process_single_paper(sample_paper_pair, sample_config)

        assert result is False


class TestMainCLI:
    """Test main CLI function."""

    @patch("paper_reviewer.main.scan_directory")
    @patch("paper_reviewer.main.load_config")
    @patch("paper_reviewer.main.process_single_paper")
    def test_main_success(self, mock_process, mock_config, mock_scan, sample_config, sample_paper_pair):
        """Test main function with successful processing."""
        mock_config.return_value = sample_config
        mock_scan.return_value = [sample_paper_pair]
        mock_process.return_value = True

        exit_code = main(sample_paper_pair.pdf_path.parent)

        assert exit_code == 0
        mock_process.assert_called_once()

    @patch("paper_reviewer.main.scan_directory")
    @patch("paper_reviewer.main.load_config")
    def test_main_no_papers(self, mock_config, mock_scan, sample_config):
        """Test main function with no papers found."""
        mock_config.return_value = sample_config
        mock_scan.return_value = []

        exit_code = main(Path(__file__).parent)

        assert exit_code == 0

    @patch("paper_reviewer.main.load_config")
    def test_main_config_error(self, mock_config):
        """Test main function with configuration error."""
        mock_config.side_effect = ValueError("Config error")

        exit_code = main(Path(__file__).parent)

        assert exit_code == 1

    @patch("paper_reviewer.main.scan_directory")
    @patch("paper_reviewer.main.load_config")
    def test_main_scan_error(self, mock_config, mock_scan, sample_config):
        """Test main function with scan error."""
        mock_config.return_value = sample_config
        mock_scan.side_effect = Exception("Scan error")

        exit_code = main(Path(__file__).parent)

        assert exit_code == 1
