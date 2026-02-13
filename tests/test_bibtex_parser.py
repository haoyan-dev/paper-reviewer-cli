"""Unit tests for BibTeX parser module."""

import pytest
from pathlib import Path

from paper_reviewer.bibtex_parser import extract_metadata, parse_bibtex_file
from paper_reviewer.errors import BibTeXParseError
from paper_reviewer.models import BibTeXEntry


class TestParseBibtexFile:
    """Test parse_bibtex_file function."""

    def test_parse_valid_single_entry(self, temp_dir):
        """Test parsing a valid BibTeX file with single entry."""
        bib_file = temp_dir / "test.bib"
        bib_file.write_text(
            """@article{test2024,
  title={Test Paper Title},
  author={Doe, John and Smith, Jane},
  year={2024},
  url={https://example.com/paper},
  doi={10.1000/test.doi}
}"""
        )

        entries = parse_bibtex_file(bib_file)

        assert len(entries) == 1
        assert entries[0].title == "Test Paper Title"
        assert entries[0].bib_key == "test2024"
        assert entries[0].year == 2024
        assert str(entries[0].url) == "https://example.com/paper"
        assert entries[0].doi == "10.1000/test.doi"

    def test_parse_multiple_entries(self, temp_dir):
        """Test parsing BibTeX file with multiple entries."""
        bib_file = temp_dir / "test.bib"
        bib_file.write_text(
            """@article{test2024,
  title={First Paper},
  ID={test2024}
}
@article{test2023,
  title={Second Paper},
  ID={test2023}
}"""
        )

        entries = parse_bibtex_file(bib_file)

        assert len(entries) == 2
        assert entries[0].bib_key == "test2024"
        assert entries[1].bib_key == "test2023"

    def test_parse_from_fixture(self):
        """Test parsing sample.bib fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample.bib"
        entries = parse_bibtex_file(fixture_path)

        assert len(entries) >= 2
        # Check first entry
        test_entry = next(e for e in entries if e.bib_key == "test2024")
        assert test_entry.title == "Test Paper Title"
        # Author parsing may split "Doe, John and Smith, Jane" into ["Doe", "John", "Smith", "Jane"]
        # or keep as ["Doe, John", "Smith, Jane"] - check for either format
        author_names = " ".join(test_entry.authors)
        assert "John" in author_names and "Doe" in author_names
        assert test_entry.year == 2024

    def test_parse_utf8_encoding(self):
        """Test parsing UTF-8 encoded BibTeX file."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_utf8.bib"
        entries = parse_bibtex_file(fixture_path)

        assert len(entries) == 1
        assert "Unicode" in entries[0].title
        assert "Café" in entries[0].title or "naïve" in entries[0].title

    def test_file_not_found(self, temp_dir):
        """Test FileNotFoundError for non-existent file."""
        bib_file = temp_dir / "nonexistent.bib"

        with pytest.raises(FileNotFoundError):
            parse_bibtex_file(bib_file)

    def test_invalid_file_path(self, temp_dir):
        """Test error when path is a directory."""
        with pytest.raises(BibTeXParseError):
            parse_bibtex_file(temp_dir)

    def test_empty_file(self):
        """Test parsing empty BibTeX file."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_empty.bib"

        with pytest.raises(BibTeXParseError) as exc_info:
            parse_bibtex_file(fixture_path)
        assert "No valid entries" in str(exc_info.value)

    def test_malformed_bibtex(self):
        """Test parsing malformed BibTeX file."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_malformed.bib"

        # Should either raise error or skip malformed entry
        try:
            entries = parse_bibtex_file(fixture_path)
            # If it doesn't raise, should have no valid entries
            assert len(entries) == 0
        except BibTeXParseError:
            # Or it should raise an error
            pass

    def test_missing_required_fields(self, temp_dir):
        """Test BibTeX entry with missing required fields."""
        bib_file = temp_dir / "test.bib"
        bib_file.write_text(
            """@article{,
  year={2024}
}"""
        )

        # Should skip entries without title or ID
        try:
            entries = parse_bibtex_file(bib_file)
            assert len(entries) == 0
        except BibTeXParseError:
            # Or raise error if no valid entries
            pass


class TestExtractMetadata:
    """Test extract_metadata function."""

    def test_extract_complete_entry(self):
        """Test extracting metadata from complete entry."""
        entry = {
            "ID": "test2024",
            "title": "Test Paper",
            "author": "John Doe and Jane Smith",
            "year": "2024",
            "url": "https://example.com",
            "doi": "10.1000/test",
        }

        bibtex_entry = extract_metadata(entry)

        assert isinstance(bibtex_entry, BibTeXEntry)
        assert bibtex_entry.bib_key == "test2024"
        assert bibtex_entry.title == "Test Paper"
        assert bibtex_entry.year == 2024
        # HttpUrl normalizes URLs and may add trailing slash
        assert str(bibtex_entry.url).rstrip("/") == "https://example.com"
        assert bibtex_entry.doi == "10.1000/test"

    def test_extract_minimal_entry(self):
        """Test extracting metadata with only required fields."""
        entry = {
            "ID": "minimal2024",
            "title": "Minimal Paper",
        }

        bibtex_entry = extract_metadata(entry)

        assert bibtex_entry.bib_key == "minimal2024"
        assert bibtex_entry.title == "Minimal Paper"
        assert bibtex_entry.year is None
        assert bibtex_entry.url is None
        assert bibtex_entry.doi is None
        assert bibtex_entry.authors == []

    def test_extract_missing_title(self):
        """Test error when title is missing."""
        entry = {
            "ID": "test2024",
        }

        with pytest.raises(BibTeXParseError) as exc_info:
            extract_metadata(entry)
        assert "title" in str(exc_info.value).lower()

    def test_extract_missing_id(self):
        """Test error when ID is missing."""
        entry = {
            "title": "Test Paper",
        }

        with pytest.raises(BibTeXParseError) as exc_info:
            extract_metadata(entry)
        assert "ID" in str(exc_info.value)

    def test_extract_author_parsing_comma(self):
        """Test author parsing with comma separator."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "author": "Doe, John, Smith, Jane",
        }

        bibtex_entry = extract_metadata(entry)

        assert len(bibtex_entry.authors) >= 2
        assert any("Doe" in a for a in bibtex_entry.authors)
        assert any("Smith" in a for a in bibtex_entry.authors)

    def test_extract_author_parsing_and(self):
        """Test author parsing with 'and' separator."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "author": "John Doe and Jane Smith",
        }

        bibtex_entry = extract_metadata(entry)

        assert len(bibtex_entry.authors) >= 2

    def test_extract_author_list(self):
        """Test author parsing from list format."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "author": ["John Doe", "Jane Smith"],
        }

        bibtex_entry = extract_metadata(entry)

        assert len(bibtex_entry.authors) == 2
        assert "John Doe" in bibtex_entry.authors
        assert "Jane Smith" in bibtex_entry.authors

    def test_extract_year_valid(self):
        """Test year parsing with valid year."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "year": "2024",
        }

        bibtex_entry = extract_metadata(entry)

        assert bibtex_entry.year == 2024

    def test_extract_year_invalid(self):
        """Test year parsing with invalid year."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "year": "invalid",
        }

        bibtex_entry = extract_metadata(entry)

        assert bibtex_entry.year is None

    def test_extract_year_out_of_range(self):
        """Test year parsing with out-of-range year."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "year": "1800",  # Below minimum
        }

        bibtex_entry = extract_metadata(entry)

        # Should still parse but might be validated by model
        assert bibtex_entry.year == 1800 or bibtex_entry.year is None

    def test_extract_url_only(self):
        """Test extraction with URL but no DOI."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "url": "https://example.com",
        }

        bibtex_entry = extract_metadata(entry)

        assert bibtex_entry.url is not None
        assert bibtex_entry.doi is None

    def test_extract_doi_only(self):
        """Test extraction with DOI but no URL."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "doi": "10.1000/test",
        }

        bibtex_entry = extract_metadata(entry)

        assert bibtex_entry.doi == "10.1000/test"
        assert bibtex_entry.url is None

    def test_extract_alternative_author_field(self):
        """Test extraction with 'authors' field instead of 'author'."""
        entry = {
            "ID": "test2024",
            "title": "Test",
            "authors": "John Doe",
        }

        bibtex_entry = extract_metadata(entry)

        assert len(bibtex_entry.authors) > 0
