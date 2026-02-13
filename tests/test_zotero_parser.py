"""Unit tests for Zotero parser module."""

import pytest
from pathlib import Path

from paper_reviewer.errors import BibTeXParseError
from paper_reviewer.models import PaperPair
from paper_reviewer.zotero_parser import (
    extract_pdf_path_from_file_field,
    parse_zotero_bib_file,
)


class TestExtractPdfPathFromFileField:
    """Test extract_pdf_path_from_file_field function."""

    def test_windows_path_with_escaped_backslashes(self, temp_dir):
        """Test Windows path with escaped backslashes (Zotero format)."""
        # Create a test PDF file
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_text("test content")

        # Zotero format: C\:\\Users\\... (escaped backslashes)
        # After bibtexparser, might be C:\\Users\\... (double backslash)
        # We need to handle both
        test_path = str(pdf_file).replace("\\", "\\\\")  # Double backslash for Windows
        file_field = f"{{PDF:{test_path}:application/pdf}}"

        result = extract_pdf_path_from_file_field(file_field)

        assert result is not None
        assert result == pdf_file
        assert result.exists()

    def test_windows_path_normalized(self, temp_dir):
        """Test Windows path that's already normalized."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_text("test content")

        # Already normalized path
        test_path = str(pdf_file)
        file_field = f"{{PDF:{test_path}:application/pdf}}"

        result = extract_pdf_path_from_file_field(file_field)

        assert result is not None
        assert result == pdf_file

    def test_unix_path(self, temp_dir):
        """Test Unix path format."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_text("test content")

        # Unix path format
        test_path = f"/home/user/papers/{pdf_file.name}"
        # Create the file at that location for testing
        unix_path = temp_dir / "home" / "user" / "papers"
        unix_path.mkdir(parents=True, exist_ok=True)
        unix_pdf = unix_path / pdf_file.name
        unix_pdf.write_text("test content")

        file_field = f"{{PDF:{str(unix_pdf).replace(chr(92), '/')}:application/pdf}}"

        result = extract_pdf_path_from_file_field(file_field)

        assert result is not None
        assert result.exists()

    def test_invalid_format(self):
        """Test invalid file field format."""
        file_field = "invalid format"
        result = extract_pdf_path_from_file_field(file_field)
        assert result is None

    def test_missing_pdf_prefix(self):
        """Test file field without PDF prefix."""
        file_field = "{DOC:/path/to/file.doc:application/msword}"
        result = extract_pdf_path_from_file_field(file_field)
        assert result is None

    def test_nonexistent_path(self):
        """Test with non-existent file path."""
        file_field = "{PDF:/nonexistent/path/file.pdf:application/pdf}"
        result = extract_pdf_path_from_file_field(file_field)
        assert result is None

    def test_empty_string(self):
        """Test with empty string."""
        result = extract_pdf_path_from_file_field("")
        assert result is None

    def test_none_value(self):
        """Test with None value."""
        result = extract_pdf_path_from_file_field(None)
        assert result is None


class TestParseZoteroBibFile:
    """Test parse_zotero_bib_file function."""

    def test_parse_valid_zotero_bib_with_file_field(self, temp_dir):
        """Test parsing Zotero BibTeX file with file field."""
        # Create test PDF
        pdf_file = temp_dir / "test_paper.pdf"
        pdf_file.write_text("test PDF content")

        # Create BibTeX file with Zotero file field format
        bib_file = temp_dir / "test.bib"
        pdf_path_str = str(pdf_file).replace("\\", "\\\\")  # Escape for Windows
        bib_file.write_text(
            f"""@article{{test2024,
  title={{Test Paper Title}},
  author={{Doe, John}},
  year={{2024}},
  file={{PDF:{pdf_path_str}:application/pdf}}
}}"""
        )

        paper_pairs = parse_zotero_bib_file(bib_file)

        assert len(paper_pairs) == 1
        assert isinstance(paper_pairs[0], PaperPair)
        assert paper_pairs[0].metadata.bib_key == "test2024"
        assert paper_pairs[0].metadata.title == "Test Paper Title"
        assert paper_pairs[0].pdf_path == pdf_file
        assert paper_pairs[0].pdf_path.exists()

    def test_parse_multiple_entries(self, temp_dir):
        """Test parsing BibTeX file with multiple entries."""
        # Create test PDFs
        pdf1 = temp_dir / "paper1.pdf"
        pdf1.write_text("content1")
        pdf2 = temp_dir / "paper2.pdf"
        pdf2.write_text("content2")

        bib_file = temp_dir / "test.bib"
        pdf1_str = str(pdf1).replace("\\", "\\\\")
        pdf2_str = str(pdf2).replace("\\", "\\\\")
        bib_file.write_text(
            f"""@article{{test2024,
  title={{First Paper}},
  file={{PDF:{pdf1_str}:application/pdf}}
}}
@article{{test2023,
  title={{Second Paper}},
  file={{PDF:{pdf2_str}:application/pdf}}
}}"""
        )

        paper_pairs = parse_zotero_bib_file(bib_file)

        assert len(paper_pairs) == 2
        assert paper_pairs[0].metadata.bib_key == "test2024"
        assert paper_pairs[1].metadata.bib_key == "test2023"
        assert paper_pairs[0].pdf_path == pdf1
        assert paper_pairs[1].pdf_path == pdf2

    def test_skip_entry_without_file_field(self, temp_dir):
        """Test that entries without file field are skipped."""
        bib_file = temp_dir / "test.bib"
        bib_file.write_text(
            """@article{test2024,
  title={Test Paper},
  author={Doe, John}
}"""
        )

        with pytest.raises(BibTeXParseError) as exc_info:
            parse_zotero_bib_file(bib_file)
        assert "No valid entries with PDF paths" in str(exc_info.value)

    def test_skip_entry_with_invalid_file_field(self, temp_dir):
        """Test that entries with invalid file field are skipped."""
        bib_file = temp_dir / "test.bib"
        bib_file.write_text(
            """@article{test2024,
  title={Test Paper},
  file={PDF:/nonexistent/path.pdf:application/pdf}
}"""
        )

        with pytest.raises(BibTeXParseError) as exc_info:
            parse_zotero_bib_file(bib_file)
        assert "No valid entries with PDF paths" in str(exc_info.value)

    def test_mixed_valid_and_invalid_entries(self, temp_dir):
        """Test file with both valid and invalid entries."""
        pdf_file = temp_dir / "valid.pdf"
        pdf_file.write_text("content")

        bib_file = temp_dir / "test.bib"
        pdf_str = str(pdf_file).replace("\\", "\\\\")
        bib_file.write_text(
            f"""@article{{valid2024,
  title={{Valid Paper}},
  file={{PDF:{pdf_str}:application/pdf}}
}}
@article{{invalid2024,
  title={{Invalid Paper}},
  file={{PDF:/nonexistent/path.pdf:application/pdf}}
}}
@article{{no_file2024,
  title={{No File Paper}}
}}"""
        )

        paper_pairs = parse_zotero_bib_file(bib_file)

        # Should only return the valid entry
        assert len(paper_pairs) == 1
        assert paper_pairs[0].metadata.bib_key == "valid2024"

    def test_file_not_found(self, temp_dir):
        """Test FileNotFoundError for non-existent BibTeX file."""
        bib_file = temp_dir / "nonexistent.bib"

        with pytest.raises(FileNotFoundError):
            parse_zotero_bib_file(bib_file)

    def test_invalid_file_path(self, temp_dir):
        """Test error when path is a directory."""
        with pytest.raises(BibTeXParseError):
            parse_zotero_bib_file(temp_dir)

    def test_empty_file(self, temp_dir):
        """Test parsing empty BibTeX file."""
        bib_file = temp_dir / "empty.bib"
        bib_file.write_text("")

        with pytest.raises(BibTeXParseError) as exc_info:
            parse_zotero_bib_file(bib_file)
        assert "No entries found" in str(exc_info.value) or "No valid entries" in str(
            exc_info.value
        )

    def test_zotero_sample_format(self, temp_dir):
        """Test with Zotero sample format (Windows path with escaped backslashes)."""
        # Create a test PDF
        pdf_file = temp_dir / "Chi et al. - 2024 - Universal Manipulation Interface In-The-Wild Robot Teaching Without In-The-Wild Robots.pdf"
        pdf_file.write_text("test content")

        # Simulate Zotero format: C\:\\Users\\... (with escaped backslashes)
        # In actual Zotero export, it might be: C\:\\Users\\haoyan.li\\Zotero\\storage\\F8XWENS7\\file.pdf
        # We'll use the temp_dir path instead
        pdf_path_str = str(pdf_file).replace("\\", "\\\\")
        
        bib_file = temp_dir / "zotero_sample.bib"
        bib_file.write_text(
            f"""@inproceedings{{chi_universal_2024,
	title = {{Universal Manipulation Interface}},
	author = {{Chi, Cheng}},
	year = {{2024}},
	file = {{PDF:{pdf_path_str}:application/pdf}},
}}"""
        )

        paper_pairs = parse_zotero_bib_file(bib_file)

        assert len(paper_pairs) == 1
        assert paper_pairs[0].metadata.bib_key == "chi_universal_2024"
        assert paper_pairs[0].pdf_path == pdf_file
        assert paper_pairs[0].pdf_path.exists()
