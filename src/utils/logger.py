"""로깅 설정."""

import logging
import sys


def setup_logger(
    name: str = "doc-talk",
    level: int = logging.INFO,
    format_string: str | None = None,
) -> logging.Logger:
    """로거 설정.

    Args:
        name: 로거 이름
        level: 로그 레벨
        format_string: 로그 포맷 문자열

    Returns:
        설정된 로거 인스턴스
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# 기본 로거 인스턴스
logger = setup_logger()
