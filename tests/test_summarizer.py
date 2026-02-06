"""ConversationSummarizer 단위 테스트."""

import pytest
from unittest.mock import MagicMock, patch

from core.summarizer import ConversationSummarizer
from config.settings import settings


@pytest.fixture
def summarizer():
    """Mock client가 있는 summarizer."""
    with patch("core.summarizer.Anthropic") as mock_cls:
        mock_client = mock_cls.return_value
        mock_response = MagicMock()
        text_block = MagicMock()
        text_block.text = "요약된 대화 내용입니다."
        mock_response.content = [text_block]
        mock_client.messages.create.return_value = mock_response

        s = ConversationSummarizer(api_key="test-key")
        yield s


class TestShouldSummarize:
    """should_summarize 테스트."""

    def test_short_history_no_summarize(self, summarizer):
        """짧은 대화 → 요약 불필요."""
        history = [{"role": "user", "content": f"msg {i}"} for i in range(3)]
        assert summarizer.should_summarize(history) is False

    def test_long_history_summarize(self, summarizer):
        """긴 대화 → 요약 필요."""
        threshold = settings.cost_optimization.summarize_after_messages
        history = [{"role": "user", "content": f"msg {i}"} for i in range(threshold + 5)]
        assert summarizer.should_summarize(history) is True

    def test_disabled_no_summarize(self, summarizer):
        """요약 비활성화."""
        original = settings.cost_optimization.conversation_summarization_enabled
        try:
            settings.cost_optimization.conversation_summarization_enabled = False
            history = [{"role": "user", "content": f"msg {i}"} for i in range(100)]
            assert summarizer.should_summarize(history) is False
        finally:
            settings.cost_optimization.conversation_summarization_enabled = original

    def test_exact_threshold(self, summarizer):
        """정확히 threshold인 경우 → 요약 불필요."""
        threshold = settings.cost_optimization.summarize_after_messages
        history = [{"role": "user", "content": f"msg {i}"} for i in range(threshold)]
        assert summarizer.should_summarize(history) is False


class TestSummarizeHistory:
    """summarize_history 테스트."""

    def test_short_history_returns_as_is(self, summarizer):
        """짧은 대화 → 그대로 반환."""
        history = [{"role": "user", "content": "hello"}]
        result = summarizer.summarize_history(history)
        assert result == history

    def test_long_history_summarized(self, summarizer):
        """긴 대화 → 요약 + 최근 메시지."""
        threshold = settings.cost_optimization.summarize_after_messages
        max_recent = settings.cost_optimization.max_recent_messages
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"메시지 {i}"}
            for i in range(threshold + 10)
        ]
        result = summarizer.summarize_history(history)
        # 요약(2) + 최근(max_recent)
        assert len(result) == 2 + max_recent
        assert "[이전 대화 요약]" in result[0]["content"]

    def test_summary_contains_recent_messages(self, summarizer):
        """최근 메시지 유지 확인."""
        threshold = settings.cost_optimization.summarize_after_messages
        max_recent = settings.cost_optimization.max_recent_messages
        history = [
            {"role": "user", "content": f"메시지 {i}"}
            for i in range(threshold + 10)
        ]
        result = summarizer.summarize_history(history)
        recent_contents = [m["content"] for m in result[2:]]
        # 마지막 메시지가 포함되어야 함
        last_msg = history[-1]["content"]
        assert last_msg in recent_contents


class TestGenerateSummary:
    """_generate_summary 테스트."""

    def test_generate_summary_calls_api(self, summarizer):
        """API 호출로 요약 생성."""
        messages = [
            {"role": "user", "content": "파이썬 알려줘"},
            {"role": "assistant", "content": "파이썬은 인터프리터 언어입니다."},
        ]
        result = summarizer._generate_summary(messages)
        assert result == "요약된 대화 내용입니다."
        summarizer.client.messages.create.assert_called_once()

    def test_generate_summary_api_failure_fallback(self, summarizer):
        """API 실패 시 simple_compress 폴백."""
        summarizer.client.messages.create.side_effect = Exception("API 오류")
        messages = [
            {"role": "user", "content": "이것은 충분히 긴 메시지입니다 테스트용"},
        ]
        result = summarizer._generate_summary(messages)
        assert "대화 주제:" in result

    def test_generate_summary_no_text_block(self, summarizer):
        """텍스트 블록 없는 응답."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(spec=[])]  # text attr 없음
        summarizer.client.messages.create.return_value = mock_response
        messages = [{"role": "user", "content": "test"}]
        result = summarizer._generate_summary(messages)
        assert "생성하지 못했습니다" in result


class TestFormatConversation:
    """_format_conversation 테스트."""

    def test_format_basic(self, summarizer):
        """기본 포맷팅."""
        messages = [
            {"role": "user", "content": "안녕"},
            {"role": "assistant", "content": "반갑습니다"},
        ]
        result = summarizer._format_conversation(messages)
        assert "사용자: 안녕" in result
        assert "AI: 반갑습니다" in result

    def test_format_long_content_truncated(self, summarizer):
        """긴 내용 자르기."""
        messages = [{"role": "user", "content": "a" * 1000}]
        result = summarizer._format_conversation(messages)
        assert "..." in result
        assert len(result) < 600

    def test_format_list_content(self, summarizer):
        """리스트 형태 콘텐츠 (tool use 등)."""
        text_item = MagicMock()
        text_item.text = "텍스트 파트"
        messages = [{"role": "assistant", "content": [text_item]}]
        result = summarizer._format_conversation(messages)
        assert "텍스트 파트" in result

    def test_format_list_content_dict(self, summarizer):
        """딕셔너리 형태 리스트 콘텐츠."""
        messages = [{"role": "assistant", "content": [{"type": "text", "text": "딕트 텍스트"}]}]
        result = summarizer._format_conversation(messages)
        assert "딕트 텍스트" in result


class TestSimpleCompress:
    """_simple_compress 테스트."""

    def test_simple_compress(self, summarizer):
        """간단한 압축."""
        messages = [
            {"role": "user", "content": "이것은 20자보다 긴 메시지입니다 테스트용입니다"},
            {"role": "assistant", "content": "이것도 20자보다 긴 응답입니다 테스트용입니다"},
        ]
        result = summarizer._simple_compress(messages)
        assert "대화 주제:" in result

    def test_simple_compress_short_messages_excluded(self, summarizer):
        """짧은 메시지 제외."""
        messages = [
            {"role": "user", "content": "짧음"},
            {"role": "user", "content": "이것은 충분히 긴 메시지입니다 테스트"},
        ]
        result = summarizer._simple_compress(messages)
        assert "짧음" not in result

    def test_simple_compress_max_5_topics(self, summarizer):
        """최대 5개 주제."""
        messages = [
            {"role": "user", "content": f"이것은 충분히 긴 메시지입니다 주제 {i}번입니다"} for i in range(10)
        ]
        result = summarizer._simple_compress(messages)
        # "대화 주제: " 이후 콤마 개수가 4 이하 (5개 항목)
        topics_part = result.replace("대화 주제: ", "")
        assert topics_part.count(",") <= 4


class TestEstimateTokenSavings:
    """estimate_token_savings 테스트."""

    def test_basic_savings(self, summarizer):
        """기본 절감량 계산."""
        original = [{"content": "a" * 400}] * 10  # 4000 chars → ~1000 tokens
        summarized = [{"content": "a" * 100}] * 3  # 300 chars → ~75 tokens
        result = summarizer.estimate_token_savings(original, summarized)
        assert result["original_tokens"] > result["summarized_tokens"]
        assert result["saved_tokens"] > 0
        assert result["savings_percent"] > 0

    def test_no_savings(self, summarizer):
        """절감 없음."""
        history = [{"content": "test"}]
        result = summarizer.estimate_token_savings(history, history)
        assert result["saved_tokens"] == 0
        assert result["savings_percent"] == 0

    def test_empty_original(self, summarizer):
        """빈 원본."""
        result = summarizer.estimate_token_savings([], [])
        assert result["original_tokens"] == 0
        assert result["savings_percent"] == 0
