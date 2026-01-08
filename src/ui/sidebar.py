"""사이드바 UI 컴포넌트."""

import html
from typing import TYPE_CHECKING

import streamlit as st

from src.core.document_store import DocumentStore
from src.core.pdf_processor import PDFProcessor
from src.ui.components import display_error, display_success, display_warning
from src.utils.exceptions import PDFProcessingError, VectorStoreError
from src.utils.helpers import calculate_file_hash
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.config import Settings


def render_sidebar(
    settings: "Settings",
    pdf_processor: PDFProcessor,
    document_store: DocumentStore,
) -> None:
    """사이드바 렌더링.

    Args:
        settings: 애플리케이션 설정
        pdf_processor: PDF 처리기
        document_store: 문서 저장소
    """
    with st.sidebar:
        st.title("문서 관리")

        # PDF 업로드 섹션
        render_upload_section(settings, pdf_processor, document_store)

        st.divider()

        # 문서 목록 섹션
        render_document_list(document_store)


def render_upload_section(
    settings: "Settings",
    pdf_processor: PDFProcessor,
    document_store: DocumentStore,
) -> None:
    """PDF 업로드 섹션.

    Args:
        settings: 애플리케이션 설정
        pdf_processor: PDF 처리기
        document_store: 문서 저장소
    """
    st.subheader("PDF 업로드")

    uploaded_files = st.file_uploader(
        "PDF 파일을 선택하세요",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_uploader",
    )

    if uploaded_files:
        if st.button("업로드 처리", type="primary"):
            process_uploaded_files(uploaded_files, pdf_processor, document_store)


def process_uploaded_files(
    uploaded_files: list,
    pdf_processor: PDFProcessor,
    document_store: DocumentStore,
) -> None:
    """업로드된 파일 처리.

    Args:
        uploaded_files: 업로드된 파일 리스트
        pdf_processor: PDF 처리기
        document_store: 문서 저장소
    """
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_files = len(uploaded_files)
    success_count = 0

    for i, uploaded_file in enumerate(uploaded_files):
        filename = uploaded_file.name
        status_text.text(f"처리 중: {filename}")

        try:
            # 중복 체크
            file_hash = calculate_file_hash(uploaded_file)

            if document_store.is_duplicate(file_hash):
                display_warning(f"이미 등록된 문서입니다: {filename}")
                continue

            # PDF 처리
            chunks, processed_doc = pdf_processor.process(uploaded_file, filename)

            # 벡터 저장소에 추가
            document_store.add_documents(chunks, processed_doc)

            success_count += 1
            display_success(f"업로드 완료: {filename}")

        except PDFProcessingError as e:
            display_error(f"{filename}: {e.message}")
        except VectorStoreError as e:
            display_error(f"{filename}: {e.message}")
        except Exception as e:
            logger.error(f"파일 처리 실패: {filename} - {e}")
            display_error(f"{filename}: 처리 중 오류가 발생했습니다.")

        progress_bar.progress((i + 1) / total_files)

    status_text.text(f"완료: {success_count}/{total_files} 파일 처리됨")


def render_document_list(document_store: DocumentStore) -> None:
    """문서 목록 렌더링.

    Args:
        document_store: 문서 저장소
    """
    st.subheader("등록된 문서")

    documents = document_store.get_documents()

    if not documents:
        st.info("등록된 문서가 없습니다.")
        return

    for doc in documents:
        col1, col2, col3 = st.columns([0.1, 0.7, 0.2])

        with col1:
            # 활성화 체크박스
            is_active = st.checkbox(
                "",
                value=doc.is_active,
                key=f"active_{doc.id}",
                label_visibility="collapsed",
            )
            if is_active != doc.is_active:
                document_store.toggle_document_active(doc.id)
                st.rerun()

        with col2:
            status_icon = "[v]" if doc.is_active else "[ ]"
            st.markdown(f"{status_icon} **{html.escape(doc.filename)}**")
            st.caption(f"{doc.total_pages}페이지 | {doc.chunk_count}청크")

        with col3:
            if st.button("삭제", key=f"delete_{doc.id}"):
                try:
                    document_store.remove_document(doc.id)
                    display_success(f"삭제됨: {doc.filename}")
                    st.rerun()
                except VectorStoreError as e:
                    display_error(e.message)
