# doc-talk

PDF 문서를 업로드하고 자연어로 질문하면 문서 내용을 기반으로 답변하는 RAG(Retrieval-Augmented Generation) 기반 채팅 어시스턴트입니다.

## 주요 기능

- **PDF 업로드**: 단일/다중 PDF 파일 업로드 및 자동 처리
- **질의응답 (Q&A)**: 한국어/영어 지원, 스트리밍 응답
- **출처 표시**: 페이지 번호와 원문 인용 제공
- **대화 히스토리**: 최근 10개 대화 컨텍스트 유지
- **다중 문서 관리**: 문서 목록, 선택/해제, 삭제 기능

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 언어 | Python 3.11+ |
| UI | Streamlit |
| LLM | Groq API (Llama 3.3 70B) |
| Embedding | HuggingFace (BGE-M3) |
| Vector DB | ChromaDB |
| 오케스트레이션 | LangChain |

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/jin-chillo/doc-talk.git
cd doc-talk
```

### 2. 의존성 설치

```bash
# 개발 의존성 포함
make install
# 또는
pip install -e ".[dev]"
```

### 3. 환경 변수 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집하여 Groq API 키 설정
# GROQ_API_KEY=your_groq_api_key_here
```

Groq API 키는 [https://console.groq.com](https://console.groq.com)에서 무료로 발급받을 수 있습니다.

### 4. 실행

```bash
make dev
# 또는
streamlit run src/main.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

## 사용법

1. **문서 업로드**: 사이드바에서 PDF 파일을 업로드합니다
2. **문서 선택**: 체크박스로 검색에 사용할 문서를 선택합니다
3. **질문 입력**: 채팅창에 질문을 입력합니다
4. **답변 확인**: AI가 문서 내용을 기반으로 답변하고 출처를 표시합니다

## 개발

```bash
# 테스트 실행
make test

# 린트 검사
make lint

# 코드 포맷팅
make format

# 캐시 정리
make clean
```

## 프로젝트 구조

```
doc-talk/
├── src/
│   ├── main.py                 # Streamlit 앱 진입점
│   ├── config.py               # 설정 관리
│   ├── core/                   # 핵심 비즈니스 로직
│   │   ├── pdf_processor.py    # PDF 처리
│   │   ├── rag_engine.py       # RAG 파이프라인
│   │   ├── conversation.py     # 대화 관리
│   │   └── document_store.py   # 벡터 저장소
│   ├── models/                 # Pydantic 데이터 모델
│   ├── ui/                     # UI 컴포넌트
│   └── utils/                  # 유틸리티
├── tests/                      # 테스트
├── data/                       # 데이터 (uploads, chroma_db)
├── docs/                       # 문서 (PRD, TRD)
└── pyproject.toml
```

## 환경 변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `GROQ_API_KEY` | O | - | Groq API 키 |
| `EMBEDDING_MODEL` | X | BAAI/bge-m3 | 임베딩 모델 |
| `LLM_MODEL` | X | llama-3.3-70b-versatile | LLM 모델 |
| `CHUNK_SIZE` | X | 1000 | 청크 크기 |
| `CHUNK_OVERLAP` | X | 200 | 청크 오버랩 |
| `MAX_HISTORY` | X | 10 | 최대 대화 히스토리 |

## 제약 사항

- PDF 최대 파일 크기: 50MB
- PDF 최대 페이지: 500페이지
- 동시 사용자: 1명 (로컬 실행 기준)

## 라이선스

MIT
