"""설정 관리 모듈."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    groq_api_key: str

    # Model Settings
    embedding_model: str = "BAAI/bge-m3"
    llm_model: str = "llama-3.1-8b-instant"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 2048

    # Chunking Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # RAG Settings
    retrieval_k: int = 4
    max_history: int = 10
    max_question_length: int = 2000  # 프롬프트 인젝션 방지 및 토큰 제한

    # File Constraints
    max_file_size_mb: int = 50
    max_pages: int = 500

    # Paths
    data_dir: Path = Path("data")
    uploads_dir: Path = Path("data/uploads")
    chroma_dir: Path = Path("data/chroma_db")

    def model_post_init(self, __context: object) -> None:
        """초기화 후 디렉토리 생성."""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """설정 인스턴스 반환 (싱글톤 패턴).

    Note: pydantic-settings가 런타임에 .env에서 자동으로 인자를 로드함
    """
    return Settings()  # type: ignore[call-arg]
