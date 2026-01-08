"""대화 관리 테스트."""


from src.core.conversation import ConversationManager
from src.models.message import MessageRole, Source


class TestConversationManager:
    """ConversationManager 테스트 클래스."""

    def test_add_message(self, test_settings):
        """메시지 추가 테스트."""
        manager = ConversationManager(test_settings)

        message = manager.add_message(MessageRole.USER, "안녕하세요")

        assert message.role == MessageRole.USER
        assert message.content == "안녕하세요"
        assert len(manager) == 1

    def test_add_message_with_sources(self, test_settings):
        """출처 포함 메시지 추가."""
        manager = ConversationManager(test_settings)

        sources = [Source(document_name="test.pdf", page=1, content_preview="테스트")]
        message = manager.add_message(MessageRole.ASSISTANT, "답변입니다.", sources)

        assert len(message.sources) == 1
        assert message.sources[0].document_name == "test.pdf"

    def test_trim_history(self, test_settings):
        """히스토리 트림 테스트."""
        test_settings.max_history = 2
        manager = ConversationManager(test_settings)

        # 4쌍 = 8개 메시지 추가
        for i in range(4):
            manager.add_message(MessageRole.USER, f"질문 {i}")
            manager.add_message(MessageRole.ASSISTANT, f"답변 {i}")

        # max_history=2 이므로 4개만 유지
        assert len(manager) == 4

    def test_clear(self, test_settings):
        """히스토리 초기화."""
        manager = ConversationManager(test_settings)

        manager.add_message(MessageRole.USER, "테스트")
        manager.clear()

        assert len(manager) == 0

    def test_get_formatted_history(self, test_settings):
        """포맷된 히스토리."""
        manager = ConversationManager(test_settings)

        manager.add_message(MessageRole.USER, "질문입니다")
        manager.add_message(MessageRole.ASSISTANT, "답변입니다")

        formatted = manager.get_formatted_history()

        assert "사용자: 질문입니다" in formatted
        assert "어시스턴트: 답변입니다" in formatted

    def test_get_last_message(self, test_settings):
        """마지막 메시지 조회."""
        manager = ConversationManager(test_settings)

        manager.add_message(MessageRole.USER, "첫 번째")
        manager.add_message(MessageRole.USER, "두 번째")

        last = manager.get_last_message()

        assert last is not None
        assert last.content == "두 번째"

    def test_get_last_message_empty(self, test_settings):
        """빈 히스토리에서 마지막 메시지."""
        manager = ConversationManager(test_settings)

        assert manager.get_last_message() is None

    def test_get_chat_history_for_llm(self, test_settings):
        """LLM용 히스토리 포맷."""
        manager = ConversationManager(test_settings)

        manager.add_message(MessageRole.USER, "질문")
        manager.add_message(MessageRole.ASSISTANT, "답변")

        history = manager.get_chat_history_for_llm()

        assert len(history) == 2
        assert history[0] == ("user", "질문")
        assert history[1] == ("assistant", "답변")

    def test_get_history_returns_copy(self, test_settings):
        """히스토리 복사본 반환 확인."""
        manager = ConversationManager(test_settings)

        manager.add_message(MessageRole.USER, "테스트")
        history1 = manager.get_history()
        history2 = manager.get_history()

        assert history1 is not history2
        assert history1[0].content == history2[0].content
