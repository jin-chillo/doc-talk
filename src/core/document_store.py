"""문서 저장소 관리 모듈."""

import json
from pathlib import Path

import streamlit as st
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import Settings
from src.models.document import ProcessedDocument
from src.utils.exceptions import EmbeddingError, VectorStoreError
from src.utils.logger import logger


@st.cache_resource
def get_cached_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    """캐시된 임베딩 모델 반환.

    Args:
        model_name: 모델 이름

    Returns:
        HuggingFaceEmbeddings 인스턴스
    """
    logger.info(f"임베딩 모델 로드 (캐시): {model_name}")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


class DocumentStore:
    """문서 벡터 저장소 관리 클래스."""

    def __init__(self, settings: Settings) -> None:
        """초기화.

        Args:
            settings: 애플리케이션 설정
        """
        self.settings = settings
        self._embeddings: HuggingFaceEmbeddings | None = None
        self._vectorstore: Chroma | None = None
        self._documents: dict[str, ProcessedDocument] = {}

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """임베딩 모델 반환 (지연 로딩)."""
        if self._embeddings is None:
            self._embeddings = self._load_embeddings()
        return self._embeddings

    def _load_embeddings(self) -> HuggingFaceEmbeddings:
        """임베딩 모델 로드 (캐싱 사용)."""
        try:
            logger.info(f"임베딩 모델 로드: {self.settings.embedding_model}")
            return get_cached_embeddings(self.settings.embedding_model)
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            raise EmbeddingError(f"임베딩 모델을 로드할 수 없습니다: {e}") from e

    @property
    def vectorstore(self) -> Chroma:
        """벡터 저장소 반환."""
        if self._vectorstore is None:
            self._vectorstore = self._initialize_vectorstore()
        return self._vectorstore

    def _initialize_vectorstore(self) -> Chroma:
        """벡터 저장소 초기화."""
        try:
            return Chroma(
                persist_directory=str(self.settings.chroma_dir),
                embedding_function=self.embeddings,
                collection_name="doc_talk",
            )
        except Exception as e:
            logger.error(f"벡터 저장소 초기화 실패: {e}")
            raise VectorStoreError(f"벡터 저장소를 초기화할 수 없습니다: {e}") from e

    def add_documents(
        self,
        chunks: list[Document],
        processed_doc: ProcessedDocument,
    ) -> None:
        """문서 청크 추가.

        Args:
            chunks: 청크 리스트
            processed_doc: 처리된 문서 정보

        Raises:
            VectorStoreError: 추가 실패 시
        """
        try:
            self.vectorstore.add_documents(chunks)
            self._documents[processed_doc.id] = processed_doc
            logger.info(f"문서 추가 완료: {processed_doc.filename}")
        except Exception as e:
            logger.error(f"문서 추가 실패: {e}")
            raise VectorStoreError(f"문서를 추가할 수 없습니다: {e}") from e

    def remove_document(self, doc_id: str) -> bool:
        """문서 삭제.

        Args:
            doc_id: 문서 ID

        Returns:
            삭제 성공 여부

        Raises:
            VectorStoreError: 삭제 실패 시
        """
        if doc_id not in self._documents:
            return False

        doc = self._documents[doc_id]
        try:
            # ChromaDB에서 해당 문서의 청크들 삭제 (공개 API 사용)
            self.vectorstore.delete(where={"file_hash": doc.file_hash})
            del self._documents[doc_id]
            logger.info(f"문서 삭제 완료: {doc.filename}")
            return True
        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            raise VectorStoreError(f"문서를 삭제할 수 없습니다: {e}") from e

    def get_documents(self) -> list[ProcessedDocument]:
        """등록된 문서 목록 반환.

        Returns:
            ProcessedDocument 리스트
        """
        return list(self._documents.values())

    def get_document(self, doc_id: str) -> ProcessedDocument | None:
        """문서 조회.

        Args:
            doc_id: 문서 ID

        Returns:
            ProcessedDocument 또는 None
        """
        return self._documents.get(doc_id)

    def toggle_document_active(self, doc_id: str) -> bool:
        """문서 활성화 상태 토글.

        Args:
            doc_id: 문서 ID

        Returns:
            토글 성공 여부
        """
        if doc_id in self._documents:
            self._documents[doc_id].is_active = not self._documents[doc_id].is_active
            return True
        return False

    def get_active_documents(self) -> list[ProcessedDocument]:
        """활성화된 문서 목록 반환.

        Returns:
            활성화된 ProcessedDocument 리스트
        """
        return [doc for doc in self._documents.values() if doc.is_active]

    def is_duplicate(self, file_hash: str) -> bool:
        """중복 문서 확인.

        Args:
            file_hash: 파일 해시

        Returns:
            중복 여부
        """
        return any(doc.file_hash == file_hash for doc in self._documents.values())

    def clear_all(self) -> None:
        """모든 문서 및 벡터 데이터 초기화.

        ChromaDB 컬렉션의 모든 데이터, 메모리 내 문서 메타데이터,
        업로드된 파일들을 모두 삭제합니다.

        Raises:
            VectorStoreError: 초기화 실패 시
        """
        try:
            # ChromaDB 컬렉션의 모든 문서 삭제 (vectorstore 프로퍼티로 초기화 보장)
            collection = self.vectorstore._collection
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)
            logger.info(f"ChromaDB 컬렉션 초기화 완료: {len(all_ids)}개 벡터 삭제")

            # 업로드된 파일 삭제
            deleted_files = 0
            for file_path in self.settings.uploads_dir.iterdir():
                if file_path.is_file() and file_path.name != ".gitkeep":
                    file_path.unlink()
                    deleted_files += 1
            logger.info(f"업로드 파일 삭제 완료: {deleted_files}개 파일")

            # 메모리 내 문서 메타데이터 초기화
            self._documents.clear()
            logger.info("문서 저장소 전체 초기화 완료")

        except Exception as e:
            logger.error(f"문서 저장소 초기화 실패: {e}")
            raise VectorStoreError(f"문서 저장소를 초기화할 수 없습니다: {e}") from e

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_hashes: list[str] | None = None,
    ) -> list[Document]:
        """유사도 검색.

        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter_hashes: 필터링할 파일 해시 목록

        Returns:
            검색된 Document 리스트

        Raises:
            VectorStoreError: 검색 실패 시
        """
        try:
            # 활성화된 문서만 필터링
            if filter_hashes:
                results = self.vectorstore.similarity_search(
                    query,
                    k=k,
                    filter={"file_hash": {"$in": filter_hashes}},  # type: ignore[dict-item]
                )
            else:
                results = self.vectorstore.similarity_search(query, k=k)

            return results
        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            raise VectorStoreError(f"검색 중 오류가 발생했습니다: {e}") from e

    def _get_save_path(self) -> Path:
        """저장 파일 경로 반환."""
        return self.settings.data_dir / "documents.json"

    def save(self) -> None:
        """문서 메타데이터를 파일에 저장."""
        save_path = self._get_save_path()
        try:
            data = {
                doc_id: doc.model_dump(mode="json")
                for doc_id, doc in self._documents.items()
            }
            save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            logger.info(f"문서 메타데이터 저장 완료: {len(self._documents)}개 문서")
        except Exception as e:
            logger.error(f"문서 메타데이터 저장 실패: {e}")

    def load(self) -> None:
        """파일에서 문서 메타데이터 복원."""
        save_path = self._get_save_path()
        if not save_path.exists():
            logger.info("저장된 문서 메타데이터 없음")
            return

        try:
            data = json.loads(save_path.read_text())
            self._documents = {
                doc_id: ProcessedDocument.model_validate(doc_data)
                for doc_id, doc_data in data.items()
            }
            logger.info(f"문서 메타데이터 복원 완료: {len(self._documents)}개 문서")
        except Exception as e:
            logger.error(f"문서 메타데이터 복원 실패: {e}")
            self._documents = {}
