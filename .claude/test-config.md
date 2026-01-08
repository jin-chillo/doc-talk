# pytest 테스트 설정

## 적용 대상

- Python 프로젝트 전체
- FastAPI, Django, Flask

---

## 설치

```bash
# Poetry
poetry add -D pytest pytest-cov pytest-asyncio pytest-mock httpx

# pip
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx
```

---

## 설정 파일

### pyproject.toml

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 80
show_missing = true
```

### conftest.py

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.main import app
from src.db.base import Base

# 테스트 DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

---

## 테스트 작성 예시

### 단위 테스트

```python
import pytest
from src.services.user import UserService

class TestUserService:
    def test_create_user(self, mocker):
        # Arrange
        mock_repo = mocker.Mock()
        mock_repo.create.return_value = {"id": 1, "name": "John"}
        service = UserService(mock_repo)

        # Act
        result = service.create(name="John", email="john@example.com")

        # Assert
        assert result["name"] == "John"
        mock_repo.create.assert_called_once()

    def test_create_user_invalid_email(self):
        service = UserService(mock_repo)

        with pytest.raises(ValueError, match="Invalid email"):
            service.create(name="John", email="invalid")
```

### 비동기 테스트

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_users(client: AsyncClient):
    response = await client.get("/api/v1/users")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    payload = {
        "name": "John",
        "email": "john@example.com",
        "password": "password123"
    }

    response = await client.post("/api/v1/users", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John"
    assert "password" not in data
```

### 파라미터화 테스트

```python
import pytest

@pytest.mark.parametrize("email,is_valid", [
    ("user@example.com", True),
    ("user@domain.co.kr", True),
    ("invalid", False),
    ("@example.com", False),
    ("user@", False),
])
def test_validate_email(email: str, is_valid: bool):
    result = validate_email(email)
    assert result == is_valid
```

### Fixture 사용

```python
import pytest

@pytest.fixture
def sample_user():
    return {
        "id": 1,
        "name": "John",
        "email": "john@example.com"
    }

@pytest.fixture
def admin_user(sample_user):
    return {**sample_user, "role": "admin"}

def test_user_permissions(admin_user):
    assert admin_user["role"] == "admin"
```

---

## 명령어

```bash
pytest                           # 전체 테스트
pytest tests/unit/               # 특정 디렉토리
pytest -k "test_create"          # 이름으로 필터
pytest -m unit                   # 마커로 필터
pytest --cov=src                 # 커버리지
pytest --cov=src --cov-report=html  # HTML 리포트
pytest -x                        # 첫 실패시 중단
pytest --lf                      # 마지막 실패 테스트만
```

---

## 디렉토리 구조

```
tests/
├── conftest.py          # 공통 fixture
├── unit/                # 단위 테스트
│   ├── __init__.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/         # 통합 테스트
│   ├── __init__.py
│   └── test_api.py
└── e2e/                 # E2E 테스트
    └── test_workflows.py
```
