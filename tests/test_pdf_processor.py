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

    def test_save_uploaded_file_hidden_file(self, test_settings):
        """숨김 파일 업로드 거부."""
        processor = PDFProcessor(test_settings)
        fake_file = BytesIO(b"test content")

        with pytest.raises(PDFProcessingError) as exc_info:
            processor.save_uploaded_file(fake_file, ".hidden.pdf")

        assert "숨김 파일" in str(exc_info.value)

    def test_save_uploaded_file_path_traversal(self, test_settings):
        """Path Traversal 공격 방지."""
        processor = PDFProcessor(test_settings)
        fake_file = BytesIO(b"test content")

        # 디렉토리 탐색 시도 - basename만 사용되어야 함
        file_path = processor.save_uploaded_file(fake_file, "../../../etc/passwd.pdf")

        # basename만 추출되어 안전한 경로로 저장됨
        assert file_path.name == "passwd.pdf"
        assert test_settings.uploads_dir in file_path.parents or file_path.parent == test_settings.uploads_dir

    def test_clean_text_null_characters(self, test_settings):
        """NULL 문자 제거."""
        processor = PDFProcessor(test_settings)

        text = "테스트\x00문자\x00열"
        cleaned = processor._clean_text(text)

        assert "\x00" not in cleaned
        assert cleaned == "테스트문자열"

    def test_clean_text_control_characters(self, test_settings):
        """제어 문자 제거."""
        processor = PDFProcessor(test_settings)

        text = "테스트\x01\x02\x03문자열"
        cleaned = processor._clean_text(text)

        assert "\x01" not in cleaned
        assert "\x02" not in cleaned
        assert cleaned == "테스트문자열"

    def test_clean_text_nbsp(self, test_settings):
        """Non-breaking space 변환."""
        processor = PDFProcessor(test_settings)

        text = "테스트\xa0문자열"
        cleaned = processor._clean_text(text)

        assert "\xa0" not in cleaned
        assert " " in cleaned

    @patch("src.core.pdf_processor.pypdf")
    @patch("builtins.open", new_callable=MagicMock)
    def test_load_pdf_general_exception(self, mock_open, mock_pypdf, test_settings):
        """PDF 로드 시 일반 예외 처리."""
        processor = PDFProcessor(test_settings)

        mock_pypdf.PdfReader.side_effect = Exception("파일 손상")

        with pytest.raises(PDFProcessingError) as exc_info:
            processor.load_pdf(Path("/fake/path.pdf"))

        assert "읽을 수 없습니다" in str(exc_info.value)

    @patch.object(PDFProcessor, "validate_file")
    @patch.object(PDFProcessor, "save_uploaded_file")
    @patch.object(PDFProcessor, "load_pdf")
    @patch.object(PDFProcessor, "split_documents")
    def test_process_success(
        self, mock_split, mock_load, mock_save, mock_validate, test_settings
    ):
        """전체 파이프라인 성공."""
        from langchain_core.documents import Document

        processor = PDFProcessor(test_settings)

        # 모킹 설정
        mock_validate.return_value = (True, "")
        mock_save.return_value = Path("/fake/test.pdf")

        mock_docs = [
            Document(page_content="내용 1", metadata={}),
            Document(page_content="내용 2", metadata={}),
        ]
        mock_load.return_value = mock_docs

        mock_chunks = [
            Document(page_content="청크 1", metadata={}),
            Document(page_content="청크 2", metadata={}),
            Document(page_content="청크 3", metadata={}),
        ]
        mock_split.return_value = mock_chunks

        fake_file = BytesIO(b"%PDF-1.4 test content")
        chunks, processed_doc = processor.process(fake_file, "test.pdf")

        assert len(chunks) == 3
        assert processed_doc.filename == "test.pdf"
        assert processed_doc.total_pages == 2
        assert processed_doc.chunk_count == 3

    @patch.object(PDFProcessor, "validate_file")
    def test_process_validation_failure(self, mock_validate, test_settings):
        """파이프라인에서 검증 실패."""
        processor = PDFProcessor(test_settings)
        mock_validate.return_value = (False, "잘못된 파일 형식")

        fake_file = BytesIO(b"not a pdf")

        with pytest.raises(PDFProcessingError) as exc_info:
            processor.process(fake_file, "test.txt")

        assert "잘못된 파일 형식" in str(exc_info.value)

    @patch.object(PDFProcessor, "validate_file")
    @patch.object(PDFProcessor, "save_uploaded_file")
    @patch.object(PDFProcessor, "load_pdf")
    def test_process_cleanup_on_failure(
        self, mock_load, mock_save, mock_validate, test_settings, tmp_path
    ):
        """파이프라인 실패 시 파일 정리."""
        processor = PDFProcessor(test_settings)

        # 임시 파일 생성
        temp_file = tmp_path / "temp.pdf"
        temp_file.write_bytes(b"temp content")

        mock_validate.return_value = (True, "")
        mock_save.return_value = temp_file
        mock_load.side_effect = Exception("로드 실패")

        fake_file = BytesIO(b"%PDF-1.4 test")

        with pytest.raises(Exception):
            processor.process(fake_file, "test.pdf")

        # 파일이 삭제되었는지 확인
        assert not temp_file.exists()
