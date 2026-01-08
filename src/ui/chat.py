"""채팅 UI 컴포넌트."""

import streamlit as st

from src.core.conversation import ConversationManager
from src.core.rag_engine import RAGEngine
from src.models.message import MessageRole
from src.ui.components import display_error, display_sources
from src.utils.exceptions import LLMError
from src.utils.logger import logger


def render_chat(
    rag_engine: RAGEngine,
    conversation: ConversationManager,
) -> None:
    """채팅 인터페이스 렌더링.

    Args:
        rag_engine: RAG 엔진
        conversation: 대화 관리자
    """
    st.title("doc-talk")
    st.caption("PDF 문서 기반 AI 채팅 어시스턴트")

    # 대화 초기화 버튼
    col1, col2 = st.columns([0.85, 0.15])
    with col2:
        if st.button("초기화"):
            conversation.clear()
            st.rerun()

    # 채팅 히스토리 표시
    render_chat_history(conversation)

    # 입력 영역
    render_chat_input(rag_engine, conversation)


def render_chat_history(conversation: ConversationManager) -> None:
    """채팅 히스토리 렌더링.

    Args:
        conversation: 대화 관리자
    """
    messages = conversation.get_history()

    for message in messages:
        if message.role == MessageRole.USER:
            with st.chat_message("user"):
                st.markdown(message.content)
        elif message.role == MessageRole.ASSISTANT:
            with st.chat_message("assistant"):
                st.markdown(message.content)
                display_sources(message.sources)


def render_chat_input(
    rag_engine: RAGEngine,
    conversation: ConversationManager,
) -> None:
    """채팅 입력 렌더링.

    Args:
        rag_engine: RAG 엔진
        conversation: 대화 관리자
    """
    # 문서 존재 여부 확인
    has_documents = len(rag_engine.document_store.get_active_documents()) > 0

    if not has_documents:
        st.info("먼저 사이드바에서 PDF 문서를 업로드해주세요.")

    # 입력창
    if prompt := st.chat_input(
        "질문을 입력하세요...",
        disabled=not has_documents,
    ):
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(prompt)

        # 어시스턴트 응답
        with st.chat_message("assistant"):
            try:
                # 스트리밍 응답
                response_placeholder = st.empty()
                sources_placeholder = st.empty()

                full_response = ""
                final_sources: list = []

                for chunk, sources in rag_engine.query_stream(prompt):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                    final_sources = sources

                # 최종 응답
                response_placeholder.markdown(full_response)

                # 출처 표시
                with sources_placeholder:
                    display_sources(final_sources)

            except LLMError as e:
                display_error(e.message)
            except Exception as e:
                logger.error(f"채팅 응답 실패: {e}")
                display_error("응답 생성 중 오류가 발생했습니다.")
