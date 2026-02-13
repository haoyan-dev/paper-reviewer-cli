"""Custom exceptions for paper reviewer CLI."""


class PaperReviewerError(Exception):
    """Base exception for all paper reviewer errors."""

    def __init__(self, message: str, file_path: str | None = None):
        """
        Initialize error with message and optional file path.

        Args:
            message: Error message
            file_path: Optional path to file that caused the error
        """
        self.message = message
        self.file_path = file_path
        if file_path:
            super().__init__(f"{message} (file: {file_path})")
        else:
            super().__init__(message)


class BibTeXParseError(PaperReviewerError):
    """Raised when BibTeX file parsing fails."""

    pass


class PDFNotFoundError(PaperReviewerError):
    """Raised when PDF file cannot be found or matched."""

    pass


class GeminiAPIError(PaperReviewerError):
    """Raised when Gemini API calls fail."""

    pass


class NotionAPIError(PaperReviewerError):
    """Raised when Notion API calls fail."""

    pass
