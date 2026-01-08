"""DocumentStore 테스트."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from src.core.document_store import DocumentStore
from src.models.document import ProcessedDocument
from src.utils.exceptions import EmbeddingError, VectorStoreError


class TestDocumentStore:
    """DocumentStore 테스트 클래스."""

    @pytest.fixture
    def mock_chroma(self):
        """모킹된 ChromaDB."""
        with patch("src.core.document_store.Chroma") as mock:
            mock_instance = MagicMock()
            mock_collection = MagicMock()
            mock_instance._collection = mock_collection
            mock_instance.add_documents.return_value = None
            mock_instance.similarity_search.return_value = [
                Document(
                    page_content="테스트 내용",
                    metadata={"source": "test.pdf", "page": 1, "file_hash": "hash123"},
                )
            ]
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def document_store(self, test_settings, mock_embeddings, mock_chroma):
        """DocumentStore 인스턴스."""
        return DocumentStore(settings=test_settings)

    @pytest.fixture
    def sample_processed_doc(self) -> ProcessedDocument:
        """샘플 처리된 문서."""
        return ProcessedDocument(
            id="doc-123",
            filename="sample.pdf",
            total_pages=5,
            chunk_count=10,
            file_hash="hash123",
            is_active=True,
        )

    @pytest.fixture
    def sample_chunks(self) -> list[Document]:
        """샘플 청크 리스트."""
        return [
            Document(
                page_content="첫 번째 청크 내용",
                metadata={"source": "sample.pdf", "page": 1, "file_hash": "hash123"},
            ),
            Document(
                page_content="두 번째 청크 내용",
                metadata={"source": "sample.pdf", "page": 2, "file_hash": "hash123"},
            ),
        ]

    def test_embeddings_lazy_loading(self, test_settings, mock_embeddings):
        """임베딩 지연 로딩 확인.

        임베딩 모델은 처음 접근 시에만 로드되어야 함.
        """
        store = DocumentStore(settings=test_settings)

        # 초기에는 None
        assert store._embeddings is None

        # 접근 시 로딩
        embeddings = store.embeddings

        assert embeddings is not None
        assert store._embeddings is not None

    def test_load_embeddings_error(self, test_settings):
        """임베딩 모델 로드 실패 시 예외 발생."""
        store = DocumentStore(settings=test_settings)

        with patch(
            "src.core.document_store.get_cached_embeddings",
            side_effect=Exception("모델 로드 실패"),
        ):
            with pytest.raises(EmbeddingError) as exc_info:
                store._load_embeddings()

            assert "임베딩 모델을 로드할 수 없습니다" in str(exc_info.value)

    def test_vectorstore_initialization(
        self, document_store, mock_chroma, test_settings
    ):
        """벡터 저장소 초기화 확인."""
        vectorstore = document_store.vectorstore

        assert vectorstore is not None
        assert document_store._vectorstore is not None

    def test_add_documents(
        self, document_store, sample_chunks, sample_processed_doc, mock_chroma
    ):
        """문서 청크 추가 기능 테스트.

        문서와 청크를 벡터 저장소에 추가하고 내부 딕셔너리에도 저장되는지 확인.
        """
        document_store.add_documents(sample_chunks, sample_processed_doc)

        # 벡터 저장소 호출 확인
        mock_chroma.add_documents.assert_called_once_with(sample_chunks)

        # 내부 딕셔너리에 저장 확인
        assert sample_processed_doc.id in document_store._documents
        assert (
            document_store._documents[sample_processed_doc.id] == sample_processed_doc
        )

    def test_add_documents_error(
        self, document_store, sample_chunks, sample_processed_doc, mock_chroma
    ):
        """문서 추가 실패 시 예외 발생."""
        mock_chroma.add_documents.side_effect = Exception("벡터 저장소 에러")

        with pytest.raises(VectorStoreError) as exc_info:
            document_store.add_documents(sample_chunks, sample_processed_doc)

        assert "문서를 추가할 수 없습니다" in str(exc_info.value)

    def test_remove_document(
        self, document_store, sample_chunks, sample_processed_doc, mock_chroma
    ):
        """문서 삭제 기능 테스트.

        존재하는 문서를 삭제하고 True 반환 확인.
        """
        # 먼저 문서 추가
        document_store.add_documents(sample_chunks, sample_processed_doc)

        # 삭제
        result = document_store.remove_document(sample_processed_doc.id)

        assert result is True
        assert sample_processed_doc.id not in document_store._documents
        # 공개 API 사용 확인 (vectorstore.delete)
        mock_chroma.delete.assert_called_once_with(
            where={"file_hash": sample_processed_doc.file_hash}
        )

    def test_remove_document_not_found(self, document_store):
        """존재하지 않는 문서 삭제 시 False 반환.

        등록되지 않은 문서 ID로 삭제 시도 시 False를 반환해야 함.
        """
        result = document_store.remove_document("non-existent-id")

        assert result is False

    def test_remove_document_error(
        self, document_store, sample_chunks, sample_processed_doc, mock_chroma
    ):
        """문서 삭제 실패 시 예외 발생."""
        document_store.add_documents(sample_chunks, sample_processed_doc)

        # 공개 API 사용 (vectorstore.delete)
        mock_chroma.delete.side_effect = Exception("삭제 실패")

        with pytest.raises(VectorStoreError) as exc_info:
            document_store.remove_document(sample_processed_doc.id)

        assert "문서를 삭제할 수 없습니다" in str(exc_info.value)

    def test_get_documents(self, document_store, sample_chunks, sample_processed_doc):
        """전체 문서 조회 테스트.

        등록된 모든 문서를 리스트로 반환하는지 확인.
        """
        # 빈 상태
        assert document_store.get_documents() == []

        # 문서 추가
        document_store.add_documents(sample_chunks, sample_processed_doc)

        # 조회
        documents = document_store.get_documents()

        assert len(documents) == 1
        assert documents[0] == sample_processed_doc

    def test_get_document(self, document_store, sample_chunks, sample_processed_doc):
        """특정 문서 조회 테스트."""
        # 문서 추가
        document_store.add_documents(sample_chunks, sample_processed_doc)

        # 존재하는 문서 조회
        doc = document_store.get_document(sample_processed_doc.id)
        assert doc == sample_processed_doc

        # 존재하지 않는 문서 조회
        doc = document_store.get_document("non-existent-id")
        assert doc is None

    def test_toggle_document_active(
        self, document_store, sample_chunks, sample_processed_doc
    ):
        """문서 활성화/비활성화 토글 테스트.

        토글 호출 시 is_active 상태가 반전되는지 확인.
        """
        # 문서 추가 (기본 is_active=True)
        document_store.add_documents(sample_chunks, sample_processed_doc)

        # 비활성화
        result = document_store.toggle_document_active(sample_processed_doc.id)
        assert result is True
        assert document_store._documents[sample_processed_doc.id].is_active is False

        # 다시 활성화
        result = document_store.toggle_document_active(sample_processed_doc.id)
        assert result is True
        assert document_store._documents[sample_processed_doc.id].is_active is True

    def test_toggle_document_active_not_found(self, document_store):
        """존재하지 않는 문서 토글 시 False 반환."""
        result = document_store.toggle_document_active("non-existent-id")

        assert result is False

    def test_get_active_documents(
        self, document_store, sample_chunks, sample_processed_doc
    ):
        """활성 문서만 조회 테스트.

        is_active=True인 문서만 반환되는지 확인.
        """
        # 두 개의 문서 추가
        doc1 = sample_processed_doc
        doc2 = ProcessedDocument(
            id="doc-456",
            filename="another.pdf",
            total_pages=3,
            chunk_count=6,
            file_hash="hash456",
            is_active=False,
        )

        chunks2 = [
            Document(
                page_content="내용",
                metadata={"source": "another.pdf", "page": 1, "file_hash": "hash456"},
            )
        ]

        document_store.add_documents(sample_chunks, doc1)
        document_store.add_documents(chunks2, doc2)

        # 활성 문서만 조회
        active_docs = document_store.get_active_documents()

        assert len(active_docs) == 1
        assert active_docs[0].id == doc1.id
        assert active_docs[0].is_active is True

    def test_is_duplicate(self, document_store, sample_chunks, sample_processed_doc):
        """중복 문서 확인 테스트.

        동일한 file_hash를 가진 문서가 있는지 확인.
        """
        # 중복 아님
        assert document_store.is_duplicate("hash123") is False

        # 문서 추가
        document_store.add_documents(sample_chunks, sample_processed_doc)

        # 중복 확인
        assert document_store.is_duplicate("hash123") is True
        assert document_store.is_duplicate("other-hash") is False

    def test_similarity_search(self, document_store, mock_chroma):
        """유사도 검색 테스트.

        쿼리에 대한 유사 문서를 k개 반환하는지 확인.
        """
        results = document_store.similarity_search("테스트 질문", k=4)

        assert len(results) == 1
        assert results[0].page_content == "테스트 내용"
        mock_chroma.similarity_search.assert_called_once_with("테스트 질문", k=4)

    def test_similarity_search_with_filter(self, document_store, mock_chroma):
        """필터링된 유사도 검색 테스트.

        특정 파일 해시만 검색하도록 필터링.
        """
        filter_hashes = ["hash123", "hash456"]

        results = document_store.similarity_search(
            "테스트 질문", k=5, filter_hashes=filter_hashes
        )

        assert len(results) == 1
        mock_chroma.similarity_search.assert_called_once_with(
            "테스트 질문",
            k=5,
            filter={"file_hash": {"$in": filter_hashes}},
        )

    def test_similarity_search_error(self, document_store, mock_chroma):
        """유사도 검색 실패 시 예외 발생."""
        mock_chroma.similarity_search.side_effect = Exception("검색 실패")

        with pytest.raises(VectorStoreError) as exc_info:
            document_store.similarity_search("테스트 질문")

        assert "검색 중 오류가 발생했습니다" in str(exc_info.value)
