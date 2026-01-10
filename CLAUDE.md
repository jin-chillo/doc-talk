# doc-talk - Claude 작업 가이드

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **이름** | doc-talk |
| **설명** | PDF 문서를 업로드하고 자연어로 질문하면 문서 내용을 기반으로 답변하는 RAG 기반 채팅 어시스턴트 |
| **버전** | 1.0.0 |

---

## 기술 스택

| 레이어 | 기술 | 선택 이유 |
|--------|------|----------|
| **언어** | Python 3.11+ | 타입 힌트 필수 |
| **UI** | Streamlit | 빠른 개발, Python 친화적 |
| **LLM** | Groq API (Llama 3.1 8B) | 무료 티어, 초고속 추론, 한국어 지원 |
| **Embedding** | HuggingFace (BGE-M3) | 무료, 다국어 지원 |
| **Vector DB** | ChromaDB | 무료, 설치 간편, 메타데이터 지원 |
| **PDF 처리** | PyPDF + Unstructured | 안정적, 다양한 PDF 형식 지원 |
| **오케스트레이션** | LangChain | RAG 표준 프레임워크 |
| **패키지 관리** | uv / pip | |
| **린터/포맷터** | Ruff | |
| **타입 체크** | mypy | |
| **테스트** | pytest | |
| **Git 훅** | pre-commit | |

---

## 프로젝트 구조

```
doc-talk/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Streamlit 앱 진입점
│   ├── config.py               # 설정 관리 (pydantic-settings)
│   │
│   ├── core/                   # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── pdf_processor.py    # PDF 처리
│   │   ├── rag_engine.py       # RAG 파이프라인
│   │   ├── conversation.py     # 대화 관리
│   │   └── document_store.py   # 문서 저장소 관리
│   │
│   ├── models/                 # Pydantic 데이터 모델
│   │   ├── __init__.py
│   │   ├── document.py         # 문서 모델
│   │   ├── message.py          # 메시지 모델
│   │   └── source.py           # 출처 모델
│   │
│   ├── ui/                     # UI 컴포넌트
│   │   ├── __init__.py
│   │   ├── sidebar.py          # 사이드바 (문서 관리)
│   │   ├── chat.py             # 채팅 인터페이스
│   │   └── components.py       # 공통 컴포넌트
│   │
│   └── utils/                  # 유틸리티
│       ├── __init__.py
│       ├── logger.py           # 로깅
│       └── helpers.py          # 헬퍼 함수
│
├── tests/                      # 테스트
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_pdf_processor.py
│   ├── test_rag_engine.py
│   └── test_conversation.py
│
├── data/                       # 데이터 디렉토리
│   ├── uploads/                # 업로드된 PDF
│   └── chroma_db/              # 벡터 저장소
│
├── docs/                       # 문서
│   ├── PRD.md                  # 제품 요구사항
│   └── TRD.md                  # 기술 요구사항
│
├── .env.example                # 환경변수 예시
├── .gitignore
├── pyproject.toml
├── README.md
└── Makefile                    # 개발 명령어
```

---

## 명령어

```bash
# 의존성 설치
make install
# 또는
pip install -e ".[dev]"

# 개발 서버 실행
make dev
# 또는
streamlit run src/main.py

# 테스트 실행
make test
# 또는
pytest tests/ -v --cov=src

# 린트 검사
make lint
# 또는
ruff check src/ tests/
mypy src/

# 코드 포맷팅
make format
# 또는
ruff format src/ tests/
```

---

## 코딩 컨벤션

### 필수 규칙
- 모든 함수에 **타입 힌트** 필수
- **Docstring** 작성 (핵심 함수/클래스)
- **Pydantic** 모델로 데이터 검증
- 설정은 `pydantic-settings`의 `BaseSettings` 사용

### 금지 패턴
- 타입 힌트 없는 함수
- `except:` (bare except)
- 전역 상태 사용
- 문서에 없는 내용 추측 응답

### 에러 처리 패턴
커스텀 예외 클래스 사용: `DocTalkError`, `PDFProcessingError`, `EmbeddingError`, `LLMError`, `VectorStoreError`

### 캐싱 패턴
- `@st.cache_resource`: 임베딩 모델 (앱 재시작까지 유지)
- `@st.cache_data`: PDF 처리 결과

---

## 테스트 및 품질

### 커버리지 목표
- **전체**: 50% 이상
- **core 모듈**: 70% 이상

### 품질 기준
- 린팅 에러 **0개**
- 비동기 테스트: pytest-asyncio

```bash
pytest --cov=src                 # 커버리지 포함
```

---

## 환경변수

```bash
# .env
GROQ_API_KEY=your_groq_api_key_here

# Optional
EMBEDDING_MODEL=BAAI/bge-m3
LLM_MODEL=llama-3.1-8b-instant
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_HISTORY=10
```

---

## 핵심 기능 요구사항

### P0 (필수)
1. **PDF 업로드 및 처리**: 단일/다중 PDF 업로드, 텍스트 추출 및 벡터화
2. **질의응답 (Q&A)**: 한국어/영어 지원, 3초 이내 첫 응답
3. **출처 표시**: 페이지 번호, 관련 원문 텍스트 인용
4. **대화 히스토리**: 최근 10개 대화 컨텍스트 유지
5. **다중 문서 관리**: 문서 목록, 선택/해제, 삭제

### P1 (선택)
- 답변 스트리밍 (타이핑 효과)
- 대화 내보내기 (마크다운/텍스트)
- 문서 요약

### 제약사항
- PDF 최대 파일 크기: **50MB**
- PDF 최대 페이지: **500페이지**

### 성능 요구사항
| 항목 | 목표 |
|------|------|
| PDF 처리 시간 | 10페이지당 5초 이내 |
| 첫 응답 시간 | 3초 이내 (스트리밍) |
| 동시 사용자 | 1명 (로컬 실행) |

---

## 범위 외 (v1.0 제외)

- 이미지/표 OCR 처리
- 사용자 인증/로그인
- 데이터베이스 영구 저장
- 모바일 UI 최적화
- 다국어 UI (한국어만)

---

## 보안 고려사항

| 항목 | 대책 |
|------|------|
| API 키 | `.env` 파일, `.gitignore` 처리 |
| 업로드 파일 | 확장자/크기 검증 |
| 사용자 입력 | 프롬프트 인젝션 기본 방지 |

---

## Git 브랜치 전략

`main` → `develop` → `feature/*`

---

## 참고 문서

- [PRD](docs/PRD.md) - 제품 요구사항
- [TRD](docs/TRD.md) - 기술 설계
- [LangChain RAG](https://python.langchain.com/docs/tutorials/rag/)
- [Groq API](https://console.groq.com/docs)
- [ChromaDB](https://docs.trychroma.com/)
- [Streamlit](https://docs.streamlit.io/)
