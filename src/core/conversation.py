"""대화 관리 모듈."""

import json
from pathlib import Path

from src.config import Settings
from src.models.message import Message, MessageRole, Source
from src.utils.logger import logger


class ConversationManager:
    """대화 히스토리 관리 클래스."""

    def __init__(self, settings: Settings) -> None:
        """초기화.

        Args:
            settings: 애플리케이션 설정
        """
        self.settings = settings
        self._history: list[Message] = []

    def add_message(
        self,
        role: MessageRole,
        content: str,
        sources: list[Source] | None = None,
    ) -> Message:
        """메시지 추가.

        Args:
            role: 메시지 역할
            content: 메시지 내용
            sources: 출처 목록 (선택)

        Returns:
            생성된 Message 객체
        """
        message = Message(
            role=role,
            content=content,
            sources=sources or [],
        )
        self._history.append(message)

        # 최대 히스토리 유지
        self._trim_history()

        return message

    def _trim_history(self) -> None:
        """히스토리 최대 개수 유지."""
        max_messages = self.settings.max_history * 2  # user + assistant 쌍
        if len(self._history) >= max_messages:
            # 가장 오래된 메시지부터 삭제 (시스템 메시지 제외)
            self._history = self._history[-max_messages:]

    def get_history(self) -> list[Message]:
        """전체 히스토리 반환.

        Returns:
            메시지 리스트 복사본
        """
        return self._history.copy()

    def get_chat_history_for_llm(self) -> list[tuple[str, str]]:
        """LLM에 전달할 형식의 대화 히스토리.

        Returns:
            (역할, 내용) 튜플 리스트
        """
        history = []
        for msg in self._history:
            if msg.role in (MessageRole.USER, MessageRole.ASSISTANT):
                history.append((msg.role.value, msg.content))
        return history

    def get_formatted_history(self) -> str:
        """문자열 형식의 대화 히스토리.

        Returns:
            포맷된 히스토리 문자열
        """
        formatted = []
        for msg in self._history:
            if msg.role == MessageRole.USER:
                formatted.append(f"사용자: {msg.content}")
            elif msg.role == MessageRole.ASSISTANT:
                formatted.append(f"어시스턴트: {msg.content}")
        return "\n".join(formatted)

    def clear(self) -> None:
        """히스토리 초기화."""
        self._history.clear()

    def get_last_message(self) -> Message | None:
        """마지막 메시지 반환.

        Returns:
            마지막 Message 또는 None
        """
        return self._history[-1] if self._history else None

    def __len__(self) -> int:
        """메시지 수 반환."""
        return len(self._history)

    def _get_save_path(self) -> Path:
        """저장 파일 경로 반환."""
        return self.settings.data_dir / "conversation.json"

    def save(self) -> None:
        """대화 히스토리를 파일에 저장."""
        save_path = self._get_save_path()
        try:
            data = [msg.model_dump(mode="json") for msg in self._history]
            save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            logger.info(f"대화 히스토리 저장 완료: {len(self._history)}개 메시지")
        except Exception as e:
            logger.error(f"대화 히스토리 저장 실패: {e}")

    def load(self) -> None:
        """파일에서 대화 히스토리 복원."""
        save_path = self._get_save_path()
        if not save_path.exists():
            logger.info("저장된 대화 히스토리 없음")
            return

        try:
            data = json.loads(save_path.read_text())
            self._history = [Message.model_validate(msg) for msg in data]
            logger.info(f"대화 히스토리 복원 완료: {len(self._history)}개 메시지")
        except Exception as e:
            logger.error(f"대화 히스토리 복원 실패: {e}")
            self._history = []
