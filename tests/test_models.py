"""모델 테스트."""

from datetime import datetime

import pytest
from langchain_core.documents import Document
from pydantic import ValidationError

from src.models.document import DocumentMetadata, ProcessedDocument
from src.models.message import Message, MessageRole, Source
from src.models.source import create_source_from_document


class TestDocumentMetadata:
    """DocumentMetadata 테스트 클래스."""

    def test_create_with_required_fields(self):
        """필수 필드로 생성."""
        metadata = DocumentMetadata(
            source="test.pdf",
            page=1,
            total_pages=10,
        )

        assert metadata.source == "test.pdf"
        assert metadata.page == 1
        assert metadata.total_pages == 10
        assert isinstance(metadata.created_at, datetime)
        assert metadata.file_hash is None

    def test_create_with_all_fields(self):
        """모든 필드로 생성."""
        now = datetime.now()
        metadata = DocumentMetadata(
            source="test.pdf",
            page=5,
            total_pages=20,
            created_at=now,
            file_hash="abc123",
        )

        assert metadata.source == "test.pdf"
        assert metadata.page == 5
        assert metadata.total_pages == 20
        assert metadata.created_at == now
        assert metadata.file_hash == "abc123"

    def test_missing_required_field_source(self):
        """source 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentMetadata(
                page=1,
                total_pages=10,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("source",) for error in errors)

    def test_missing_required_field_page(self):
        """page 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentMetadata(
                source="test.pdf",
                total_pages=10,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("page",) for error in errors)

    def test_missing_required_field_total_pages(self):
        """total_pages 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentMetadata(
                source="test.pdf",
                page=1,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("total_pages",) for error in errors)


class TestProcessedDocument:
    """ProcessedDocument 테스트 클래스."""

    def test_create_with_required_fields(self):
        """필수 필드로 생성."""
        doc = ProcessedDocument(
            id="doc123",
            filename="test.pdf",
            total_pages=10,
            chunk_count=5,
            file_hash="abc123",
        )

        assert doc.id == "doc123"
        assert doc.filename == "test.pdf"
        assert doc.total_pages == 10
        assert doc.chunk_count == 5
        assert doc.file_hash == "abc123"
        assert isinstance(doc.created_at, datetime)
        assert doc.is_active is True

    def test_create_with_all_fields(self):
        """모든 필드로 생성."""
        now = datetime.now()
        doc = ProcessedDocument(
            id="doc456",
            filename="document.pdf",
            total_pages=50,
            chunk_count=25,
            created_at=now,
            file_hash="xyz789",
            is_active=False,
        )

        assert doc.id == "doc456"
        assert doc.filename == "document.pdf"
        assert doc.total_pages == 50
        assert doc.chunk_count == 25
        assert doc.created_at == now
        assert doc.file_hash == "xyz789"
        assert doc.is_active is False

    def test_default_values(self):
        """기본값 확인."""
        doc = ProcessedDocument(
            id="doc789",
            filename="test.pdf",
            total_pages=10,
            chunk_count=5,
            file_hash="hash123",
        )

        # created_at은 자동 생성
        assert isinstance(doc.created_at, datetime)
        # is_active 기본값은 True
        assert doc.is_active is True

    def test_missing_required_field_id(self):
        """id 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessedDocument(
                filename="test.pdf",
                total_pages=10,
                chunk_count=5,
                file_hash="abc123",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("id",) for error in errors)

    def test_missing_required_field_filename(self):
        """filename 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessedDocument(
                id="doc123",
                total_pages=10,
                chunk_count=5,
                file_hash="abc123",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("filename",) for error in errors)

    def test_missing_required_field_total_pages(self):
        """total_pages 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessedDocument(
                id="doc123",
                filename="test.pdf",
                chunk_count=5,
                file_hash="abc123",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("total_pages",) for error in errors)

    def test_missing_required_field_chunk_count(self):
        """chunk_count 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessedDocument(
                id="doc123",
                filename="test.pdf",
                total_pages=10,
                file_hash="abc123",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("chunk_count",) for error in errors)

    def test_missing_required_field_file_hash(self):
        """file_hash 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessedDocument(
                id="doc123",
                filename="test.pdf",
                total_pages=10,
                chunk_count=5,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("file_hash",) for error in errors)


class TestMessageRole:
    """MessageRole Enum 테스트 클래스."""

    def test_enum_values(self):
        """Enum 값 확인."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"

    def test_enum_members(self):
        """Enum 멤버 확인."""
        roles = [role.value for role in MessageRole]
        assert "user" in roles
        assert "assistant" in roles
        assert "system" in roles
        assert len(roles) == 3


class TestSource:
    """Source 테스트 클래스."""

    def test_create_with_all_fields(self):
        """모든 필드로 생성."""
        source = Source(
            document_name="test.pdf",
            page=5,
            content_preview="This is a preview text...",
        )

        assert source.document_name == "test.pdf"
        assert source.page == 5
        assert source.content_preview == "This is a preview text..."

    def test_missing_required_field_document_name(self):
        """document_name 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            Source(
                page=5,
                content_preview="Preview text",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("document_name",) for error in errors)

    def test_missing_required_field_page(self):
        """page 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            Source(
                document_name="test.pdf",
                content_preview="Preview text",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("page",) for error in errors)

    def test_missing_required_field_content_preview(self):
        """content_preview 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            Source(
                document_name="test.pdf",
                page=5,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("content_preview",) for error in errors)


class TestMessage:
    """Message 테스트 클래스."""

    def test_create_user_message(self):
        """사용자 메시지 생성."""
        message = Message(
            role=MessageRole.USER,
            content="What is the capital of France?",
        )

        assert message.role == MessageRole.USER
        assert message.content == "What is the capital of France?"
        assert message.sources == []
        assert isinstance(message.timestamp, datetime)

    def test_create_assistant_message(self):
        """어시스턴트 메시지 생성."""
        message = Message(
            role=MessageRole.ASSISTANT,
            content="The capital of France is Paris.",
        )

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "The capital of France is Paris."
        assert message.sources == []
        assert isinstance(message.timestamp, datetime)

    def test_create_system_message(self):
        """시스템 메시지 생성."""
        message = Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant.",
        )

        assert message.role == MessageRole.SYSTEM
        assert message.content == "You are a helpful assistant."
        assert message.sources == []
        assert isinstance(message.timestamp, datetime)

    def test_create_message_with_sources(self):
        """출처가 포함된 메시지 생성."""
        source1 = Source(
            document_name="doc1.pdf",
            page=1,
            content_preview="Preview 1",
        )
        source2 = Source(
            document_name="doc2.pdf",
            page=3,
            content_preview="Preview 2",
        )

        message = Message(
            role=MessageRole.ASSISTANT,
            content="Answer based on documents",
            sources=[source1, source2],
        )

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Answer based on documents"
        assert len(message.sources) == 2
        assert message.sources[0].document_name == "doc1.pdf"
        assert message.sources[1].document_name == "doc2.pdf"

    def test_create_message_with_custom_timestamp(self):
        """커스텀 타임스탬프로 메시지 생성."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        message = Message(
            role=MessageRole.USER,
            content="Test message",
            timestamp=custom_time,
        )

        assert message.timestamp == custom_time

    def test_default_empty_sources(self):
        """sources 기본값 확인."""
        message = Message(
            role=MessageRole.USER,
            content="Test",
        )

        assert message.sources == []
        assert isinstance(message.sources, list)

    def test_missing_required_field_role(self):
        """role 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            Message(content="Test content")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("role",) for error in errors)

    def test_missing_required_field_content(self):
        """content 필드 누락 시 에러."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role=MessageRole.USER)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("content",) for error in errors)


class TestCreateSourceFromDocument:
    """create_source_from_document 함수 테스트 클래스."""

    def test_create_with_full_metadata(self):
        """전체 메타데이터가 있는 문서로 생성."""
        doc = Document(
            page_content="This is a test document content.",
            metadata={
                "source": "test.pdf",
                "page": 5,
            },
        )

        source = create_source_from_document(doc)

        assert source.document_name == "test.pdf"
        assert source.page == 5
        assert source.content_preview == "This is a test document content."

    def test_create_with_missing_metadata(self):
        """메타데이터가 없는 문서로 생성."""
        doc = Document(
            page_content="Content without metadata.",
            metadata={},
        )

        source = create_source_from_document(doc)

        assert source.document_name == "Unknown"
        assert source.page == 0
        assert source.content_preview == "Content without metadata."

    def test_create_with_partial_metadata(self):
        """일부 메타데이터만 있는 문서로 생성."""
        doc = Document(
            page_content="Partial metadata content.",
            metadata={"source": "partial.pdf"},
        )

        source = create_source_from_document(doc)

        assert source.document_name == "partial.pdf"
        assert source.page == 0
        assert source.content_preview == "Partial metadata content."

    def test_preview_length_truncation(self):
        """preview_length에 따른 텍스트 자르기."""
        long_content = "A" * 300
        doc = Document(
            page_content=long_content,
            metadata={"source": "long.pdf", "page": 1},
        )

        source = create_source_from_document(doc, preview_length=200)

        assert source.document_name == "long.pdf"
        assert source.page == 1
        assert len(source.content_preview) == 203  # 200 + "..."
        assert source.content_preview.endswith("...")
        assert source.content_preview == "A" * 200 + "..."

    def test_preview_length_no_truncation(self):
        """짧은 텍스트는 자르지 않음."""
        short_content = "Short content"
        doc = Document(
            page_content=short_content,
            metadata={"source": "short.pdf", "page": 2},
        )

        source = create_source_from_document(doc, preview_length=200)

        assert source.document_name == "short.pdf"
        assert source.page == 2
        assert source.content_preview == "Short content"
        assert not source.content_preview.endswith("...")

    def test_preview_length_exact_boundary(self):
        """정확히 preview_length인 텍스트."""
        exact_content = "A" * 200
        doc = Document(
            page_content=exact_content,
            metadata={"source": "exact.pdf", "page": 3},
        )

        source = create_source_from_document(doc, preview_length=200)

        assert source.document_name == "exact.pdf"
        assert source.page == 3
        assert source.content_preview == exact_content
        assert not source.content_preview.endswith("...")

    def test_custom_preview_length(self):
        """커스텀 preview_length 사용."""
        content = "X" * 150
        doc = Document(
            page_content=content,
            metadata={"source": "custom.pdf", "page": 4},
        )

        source = create_source_from_document(doc, preview_length=50)

        assert source.document_name == "custom.pdf"
        assert source.page == 4
        assert len(source.content_preview) == 53  # 50 + "..."
        assert source.content_preview == "X" * 50 + "..."

    def test_empty_content(self):
        """빈 콘텐츠 처리."""
        doc = Document(
            page_content="",
            metadata={"source": "empty.pdf", "page": 1},
        )

        source = create_source_from_document(doc)

        assert source.document_name == "empty.pdf"
        assert source.page == 1
        assert source.content_preview == ""

    def test_korean_content(self):
        """한국어 콘텐츠 처리."""
        korean_content = "이것은 한국어 문서 내용입니다. " * 20
        doc = Document(
            page_content=korean_content,
            metadata={"source": "korean.pdf", "page": 7},
        )

        source = create_source_from_document(doc, preview_length=50)

        assert source.document_name == "korean.pdf"
        assert source.page == 7
        assert len(source.content_preview) == 53
        assert source.content_preview.endswith("...")
