"""헬퍼 함수."""

import hashlib
from typing import BinaryIO


def calculate_file_hash(file: BinaryIO) -> str:
    """파일 해시 계산 (SHA-256).

    Args:
        file: 파일 객체

    Returns:
        SHA-256 해시 문자열
    """
    sha256_hash = hashlib.sha256()
    file.seek(0)
    for chunk in iter(lambda: file.read(8192), b""):
        sha256_hash.update(chunk)
    file.seek(0)
    return sha256_hash.hexdigest()


def validate_pdf_file(
    file: BinaryIO,
    filename: str,
    max_size_mb: int,
) -> tuple[bool, str]:
    """PDF 파일 유효성 검증.

    Args:
        file: 파일 객체
        filename: 파일명
        max_size_mb: 최대 파일 크기 (MB)

    Returns:
        (유효 여부, 에러 메시지) 튜플
    """
    # 확장자 검증
    if not filename.lower().endswith(".pdf"):
        return False, "PDF 파일만 업로드 가능합니다."

    # 크기 검증
    file.seek(0, 2)  # 파일 끝으로 이동
    file_size = file.tell()
    file.seek(0)

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"파일 크기가 {max_size_mb}MB를 초과합니다."

    return True, ""
