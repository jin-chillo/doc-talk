"""PDF 프로세서 테스트."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.pdf_processor import PDFProcessor
from src.utils.exceptions import PDFProcessingError


class TestPDFProcessor:
    """PDFProcessor 테스트 클래스."""

    def test_validate_file_valid_pdf(self, test_settings):
        """유효한 PDF 파일 검증."""
        processor = PDFProcessor(test_settings)

        # 가짜 PDF 파일 생성 (작은 크기)
        fake_pdf = BytesIO(b"%PDF-1.4" + b"\x00" * 1000)

        is_valid, error = processor.validate_file(fake_pdf, "test.pdf")

        assert is_valid is True
        assert error == ""

    def test_validate_file_wrong_extension(self, test_settings):
        """잘못된 확장자 검증."""
        processor = PDFProcessor(test_settings)
        fake_file = BytesIO(b"test content")

        is_valid, error = processor.validate_file(fake_file, "test.txt")

        assert is_valid is False
        assert "PDF 파일만" in error

    def test_validate_file_too_large(self, test_settings):
        """파일 크기 초과 검증."""
        test_settings.max_file_size_mb = 1  # 1MB로 제한
        processor = PDFProcessor(test_settings)

        # 2MB 파일 생성 (PDF 매직 바이트 포함)
        large_file = BytesIO(b"%PDF-1.4" + b"\x00" * (2 * 1024 * 1024 - 8))

        is_valid, error = processor.validate_file(large_file, "large.pdf")

        assert is_valid is False
        assert "초과" in error

    @patch("src.core.pdf_processor.pypdf")
    @patch("src.core.pdf_processor.PyPDFLoader")
    @patch("builtins.open", new_callable=MagicMock)
    def test_load_pdf_success(self, mock_open, mock_loader, mock_pypdf, test_settings):
        """PDF 로드 성공."""
        processor = PDFProcessor(test_settings)

        # pypdf.PdfReader 모킹 (페이지 수 검증용)
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock()]  # 1페이지
        mock_pypdf.PdfReader.return_value = mock_reader

        mock_doc = MagicMock()
        mock_doc.page_content = "테스트 내용"
        mock_doc.metadata = {"page": 0}

        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance

        result = processor.load_pdf(Path("/fake/path.pdf"))

        assert len(result) == 1
        assert result[0].page_content == "테스트 내용"

    @patch("src.core.pdf_processor.pypdf")
    @patch("src.core.pdf_processor.PyPDFLoader")
    @patch("builtins.open", new_callable=MagicMock)
    def test_load_pdf_too_many_pages(self, mock_open, mock_loader, mock_pypdf, test_settings):
        """페이지 수 초과."""
        test_settings.max_pages = 5
        processor = PDFProcessor(test_settings)

        # pypdf.PdfReader 모킹 (10페이지로 설정하여 초과 유발)
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock() for _ in range(10)]
        mock_pypdf.PdfReader.return_value = mock_reader

        with pytest.raises(PDFProcessingError) as exc_info:
            processor.load_pdf(Path("/fake/path.pdf"))

        assert "초과" in str(exc_info.value)

    def test_split_documents(self, test_settings):
        """문서 분할 테스트."""
        from langchain_core.documents import Document

        processor = PDFProcessor(test_settings)

        real_doc = Document(
            page_content="테스트 내용입니다. " * 200,
            metadata={"page": 1},
        )

        chunks = processor.split_documents([real_doc])

        assert len(chunks) >= 1

    def test_save_uploaded_file(self, test_settings):
        """파일 저장 테스트."""
        processor = PDFProcessor(test_settings)
        fake_file = BytesIO(b"test content")

        file_path = processor.save_uploaded_file(fake_file, "test.pdf")

        assert file_path.exists()
        assert file_path.name == "test.pdf"
