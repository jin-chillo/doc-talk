# TRD (Technical Requirements Document)
## doc-talk - 기술 설계 문서

---

## 1. 시스템 아키텍처

### 1.1 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ PDF      │  │ Chat     │  │ Document │  │ Conversation     │ │
│  │ Uploader │  │ Interface│  │ Manager  │  │ History          │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                      Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ PDF          │  │ RAG          │  │ Conversation           │ │
│  │ Processor    │  │ Engine       │  │ Manager                │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                      Infrastructure Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ LLM Provider │  │ Embedding    │  │ Vector Store           │ │
│  │ (Groq API)   │  │ (HuggingFace)│  │ (ChromaDB)             │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 데이터 흐름

```
PDF Upload → Text Extraction → Chunking → Embedding → Vector Store
                                                           ↓
User Query → Query Embedding → Similarity Search → Context Retrieval
                                                           ↓
                        Context + Query → LLM → Response + Sources
```

### 1.3 제약사항

- PDF 최대 파일 크기: **50MB**
- PDF 최대 페이지: **500페이지**

---

## 2. 기술 스택

### 2.1 핵심 기술

| 레이어 | 기술 | 선택 이유 |
|--------|------|----------|
| **UI** | Streamlit | 빠른 개발, Python 친화적, 무료 호스팅 |
| **LLM** | Groq API (Llama 3.3 70B) | 무료 티어, 초고속 추론, 한국어 지원 |
| **Embedding** | HuggingFace (BGE-M3) | 무료, 다국어 지원, 로컬 실행 |
| **Vector DB** | ChromaDB | 무료, 설치 간편, 메타데이터 지원 |
| **PDF 처리** | PyPDF + Unstructured | 안정적, 다양한 PDF 형식 지원 |
| **오케스트레이션** | LangChain | RAG 표준 프레임워크, 풍부한 문서 |

### 2.2 개발 환경

| 항목 | 버전/도구 |
|------|----------|
| Python | 3.11+ |
| 패키지 관리 | uv 또는 pip |
| 코드 포맷터 | Ruff |
| 타입 체크 | mypy |
| 테스트 | pytest |
| Git 훅 | pre-commit |

### 2.3 의존성 목록

```toml
# pyproject.toml (주요 의존성)
[project]
dependencies = [
    # Core
    "langchain>=0.3.0",
    "langchain-community>=0.3.0",
    "langchain-groq>=0.2.0",
    "langchain-huggingface>=0.1.0",
    "langchain-chroma>=0.1.0",

    # PDF Processing
    "pypdf>=4.0.0",
    "unstructured>=0.15.0",

    # Vector Store
    "chromadb>=0.5.0",

    # UI
    "streamlit>=1.40.0",

    # Utilities
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.8.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]
```

---

## 3. 모듈 설계

### 3.1 디렉토리 구조

```
doc-talk/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Streamlit 앱 진입점
│   ├── config.py               # 설정 관리
│   │
│   ├── core/                   # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── pdf_processor.py    # PDF 처리
│   │   ├── rag_engine.py       # RAG 파이프라인
│   │   ├── conversation.py     # 대화 관리
│   │   └── document_store.py   # 문서 저장소 관리
│   │
│   ├── models/                 # 데이터 모델
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
│   ├── PRD.md
│   └── TRD.md
│
├── .env.example                # 환경변수 예시
├── .gitignore
├── pyproject.toml
├── README.md
└── Makefile                    # 개발 명령어
```

### 3.2 핵심 클래스 설계

| 클래스 | 역할 | 주요 메서드 |
|--------|------|------------|
| `PDFProcessor` | PDF 문서 처리 | `load_pdf()`, `split_documents()`, `process()` |
| `RAGEngine` | RAG 파이프라인 | `add_documents()`, `query()`, `get_relevant_documents()` |
| `ConversationManager` | 대화 히스토리 관리 | `add_message()`, `get_history()`, `clear()` |

---

## 4. LLM 설정

LangChain의 `ChatGroq` 사용:
- **모델**: `llama-3.3-70b-versatile`
- **temperature**: 0.1
- **max_tokens**: 2048

---

## 5. 데이터 모델

Pydantic 기반 모델:

| 모델 | 필드 |
|------|------|
| `DocumentMetadata` | source, page, total_pages, created_at |
| `Document` | id, content, metadata |
| `Source` | document_name, page, content_preview |
| `Message` | role, content, sources, timestamp |

---

## 6. 설정 관리

`pydantic-settings`의 `BaseSettings` 사용, `.env` 파일에서 로드

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `GROQ_API_KEY` | (필수) | Groq API 키 |
| `EMBEDDING_MODEL` | BAAI/bge-m3 | 임베딩 모델 |
| `LLM_MODEL` | llama-3.3-70b-versatile | LLM 모델 |
| `CHUNK_SIZE` | 1000 | 청크 크기 |
| `CHUNK_OVERLAP` | 200 | 청크 오버랩 |
| `MAX_HISTORY` | 10 | 최대 대화 히스토리 |

---

## 7. 프롬프트 설계

### 시스템 프롬프트 핵심 규칙
- 문서 컨텍스트 기반 답변
- 문서에 없는 내용은 "찾을 수 없습니다" 응답
- 한국어 자연스러운 답변

### RAG 프롬프트 구조
`{context}` + `{chat_history}` + `{question}` → LLM → 답변

---

## 8. 에러 처리

### 커스텀 예외 클래스
`DocTalkError` (기본) → `PDFProcessingError`, `EmbeddingError`, `LLMError`, `VectorStoreError`

### 에러 핸들링 전략
| 에러 유형 | 사용자 메시지 |
|----------|--------------|
| PDF 파싱 실패 | "PDF 파일을 읽을 수 없습니다" |
| API 한도 초과 | "일일 사용량을 초과했습니다" |
| 문서 없음 | "먼저 PDF 문서를 업로드해주세요" |

---

## 9. 테스트 전략

| 레벨 | 대상 | 커버리지 목표 |
|------|------|--------------|
| Unit | core/ 모듈 | 70% |
| Integration | RAG 파이프라인 | 50% |
| E2E | 주요 사용자 흐름 | 수동 테스트 |

---

## 10. 배포

- **로컬**: `streamlit run src/main.py`
- **향후 옵션**: Streamlit Cloud, HuggingFace Spaces, Railway

---

## 11. 성능 최적화

| 항목 | 전략 |
|------|------|
| 임베딩 | `@st.cache_resource` - 모델 1회 로드 |
| PDF 처리 | `@st.cache_data` - 해시 기반 중복 체크 |
| 벡터 검색 | k값 조정 (기본 4) |
| LLM 호출 | 스트리밍 응답 |

---

## 12. 보안 고려사항

| 항목 | 대책 |
|------|------|
| API 키 | .env 파일, gitignore 처리 |
| 업로드 파일 | 확장자/크기 검증 |
| 사용자 입력 | 프롬프트 인젝션 기본 방지 |

---

## 13. 개발 워크플로우

- **Makefile**: install, dev, test, lint, format
- **Git 브랜치**: `main` → `develop` → `feature/*`

---

## 14. 참고 자료

- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Groq API Documentation](https://console.groq.com/docs)
- [BGE-M3 Model Card](https://huggingface.co/BAAI/bge-m3)
