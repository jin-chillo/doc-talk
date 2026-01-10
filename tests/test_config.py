"""config.py 테스트."""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


class TestSettings:
    """Settings 클래스 테스트."""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """기본값이 올바르게 설정되는지 테스트."""
        # 환경 변수를 모두 제거하여 .env 파일 영향을 차단
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        monkeypatch.delenv("RETRIEVAL_K", raising=False)
        monkeypatch.delenv("MAX_HISTORY", raising=False)
        monkeypatch.delenv("CHUNK_SIZE", raising=False)
        monkeypatch.delenv("CHUNK_OVERLAP", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # 빈 .env 파일 생성하여 프로젝트 루트의 .env 파일 무효화
            env_file = tmppath / ".env"
            env_file.write_text("")
            monkeypatch.chdir(tmppath)

            settings = Settings(
                groq_api_key="test-key-12345",
                data_dir=tmppath,
                uploads_dir=tmppath / "uploads",
                chroma_dir=tmppath / "chroma_db",
            )

            # API Keys
            assert settings.groq_api_key == "test-key-12345"

            # Model Settings
            assert settings.embedding_model == "BAAI/bge-m3"
            assert settings.llm_model == "llama-3.1-8b-instant"
            assert settings.llm_temperature == 0.0
            assert settings.llm_max_tokens == 2048

            # Chunking Settings
            assert settings.chunk_size == 1000
            assert settings.chunk_overlap == 200

            # RAG Settings
            assert settings.retrieval_k == 4
            assert settings.max_history == 10
            assert settings.max_question_length == 2000

            # File Constraints
            assert settings.max_file_size_mb == 50
            assert settings.max_pages == 500

    def test_custom_values_override_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """커스텀 값이 기본값을 오버라이드하는지 테스트."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # 빈 .env 파일 생성
            env_file = tmppath / ".env"
            env_file.write_text("")
            monkeypatch.chdir(tmppath)

            settings = Settings(
                groq_api_key="custom-api-key",
                embedding_model="custom-embedding-model",
                llm_model="custom-llm-model",
                llm_temperature=0.7,
                llm_max_tokens=4096,
                chunk_size=1500,
                chunk_overlap=300,
                retrieval_k=6,
                max_history=20,
                max_question_length=3000,
                max_file_size_mb=100,
                max_pages=1000,
                data_dir=tmppath,
                uploads_dir=tmppath / "custom_uploads",
                chroma_dir=tmppath / "custom_chroma",
            )

            assert settings.groq_api_key == "custom-api-key"
            assert settings.embedding_model == "custom-embedding-model"
            assert settings.llm_model == "custom-llm-model"
            assert settings.llm_temperature == 0.7
            assert settings.llm_max_tokens == 4096
            assert settings.chunk_size == 1500
            assert settings.chunk_overlap == 300
            assert settings.retrieval_k == 6
            assert settings.max_history == 20
            assert settings.max_question_length == 3000
            assert settings.max_file_size_mb == 100
            assert settings.max_pages == 1000
            assert settings.uploads_dir == tmppath / "custom_uploads"
            assert settings.chroma_dir == tmppath / "custom_chroma"

    def test_directories_created_in_model_post_init(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """model_post_init에서 디렉토리가 생성되는지 테스트."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # 빈 .env 파일 생성
            env_file = tmppath / ".env"
            env_file.write_text("")
            monkeypatch.chdir(tmppath)

            uploads_path = tmppath / "uploads"
            chroma_path = tmppath / "chroma_db"

            # 디렉토리가 아직 존재하지 않는지 확인
            assert not uploads_path.exists()
            assert not chroma_path.exists()

            # Settings 생성 시 디렉토리가 자동으로 생성됨
            settings = Settings(
                groq_api_key="test-key",
                data_dir=tmppath,
                uploads_dir=uploads_path,
                chroma_dir=chroma_path,
            )

            # 디렉토리가 생성되었는지 확인
            assert settings.uploads_dir.exists()
            assert settings.chroma_dir.exists()
            assert settings.uploads_dir.is_dir()
            assert settings.chroma_dir.is_dir()

    def test_directories_already_exist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """디렉토리가 이미 존재할 때 에러가 발생하지 않는지 테스트."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # 빈 .env 파일 생성
            env_file = tmppath / ".env"
            env_file.write_text("")
            monkeypatch.chdir(tmppath)

            uploads_path = tmppath / "uploads"
            chroma_path = tmppath / "chroma_db"

            # 디렉토리를 미리 생성
            uploads_path.mkdir(parents=True, exist_ok=True)
            chroma_path.mkdir(parents=True, exist_ok=True)

            # Settings 생성 시 에러가 발생하지 않아야 함
            settings = Settings(
                groq_api_key="test-key",
                data_dir=tmppath,
                uploads_dir=uploads_path,
                chroma_dir=chroma_path,
            )

            assert settings.uploads_dir.exists()
            assert settings.chroma_dir.exists()

    def test_missing_groq_api_key_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GROQ_API_KEY가 없을 때 ValidationError가 발생하는지 테스트."""
        # 환경 변수 제거
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # 빈 .env 파일 생성
            env_file = tmppath / ".env"
            env_file.write_text("")
            monkeypatch.chdir(tmppath)

            with pytest.raises(ValidationError) as exc_info:
                Settings(
                    data_dir=tmppath,
                    uploads_dir=tmppath / "uploads",
                    chroma_dir=tmppath / "chroma_db",
                )

            # groq_api_key 필드에서 에러가 발생했는지 확인
            errors = exc_info.value.errors()
            assert len(errors) > 0
            assert any(error["loc"] == ("groq_api_key",) for error in errors)

    def test_env_file_loading(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """환경 변수 파일(.env)에서 값을 로드하는지 테스트."""
        # 환경 변수 제거
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        # .env 파일 생성
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GROQ_API_KEY=env-file-api-key\n"
            "EMBEDDING_MODEL=env-embedding-model\n"
            "LLM_MODEL=env-llm-model\n"
            "CHUNK_SIZE=1200\n"
        )

        # 현재 디렉토리를 tmp_path로 변경
        monkeypatch.chdir(tmp_path)

        settings = Settings(
            data_dir=tmp_path / "data",
            uploads_dir=tmp_path / "data/uploads",
            chroma_dir=tmp_path / "data/chroma_db",
        )

        assert settings.groq_api_key == "env-file-api-key"
        assert settings.embedding_model == "env-embedding-model"
        assert settings.llm_model == "env-llm-model"
        assert settings.chunk_size == 1200

    def test_path_types(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Path 타입이 올바르게 처리되는지 테스트."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # 빈 .env 파일 생성
            env_file = tmppath / ".env"
            env_file.write_text("")
            monkeypatch.chdir(tmppath)

            settings = Settings(
                groq_api_key="test-key",
                data_dir=tmppath,
                uploads_dir=tmppath / "uploads",
                chroma_dir=tmppath / "chroma_db",
            )

            assert isinstance(settings.data_dir, Path)
            assert isinstance(settings.uploads_dir, Path)
            assert isinstance(settings.chroma_dir, Path)

    def test_numeric_constraints(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """숫자 타입의 값들이 올바른 타입인지 테스트."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # 빈 .env 파일 생성
            env_file = tmppath / ".env"
            env_file.write_text("")
            monkeypatch.chdir(tmppath)

            settings = Settings(
                groq_api_key="test-key",
                data_dir=tmppath,
                uploads_dir=tmppath / "uploads",
                chroma_dir=tmppath / "chroma_db",
            )

            # Integer types
            assert isinstance(settings.chunk_size, int)
            assert isinstance(settings.chunk_overlap, int)
            assert isinstance(settings.retrieval_k, int)
            assert isinstance(settings.max_history, int)
            assert isinstance(settings.max_question_length, int)
            assert isinstance(settings.max_file_size_mb, int)
            assert isinstance(settings.max_pages, int)
            assert isinstance(settings.llm_max_tokens, int)

            # Float type
            assert isinstance(settings.llm_temperature, float)

            # Positive values
            assert settings.chunk_size > 0
            assert settings.chunk_overlap >= 0
            assert settings.retrieval_k > 0
            assert settings.max_history > 0
            assert settings.max_question_length > 0
            assert settings.max_file_size_mb > 0
            assert settings.max_pages > 0
            assert settings.llm_temperature >= 0


class TestGetSettings:
    """get_settings() 함수 테스트."""

    def test_returns_settings_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Settings 인스턴스를 반환하는지 테스트."""
        monkeypatch.setenv("GROQ_API_KEY", "test-key-from-env")

        # get_settings 캐시 초기화
        get_settings.cache_clear()

        with tempfile.TemporaryDirectory():
            settings = get_settings()
            assert isinstance(settings, Settings)
            assert settings.groq_api_key == "test-key-from-env"

    def test_caching_behavior(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """캐싱이 올바르게 동작하는지 테스트 (같은 인스턴스 반환)."""
        monkeypatch.setenv("GROQ_API_KEY", "test-key-cached")

        # get_settings 캐시 초기화
        get_settings.cache_clear()

        with tempfile.TemporaryDirectory():
            settings1 = get_settings()
            settings2 = get_settings()

            # 같은 인스턴스를 반환해야 함
            assert settings1 is settings2
            assert id(settings1) == id(settings2)

    def test_cache_clear_returns_new_instance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """캐시를 클리어하면 새로운 인스턴스를 반환하는지 테스트."""
        monkeypatch.setenv("GROQ_API_KEY", "test-key-new")

        with tempfile.TemporaryDirectory():
            # 첫 번째 인스턴스
            get_settings.cache_clear()
            settings1 = get_settings()

            # 캐시 클리어 후 두 번째 인스턴스
            get_settings.cache_clear()
            settings2 = get_settings()

            # 다른 인스턴스를 반환해야 함
            assert settings1 is not settings2
            assert id(settings1) != id(settings2)

    def test_settings_singleton_pattern(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """싱글톤 패턴이 올바르게 구현되었는지 테스트."""
        monkeypatch.setenv("GROQ_API_KEY", "singleton-test-key")

        get_settings.cache_clear()

        with tempfile.TemporaryDirectory():
            # 여러 번 호출해도 같은 인스턴스
            instances = [get_settings() for _ in range(5)]

            # 모든 인스턴스가 동일해야 함
            for instance in instances[1:]:
                assert instance is instances[0]

    def test_cache_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """lru_cache의 cache_info가 올바르게 동작하는지 테스트."""
        monkeypatch.setenv("GROQ_API_KEY", "cache-info-test-key")

        get_settings.cache_clear()

        with tempfile.TemporaryDirectory():
            # 초기 상태: hits=0, misses=0
            info = get_settings.cache_info()
            assert info.hits == 0
            assert info.misses == 0

            # 첫 호출: miss
            get_settings()
            info = get_settings.cache_info()
            assert info.misses == 1

            # 두 번째 호출: hit
            get_settings()
            info = get_settings.cache_info()
            assert info.hits == 1

            # 세 번째 호출: hit
            get_settings()
            info = get_settings.cache_info()
            assert info.hits == 2
