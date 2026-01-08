"""Streamlit 환경에서 LLM 직접 테스트."""

import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import get_settings

st.title("LLM 직접 테스트")

get_settings.cache_clear()
settings = get_settings()

st.write(f"**모델:** {settings.llm_model}")

context = """[문서 1] (출처: Anthropic Invoice2507.pdf, 페이지: 1)
Invoice number G6U94R2H0001
Date of issue July 4, 2025
Amount due S$275.23
Bill to: OTOZ LABS PTE. LTD."""

SYSTEM_PROMPT = f"""You are a document-based Q&A assistant.
ONLY use information from this document:
{context}

Rules:
1. ONLY answer based on the document above
2. Quote exact values from the document
3. Respond in Korean
4. Do NOT make up any information"""

if st.button("테스트 실행"):
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=0,
        max_tokens=500,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "결제 금액이 얼마야?"),
    ])

    chain = prompt | llm | StrOutputParser()

    st.write("**응답:**")
    response_area = st.empty()
    full_response = ""

    for chunk in chain.stream({}):
        full_response += chunk
        response_area.write(full_response)

    st.success("완료!")
