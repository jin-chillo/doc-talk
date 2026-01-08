"""출처 관련 유틸리티."""

from langchain_core.documents import Document

from src.models.message import Source


def create_source_from_document(doc: Document, preview_length: int = 200) -> Source:
    """LangChain Document에서 Source 생성.

    Args:
        doc: LangChain Document 객체
        preview_length: 미리보기 텍스트 길이

    Returns:
        Source 객체
    """
    metadata = doc.metadata
    content_preview = doc.page_content[:preview_length]
    if len(doc.page_content) > preview_length:
        content_preview += "..."

    return Source(
        document_name=metadata.get("source", "Unknown"),
        page=metadata.get("page", 0),
        content_preview=content_preview,
    )
