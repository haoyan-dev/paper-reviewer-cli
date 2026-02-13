"""Unit tests for PDF finder module."""

import logging
from pathlib import Path

import pytest

from paper_reviewer.pdf_finder import find_pdf_in_directory


class TestFindPdfInDirectory:
    """Test find_pdf_in_directory function."""

    def test_find_single_pdf(self, temp_dir):
        """Test finding PDF in directory with single PDF."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        result = find_pdf_in_directory(temp_dir)

        assert result is not None
        assert result == pdf_file
        assert result.exists()

    def test_find_pdf_case_insensitive_lower(self, temp_dir):
        """Test finding PDF with lowercase extension."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        result = find_pdf_in_directory(temp_dir)

        assert result is not None
        assert result.name == "test.pdf"

    def test_find_pdf_case_insensitive_upper(self, temp_dir):
        """Test finding PDF with uppercase extension."""
        pdf_file = temp_dir / "test.PDF"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        result = find_pdf_in_directory(temp_dir)

        assert result is not None
        assert result.name == "test.PDF"

    def test_find_pdf_case_insensitive_mixed(self, temp_dir):
        """Test finding PDF with mixed case extension."""
        pdf_file = temp_dir / "test.Pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        result = find_pdf_in_directory(temp_dir)

        assert result is not None
        assert result.name == "test.Pdf"

    def test_find_pdf_recursive(self, temp_dir):
        """Test finding PDF in subdirectory."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        pdf_file = subdir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        result = find_pdf_in_directory(temp_dir)

        assert result is not None
        assert result == pdf_file
        assert "subdir" in str(result)

    def test_find_pdf_nested_multiple_levels(self, temp_dir):
        """Test finding PDF nested multiple levels deep."""
        level1 = temp_dir / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)
        pdf_file = level2 / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        result = find_pdf_in_directory(temp_dir)

        assert result is not None
        assert result == pdf_file

    def test_multiple_pdfs_returns_first(self, temp_dir, caplog):
        """Test behavior when multiple PDFs exist."""
        pdf1 = temp_dir / "first.pdf"
        pdf2 = temp_dir / "second.pdf"
        pdf1.write_bytes(b"%PDF-1.4\n")
        pdf2.write_bytes(b"%PDF-1.4\n")

        with caplog.at_level(logging.WARNING):
            result = find_pdf_in_directory(temp_dir)

        assert result is not None
        # Should return first one found
        assert result in [pdf1, pdf2]
        # Should log warning
        assert "Multiple PDF files" in caplog.text

    def test_no_pdf_files(self, temp_dir):
        """Test directory with no PDF files."""
        # Create some non-PDF files
        (temp_dir / "test.txt").write_text("test")
        (temp_dir / "test.doc").write_text("test")

        result = find_pdf_in_directory(temp_dir)

        assert result is None

    def test_nonexistent_directory(self):
        """Test non-existent directory."""
        nonexistent = Path("/nonexistent/directory/that/does/not/exist")

        result = find_pdf_in_directory(nonexistent)

        assert result is None

    def test_path_not_directory(self, temp_dir):
        """Test path that is not a directory."""
        file_path = temp_dir / "not_a_dir.txt"
        file_path.write_text("test")

        result = find_pdf_in_directory(file_path)

        assert result is None

    def test_empty_directory(self, temp_dir):
        """Test empty directory."""
        result = find_pdf_in_directory(temp_dir)

        assert result is None

    def test_directory_with_only_directories(self, temp_dir):
        """Test directory containing only subdirectories."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        result = find_pdf_in_directory(temp_dir)

        assert result is None

    def test_only_files_not_directories(self, temp_dir):
        """Test that only actual files are returned, not directories."""
        # Create a directory named like a PDF
        pdf_dir = temp_dir / "fake.pdf"
        pdf_dir.mkdir()

        result = find_pdf_in_directory(temp_dir)

        # Should not return the directory
        assert result is None or result.is_file()

    def test_from_fixture_paper1(self):
        """Test finding PDF in paper1 fixture."""
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_papers" / "paper1"

        result = find_pdf_in_directory(fixture_dir)

        assert result is not None
        assert result.name == "paper1.pdf"

    def test_from_fixture_paper2(self):
        """Test finding PDF in paper2 fixture (nested)."""
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_papers" / "paper2"

        result = find_pdf_in_directory(fixture_dir)

        assert result is not None
        assert "paper2.PDF" in result.name

    def test_from_fixture_paper3_multiple(self, caplog):
        """Test finding PDF in paper3 fixture with multiple PDFs."""
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_papers" / "paper3"

        with caplog.at_level(logging.WARNING):
            result = find_pdf_in_directory(fixture_dir)

        assert result is not None
        assert result.exists()
        # Should log warning about multiple PDFs
        assert "Multiple PDF files" in caplog.text

    def test_from_fixture_empty_dir(self):
        """Test finding PDF in empty directory fixture."""
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_papers" / "empty_dir"

        result = find_pdf_in_directory(fixture_dir)

        assert result is None
