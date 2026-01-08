.PHONY: install dev test lint format clean help

# 기본 타겟
help:
	@echo "사용 가능한 명령어:"
	@echo "  make install  - 의존성 설치 (개발 포함)"
	@echo "  make dev      - 개발 서버 실행"
	@echo "  make test     - 테스트 실행"
	@echo "  make lint     - 린트 검사"
	@echo "  make format   - 코드 포맷팅"
	@echo "  make clean    - 캐시 파일 삭제"

# 의존성 설치
install:
	pip install -e ".[dev]"

# 개발 서버 실행
dev:
	streamlit run src/main.py

# 테스트 실행
test:
	pytest tests/ -v --cov=src --cov-report=term-missing

# 린트 검사
lint:
	ruff check src/ tests/
	mypy src/

# 코드 포맷팅
format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# 캐시 파일 삭제
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
