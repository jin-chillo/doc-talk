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

    def test_validate_question_empty(self, rag_engine):
        """빈 질문 검증."""
        with pytest.raises(ValueError) as exc_info:
            rag_engine._validate_question("")

        assert "질문을 입력해주세요" in str(exc_info.value)

    def test_validate_question_whitespace(self, rag_engine):
        """공백만 있는 질문 검증."""
        with pytest.raises(ValueError) as exc_info:
            rag_engine._validate_question("   ")

        assert "질문을 입력해주세요" in str(exc_info.value)

    def test_validate_question_too_long(self, rag_engine, test_settings):
        """너무 긴 질문 검증."""
        long_question = "a" * (test_settings.max_question_length + 1)

        with pytest.raises(ValueError) as exc_info:
            rag_engine._validate_question(long_question)

        assert "너무 깁니다" in str(exc_info.value)

    def test_validate_question_valid(self, rag_engine):
        """유효한 질문 검증."""
        # 예외가 발생하지 않아야 함
        rag_engine._validate_question("유효한 질문입니다")

    @patch.object(RAGEngine, "retrieve")
    def test_query_validation_error(self, mock_retrieve, rag_engine):
        """질문 검증 실패 시 ValueError 전파."""
        with pytest.raises(ValueError):
            rag_engine.query("")

        # retrieve가 호출되지 않아야 함
        mock_retrieve.assert_not_called()

    @patch.object(RAGEngine, "retrieve")
    def test_query_validation_error_too_long(self, mock_retrieve, rag_engine):
        """너무 긴 질문 시 ValueError 전파."""
        long_question = "a" * (rag_engine.settings.max_question_length + 1)

        with pytest.raises(ValueError) as exc_info:
            rag_engine.query(long_question)

        assert "너무 깁니다" in str(exc_info.value)
        mock_retrieve.assert_not_called()

    @patch.object(RAGEngine, "retrieve")
    def test_query_stream_no_documents(self, mock_retrieve, rag_engine):
        """스트리밍에서 문서 없을 때."""
        mock_retrieve.return_value = []

        results = list(rag_engine.query_stream("테스트 질문"))

        assert len(results) == 1
        answer, sources = results[0]
        assert "찾을 수 없습니다" in answer
        assert len(sources) == 0

    @patch.object(RAGEngine, "retrieve")
    def test_query_stream_validation_error(self, mock_retrieve, rag_engine):
        """스트리밍에서 질문 검증 실패."""
        with pytest.raises(ValueError):
            list(rag_engine.query_stream(""))

        mock_retrieve.assert_not_called()

    @patch.object(RAGEngine, "retrieve")
    @patch("src.core.rag_engine.ChatGroq")
    def test_query_stream_with_documents(
        self, mock_llm_class, mock_retrieve, rag_engine
    ):
        """스트리밍에서 문서가 있을 때."""
        mock_docs = [
            Document(
                page_content="테스트 내용",
                metadata={"source": "test.pdf", "page": 1, "file_hash": "abc"},
            )
        ]
        mock_retrieve.return_value = mock_docs

        # LLM 스트리밍 모킹
        mock_llm = MagicMock()
        mock_chunk1 = MagicMock()
        mock_chunk1.content = "안녕"
        mock_chunk2 = MagicMock()
        mock_chunk2.content = "하세요"
        mock_llm.stream.return_value = [mock_chunk1, mock_chunk2]
        mock_llm_class.return_value = mock_llm

        # _llm 직접 설정
        rag_engine._llm = mock_llm
        rag_engine._current_model = rag_engine.settings.llm_model

        results = list(rag_engine.query_stream("테스트 질문"))

        assert len(results) == 2
        assert results[0][0] == "안녕"
        assert results[1][0] == "하세요"
        assert len(results[0][1]) == 1  # sources

    def test_llm_lazy_loading(self, rag_engine):
        """LLM 지연 로딩 확인."""
        assert rag_engine._llm is None

        with patch("src.core.rag_engine.ChatGroq") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            llm = rag_engine.llm

            assert llm is not None
            mock_llm_class.assert_called_once()

    def test_llm_refresh_on_model_change(self, rag_engine):
        """모델 변경 시 LLM 재생성."""
        with patch("src.core.rag_engine.ChatGroq") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            # 첫 번째 호출
            _ = rag_engine.llm
            assert mock_llm_class.call_count == 1

            # 같은 모델로 다시 호출 - 재생성 안 됨
            _ = rag_engine.llm
            assert mock_llm_class.call_count == 1

            # 모델 변경
            rag_engine.settings.llm_model = "different-model"
            _ = rag_engine.llm
            assert mock_llm_class.call_count == 2
