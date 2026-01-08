"""커스텀 예외 클래스."""


class DocTalkError(Exception):
    """doc-talk 기본 예외."""

    def __init__(self, message: str = "알 수 없는 오류가 발생했습니다.") -> None:
        self.message = message
        super().__init__(self.message)


class PDFProcessingError(DocTalkError):
    """PDF 처리 관련 예외."""

    def __init__(self, message: str = "PDF 파일을 처리할 수 없습니다.") -> None:
        super().__init__(message)


class EmbeddingError(DocTalkError):
    """임베딩 관련 예외."""

    def __init__(self, message: str = "임베딩 처리 중 오류가 발생했습니다.") -> None:
        super().__init__(message)


class LLMError(DocTalkError):
    """LLM 관련 예외."""

    def __init__(self, message: str = "LLM 응답 생성 중 오류가 발생했습니다.") -> None:
        super().__init__(message)


class VectorStoreError(DocTalkError):
    """벡터 저장소 관련 예외."""

    def __init__(self, message: str = "벡터 저장소 작업 중 오류가 발생했습니다.") -> None:
        super().__init__(message)
