"""RAG 엔진 테스트."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from src.core.conversation import ConversationManager
from src.core.document_store import DocumentStore
from src.core.rag_engine import RAGEngine
from src.models.document import ProcessedDocument


class TestRAGEngine:
    """RAGEngine 테스트 클래스."""

    @pytest.fixture
    def mock_document_store(self, test_settings):
        """모킹된 문서 저장소."""
        store = MagicMock(spec=DocumentStore)
        store.get_active_documents.return_value = [
            ProcessedDocument(
                id="test-id",
                filename="test.pdf",
                total_pages=10,
                chunk_count=20,
                file_hash="abc123",
            )
        ]
        return store

    @pytest.fixture
    def rag_engine(self, test_settings, mock_document_store):
        """RAG 엔진 인스턴스."""
        conversation = ConversationManager(test_settings)
        return RAGEngine(
            settings=test_settings,
            document_store=mock_document_store,
            conversation_manager=conversation,
        )

    def test_format_context(self, rag_engine):
        """컨텍스트 포맷 테스트."""
        docs = [
            Document(
                page_content="내용 1",
                metadata={"source": "test.pdf", "page": 1},
            ),
            Document(
                page_content="내용 2",
                metadata={"source": "test.pdf", "page": 2},
            ),
        ]

        context = rag_engine._format_context(docs)

        assert "[문서 1]" in context
        assert "[문서 2]" in context
        assert "페이지: 1" in context
        assert "내용 1" in context

    def test_get_active_file_hashes(self, rag_engine, mock_document_store):
        """활성 파일 해시 조회."""
        hashes = rag_engine._get_active_file_hashes()

        assert len(hashes) == 1
        assert "abc123" in hashes

    def test_retrieve_no_active_docs(self, rag_engine, mock_document_store):
        """활성 문서 없을 때 검색."""
        mock_document_store.get_active_documents.return_value = []

        results = rag_engine.retrieve("테스트")

        assert len(results) == 0

    def test_retrieve_with_active_docs(self, rag_engine, mock_document_store):
        """활성 문서 있을 때 검색."""
        mock_docs = [
            Document(page_content="결과", metadata={"source": "test.pdf", "page": 1})
        ]
        mock_document_store.similarity_search.return_value = mock_docs

        results = rag_engine.retrieve("테스트 질문")

        assert len(results) == 1
        mock_document_store.similarity_search.assert_called_once()

    @patch.object(RAGEngine, "retrieve")
    def test_query_no_documents(self, mock_retrieve, rag_engine):
        """문서 없을 때 쿼리."""
        mock_retrieve.return_value = []

        answer, sources = rag_engine.query("테스트 질문")

        assert "찾을 수 없습니다" in answer
        assert len(sources) == 0

    def test_format_context_empty(self, rag_engine):
        """빈 문서 리스트 포맷."""
        context = rag_engine._format_context([])

        assert context == ""

    def test_format_context_missing_metadata(self, rag_engine):
        """메타데이터 없는 문서 포맷."""
        docs = [
            Document(page_content="내용", metadata={}),
        ]

        context = rag_engine._format_context(docs)

        assert "Unknown" in context
        assert "?" in context
