"""문서 관련 데이터 모델."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """문서 메타데이터."""

    source: str = Field(..., description="원본 파일명")
    page: int = Field(..., description="페이지 번호 (1-based)")
    total_pages: int = Field(..., description="전체 페이지 수")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    file_hash: str | None = Field(default=None, description="파일 해시 (중복 체크용)")


class ProcessedDocument(BaseModel):
    """처리된 문서."""

    id: str = Field(..., description="문서 고유 ID")
    filename: str = Field(..., description="원본 파일명")
    total_pages: int = Field(..., description="전체 페이지 수")
    chunk_count: int = Field(..., description="청크 수")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    file_hash: str = Field(..., description="파일 해시")
    is_active: bool = Field(default=True, description="활성화 여부")
