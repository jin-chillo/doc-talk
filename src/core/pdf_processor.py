"""PDF 처리 모듈."""

import uuid
from pathlib import Path
from typing import BinaryIO

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import Settings
from src.models.document import ProcessedDocument
from src.utils.exceptions import PDFProcessingError
from src.utils.helpers import calculate_file_hash, validate_pdf_file
from src.utils.logger import logger


class PDFProcessor:
    """PDF 문서 처리 클래스."""

    def __init__(self, settings: Settings) -> None:
        """초기화.

        Args:
            settings: 애플리케이션 설정
        """
        self.settings = settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )

    def validate_file(self, file: BinaryIO, filename: str) -> tuple[bool, str]:
        """파일 유효성 검증.

        Args:
            file: 파일 객체
            filename: 파일명

        Returns:
            (유효 여부, 에러 메시지) 튜플
        """
        return validate_pdf_file(
            file=file,
            filename=filename,
            max_size_mb=self.settings.max_file_size_mb,
        )

    def save_uploaded_file(self, file: BinaryIO, filename: str) -> Path:
        """업로드된 파일 저장.

        Args:
            file: 파일 객체
            filename: 파일명

        Returns:
            저장된 파일 경로
        """
        file_path = self.settings.uploads_dir / filename
        with open(file_path, "wb") as f:
            f.write(file.read())
        file.seek(0)
        return file_path

    def load_pdf(self, file_path: Path) -> list[Document]:
        """PDF 파일 로드.

        Args:
            file_path: PDF 파일 경로

        Returns:
            LangChain Document 리스트

        Raises:
            PDFProcessingError: PDF 로드 실패 시
        """
        try:
            loader = PyPDFLoader(str(file_path))
            documents = loader.load()

            # 페이지 수 검증
            if len(documents) > self.settings.max_pages:
                raise PDFProcessingError(
                    f"페이지 수가 {self.settings.max_pages}페이지를 초과합니다."
                )

            return documents
        except PDFProcessingError:
            raise
        except Exception as e:
            logger.error(f"PDF 로드 실패: {e}")
            raise PDFProcessingError(f"PDF 파일을 읽을 수 없습니다: {e}") from e

    def _clean_text(self, text: str) -> str:
        """텍스트에서 특수 문자 제거.

        Args:
            text: 원본 텍스트

        Returns:
            정리된 텍스트
        """
        import re

        # NULL 문자 및 기타 제어 문자 제거
        text = text.replace("\x00", "")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Non-breaking space를 일반 공백으로 변환
        text = text.replace("\xa0", " ")
        return text

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """문서를 청크로 분할.

        Args:
            documents: 원본 문서 리스트

        Returns:
            분할된 청크 리스트
        """
        # 텍스트 정리
        for doc in documents:
            doc.page_content = self._clean_text(doc.page_content)

        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"문서 분할 완료: {len(documents)} 페이지 -> {len(chunks)} 청크")
        return chunks

    def process(
        self,
        file: BinaryIO,
        filename: str,
    ) -> tuple[list[Document], ProcessedDocument]:
        """PDF 처리 전체 파이프라인.

        Args:
            file: 파일 객체
            filename: 파일명

        Returns:
            (청크 리스트, ProcessedDocument) 튜플

        Raises:
            PDFProcessingError: 처리 실패 시
        """
        # 유효성 검증
        is_valid, error_msg = self.validate_file(file, filename)
        if not is_valid:
            raise PDFProcessingError(error_msg)

        # 파일 해시 계산
        file_hash = calculate_file_hash(file)

        # 파일 저장
        file_path = self.save_uploaded_file(file, filename)

        try:
            # PDF 로드
            documents = self.load_pdf(file_path)

            # 메타데이터 보강
            total_pages = len(documents)
            for i, doc in enumerate(documents):
                doc.metadata.update(
                    {
                        "source": filename,
                        "page": i + 1,
                        "total_pages": total_pages,
                        "file_hash": file_hash,
                    }
                )

            # 청크 분할
            chunks = self.split_documents(documents)

            # ProcessedDocument 생성
            processed_doc = ProcessedDocument(
                id=str(uuid.uuid4()),
                filename=filename,
                total_pages=total_pages,
                chunk_count=len(chunks),
                file_hash=file_hash,
            )

            logger.info(
                f"PDF 처리 완료: {filename} ({total_pages} 페이지, {len(chunks)} 청크)"
            )

            return chunks, processed_doc

        except Exception:
            # 실패 시 파일 삭제
            if file_path.exists():
                file_path.unlink()
            raise
