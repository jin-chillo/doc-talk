"""테스트 설정 및 픽스처."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import Settings


@pytest.fixture
def test_settings() -> Generator[Settings, None, None]:
    """테스트용 설정."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        yield Settings(
            groq_api_key="test-api-key",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            llm_model="llama-3.3-70b-versatile",
            chunk_size=500,
            chunk_overlap=100,
            data_dir=tmppath,
            uploads_dir=tmppath / "uploads",
            chroma_dir=tmppath / "chroma_db",
        )


@pytest.fixture
def sample_pdf_content() -> bytes:
    """샘플 PDF 바이트 콘텐츠."""
    # 간단한 PDF 헤더 (실제 테스트에서는 실제 PDF 파일 사용 권장)
    return b"%PDF-1.4\n" + b"\x00" * 1000


@pytest.fixture
def mock_embeddings():
    """모킹된 임베딩."""
    with patch("src.core.document_store.HuggingFaceEmbeddings") as mock:
        mock_instance = MagicMock()
        mock_instance.embed_documents.return_value = [[0.1] * 384]
        mock_instance.embed_query.return_value = [0.1] * 384
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm():
    """모킹된 LLM."""
    with patch("src.core.rag_engine.ChatGroq") as mock:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="테스트 응답입니다.")
        mock.return_value = mock_instance
        yield mock_instance
