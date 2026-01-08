"""메시지 관련 데이터 모델."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """메시지 역할."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Source(BaseModel):
    """답변 출처."""

    document_name: str = Field(..., description="문서명")
    page: int = Field(..., description="페이지 번호")
    content_preview: str = Field(..., description="원문 미리보기 (200자)")


class Message(BaseModel):
    """대화 메시지."""

    role: MessageRole = Field(..., description="메시지 역할")
    content: str = Field(..., description="메시지 내용")
    sources: list[Source] = Field(default_factory=list, description="출처 목록")
    timestamp: datetime = Field(default_factory=datetime.now)
