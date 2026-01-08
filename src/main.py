"""doc-talk 메인 애플리케이션."""

import streamlit as st

from src.config import Settings, get_settings
from src.core.conversation import ConversationManager
from src.core.document_store import DocumentStore
from src.core.pdf_processor import PDFProcessor
from src.core.rag_engine import RAGEngine
from src.ui.chat import render_chat
from src.ui.sidebar import render_sidebar


def initialize_session_state(settings: Settings) -> None:
    """세션 상태 초기화.

    Args:
        settings: 애플리케이션 설정
    """
    if "document_store" not in st.session_state:
        st.session_state.document_store = DocumentStore(settings)

    if "conversation" not in st.session_state:
        st.session_state.conversation = ConversationManager(settings)

    if "pdf_processor" not in st.session_state:
        st.session_state.pdf_processor = PDFProcessor(settings)

    if "rag_engine" not in st.session_state:
        st.session_state.rag_engine = RAGEngine(
            settings=settings,
            document_store=st.session_state.document_store,
            conversation_manager=st.session_state.conversation,
        )


def main() -> None:
    """메인 함수."""
    # 페이지 설정
    st.set_page_config(
        page_title="doc-talk",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 설정 캐시 클리어 (환경변수 변경 반영)
    get_settings.cache_clear()

    # 설정 로드
    try:
        settings = get_settings()
    except Exception as e:
        st.error(f"설정 로드 실패: {e}")
        st.info("`.env` 파일에 `GROQ_API_KEY`가 설정되어 있는지 확인하세요.")
        st.stop()

    # 모델 설정 변경 시 세션 초기화
    if "current_model" not in st.session_state:
        st.session_state.current_model = settings.llm_model
    elif st.session_state.current_model != settings.llm_model:
        # 모델이 변경되면 RAG 엔진 재생성
        st.session_state.current_model = settings.llm_model
        if "rag_engine" in st.session_state:
            del st.session_state.rag_engine

    # 세션 상태 초기화
    initialize_session_state(settings)

    # 사이드바 렌더링
    render_sidebar(
        settings=settings,
        pdf_processor=st.session_state.pdf_processor,
        document_store=st.session_state.document_store,
    )

    # 채팅 인터페이스 렌더링
    render_chat(
        rag_engine=st.session_state.rag_engine,
        conversation=st.session_state.conversation,
    )


if __name__ == "__main__":
    main()
