"""공통 UI 컴포넌트."""

import streamlit as st

from src.models.message import Source


def display_sources(sources: list[Source]) -> None:
    """출처 표시 컴포넌트.

    Args:
        sources: 출처 목록
    """
    if not sources:
        return

    with st.expander("출처 보기", expanded=False):
        for i, source in enumerate(sources, 1):
            st.markdown(
                f"""
**출처 {i}**: {source.document_name} (페이지 {source.page})
> {source.content_preview}
"""
            )
            if i < len(sources):
                st.divider()


def display_error(message: str) -> None:
    """에러 메시지 표시.

    Args:
        message: 에러 메시지
    """
    st.error(message)


def display_success(message: str) -> None:
    """성공 메시지 표시.

    Args:
        message: 성공 메시지
    """
    st.success(message)


def display_warning(message: str) -> None:
    """경고 메시지 표시.

    Args:
        message: 경고 메시지
    """
    st.warning(message)
